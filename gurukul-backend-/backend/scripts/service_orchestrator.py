"""
service_orchestrator.py — Gurukul Service Supervisor
=====================================================

Standalone Python supervisor that starts and keeps alive the core
Gurukul services.  Run this instead of (or alongside) start-all.bat
for fully automated recovery.

Services managed:
  Name               | Command
  -------------------|-------------------------------------------------------
  GurkulBackend      | uvicorn app.main:app --host 0.0.0.0 --port 3000
  VaaniEngine        | python start.py              (vaani-engine dir)
  VaaniEngine        | python start.py              (vaani-engine dir)
  BucketConsumer     | python scripts/start_bucket_consumer.py (backend)

Usage:
    cd Gurukul
    python backend/scripts/service_orchestrator.py

Flags:
    --no-frontend   Skip frontend npm dev servers (headless mode)
    --poll 30       Health check interval in seconds (default: 30)
"""

import argparse
import logging
import os
import subprocess
import sys
import time
import signal
import threading
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------
RUNTIME_EVENTS_FILE = "runtime_events.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Orchestrator")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def record_event(service: str, event_type: str, detail: str):
    """Record orchestrator event to runtime_events.json."""
    entry = {
        "source": "Orchestrator",
        "service": service,
        "event": event_type,
        "detail": detail[:200],
        "timestamp": datetime.now().isoformat(),
        "unix_time": time.time()
    }
    try:
        with open(os.path.join(BASE_DIR, RUNTIME_EVENTS_FILE), "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write to {RUNTIME_EVENTS_FILE}: {e}")

# ---------------------------------------------------------------------------
# Service definition
# ---------------------------------------------------------------------------

@dataclass
class ManagedService:
    name: str
    cmd: List[str]
    cwd: str
    health_url: Optional[str] = None
    restart_delay: int = 60              # Cooldown seconds (60-120 range)
    max_restarts: int = 3                # Strict limit
    depends_on: Optional[str] = None     # Name of service that must be healthy first
    restart_count: int = field(default=0, init=False)
    proc: Optional[subprocess.Popen] = field(default=None, init=False)
    _stop: bool = field(default=False, init=False)
    _last_restart: float = field(default=0.0, init=False)

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        if self.restart_count >= self.max_restarts:
            logger.critical(f"[{self.name}] Max restarts ({self.max_restarts}) reached. Manual intervention required.")
            record_event(self.name, "TERMINATED", "Max restarts reached")
            return False

        logger.info(f"[{self.name}] Starting: {' '.join(self.cmd)}")
        record_event(self.name, "STARTING", f"Attempt #{self.restart_count + 1}")
        try:
            self.proc = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
            )
            self._last_restart = time.time()
            return True
        except Exception as exc:
            logger.error(f"[{self.name}] Failed to start: {exc}")
            record_event(self.name, "START_FAILED", str(exc))
            return False

    def stop(self):
        self._stop = True
        if self.proc and self.proc.poll() is None:
            logger.info(f"[{self.name}] Stopping...")
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except:
                self.proc.kill()
            record_event(self.name, "STOPPED", "Graceful shutdown")

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ServiceOrchestrator:
    def __init__(self, poll_interval: int = 30, include_frontend: bool = True):
        self._poll = poll_interval
        self._stop_event = threading.Event()
        self._services: List[ManagedService] = self._build_service_list(include_frontend)

    def _build_service_list(self, include_frontend: bool) -> List[ManagedService]:
        python = sys.executable
        services = [
            ManagedService(
                name="VaaniEngine",
                cmd=[python, "voice_service_api.py"],
                cwd=os.path.join(BASE_DIR, "vaani-engine"),
                health_url="http://localhost:8008/health",
            ),
            ManagedService(
                name="GurkulBackend",
                cmd=[python, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"],
                cwd=os.path.join(BASE_DIR, "backend"),
                health_url="http://localhost:3000/system/health",
                depends_on="VaaniEngine"
            ),
            ManagedService(
                name="BucketConsumer",
                cmd=[python, "scripts/start_bucket_consumer.py"],
                cwd=os.path.join(BASE_DIR, "backend"),
                depends_on="GurkulBackend"
            ),
        ]
        if include_frontend:
            services += [
                ManagedService(name="GurkulFrontend", cmd=["npm", "run", "dev"], cwd=os.path.join(BASE_DIR, "Frontend")),
                ManagedService(name="EMSFrontend", cmd=["npm", "run", "dev"], cwd=os.path.join(BASE_DIR, "EMS-System", "frontend")),
            ]
        return services

    def start_all(self):
        logger.info("=== Gurukul Orchestrator: Deterministic Startup Sequence ===")
        record_event("System", "ORCHESTRATION_START", "Initiating service sequence")
        
        for svc in self._services:
            # Check dependency
            if svc.depends_on:
                logger.info(f"[{svc.name}] Waiting for dependency: {svc.depends_on}")
                while not self._is_service_healthy(svc.depends_on) and not self._stop_event.is_set():
                    time.sleep(5)

            if self._stop_event.is_set(): break
            
            if svc.start():
                time.sleep(5) # Give it a moment to bind ports
                threading.Thread(target=self._drain_output, args=(svc,), daemon=True).start()

    def _is_service_healthy(self, name: str) -> bool:
        svc = next((s for s in self._services if s.name == name), None)
        if not svc or not svc.is_alive(): return False
        if not svc.health_url: return True # Assume alive if proc is up
        try:
            import requests
            r = requests.get(svc.health_url, timeout=2)
            return r.status_code == 200
        except:
            return False

    def _drain_output(self, service: ManagedService):
        if service.proc and service.proc.stdout:
            for line in service.proc.stdout:
                logger.info(f"  [{service.name}] {line.rstrip()}")

    def run(self):
        self.start_all()
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

        try:
            while not self._stop_event.is_set():
                self._check_and_recover()
                self._stop_event.wait(timeout=self._poll)
        finally:
            self.stop_all()

    def _check_and_recover(self):
        for svc in self._services:
            if svc._stop: continue
            if not svc.is_alive():
                now = time.time()
                if now - svc._last_restart < svc.restart_delay:
                    continue # In cooldown

                logger.warning(f"[{svc.name}] Dead. Attempting recovery...")
                svc.restart_count += 1
                if svc.start():
                    threading.Thread(target=self._drain_output, args=(svc,), daemon=True).start()

    def stop_all(self):
        logger.info("=== Gurukul Orchestrator: Shutdown ===")
        for svc in reversed(self._services):
            svc.stop()

    def _handle_exit(self, signum, frame):
        self._stop_event.set()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-frontend", action="store_true")
    parser.add_argument("--poll", type=int, default=30)
    args = parser.parse_args()

    orch = ServiceOrchestrator(poll_interval=args.poll, include_frontend=not args.no_frontend)
    orch.run()
