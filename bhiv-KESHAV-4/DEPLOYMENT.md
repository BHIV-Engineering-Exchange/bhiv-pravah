# KESHAV Production Deployment Guide

**Status:** Production Ready  
**Last Updated:** 2025-01-XX  
**Maintainer:** Rajaryan Verma

---

## Quick Start

### Local Development
```bash
pip install -e ".[dev]"
python api.py
```

### Production (Docker)
```bash
docker build -t keshav:latest .
docker run -p 5000:5000 keshav:latest
```

### Production (Docker Compose)
```bash
docker-compose up -d
```

### Production (Kubernetes)
```bash
kubectl apply -f k8s-deployment.yaml
```

---

## Deployment Options

### 1. Docker Container (Recommended)

**Build:**
```bash
docker build -t keshav:latest .
```

**Run:**
```bash
docker run -d \
  --name keshav-api \
  -p 5000:5000 \
  -e MAX_CONTENT_MB=1 \
  --restart unless-stopped \
  keshav:latest
```

**Health Check:**
```bash
curl http://localhost:5000/health
```

---

### 2. Docker Compose

**Start:**
```bash
docker-compose up -d
```

**Stop:**
```bash
docker-compose down
```

**Logs:**
```bash
docker-compose logs -f keshav
```

**Scale:**
```bash
docker-compose up -d --scale keshav=3
```

---

### 3. Kubernetes

**Deploy:**
```bash
kubectl apply -f k8s-deployment.yaml
```

**Check Status:**
```bash
kubectl get pods -n keshav
kubectl get svc -n keshav
```

**View Logs:**
```bash
kubectl logs -n keshav -l app=keshav --tail=100 -f
```

**Scale:**
```bash
kubectl scale deployment keshav-api -n keshav --replicas=5
```

**Delete:**
```bash
kubectl delete -f k8s-deployment.yaml
```

---

### 4. Bare Metal / VM

**Install:**
```bash
pip install -e .
```

**Run (Production):**
```bash
gunicorn "api:app" \
  --workers 4 \
  --bind 0.0.0.0:5000 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

**Run (Systemd Service):**
```bash
sudo cp keshav.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable keshav
sudo systemctl start keshav
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5000` | Listening port |
| `DEBUG` | `false` | Flask debug mode (NEVER true in production) |
| `MAX_CONTENT_MB` | `1` | Max request body size in MB |
| `WORKERS` | `4` | Gunicorn worker processes |

### Gunicorn Configuration

**Recommended Settings:**
- **Workers:** `2-4 × CPU cores`
- **Timeout:** `30s` (adjust based on workload)
- **Max Requests:** `1000` (worker restart for memory leak prevention)
- **Max Requests Jitter:** `100` (stagger worker restarts)

**Example:**
```bash
gunicorn "api:app" \
  --workers 8 \
  --bind 0.0.0.0:5000 \
  --timeout 30 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

---

## Monitoring

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "OK",
  "service": "KESHAV"
}
```

**Usage:**
```bash
curl http://localhost:5000/health
```

---

### Metrics (Prometheus)

**Endpoint:** `GET /metrics`

**Metrics Exposed:**
- `keshav_requests_total` — Total requests
- `keshav_request_errors_total` — Total errors
- `keshav_request_success_rate` — Success rate (0-1)
- `keshav_request_latency_seconds` — Latency (p50, p95, p99)
- `keshav_unique_traces_total` — Unique trace IDs processed
- `keshav_severity_total{severity="HIGH|MEDIUM|LOW"}` — Severity distribution

**Usage:**
```bash
curl http://localhost:5000/metrics
```

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'keshav'
    static_configs:
      - targets: ['keshav-service:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

---

### Metrics (JSON)

**Endpoint:** `GET /metrics/json`

**Response:**
```json
{
  "request_count": 1234,
  "request_errors": 5,
  "request_success_rate": 0.9959,
  "avg_latency_seconds": 0.0234,
  "p95_latency_seconds": 0.0456,
  "p99_latency_seconds": 0.0789,
  "severity_distribution": {
    "HIGH": 123,
    "MEDIUM": 456,
    "LOW": 655
  },
  "unique_traces_processed": 1234
}
```

---

### Logging

**Format:**
```
2025-01-01 12:00:00,123 INFO keshav.api POST /analyze trace_id=trace-001
2025-01-01 12:00:00,234 INFO keshav.api pipeline OK trace_id=trace-001
```

**Log Levels:**
- `INFO` — Successful requests
- `WARNING` — Failed requests (invalid input)
- `ERROR` — Internal errors (unhandled exceptions)

**Docker Logs:**
```bash
docker logs -f keshav-api
```

**Kubernetes Logs:**
```bash
kubectl logs -n keshav -l app=keshav --tail=100 -f
```

---

## Performance Tuning

### Resource Limits

**Docker:**
```bash
docker run -d \
  --name keshav-api \
  -p 5000:5000 \
  --memory="512m" \
  --cpus="0.5" \
  keshav:latest
