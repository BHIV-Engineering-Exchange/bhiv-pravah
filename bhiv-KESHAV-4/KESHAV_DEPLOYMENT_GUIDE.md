# KESHAV Deployment Guide

**Owner:** Rajaryan Verma
**Date:** 2026-06-17
**Status:** Production Ready

---

## Prerequisites

- Python 3.10+
- pip
- (Optional) Docker, kubectl for container/K8s deployment

---

## Environment Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd KESHAV-4
```

### 2. Install Dependencies
```bash
# Production only
pip install -e .

# With development tools (pytest, ruff, mypy)
pip install -e ".[dev]"
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for production) |
| `PORT` | `5000` | Listening port |
| `DEBUG` | `false` | Flask debug mode (**never** `true` in production) |
| `MAX_CONTENT_MB` | `1` | Max request body size in MB |
| `WORKERS` | `4` | Gunicorn worker processes |

### 4. Validate Installation
```bash
# Run all tests
python -m pytest tests/ -q --tb=short
# Expected: 123 passed

# Check coverage
python -m pytest --cov=analyzer --cov=tantra tests/
# Expected: TOTAL 100%

# Run lint
python -m ruff check analyzer tantra tests api.py metrics.py
# Expected: All checks passed

# Run type check
python -m mypy analyzer
# Expected: Success: no issues found in 7 source files
```

---

## Deployment Options

### Option 1: Local Development
```bash
python api.py
# Server starts at http://127.0.0.1:5000
```

### Option 2: Production (Gunicorn)
```bash
gunicorn "api:app" \
  --workers 4 \
  --bind 0.0.0.0:5000 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Option 3: Docker
```bash
# Build
docker build -t keshav:latest .

# Run
docker run -d \
  --name keshav-api \
  -p 5000:5000 \
  -e MAX_CONTENT_MB=1 \
  --restart unless-stopped \
  keshav:latest

# Verify
curl http://localhost:5000/health
```

### Option 4: Docker Compose
```bash
docker-compose up -d
docker-compose logs -f keshav
```

### Option 5: Kubernetes
```bash
kubectl apply -f k8s-deployment.yaml
kubectl get pods -n keshav
kubectl get svc -n keshav
```

### Option 6: Systemd Service
```bash
sudo cp keshav.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable keshav
sudo systemctl start keshav
```

---

## Post-Deployment Verification

```bash
# 1. Health check
curl http://localhost:5000/health
# Expected: {"status": "OK", "service": "KESHAV"}

# 2. Valid payload
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d @sample_input.json
# Expected: 200 with root_cause, resolution_signal, severity

# 3. Fail-closed test
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"execution_id": "test"}'
# Expected: 400 with INVALID_INPUT_CONTRACT

# 4. Metrics
curl http://localhost:5000/metrics
# Expected: Prometheus-format metrics
```

---

## Rollback Procedure

### Docker
```bash
# Pre-deployment: tag current image
docker tag keshav:latest keshav:previous

# Rollback
docker stop keshav-api && docker rm keshav-api
docker run -d --name keshav-api -p 5000:5000 --restart unless-stopped keshav:previous
```

### Kubernetes
```bash
# View history
kubectl rollout history deployment/keshav-api -n keshav

# Rollback to previous
kubectl rollout undo deployment/keshav-api -n keshav

# Rollback to specific revision
kubectl rollout undo deployment/keshav-api -n keshav --to-revision=2
```

### Git
```bash
git log --oneline -5
git revert <commit-hash>
pip install -e .
# Restart the service
```

---

## Monitoring

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Liveness + readiness |
| `/metrics` | GET | Prometheus-format metrics |
| `/metrics/json` | GET | JSON metrics for debugging |

### Prometheus Scrape Config
```yaml
scrape_configs:
  - job_name: 'keshav'
    static_configs:
      - targets: ['keshav-service:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Key Metrics
- `keshav_requests_total` — Total requests
- `keshav_request_errors_total` — Total errors
- `keshav_request_success_rate` — Success rate (0-1)
- `keshav_request_latency_seconds` — p50/p95/p99 latency
- `keshav_severity_total{severity="HIGH|MEDIUM|LOW"}` — Severity distribution

### Grafana Dashboard
Import `grafana-dashboard.json` into Grafana.

### Alerting
Apply `prometheus-alerts.yaml` to your Prometheus instance.
