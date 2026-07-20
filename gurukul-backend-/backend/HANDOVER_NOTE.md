# Handover Note: Gurukul Runtime Infrastructure

## Overview
The Gurukul platform has been upgraded with an autonomous runtime orchestration and monitoring layer. This layer ensures 24x7 stability by automatically detecting service failures and performing self-healing recovery actions.

## 1. Monitoring Architecture
- **Service**: `backend/app/services/runtime_monitor.py`
- **Function**: Performs active polling of all core dependencies (Vaani, PRANA, PostgreSQL, Redis).
- **Endpoint**: `/health` extends the standard health check with deep service signals (latency, status, timestamp).

## 2. Metrics System
- **Service**: `backend/app/services/system_metrics.py`
- **Function**: A FastAPI middleware that captures every request, response status, and calculates rolling latencies for Voice and AI inference.
- **Endpoint**: `GET /system/metrics` provides a JSON snapshot of system performance and error rates.

## 3. Restart Mechanism (Watchdog)
- **Service**: `backend/app/services/service_watchdog.py`
- **Function**: A background thread in the FastAPI process that runs every 60 seconds.
- **Recovery Logic**: 
  - **Database**: Recycles the SQLAlchemy connection pool.
  - **Vaani**: Sends a `/restart` signal or relaunches the `start.py` process.
  - **PRANA**: Relaunches the `start_bucket_consumer.py` script.
  - **Redis**: Re-establishes socket connections.

## 4. Service Orchestrator
- **Script**: `backend/scripts/service_orchestrator.py`
- **Function**: The "canonical" way to start Gurukul. It supervises all processes (Backend, Vaani, Bucket Consumer, Frontends) and restarts them immediately if they crash.
- **Usage**: Use `start-all.bat` and select **Option 1 (Supervised Mode)**.

## 5. Verification
- **Test Suite**: `backend/scripts/failure_simulation_test.py`
- **Coverage**: 18 tests covering monitor accuracy, watchdog thread safety, and metrics recording.

---
*Prepared for Soham Kotkar — Runtime Infrastructure*
