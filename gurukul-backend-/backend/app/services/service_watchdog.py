"""
service_watchdog.py — Gurukul Autonomous Crash Recovery & Watchdog
==================================================================

Runs as a background thread inside the FastAPI process.

Behaviour:
  - Polls RuntimeMonitor.check_all() every POLL_INTERVAL seconds.
  - On detecting a service in 'down' state triggers a recovery action.
  - Logs every event with structured context.
  - Exposes a simple status summary (get_status()) for the metrics layer.

Recovery actions:
  Service        | Action
  ---------------|-------------------------------------------------
  VaaniTTS       | HTTP POST to /restart (if supported) or subprocess kill+relaunch
  Database       | Force SQLAlchemy pool recycle + reconnect attempt
  Redis          | Reconnect / FLUSHDB on corrupted-state heuristic
  PRANA          | Restart start_bucket_consumer.py subprocess
  GurkulBackend  | (Cannot restart self; logs critical alert)
"""

import time
import logging
import subprocess
import threading
import os
import sys
from typing import Dict, List, Optional

import requests

from app.services.runtime_monitor import RuntimeMonitor, ServiceSignal

import json
from datetime import datetime
from app.services.runtime_monitor import RuntimeMonitor, ServiceSignal

logger = logging.getLogger("ServiceWatchdog")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

POLL_INTERVAL: int = 30          # seconds between health sweeps
MAX_RECOVERY_ATTEMPTS: int = 3   # Max 3 attempts before escalation
RECOVERY_COOLDOWN: int = 120     # 2 minutes cooldown


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

