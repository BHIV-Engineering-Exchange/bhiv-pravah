"""Runtime manager that composes orchestrator + service mesh."""

from __future__ import annotations

import logging
import signal
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from core import ServiceOrchestrator, get_service_mesh
from core.service_mesh import RetryPolicy

from .config_validator import (
    RuntimeManagerConfigError,
    validate_services_config,
    validate_startup_order,
)
from .discovery import find_unregistered_service_files
from . import state

logger = logging.getLogger(__name__)


class RuntimeManager:
    """Continuous runtime process manager with restart logic."""

    def __init__(self):
        self.orchestrator = ServiceOrchestrator()
        self.mesh = get_service_mesh()
        self.retry_policy = RetryPolicy(max_retries=5, initial_backoff_ms=1000, max_backoff_ms=10000)
        self.shutting_down = False
        self.started_at = time.time()
        self.restart_counts = defaultdict(int)
        self.last_restart_at = {}
        self.failure_windows = defaultdict(lambda: deque())
        self.crash_looping = set()
        self._shutdown_completed = False
        self._configure()

    def _configure(self) -> None:
        validate_services_config(self.orchestrator.services)
        validate_startup_order(self.orchestrator)
        repo_root = Path(__file__).resolve().parents[2]
        for service_file in find_unregistered_service_files(repo_root, self.orchestrator.services):
            logger.warning(
                "Discovered service file '%s' with no entry in config/services.yml — "
                "it will not be started automatically until registered.",
                service_file,
            )

    def _signal_handler(self, signum, _frame) -> None:
        logger.info("Received signal %s, starting graceful shutdown", signum)
        self._graceful_shutdown()

    def _register_signals(self) -> None:
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _graceful_shutdown(self) -> None:
        """Shutdown all child services and persist final state."""
        if self._shutdown_completed:
            return
        self.shutting_down = True
        state.write_status(self._status_payload())
        self.orchestrator._shutdown_all()
        state.write_status(self._status_payload())
        self._shutdown_completed = True

    def print_startup_plan(self) -> None:
        self.orchestrator.print_startup_plan()

    def get_startup_order(self):
        return self.orchestrator.get_startup_order()

    def start_services(self, wait_for_health: bool = True, health_check_timeout: int = 30) -> bool:
        return self.orchestrator.start_services(
            wait_for_health=wait_for_health, health_check_timeout=health_check_timeout
        )

    def _is_crash_looping(self, service_name: str) -> bool:
        now = time.time()
        window = self.failure_windows[service_name]
        while window and now - window[0] > 300:
            window.popleft()
        if len(window) >= 5:
            self.crash_looping.add(service_name)
            return True
        self.crash_looping.discard(service_name)
        return False

    def _attempt_restart(self, service_name: str) -> None:
        self.failure_windows[service_name].append(time.time())
        if self._is_crash_looping(service_name):
            logger.error("Service %s entered CRASH_LOOPING state", service_name)
            return

        attempt = self.restart_counts[service_name]
        backoff_ms = self.retry_policy.get_backoff_ms(attempt)
        time.sleep(backoff_ms / 1000.0)
        if self.orchestrator._start_service(service_name):
            self.restart_counts[service_name] += 1
            self.last_restart_at[service_name] = datetime.now(timezone.utc).isoformat()
            logger.warning("Service %s restarted successfully", service_name)
            self.orchestrator._wait_for_health(service_name, timeout=20)
        else:
            logger.error("Failed to restart service %s", service_name)

    def _status_payload(self) -> Dict:
        services = {}
        status = self.orchestrator.get_service_status()
        for service_name in self.orchestrator.services.keys():
            cfg = self.orchestrator.services.get(service_name, {})
            proc_status = status.get(service_name, {})
            running = proc_status.get("running", False)
            state_name = "healthy" if running and self.mesh.health_check(service_name) else "unhealthy"
            if service_name in self.crash_looping:
                state_name = "CRASH_LOOPING"
            services[service_name] = {
                "status": state_name,
                "pid": proc_status.get("pid"),
                "port": cfg.get("port"),
                "restarts": self.restart_counts[service_name],
                "last_restart_at": self.last_restart_at.get(service_name),
            }
        return {
            "services": services,
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "shutting_down": self.shutting_down,
        }

    def monitor_services(self, check_interval: int = 5) -> None:
        while not self.shutting_down:
            for service_name, process in list(self.orchestrator.processes.items()):
                if process and process.poll() is not None and not self.shutting_down:
                    self._attempt_restart(service_name)
            state.write_status(self._status_payload())
            self.orchestrator._print_service_summary()
            time.sleep(check_interval)

    def run(self, check_interval: int = 5) -> int:
        self._register_signals()
        if not self.start_services(wait_for_health=True, health_check_timeout=30):
            return 1
        try:
            self.monitor_services(check_interval=check_interval)
            return 0
        finally:
            self._graceful_shutdown()
