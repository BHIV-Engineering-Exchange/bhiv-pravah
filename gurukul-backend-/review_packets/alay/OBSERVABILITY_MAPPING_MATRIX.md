# Gurukul Metric → Alert → Dashboard Mapping Matrix

This document provides a deterministic, explicit mapping of Gurukul's runtime observability stack. It acts as a reference for tracking how core application telemetry is exposed, alert-bounded, visualized in Grafana, and configured within your Kubernetes cluster.

---

## 📊 Core Traceability Matrix

| Prometheus Metric Name | Exposed Type | Source Code Reference File | Alerting Thresholds | Grafana Dashboard Panel Name | Target Dependency | Windows Validation Command | Kubernetes Manifest Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`gurukul_database_healthy`** | Gauge (1/0) | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L51-L60) | **Critical**: Unreachable `0.0` for >60s | **PostgreSQL Connection Health** (Stat Indicator) | PostgreSQL Database | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_database_healthy"` | [`postgres_deploy.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/postgres_deploy.yml) |
| **`gurukul_redis_healthy`** | Gauge (1/0) | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L61-L70) | **Critical**: Ping timeout `0.0` for >60s | **Redis Cache Connectivity** (Stat Indicator) | Redis Cache | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_redis_healthy"` | *Configured via env secrets* |
| **`gurukul_watchdog_active`** | Gauge (1/0) | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L71-L78) | **Critical**: Thread Dead `0.0` for >10s | **Autonomous Watchdog Status** (Status Dial) | Background Watchdog | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_watchdog_active"` | [`backend_deploy.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/backend_deploy.yml) |
| **`gurukul_voice_latency_seconds_avg`** | Gauge | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L96-L98) | **Warning**: `> 0.20s` (200ms)<br>**Critical**: `> 0.50s` (500ms) | **Average Voice Inference Latency** (TimeSeries Graph) | Vaani TTS Engine | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_voice_latency_seconds_avg"` | [`tts_deploy.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/tts_deploy.yml) |
| **`gurukul_voice_latency_seconds_p95`** | Gauge | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L100-L102) | **Warning**: `> 0.50s` (500ms)<br>**Critical**: `> 1.50s` (1500ms) | **p95 Voice Inference Latency** (TimeSeries Graph) | Vaani TTS Engine | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_voice_latency_seconds_p95"` | [`tts_deploy.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/tts_deploy.yml) |
| **`gurukul_requests_total`** | Counter | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L80-L83) | N/A (Volume Tracking) | **HTTP API Throughput** (Stat panel) | FastAPI Web Engine | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_requests_total"` | [`backend_deploy.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/backend_deploy.yml) |
| **`gurukul_errors_total`** | Counter | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L91-L93) | **Warning**: `> 1.0%` errors<br>**Critical**: `> 5.0%` errors | **5xx Error Volume / Rate** (Gauge Panel) | FastAPI Web Engine | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_errors_total"` | [`backend_deploy.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/backend_deploy.yml) |
| **`gurukul_cpu_usage_ratio`** | Gauge | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L114-L116) | **Warning**: `> 0.80` (80%)<br>**Critical**: `> 0.90` (90%) | **Container CPU Saturation** (Bar Gauge) | Kubernetes Nodes / Pods | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_cpu_usage_ratio"` | [`backend_hpa.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/backend_hpa.yml) |
| **`gurukul_memory_usage_ratio`** | Gauge | [`prometheus_exporter.py`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/backend/app/services/prometheus_exporter.py#L118-L120) | **Warning**: `> 0.80` (80%)<br>**Critical**: `> 0.90` (90%) | **Container Memory Saturation** (Bar Gauge) | Kubernetes Nodes / Pods | `(Invoke-RestMethod http://localhost:3000/metrics) -match "gurukul_memory_usage_ratio"` | [`backend_hpa.yml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/backend_hpa.yml) |

---

## ⚙️ Detailed Component Telemetry Explanations

### 1. PostgreSQL Health Checking
Exposed in `/metrics` by issuing a live ping statement:
```python
db_healthy = 1.0
try:
    from app.core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception:
    db_healthy = 0.0
```
*   **Alert Lifecycle Action**: If `db_healthy == 0.0` is registered, the background watchdog immediately captures the unhealthy state, starts its retry sequence, and issues a warning telemetry payload to the Pravah Adapter.

### 2. Autonomous Watchdog Lifespan Checking
Exposed in `/metrics` by monitoring the daemon status of the singleton execution instance:
```python
watchdog_active = 1.0
try:
    from app.services.service_watchdog import watchdog
    if not watchdog.is_alive():
        watchdog_active = 0.0
except Exception:
    watchdog_active = 0.0
```
*   **Alert Lifecycle Action**: If this watchdog checking fails or returns `0.0`, it alerts administrators that autonomous recovery is suspended.

---

