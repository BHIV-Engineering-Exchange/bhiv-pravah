# Gurukul Production Observability Stack Report
**Prometheus Metrics and Grafana Dashboard Integration**

---

## 1. Observability Architecture
Gurukul implements a real-time observability pipeline. Metrics are automatically collected by the FastAPIs, parsed into Prometheus exposition format, and scraped by Prometheus instances before feeding into Grafana visualization dashboards.

```
[ FastAPI App ] ──▶ GET /metrics ──▶ [ Prometheus Server ] ──▶ [ Grafana Server ]
```

---

## 2. Exporter Configuration & Payload Format
The FastAPI endpoint at `GET /metrics` has been added via [prometheus_exporter.py](file:///c:/Users/pc45/Desktop/Gurukul/backend/app/services/prometheus_exporter.py) and verified to return standard plaintext formats scraped by Prometheus agents.

### Example Scraping Response
```text
# HELP gurukul_requests_total Total number of HTTP requests processed.
# TYPE gurukul_requests_total counter
gurukul_requests_total 1248590

# HELP gurukul_requests_by_status_code_total Total requests partitioned by HTTP status code.
# TYPE gurukul_requests_by_status_code_total counter
gurukul_requests_by_status_code_total{status="200"} 1246717
gurukul_requests_by_status_code_total{status="429"} 1873

# HELP gurukul_errors_total Total number of HTTP 5xx errors.
# TYPE gurukul_errors_total counter
gurukul_errors_total 0

# HELP gurukul_voice_latency_seconds_avg Average voice inference latency in seconds.
# TYPE gurukul_voice_latency_seconds_avg gauge
gurukul_voice_latency_seconds_avg 0.114

# HELP gurukul_uptime_seconds Process uptime in seconds.
# TYPE gurukul_uptime_seconds gauge
gurukul_uptime_seconds 3482.4
```

---

## 3. Grafana Dashboard Specification
A production-ready Grafana dashboard template has been designed and stored in [grafana-dashboard.json](file:///c:/Users/pc45/Desktop/Gurukul/kubernetes/grafana-dashboard.json). It provides real-time visualization of key operational parameters:

*   **API Latency Metrics**: Visualizes rolling Average and p95 latencies over time.
*   **Request & Error Volumes**: Tracks overall requests and 5xx error rate curves.
*   **Queue Depth Monitoring**: Visualizes active voice and worker queues, triggering red flags when concurrency thresholds are exceeded.
*   **CPU & Memory Gauges**: Real-time dials indicating resource saturation percentages per node/container.

---

## 4. Operational Alerting Thresholds

| Metric Target | Warning Threshold | Critical Threshold | Alert Action |
| :--- | :--- | :--- | :--- |
| **API Error Rate** | > 1.0% over 5m | > 5.0% over 2m | Slack & PagerDuty |
| **Average Latency** | > 200ms over 3m | > 500ms over 1m | Auto-scale / Scale Replicas |
| **Container Memory** | > 80% usage | > 90% usage | Trigger Node Scale-Up |
| **Redis Cache State** | Unreachable | Connection Down | Automated self-healing trigger |
| **Worker Queue Depth** | > 10 items | > 20 items | Slack alerting |
