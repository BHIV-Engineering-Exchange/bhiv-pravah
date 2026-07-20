"""
system_monitor.py — Runtime Monitoring for Gurukul Infrastructure

Exposes /system/health endpoint with deep metrics:
  - TTS service health (ping Vaani engine)
  - Vaani model load status
  - GPU availability
  - Disk usage in audio directory
  - Service uptime
  - CPU and memory usage
  - Request statistics from VoiceProvider
"""

import time
import os
import subprocess
import logging
import psutil
import shutil
import requests
from fastapi import APIRouter
from app.services.voice_provider import provider
from app.core.config import settings

logger = logging.getLogger("SystemMonitor")

router = APIRouter(prefix="/system", tags=["Infrastructure"])

START_TIME = time.time()


def _check_vaani_health() -> dict:
    """Ping the Vaani engine health endpoint."""
    vaani_url = getattr(settings, "VAANI_API_URL", "http://localhost:8008")
    try:
        resp = requests.get(f"{vaani_url}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "reachable": True,
                "status": data.get("status", "unknown"),
                "device": data.get("device", "unknown"),
                "model_loaded": data.get("status") == "healthy",
            }
        return {"reachable": True, "status": f"error_{resp.status_code}", "model_loaded": False}
    except requests.exceptions.ConnectionError:
        return {"reachable": False, "status": "unreachable", "model_loaded": False}
    except Exception as e:
        return {"reachable": False, "status": f"error: {str(e)[:80]}", "model_loaded": False}


def _check_gpu() -> dict:
    """Check GPU availability via nvidia-smi or torch."""
    gpu_info = {"available": False, "device_name": "N/A", "memory_used_mb": 0, "memory_total_mb": 0}

    # Method 1: Try torch (if available in this process)
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            gpu_info["memory_used_mb"] = round(torch.cuda.memory_allocated(0) / (1024 ** 2), 1)
            gpu_info["memory_total_mb"] = round(torch.cuda.get_device_properties(0).total_mem / (1024 ** 2), 1)
            return gpu_info
    except ImportError:
        pass
    except Exception:
        pass

    # Method 2: Try nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            if len(parts) >= 3:
                gpu_info["available"] = True
                gpu_info["device_name"] = parts[0].strip()
                gpu_info["memory_used_mb"] = float(parts[1].strip())
                gpu_info["memory_total_mb"] = float(parts[2].strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception:
        pass

    return gpu_info


def _check_disk_usage() -> dict:
    """Check disk usage for audio output directories."""
    audio_dirs = [
        os.path.join(os.getcwd(), "audio"),
        os.path.join(os.getcwd(), "audio_samples"),
        os.path.join(os.getcwd(), "..", "vaani-engine", "audio_samples"),
    ]

    disk_info = {"total_gb": 0, "used_gb": 0, "free_gb": 0, "audio_files_count": 0}

    for audio_dir in audio_dirs:
        if os.path.exists(audio_dir):
            total, used, free = shutil.disk_usage(audio_dir)
            disk_info["total_gb"] = round(total / (2 ** 30), 2)
            disk_info["used_gb"] = round(used / (2 ** 30), 2)
            disk_info["free_gb"] = round(free / (2 ** 30), 2)
            try:
                audio_files = [f for f in os.listdir(audio_dir) if f.endswith(('.wav', '.mp3'))]
                disk_info["audio_files_count"] += len(audio_files)
            except OSError:
                pass
            break  # Use first found directory for disk stats

@router.get("/health")
async def get_health():
    """
    ULTRA-LIGHTWEIGHT health check.
    Used by load balancers and Pravah 'alive' signals.
    """
    return {
        "status": "healthy",
        "service": "gurukul-backend",
        "uptime_seconds": int(time.time() - START_TIME),
        "timestamp": time.time()
    }

@router.get("/diagnostics")
async def get_system_diagnostics():
    """
    [DEPRECATED] Use /system/metrics for full telemetry.
    Deep diagnostics for 24x7 stability monitoring.
    """
    vaani_health = _check_vaani_health()
    return {
        "status": "healthy" if vaani_health["reachable"] else "degraded",
        "vaani": vaani_health,
        "infrastructure": {
            "cpu_usage_percent": psutil.cpu_percent(),
            "memory_usage_percent": psutil.virtual_memory().percent,
        }
    }
