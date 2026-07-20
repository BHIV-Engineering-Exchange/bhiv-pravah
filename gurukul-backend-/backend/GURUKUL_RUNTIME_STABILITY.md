# GURUKUL_RUNTIME_STABILITY.md

This document explains the infrastructure hardening implemented to ensure Gurukul operates 24x7 without human intervention.

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   Frontend   │────▶│  Gurukul Backend  │────▶│  Vaani Engine       │
│  (React)     │     │  (FastAPI :3000)  │     │  (XTTS :8008)       │
└─────────────┘     └──────────────────┘     └────────────────────┘
                           │                          │
                    ┌──────▼──────┐             ┌─────▼─────┐
                    │ VoiceProvider│             │ GPU / CPU  │
                    │ (Guardrails) │             │ Fallback   │
                    └──────┬──────┘             └───────────┘
                           │
                    ┌──────▼──────┐
                    │SystemMonitor │
                    │/system/health│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Watchdog    │
                    │ (Supervisor) │
                    └─────────────┘
```

**Data Flow**:
```
Frontend → Gurukul Backend → VoiceProvider → Vaani API → XTTS Model → Audio Output
```

---

## 1. Unified Startup Orchestration

All services are started in a deterministic order using `start_gurukul_services.sh` (Linux) or `start_gurukul_services.bat` (Windows):

| Step | Service | Port | Description |
|------|---------|------|-------------|
| 1 | Database | — | Verify SQL and MongoDB connectivity |
| 2 | Vaani Engine | 8008 | Load XTTS model (waits for health check) |
| 3 | Gurukul Backend | 3000 | Start API layer (waits for health check) |
| 4 | Watchdog | — | Start background supervisor |

Each step includes a **health-check waiter** — the next service only starts after the previous one reports healthy. PID files are written to `logs/` for process management.

---

## 2. Voice Engine Guardrails (`VoiceProvider`)

The `VoiceProvider` module (`backend/app/services/voice_provider.py`) enforces structural discipline on AI inference:

| Guardrail | Implementation | Detail |
|-----------|---------------|--------|
| **Input Limit** | 5000 characters | Requests exceeding this are **rejected** with `ValueError` |
| **Inference Timeout** | 20 seconds | Enforced via `asyncio.wait_for()` — aborts cleanly on timeout |
| **Request Queue** | Max 3 concurrent | Uses `asyncio.Semaphore(3)` — excess requests wait in queue |
| **Retry Logic** | 3 attempts | Linear backoff (1s, 2s, 3s) between retries |
| **Caching** | SHA-256 keyed | In-memory cache with LRU eviction at 200 entries |
| **GPU Fallback** | Automatic | Detects GPU unavailability and tracks in health metrics |

---

## 3. Runtime Monitoring (`/system/health`)

The monitoring endpoint at `/system/health` provides deep metrics:

```json
{
  "status": "healthy",
  "tts_service": "running",
  "vaani_model": "loaded",
  "gpu": "available",
  "uptime_minutes": 342,
  "voice_engine": {
    "status": "running",
    "vaani_url": "http://localhost:8008",
    "model_loaded": true,
    "gpu_mode": true,
    "requests_processed": 156,
    "successful_requests": 154,
    "failures": 2,
    "timeouts": 0,
    "cache_size": 89,
    "cache_hits": 43,
    "queue_depth": 0,
    "max_concurrency": 3,
    "max_input_chars": 5000,
    "inference_timeout_s": 20
  },
  "gpu_details": {
    "available": true,
    "device_name": "NVIDIA GeForce RTX 3060",
    "memory_used_mb": 2048.5,
    "memory_total_mb": 12288.0
  },
  "infrastructure": {
    "cpu_usage_percent": 12.3,
    "memory_usage_percent": 45.6,
    "memory_available_mb": 8192.0,
    "disk_storage": {
      "total_gb": 500.0,
      "used_gb": 120.0,
      "free_gb": 380.0,
      "audio_files_count": 156
    }
  }
}
```

The monitor actively pings the Vaani engine to verify:
- **TTS service status**: running or stopped
- **Model load state**: loaded, unloaded, or error
- **GPU availability**: detected via `torch.cuda` or `nvidia-smi`

---

## 4. Self-Healing Watchdog (`watchdog_runner.py`)

The watchdog process implements a supervisor pattern:

| Feature | Detail |
|---------|--------|
| **Health Checks** | Every 30 seconds, pings both `/system/health` and Vaani `/health` |
| **Auto-Recovery** | After 3 consecutive failures, kills stale process and restarts |
| **Memory Monitor** | Triggers alert if system memory exceeds 90% usage |
| **Platform Support** | Works on both Windows (`taskkill`) and Unix (`kill/lsof`) |
| **Audit Logging** | All watchdog actions logged to `watchdog.log` |
| **Cooldown** | 60-second cooldown after restart to allow boot completion |

Recovery triggers:
- Service unresponsive (HTTP timeout or connection refused)
- Health status reports "unhealthy" or "degraded"
- Consecutive failure count exceeds threshold (3)

---

## 5. Stability Test Evidence

All tests target the TTS engine specifically (see `STABILITY_TEST_LOG.md`):

| Test | Description | Result |
|------|-------------|--------|
| 50 Consecutive Requests | Sequential TTS load test | ✓ PASS |
| 5 Concurrent Requests | Semaphore and queue verification | ✓ PASS |
| Restart During Inference | Service recovery under load | ✓ PASS |
| GPU Unavailability | Fallback to CPU mode | ✓ PASS |
| Input Validation | Guardrail edge cases | ✓ PASS |

Tests can be re-run with:
```bash
python test_stability.py          # Full test suite
python test_stability.py --dry-run  # Syntax check only
```

---

**Gurukul Runtime Stability: HARDENED**