```

**Kubernetes:**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

### Horizontal Scaling

**Docker Compose:**
```bash
docker-compose up -d --scale keshav=5
```

**Kubernetes HPA:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: keshav-hpa
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

### Load Balancing

**Nginx:**
```nginx
upstream keshav {
    least_conn;
    server keshav-1:5000;
    server keshav-2:5000;
    server keshav-3:5000;
}

server {
    listen 80;
    location / {
        proxy_pass http://keshav;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Kubernetes Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: keshav-service
spec:
  type: LoadBalancer
  selector:
    app: keshav
  ports:
  - port: 80
    targetPort: 5000
```

---

## Security

### Container Security

**Non-root user:**
```dockerfile
USER keshav
```

**Read-only filesystem:**
```yaml
securityContext:
  readOnlyRootFilesystem: true
```

**Drop capabilities:**
```yaml
securityContext:
  capabilities:
    drop:
    - ALL
```

---

### Network Security

**Firewall rules:**
- Allow inbound: `5000/tcp` (API)
- Allow outbound: `443/tcp` (HTTPS for dependencies)
- Deny all other traffic

**TLS/SSL:**
Use reverse proxy (Nginx, Traefik, Ingress) for TLS termination.

---

### Input Validation

**Max request size:** `1 MB` (configurable via `MAX_CONTENT_MB`)

**Fail-closed validation:**
- Missing `trace_id` → 400 FAIL
- Missing `execution_id` → 400 FAIL
- Invalid JSON → 400 FAIL
- Non-dict input → 400 FAIL

---

## Rollback Procedure

### Docker

**Rollback to previous image:**
```bash
# Tag the known-good image before deploying
docker tag keshav:latest keshav:previous

# If the new deployment fails, restore the previous image
docker stop keshav-api
docker rm keshav-api
docker run -d --name keshav-api -p 5000:5000 --restart unless-stopped keshav:previous
```

### Docker Compose

**Rollback:**
```bash
docker-compose down
# Revert to previous image tag in docker-compose.yml, then:
docker-compose up -d
```

### Kubernetes

**Rollback to previous revision:**
```bash
# View rollout history
kubectl rollout history deployment/keshav-api -n keshav

# Rollback to previous revision
kubectl rollout undo deployment/keshav-api -n keshav

# Rollback to specific revision
kubectl rollout undo deployment/keshav-api -n keshav --to-revision=2

# Verify rollback
kubectl rollout status deployment/keshav-api -n keshav
```

### Bare Metal / Systemd

**Rollback:**
```bash
# Stop the service
sudo systemctl stop keshav

# Revert the code
cd /opt/keshav
git checkout <previous-known-good-tag>
pip install -e .

# Restart
sudo systemctl start keshav
```

---

## Troubleshooting

### High Latency

**Check metrics:**
```bash
curl http://localhost:5000/metrics/json | jq '.p99_latency_seconds'
```

**Increase workers:**
```bash
gunicorn "api:app" --workers 8 --bind 0.0.0.0:5000
```

---

### High Error Rate

**Check logs:**
```bash
docker logs keshav-api | grep ERROR
```

**Check metrics:**
```bash
curl http://localhost:5000/metrics/json | jq '.request_success_rate'
```

---

### Memory Leak

**Enable worker restart:**
```bash
gunicorn "api:app" --max-requests 1000 --max-requests-jitter 100
```

**Monitor memory:**
```bash
docker stats keshav-api
```

---

### Container Crash

**Check logs:**
```bash
docker logs keshav-api
```

**Check health:**
```bash
curl http://localhost:5000/health
```

**Restart:**
```bash
docker restart keshav-api
```

---

## Backup and Recovery

### Bucket State

**Bucket is in-memory only.** No persistent state.

**Recovery:** Replay from SETU input.

---

### InsightFlow Events

**InsightFlow is in-memory only.** No persistent state.

**Recovery:** Replay from SETU input.

---

## Operational Checklist

- [ ] Deploy to staging environment
- [ ] Run health check (`GET /health`)
- [ ] Run sample request (`POST /analyze`)
- [ ] Verify metrics endpoint (`GET /metrics`)
- [ ] Configure Prometheus scraping
- [ ] Configure log aggregation
- [ ] Set up alerting (error rate, latency)
- [ ] Test horizontal scaling
- [ ] Test rolling updates
- [ ] Document runbook for incidents

---

## Production Readiness Checklist

- [x] Dockerfile created
- [x] Docker Compose configuration
- [x] Kubernetes manifests
- [x] Health check endpoint
- [x] Metrics endpoint (Prometheus)
- [x] Structured logging
- [x] Non-root container user
- [x] Resource limits defined
- [x] Horizontal autoscaling configured
- [x] Rolling update strategy
- [x] Pod disruption budget
- [x] Security context hardening
- [x] Input validation
- [x] Error handling
- [x] Deployment guide

**Status:** ✅ PRODUCTION READY
