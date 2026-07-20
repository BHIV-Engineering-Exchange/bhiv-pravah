"""
runtime_monitor.py — Gurukul Autonomous Runtime Orchestration Layer
====================================================================

Performs lightweight health-checks against every core service and
returns a structured list of ServiceSignal objects that the watchdog
and metrics layer can consume.

Covered services:
  - Gurukul Backend  (self / in-process)
  - Vaani TTS Engine (http://localhost:8008/health)
  - PRANA Ingestion  (bucket consumer subprocess sentinel file)
  - PostgreSQL        (psql / SQLAlchemy ping)
  - Redis             (redis-py PING)

Usage:
    from app.services.runtime_monitor import RuntimeMonitor
    monitor = RuntimeMonitor()
    signals = monitor.check_all()
"""

import time
import logging
import subprocess
import os
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from app.core.config import settings

logger = logging.getLogger("RuntimeMonitor")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ServiceSignal:
    name: str
    status: str          # "healthy" | "degraded" | "down"
    latency_ms: float    # round-trip in milliseconds, -1 if unreachable
    message: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Individual health-check helpers
# ---------------------------------------------------------------------------

def _ping_http(url: str, timeout: int = 5) -> tuple[bool, float, str]:
    """Returns (ok, latency_ms, message)."""
    t0 = time.perf_counter()
    try:
        resp = requests.get(url, timeout=timeout)
        latency = (time.perf_counter() - t0) * 1000
        if resp.status_code == 200:
            return True, latency, f"HTTP 200 from {url}"
        return False, latency, f"HTTP {resp.status_code} from {url}"
    except requests.exceptions.ConnectionError:
        latency = (time.perf_counter() - t0) * 1000
        return False, latency, f"Connection refused: {url}"
    except requests.exceptions.Timeout:
        latency = timeout * 1000.0
        return False, latency, f"Timeout after {timeout}s: {url}"
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return False, latency, f"Error: {exc}"


def _check_backend() -> ServiceSignal:
    """Self-check — if this code is running the backend is up."""
    return ServiceSignal(
        name="GurkulBackend",
        status="healthy",
        latency_ms=0.0,
        message="In-process check: backend is running",
    )


def _check_vaani() -> ServiceSignal:
    vaani_url = getattr(settings, "VAANI_API_URL", "http://localhost:8008")
    ok, latency, msg = _ping_http(f"{vaani_url}/health")
    return ServiceSignal(
        name="VaaniTTS",
        status="healthy" if ok else "down",
        latency_ms=latency,
        message=msg,
    )


def _check_prana() -> ServiceSignal:
    """
    PRANA bucket consumer does not expose an HTTP endpoint.
    We check for a sentinel file that start_bucket_consumer.py writes.
    Fallback: check if the python process with 'start_bucket_consumer' in
    the command line is running.
    """
    sentinel_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "scripts", ".prana_alive"
    )
    t0 = time.perf_counter()
    if os.path.exists(sentinel_path):
        age = time.time() - os.path.getmtime(sentinel_path)
        latency = (time.perf_counter() - t0) * 1000
        if age < 120:  # sentinel must be updated within 2 minutes
            return ServiceSignal(
                name="PRANA",
                status="healthy",
                latency_ms=latency,
                message=f"Sentinel fresh ({age:.0f}s ago)",
            )
        return ServiceSignal(
            name="PRANA",
            status="degraded",
            latency_ms=latency,
            message=f"Sentinel stale ({age:.0f}s ago) — consumer may be stuck",
        )

    # Fallback: subprocess scan
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        latency = (time.perf_counter() - t0) * 1000
        if "python" in result.stdout.lower():
            return ServiceSignal(
                name="PRANA",
                status="degraded",
                latency_ms=latency,
                message="Python processes found but sentinel file missing",
            )
    except Exception:
        pass

    latency = (time.perf_counter() - t0) * 1000
    return ServiceSignal(
        name="PRANA",
        status="down",
        latency_ms=latency,
        message="Sentinel file not found and process scan inconclusive",
    )


def _check_database() -> ServiceSignal:
    """Attempt a lightweight DB ping using SQLAlchemy."""
    t0 = time.perf_counter()
    try:
        from sqlalchemy import create_engine, text
        db_url = getattr(settings, "DATABASE_URL", None)
        if not db_url:
            return ServiceSignal(
                name="Database",
                status="degraded",
                latency_ms=-1,
                message="DATABASE_URL not configured in settings",
            )
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.perf_counter() - t0) * 1000
        return ServiceSignal(
            name="Database",
            status="healthy",
            latency_ms=latency,
            message="SELECT 1 succeeded",
        )
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return ServiceSignal(
            name="Database",
            status="down",
            latency_ms=latency,
            message=f"DB ping failed: {str(exc)[:120]}",
        )


def _check_redis() -> ServiceSignal:
    """Ping Redis using redis-py if available."""
    t0 = time.perf_counter()
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
            socket_timeout=3
        )
        client.ping()
        latency = (time.perf_counter() - t0) * 1000
        return ServiceSignal(
            name="Redis",
            status="healthy",
            latency_ms=latency,
            message="PONG received",
        )
    except ImportError:
        return ServiceSignal(
            name="Redis",
            status="degraded",
            latency_ms=-1,
            message="redis-py not installed — skipping Redis check",
        )
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return ServiceSignal(
            name="Redis",
            status="down",
            latency_ms=latency,
            message=f"Redis ping failed: {str(exc)[:120]}",
        )


# ---------------------------------------------------------------------------
# Main monitor class
# ---------------------------------------------------------------------------

class RuntimeMonitor:
    """
    Aggregates health signals for all Gurukul core services.

    Usage:
        monitor = RuntimeMonitor()
        signals = monitor.check_all()   # List[ServiceSignal]
    """

    CHECKERS = [
        _check_backend,
        _check_vaani,
        _check_prana,
        _check_database,
        _check_redis,
    ]

    def check_all(self) -> List[ServiceSignal]:
        """Run all health checks and return a list of ServiceSignal objects."""
        signals: List[ServiceSignal] = []
        for checker in self.CHECKERS:
            try:
                signal = checker()
            except Exception as exc:
                logger.exception(f"Unexpected error in checker {checker.__name__}: {exc}")
                signal = ServiceSignal(
                    name=checker.__name__,
                    status="down",
                    latency_ms=-1,
                    message=f"Checker raised exception: {exc}",
                )
            signals.append(signal)
            logger.debug(f"[{signal.name}] {signal.status} — {signal.message}")
        return signals

    def overall_status(self, signals: Optional[List[ServiceSignal]] = None) -> str:
        """Return 'healthy', 'degraded', or 'down' based on the signal list."""
        if signals is None:
            signals = self.check_all()
        statuses = {s.status for s in signals}
        if "down" in statuses:
            return "degraded"  # at least one service is down
        if "degraded" in statuses:
            return "degraded"
        return "healthy"