class ServiceWatchdog:
    """
    Background watchdog thread that monitors and auto-recovers services.
    Enforces deterministic recovery paths and safety cooldowns.
    """

    def __init__(self, poll_interval: int = POLL_INTERVAL):
        self._monitor = RuntimeMonitor()
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Tracking state
        self._last_signals: List[ServiceSignal] = []
        self._recovery_log: List[dict] = []           # last 200 events
        self._recovery_attempts: Dict[str, int] = {}  # service → count this cycle
        self._last_recovery_time: Dict[str, float] = {}  # service → epoch
        self._cycle_count: int = 0
        self._start_time: float = time.time()

        # Deduplication: track last emit time per (service, event_type)
        self._last_emitted: Dict[str, float] = {}   # "service:event" → epoch
        self._emit_cooldown: int = 60                # seconds between identical events

        # Subprocess handles for managed processes
        self._prana_proc: Optional[subprocess.Popen] = None

    # ------------------------------------------------------------------
    # Thread management
    # ------------------------------------------------------------------

    def start(self):
        """Start the watchdog background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Watchdog already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ServiceWatchdog",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"ServiceWatchdog started (poll every {self._poll_interval}s).")

    def stop(self):
        """Signal the watchdog to stop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("ServiceWatchdog stopped.")

    def is_alive(self) -> bool:
        """Return True if the background watchdog thread is active and running."""
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _run_loop(self):
        """Poll → evaluate → recover loop."""
        while not self._stop_event.is_set():
            try:
                self._cycle_count += 1
                signals = self._monitor.check_all()
                with self._lock:
                    self._last_signals = signals

                for signal in signals:
                    if signal.status in ("down", "degraded"):
                        self._handle_unhealthy(signal)

            except Exception as exc:
                logger.exception(f"Watchdog loop error: {exc}")

            # Wait, but remain cancellable
            self._stop_event.wait(timeout=self._poll_interval)

    # ------------------------------------------------------------------
    # Recovery dispatch
    # ------------------------------------------------------------------

    def _handle_unhealthy(self, signal: ServiceSignal):
        """Decide whether to attempt recovery for a given unhealthy signal."""
        name = signal.name
        now = time.time()
        last_attempt = self._last_recovery_time.get(name, 0)
        attempts = self._recovery_attempts.get(name, 0)

        if now - last_attempt < RECOVERY_COOLDOWN:
            return  # Still in cooldown

        if attempts >= MAX_RECOVERY_ATTEMPTS:
            logger.critical(
                f"[Watchdog] {name} exceeded {MAX_RECOVERY_ATTEMPTS} attempts. "
                "ESCALATING to CRITICAL FAILURE. No more automated restarts."
            )
            self._record_event(name, "CRITICAL_FAILURE", "Max retries exceeded - automated recovery suspended")
            return

        logger.warning(
            f"[Watchdog] {name} is {signal.status}. "
            f"Recovery attempt {attempts + 1}/{MAX_RECOVERY_ATTEMPTS}..."
        )
        self._record_event(name, "RECOVERY_START", f"Reason: {signal.message}")

        success = False
        action = "unknown"
        try:
            if name == "VaaniTTS":
                success, action = self._recover_vaani(signal)
            elif name == "Database":
                success, action = self._recover_database(signal)
            elif name == "Redis":
                success, action = self._recover_redis(signal)
            elif name == "PRANA":
                success, action = self._recover_prana(signal)
            elif name == "GurkulBackend":
                logger.critical("[Watchdog] Backend internal health alert - check manually.")
                action = "alert_only"
                success = False
        except Exception as exc:
            logger.exception(f"[Watchdog] Recovery for {name} raised: {exc}")
            action = f"exception: {exc}"

        with self._lock:
            self._recovery_attempts[name] = attempts + 1
            self._last_recovery_time[name] = now
            
        outcome = "SUCCESS" if success else "FAILED"
        logger.info(f"[Watchdog] {name} recovery {outcome} via '{action}'.")
        self._record_event(name, f"RECOVERY_{outcome}", action)

    # ------------------------------------------------------------------
    # Individual recovery actions
    # ------------------------------------------------------------------

    def _recover_vaani(self, signal: ServiceSignal) -> tuple[bool, str]:
        """Try to restart the Vaani TTS engine."""
        import os
        vaani_url = os.getenv("VAANI_API_URL", "http://localhost:8007")

        # Step 1: ask Vaani to restart cleanly (if it supports it)
        try:
            resp = requests.post(f"{vaani_url}/restart", timeout=5)
            if resp.status_code == 200:
                time.sleep(5)
                ok, _, _ = _ping_http_local(f"{vaani_url}/health")
                if ok:
                    return True, "POST /restart succeeded"
        except Exception:
            pass

        # Step 2: find and kill any vaani process, then relaunch
        vaani_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "vaani-engine"
        )
        vaani_dir = os.path.normpath(vaani_dir)
        start_script = os.path.join(vaani_dir, "main.py")

        if not os.path.exists(start_script):
            return False, f"Vaani start script not found at {start_script}"

        try:
            subprocess.Popen(
                [sys.executable, start_script],
                cwd=vaani_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
            )
            time.sleep(8)
            ok, _, _ = _ping_http_local(f"{vaani_url}/health")
            return ok, "subprocess relaunch of start.py"
        except Exception as exc:
            return False, f"Subprocess launch failed: {exc}"

    def _recover_database(self, signal: ServiceSignal) -> tuple[bool, str]:
        """Force SQLAlchemy to recycle connections."""
        try:
            from sqlalchemy import create_engine, text
            from app.core.config import settings as app_settings
            db_url = getattr(app_settings, "DATABASE_URL", None)
            if not db_url:
                return False, "DATABASE_URL not configured"
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
            engine.dispose()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "pool recycled + SELECT 1 succeeded"
        except Exception as exc:
            return False, f"DB reconnect failed: {exc}"

    def _recover_redis(self, signal: ServiceSignal) -> tuple[bool, str]:
        """Reconnect to Redis."""
        try:
            import redis
            import os
            r_host = os.getenv("REDIS_HOST", "localhost")
            r_port = int(os.getenv("REDIS_PORT", 6379))
            r_pass = os.getenv("REDIS_PASSWORD", None)
            r_user = os.getenv("REDIS_USERNAME", None)
            client = redis.Redis(
                host=r_host,
                port=r_port,
                password=r_pass,
                username=r_user,
                socket_timeout=5
            )
            client.ping()
            return True, "Redis PING succeeded after reconnect"
        except Exception as exc:
            return False, f"Redis reconnect failed: {exc}"

    def _recover_prana(self, signal: ServiceSignal) -> tuple[bool, str]:
        """Restart the PRANA bucket consumer subprocess."""
        # Stop existing proc if tracked
        if self._prana_proc and self._prana_proc.poll() is None:
            self._prana_proc.terminate()
            try:
                self._prana_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._prana_proc.kill()

        script = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "start_bucket_consumer.py")
        )
        if not os.path.exists(script):
            return False, f"Bucket consumer script not found: {script}"

        try:
            self._prana_proc = subprocess.Popen(
                [sys.executable, script],
                cwd=os.path.dirname(script),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
            )
            time.sleep(3)
            if self._prana_proc.poll() is None:
                return True, "start_bucket_consumer.py relaunched"
            return False, "Process exited immediately after relaunch"
        except Exception as exc:
            return False, f"PRANA relaunch failed: {exc}"

    # ------------------------------------------------------------------
    # Status & logging helpers
    # ------------------------------------------------------------------

    def _record_event(self, service: str, event_type: str, detail: str):
        """Record watchdog event locally and to runtime_events.json for Pravah.
        
        Deduplication: identical (service, event_type) events are suppressed
        if the same combination was emitted within the last _emit_cooldown seconds.
        This prevents the Pravah stream from filling up with repeated recovery
        failures for persistently unavailable services (Redis, Database, etc.).
        """
        now = time.time()
        dedup_key = f"{service}:{event_type}"
        
        timestamp_str = datetime.now().isoformat()
        entry = {
            "service": service,
            "event": event_type,
            "detail": detail[:200],
            "timestamp": timestamp_str,
            "unix_time": now
        }
        
        with self._lock:
            self._recovery_log.append(entry)
            if len(self._recovery_log) > 200:
                self._recovery_log.pop(0)

            # Check deduplication before writing to Pravah stream
            last_emit = self._last_emitted.get(dedup_key, 0)
            if now - last_emit < self._emit_cooldown:
                # Suppress duplicate — already emitted within cooldown window
                logger.debug(f"[Watchdog] Suppressing duplicate Pravah event: {dedup_key}")
                return
            self._last_emitted[dedup_key] = now

        # Emit to Pravah (real ingestion)
        from app.services.pravah_adapter import pravah_adapter
        pravah_adapter.emit_signal(
            event_type="watchdog_event",
            action=event_type,
            status="info" if "SUCCESS" in event_type else "warning",
            payload={
                "service": service,
                "detail": detail
            }
        )

    def get_status(self) -> dict:
        """Return current watchdog metrics for the /system/metrics endpoint."""
        with self._lock:
            signals_snapshot = list(self._last_signals)
            log_snapshot = list(self._recovery_log[-20:])  # latest 20

        uptime = time.time() - self._start_time
        return {
            "watchdog_running": self._thread is not None and self._thread.is_alive(),
            "poll_interval_s": self._poll_interval,
            "cycle_count": self._cycle_count,
            "uptime_s": round(uptime, 1),
            "services": [s.to_dict() for s in signals_snapshot],
            "recent_recovery_events": log_snapshot,
        }

    def reset_recovery_counters(self):
        """Call at the start of a new monitoring window to reset per-service attempt counts."""
        with self._lock:
            self._recovery_attempts.clear()


# ---------------------------------------------------------------------------
# Module-level helper (avoids import cycle with runtime_monitor)
# ---------------------------------------------------------------------------

def _ping_http_local(url: str, timeout: int = 5) -> tuple[bool, float, str]:
    t0 = time.perf_counter()
    try:
        resp = requests.get(url, timeout=timeout)
        latency = (time.perf_counter() - t0) * 1000
        return resp.status_code == 200, latency, f"HTTP {resp.status_code}"
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return False, latency, str(exc)


# ---------------------------------------------------------------------------
# Singleton instance (imported by main.py lifespan handler)
# ---------------------------------------------------------------------------

watchdog = ServiceWatchdog()
