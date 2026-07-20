# ARTHA Observability Report

## System Observability Architecture

### Health Endpoints
| Endpoint | Purpose | Auth Required |
|----------|---------|---------------|
| `GET /health` | Basic health check | No |
| `GET /health/detailed` | Comprehensive health | No |
| `GET /health/observability` | Full observability check | No |
| `GET /health/prometheus` | Prometheus metrics | No |
| `GET /health/dashboard` | Dashboard data | No |
| `GET /ready` | Kubernetes readiness | No |
| `GET /live` | Kubernetes liveness | No |
| `GET /metrics` | Performance metrics | No |
| `GET /status` | System status | No |

### Metrics Collected
- **Request Metrics**: Total requests, error count, response times
- **Memory Metrics**: Heap used, heap total, RSS
- **Business Metrics**: Journal entries, ledger entries, payments, signals
- **Compliance Metrics**: Active traces, filing status, audit events
- **Component Health**: Database, Redis, each service

### Prometheus Format
```
# TYPE artha_uptime_seconds gauge
artha_uptime_seconds <value>

# TYPE artha_http_requests_total gauge
artha_http_requests_total <value>

# TYPE artha_http_errors_total gauge
artha_http_errors_total <value>

# TYPE artha_memory_heap_used_bytes gauge
artha_memory_heap_used_bytes <value>
```

### Dashboard Data
Available at `/health/dashboard`:
- Trace health (active, completed, failed, stuck)
- Signal health (active, critical, warning)
- Payment health (total, completed, failed, pending)
- Audit health (total, today, chain integrity)
- System metrics (uptime, requests, memory)

### Alerting Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Stuck Traces | > 0 | > 5 |
| Critical Signals | > 0 | > 3 |
| Failed Payments | > 5 | > 20 |
| Audit Chain Invalid | - | Any |
| Memory Usage | > 80% | > 95% |
| Response Time | > 500ms | > 2000ms |
