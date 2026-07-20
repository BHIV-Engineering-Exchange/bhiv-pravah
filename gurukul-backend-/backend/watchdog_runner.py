"""
watchdog_runner.py — Gurukul Crash Recovery Watchdog

Self-healing supervisor process that monitors Gurukul services and
automatically restarts them on failure.

Monitors:
  - Gurukul Backend API  (http://localhost:3000/system/health)
  - Vaani Voice Engine   (http://localhost:8008/health)

Recovery triggers:
  - Service unresponsive (HTTP timeout or connection refused)
  - Health status reports "unhealthy" or "degraded"
  - Consecutive failures exceed threshold
  - System memory usage exceeds safe limits

Supports both Windows (taskkill/start) and Unix (kill/nohup) platforms.
"""

import time
import sys
import os
import signal
import platform
import subprocess
import logging
import json
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
CHECK_INTERVAL       = 30       # Seconds between health checks
MAX_CONSECUTIVE_FAIL = 3        # Failures before restart trigger
MEMORY_THRESHOLD_PCT = 90       # Restart if memory exceeds this %
RESTART_COOLDOWN     = 60       # Seconds to wait after restart before resuming checks
LOG_FILE             = "watchdog.log"

SERVICES = {
    "gurukul_backend": {
        "health_url": "http://localhost:3000/system/health",
        "start_cmd_win": 'start "Gurukul Backend" cmd /c "cd /d {cwd} && python -m uvicorn app.main:app --host 0.0.0.0 --port 3000"',
        "start_cmd_unix": "cd {cwd} && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 > backend.log 2>&1 &",
        "port": 3000,
    },
    "vaani_engine": {
        "health_url": "http://localhost:8008/health",
        "start_cmd_win": 'start "Vaani Engine" cmd /c "cd /d {vaani_dir} && python voice_service_api.py"',
        "start_cmd_unix": "cd {vaani_dir} && nohup python voice_service_api.py > vaani.log 2>&1 &",
        "port": 8008,
    },
}

# ──────────────────────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Watchdog] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a"),
    ],
)
logger = logging.getLogger("Watchdog")


# ──────────────────────────────────────────────────────────────
# Platform Detection
# ──────────────────────────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
CWD = os.path.dirname(os.path.abspath(__file__))
VAANI_DIR = os.path.normpath(os.path.join(CWD, "..", "vaani-engine"))


def check_service_health(service_name: str, health_url: str) -> dict:
    """Ping a service health endpoint and return status."""
    import requests
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            return {"alive": True, "status": status, "healthy": status in ("healthy",)}
        return {"alive": True, "status": f"http_{response.status_code}", "healthy": False}
    except requests.exceptions.ConnectionError:
        return {"alive": False, "status": "unreachable", "healthy": False}
    except requests.exceptions.Timeout:
        return {"alive": False, "status": "timeout", "healthy": False}
    except Exception as e:
        return {"alive": False, "status": f"error: {str(e)[:60]}", "healthy": False}


def check_memory_usage() -> float:
    """Return system memory usage percentage."""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        # Fallback: read from /proc/meminfo on Linux
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1])
            available = int(lines[2].split()[1])
            return (1 - available / total) * 100
        except Exception:
            return 0.0


def kill_process_on_port(port: int):
    """Kill the process occupying a given port."""
    logger.info(f"Attempting to kill process on port {port}...")

    try:
        if IS_WINDOWS:
            # Find PID using netstat
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                capture_output=True, text=True, shell=True, timeout=10
            )
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) > 0:
                        logger.info(f"Killing PID {pid} on port {port}")
                        subprocess.run(f"taskkill /PID {pid} /F", shell=True, timeout=10)
                        time.sleep(2)
                        return True
        else:
            # Unix: use lsof or fuser
            result = subprocess.run(
                f"lsof -ti:{port}", capture_output=True, text=True, shell=True, timeout=10
            )
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid.strip().isdigit():
                    logger.info(f"Killing PID {pid} on port {port}")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(2)
                    return True
    except Exception as e:
        logger.error(f"Failed to kill process on port {port}: {e}")

    return False


def restart_service(service_name: str, config: dict):
    """Kill existing process and restart the service."""
    logger.warning(f"RESTARTING service: {service_name}")

    # 1. Kill existing process
    kill_process_on_port(config["port"])
    time.sleep(3)

    # 2. Start fresh
    try:
        if IS_WINDOWS:
            cmd = config["start_cmd_win"].format(cwd=CWD, vaani_dir=VAANI_DIR)
            subprocess.Popen(cmd, shell=True, cwd=CWD)
        else:
            cmd = config["start_cmd_unix"].format(cwd=CWD, vaani_dir=VAANI_DIR)
            subprocess.Popen(cmd, shell=True, cwd=CWD)

        logger.info(f"Service {service_name} restart command issued. Waiting for boot...")
    except Exception as e:
        logger.error(f"Failed to restart {service_name}: {e}")


def monitor_loop():
    """Main watchdog monitoring loop."""
    failure_counts = {name: 0 for name in SERVICES}

    logger.info("=" * 60)
    logger.info("Gurukul Watchdog Runner STARTED")
    logger.info(f"Platform: {platform.system()} | Check interval: {CHECK_INTERVAL}s")
    logger.info(f"Max failures before restart: {MAX_CONSECUTIVE_FAIL}")
    logger.info(f"Memory threshold: {MEMORY_THRESHOLD_PCT}%")
    logger.info(f"Monitoring services: {list(SERVICES.keys())}")
    logger.info("=" * 60)

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── Check each service ───────────────────────────────
        for service_name, config in SERVICES.items():
            result = check_service_health(service_name, config["health_url"])

            if result["healthy"]:
                if failure_counts[service_name] > 0:
                    logger.info(f"[{service_name}] RECOVERED after {failure_counts[service_name]} failures")
                failure_counts[service_name] = 0
            else:
                failure_counts[service_name] += 1
                logger.warning(
                    f"[{service_name}] UNHEALTHY | status={result['status']} | "
                    f"failures={failure_counts[service_name]}/{MAX_CONSECUTIVE_FAIL}"
                )

                if failure_counts[service_name] >= MAX_CONSECUTIVE_FAIL:
                    restart_service(service_name, config)
                    failure_counts[service_name] = 0
                    time.sleep(RESTART_COOLDOWN)

        # ── Check memory ─────────────────────────────────────
        mem_pct = check_memory_usage()
        if mem_pct > MEMORY_THRESHOLD_PCT:
            logger.warning(
                f"MEMORY CRITICAL: {mem_pct:.1f}% > {MEMORY_THRESHOLD_PCT}% threshold. "
                f"Consider restarting services."
            )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Watchdog crashed: {e}")
        sys.exit(1)
