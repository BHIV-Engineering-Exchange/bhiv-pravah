# Gurukul Runtime Stability Packet — Soham Kotkar

This packet documents the hardening of the Gurukul runtime for production stability, determinism, and Pravah integration.

## 1. Runtime Architecture & Entry Points

| Component | Responsibility | Entry Point |
| :--- | :--- | :--- |
| **Orchestrator** | Process Lifecycle | `backend/scripts/service_orchestrator.py` |
| **Backend** | API Hub | `backend/app/main.py` |
| **Watchdog** | Self-Healing | `backend/app/services/service_watchdog.py` |
| **Telemetry** | Observability | `backend/app/services/system_metrics.py` |
| **Pravah Link** | External Integration | `backend/app/services/pravah_adapter.py` |

## 2. Hardened Core Flows

### A. Deterministic Voice Startup
1. `service_orchestrator.py` starts **Vaani Engine** first.
2. It waits for `http://localhost:8008/health` to return `200 OK`.
3. Only then starts **Gurukul Backend**.
4. Result: No "Voice Engine Unreachable" errors on initial boot.

### B. Recovery Escalation
1. **ServiceWatchdog** monitors health.
2. On failure: Cooldown of 120s between attempts.
3. Max 3 internal attempts.
4. After 3: escalated to `CRITICAL_FAILURE` in `runtime_events.json`.
5. Pravah sees the event and triggers external human/DevOps alert.

## 3. Pravah Integration (Structured JSON)

Events are logged to `runtime_events.json` in root directory. Example format:

```json
{
  "source": "Orchestrator",
  "service": "VaaniEngine",
  "event": "RECOVERY_START",
  "detail": "Connection refused",
  "timestamp": "2026-04-16T13:45:00",
  "unix_time": 1713260700.0
}
```

## 4. Verification Proof (Mock Log)

```text
[Orchestrator] Starting VaaniEngine...
[Orchestrator] Waiting for VaaniEngine health...
[Orchestrator] [OK] VaaniEngine is HEALTHY.
[Orchestrator] Starting GurukulBackend...
[Main] [OK] Structured logging initialized in JSON format.
[Startup] [OK] ServiceWatchdog and PravahAdapter started.
[TELEMETRY] Pushed stats to runtime_events.json. Status: healthy.
```

## 5. Build & Stability Check
- **Max Restarts**: 3 (Enforced)
- **Restart Cooldown**: 120s (Enforced)
- **Fallback Policy**: No gTTS/pyttsx3 Fallbacks (Enforced)
- **Log Format**: Structured JSON (Standardized)
