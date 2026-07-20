# Gurukul Runtime Orchestration & Monitoring

This directory contains the infrastructure for autonomous monitoring and recovery of Gurukul services.

## Components

### 1. Runtime Monitoring (`app/services/runtime_monitor.py`)
Tracks health of:
- Gurukul Backend
- Vaani Voice Engine
- PRANA Bucket Ingestion
- Database (PostgreSQL)
- Redis

### 2. Service Watchdog (`app/services/service_watchdog.py`)
Autonomous recovery agent that pings services every 60s and attempts automatic restarts/reconnects.

### 3. System Metrics (`app/services/system_metrics.py`)
Telemetry layer exposing `/system/metrics`. Tracks:
- Request/Error counts
- Voice & AI latency (p95, avg)
- System uptime

### 4. Service Orchestrator (`scripts/service_orchestrator.py`)
Supervisor script to start and manage all Gurukul processes.

## How to Run
Use the root `start-all.bat` and choose **Option 1 (Supervised Mode)**.

Alternatively, run headless:
```bash
python scripts/service_orchestrator.py --no-frontend
```

## Running Tests
```bash
python scripts/failure_simulation_test.py
```
