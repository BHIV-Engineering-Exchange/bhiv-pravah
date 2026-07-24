# OPERATIONS REVIEW PACKET — KESHAV

**For:** DevOps, SRE, and Operations Teams  
**Prepared By:** Pritesh (Architect)  
**Date:** 2025-01-XX  
**Status:** Production Ready

---

## Operations Overview

KESHAV is a **horizontally scalable, stateless, containerized service** with comprehensive monitoring, alerting, and incident response tooling.

**Operational Characteristics:**
- ✅ Stateless (no persistent storage)
- ✅ Horizontally scalable (3-10 pods)
- ✅ Zero-downtime deployments (rolling updates)
- ✅ Self-healing (Kubernetes auto-restart)
- ✅ Observable (Prometheus metrics, Grafana dashboards)
- ✅ Alertable (10 production alerts)

---

## Deployment Options

### 1. Docker (Single Instance)

**Build:**
```bash
make docker-build
```

**Run:**
```bash
make docker-run
```

**Logs:**
```bash
make docker-logs
```

**Stop:**
```bash
docker stop keshav-api && docker rm keshav-api
```

**Use Case:** Local development, testing

---

### 2. Docker Compose (Multi-Instance)

**Start:**
```bash
make docker-compose-up
```

**Scale:**
```bash
docker-compose up -d --scale keshav=5
```

**Logs:**
```bash
make docker-compose-logs
```

**Stop:**
```bash
make docker-compose-down
```

**Use Case:** Local production testing, staging

---

### 3. Kubernetes (Production)

**Deploy:**
```bash
make k8s-deploy
```

**Status:**
```bash
make k8s-status
```

**Logs:**
```bash
make k8s-logs
```

**Scale:**
```bash
kubectl scale deployment keshav-api -n keshav --replicas=5
```

**Delete:**
```bash
make k8s-delete
```

**Use Case:** Production, high availability

---

### 4. Bare Metal / VM

**Install:**
```bash
pip install -e .
```

**Run:**
```bash
make run-prod
```

**Systemd Service:**
```bash
sudo cp keshav.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable keshav
sudo systemctl start keshav
```

**Use Case:** Legacy infrastructure, on-premises

---

## Configuration Management

### Environment Variables

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `HOST` | `0.0.0.0` | Bind address | No |
| `PORT` | `5000` | Listening port | No |
| `DEBUG` | `false` | Flask debug mode (NEVER true in production) | No |
| `MAX_CONTENT_MB` | `1` | Max request body size in MB | No |
| `WORKERS` | `4` | Gunicorn worker processes | No |

### ConfigMap (Kubernetes)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: keshav-config
  namespace: keshav
data:
  HOST: "0.0.0.0"
  PORT: "5000"
  DEBUG: "false"
  MAX_CONTENT_MB: "1"
```

**Apply:**
```bash
kubectl apply -f k8s-deployment.yaml
```

---

## Resource Management

### Resource Requests (Kubernetes)

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
```

**Meaning:**
- **Memory:** Guaranteed 256 MiB per pod
- **CPU:** Guaranteed 0.25 CPU cores per pod

---

### Resource Limits (Kubernetes)

```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Meaning:**
- **Memory:** Maximum 512 MiB per pod (OOMKilled if exceeded)
- **CPU:** Maximum 0.5 CPU cores per pod (throttled if exceeded)

---

### Horizontal Autoscaling (HPA)

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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Behavior:**
- Scale up when CPU >70% or Memory >80%
- Scale down when CPU <70% and Memory <80%
- Min replicas: 3 (high availability)
- Max replicas: 10 (cost control)

**Check Status:**
```bash
kubectl get hpa -n keshav
```

---

## High Availability

### Replica Count

**Minimum:** 3 replicas (recommended)  
**Rationale:** Survive 1 pod failure + 1 pod rolling update

**Configuration:**
```yaml
spec:
  replicas: 3
```

---

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: keshav-pdb
spec:
  minAvailable: 2
```

**Meaning:** At least 2 pods must be available during voluntary disruptions (e.g., node drain, rolling update)

**Check Status:**
```bash
kubectl get pdb -n keshav
```

---

### Rolling Update Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

**Meaning:**
- **maxSurge: 1** — Create 1 extra pod during update (4 pods total during rollout)
- **maxUnavailable: 0** — Never reduce below 3 pods during update

**Result:** Zero-downtime deployments

---

### Health Checks

**Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3
```

**Meaning:** Restart pod if health check fails 3 times (90 seconds)

**Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

**Meaning:** Remove pod from load balancer if health check fails 3 times (30 seconds)

---

## Monitoring

### Prometheus Metrics

**Endpoint:** `GET /metrics`

**Metrics Exposed:**
```
keshav_requests_total                          # Total requests
keshav_request_errors_total                    # Total errors
keshav_request_success_rate                    # Success rate (0-1)
keshav_request_latency_seconds{quantile}       # Latency (p50, p95, p99)
keshav_unique_traces_total                     # Unique traces processed
keshav_severity_total{severity}                # Severity distribution
```

**Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'keshav'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - keshav
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: keshav
    - source_labels: [__meta_kubernetes_pod_ip]
      target_label: __address__
      replacement: ${1}:5000
```

**Verify Scraping:**
```bash
curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="keshav")'
```

---

### Grafana Dashboard

**Import:** `grafana-dashboard.json`

**Panels:**
1. Request Rate (time series)
2. Error Rate (time series)
3. Request Latency (p50, p95, p99)
4. Success Rate (single stat)
5. Severity Distribution (pie chart)
6. Unique Traces Processed (single stat)

**Access:**
```
http://grafana:3000/d/keshav
```

---

### Alerting

**Rules:** `prometheus-alerts.yaml`

**Alerts:**
1. **KeshavServiceDown** (critical) — Service unreachable for 1 minute
2. **KeshavCriticalErrorRate** (critical) — Error rate >20% for 2 minutes
3. **KeshavHighErrorRate** (warning) — Error rate >5% for 5 minutes
4. **KeshavCriticalLatency** (critical) — p95 latency >5s for 2 minutes
5. **KeshavHighLatency** (warning) — p95 latency >1s for 5 minutes
6. **KeshavPodRestarting** (warning) — Pod restarting frequently
7. **KeshavHighMemoryUsage** (warning) — Memory >85% for 5 minutes
8. **KeshavHighCPUUsage** (warning) — CPU >85% for 5 minutes
9. **KeshavHighSeveritySpike** (warning) — HIGH severity >30% for 10 minutes
10. **KeshavLowRequestRate** (info) — Request rate <0.1 req/s for 10 minutes

**Load Rules:**
```bash
kubectl apply -f prometheus-alerts.yaml
```

**Verify:**
```bash
curl http://prometheus:9090/api/v1/rules | jq '.data.groups[] | select(.name=="keshav_alerts")'
```

---

## Logging

### Log Format

**Structured:**
```
2025-01-01 12:00:00,123 INFO keshav.api POST /analyze trace_id=trace-001
2025-01-01 12:00:00,234 INFO keshav.api pipeline OK trace_id=trace-001
```

**Fields:**
- Timestamp (ISO8601)
- Log level (INFO, WARNING, ERROR)
- Logger name (keshav.api)
- Message

---

### Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| INFO | Successful requests | `pipeline OK trace_id=trace-001` |
| WARNING | Failed requests (invalid input) | `pipeline FAIL trace_id=trace-001 error=INVALID_INPUT_CONTRACT` |
| ERROR | Internal errors (unhandled exceptions) | `Unhandled internal error` |

---

### Log Aggregation

**Recommendation:** Export to external system

**Options:**
1. **ELK Stack** (Elasticsearch, Logstash, Kibana)
2. **Splunk**
3. **CloudWatch Logs** (AWS)
4. **Stackdriver** (GCP)
5. **Azure Monitor** (Azure)

**Kubernetes Logging:**
```bash
kubectl logs -n keshav -l app=keshav --tail=100 -f
```

**Docker Logging:**
```bash
docker logs -f keshav-api
```

---

### Log Retention

**Docker Compose:**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Meaning:** Keep last 3 files, max 10 MB each (30 MB total)

**Kubernetes:**
- Default: Node-level log rotation (varies by cluster)
- Recommendation: Export to external log aggregation

---

## Backup & Recovery

### State

**KESHAV is stateless:**
- No persistent storage
- No database
- Bucket (in-memory only)
- InsightFlow (in-memory only)

**Conclusion:** No backup required

---

### Recovery

**Pod Failure:**
- Kubernetes auto-restarts failed pods
- No manual intervention required

**Node Failure:**
- Kubernetes reschedules pods to healthy nodes
- No manual intervention required

**Cluster Failure:**
- Redeploy to new cluster: `make k8s-deploy`
- No data loss (stateless)

---

## Disaster Recovery

### RTO (Recovery Time Objective)

**Target:** <5 minutes

**Procedure:**
1. Deploy to new cluster: `make k8s-deploy` (1 minute)
2. Verify health: `kubectl get pods -n keshav` (30 seconds)
3. Run smoke test: `curl http://keshav-service/health` (30 seconds)
4. Update DNS/load balancer (3 minutes)

---

### RPO (Recovery Point Objective)

**Target:** 0 (no data loss)

**Rationale:** Stateless architecture, no persistent data

---

### Multi-Region Deployment

**Recommendation:** Deploy to multiple regions for disaster recovery

**Architecture:**
```
Region 1 (Primary)
  ├── Kubernetes Cluster
  └── KESHAV Deployment (3 replicas)

Region 2 (Secondary)
  ├── Kubernetes Cluster
  └── KESHAV Deployment (3 replicas)

Global Load Balancer
  ├── Route to Region 1 (primary)
  └── Failover to Region 2 (if Region 1 down)
```

---

## Performance Tuning

### Worker Count

**Formula:** `2-4 × CPU cores`

**Example:**
- 2 CPU cores → 4-8 workers
- 4 CPU cores → 8-16 workers

**Configuration:**
```bash
gunicorn "api:app" --workers 8 --bind 0.0.0.0:5000
```

---

### Worker Timeout

**Default:** 30 seconds

**Recommendation:** Adjust based on workload

**Configuration:**
```bash
gunicorn "api:app" --timeout 60
```

---

### Worker Restart (Memory Leak Prevention)

**Configuration:**
```bash
gunicorn "api:app" --max-requests 1000 --max-requests-jitter 100
```

**Meaning:** Restart worker after 900-1100 requests (prevents memory leaks)

---

### Connection Limits

**Gunicorn:**
```bash
gunicorn "api:app" --worker-connections 1000
```

**Meaning:** Max 1000 concurrent connections per worker

---

## Cost Optimization

### Resource Right-Sizing

**Current:**
- Requests: 256Mi memory, 250m CPU
- Limits: 512Mi memory, 500m CPU

**Recommendation:** Monitor actual usage and adjust

**Check Usage:**
```bash
kubectl top pods -n keshav
```

---

### Autoscaling Tuning

**Current:**
- Min replicas: 3
- Max replicas: 10
- Scale on CPU >70% or Memory >80%

**Recommendation:** Adjust based on traffic patterns

**Example (Lower Min):**
```yaml
spec:
  minReplicas: 2  # Reduce cost during low traffic
  maxReplicas: 10
```

---

### Spot Instances (Cloud)

**Recommendation:** Use spot instances for non-critical workloads

**Kubernetes Node Pool:**
```yaml
nodeSelector:
  node-type: spot
tolerations:
- key: spot
  operator: Equal
  value: "true"
  effect: NoSchedule
```

---

## Troubleshooting Guide

### Issue: High Latency

**Symptoms:**
- p95 latency >1s
- Alert: `KeshavHighLatency`

**Diagnosis:**
```bash
curl http://localhost:5000/metrics/json | jq '.p95_latency_seconds'
kubectl top pods -n keshav
```

**Resolution:**
1. Increase workers: `--workers 8`
2. Scale horizontally: `kubectl scale deployment keshav-api --replicas=10`
3. Increase resource limits

---

### Issue: High Error Rate

**Symptoms:**
- Error rate >5%
- Alert: `KeshavHighErrorRate`

**Diagnosis:**
```bash
kubectl logs -n keshav -l app=keshav --tail=500 | grep ERROR
curl http://localhost:5000/metrics/json | jq '.request_success_rate'
```

**Resolution:**
1. Check upstream SETU input
2. Validate input contract
3. Check downstream service health
4. Rollback if recent deployment

---

### Issue: Pod Restarting

**Symptoms:**
- Pods in `CrashLoopBackOff`
- Alert: `KeshavPodRestarting`

**Diagnosis:**
```bash
kubectl get pods -n keshav
kubectl describe pod <pod-name> -n keshav
kubectl logs <pod-name> -n keshav --previous
```

**Resolution:**
1. Check for OOMKilled (increase memory limit)
2. Check for liveness probe failure (adjust probe settings)
3. Check for application crash (review logs, rollback)

---

### Issue: High Memory Usage

**Symptoms:**
- Memory >85% of limit
- Alert: `KeshavHighMemoryUsage`

**Diagnosis:**
```bash
kubectl top pods -n keshav
```

**Resolution:**
1. Scale horizontally: `kubectl scale deployment keshav-api --replicas=10`
2. Increase memory limit: `limits.memory: 1Gi`
3. Enable worker restart: `--max-requests 1000`

---

## Maintenance Windows

### Rolling Updates (Zero Downtime)

**Procedure:**
```bash
kubectl set image deployment/keshav-api -n keshav keshav=keshav:v2
kubectl rollout status deployment/keshav-api -n keshav
```

**Duration:** 2-5 minutes (depends on replica count)

**Downtime:** 0 (rolling update strategy)

---

### Node Maintenance

**Procedure:**
```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
# Perform node maintenance
kubectl uncordon <node-name>
```

**Impact:** Pods rescheduled to other nodes (no downtime if ≥3 replicas)

---

### Cluster Upgrade

**Procedure:**
1. Upgrade control plane
2. Upgrade worker nodes (one at a time)
3. Verify KESHAV pods running: `kubectl get pods -n keshav`

**Impact:** No downtime (pods rescheduled during node upgrades)

---

## Operational Checklist

### Daily
- [ ] Check Grafana dashboard for anomalies
- [ ] Review Prometheus alerts
- [ ] Check pod status: `kubectl get pods -n keshav`

### Weekly
- [ ] Review metrics trends (latency, error rate, throughput)
- [ ] Check resource usage: `kubectl top pods -n keshav`
- [ ] Review logs for errors

### Monthly
- [ ] Review autoscaling behavior
- [ ] Optimize resource requests/limits
- [ ] Update dependencies (security patches)
- [ ] Review incident log

### Quarterly
- [ ] Load testing
- [ ] Disaster recovery drill
- [ ] Review runbook
- [ ] Update documentation

---

## Contact Information

| Role | Name | Contact |
|------|------|---------|
| Maintainer | Rajaryan Verma | [Email/Slack] |
| Architect | Pritesh | [Email/Slack] |
| On-Call | Rotation | [PagerDuty/Opsgenie] |

---

## References

- **DEPLOYMENT.md** — Full deployment guide
- **RUNBOOK.md** — Incident response playbook
- **PRODUCTION_READY.md** — Production readiness summary
- **Grafana Dashboard** — `grafana-dashboard.json`
- **Prometheus Alerts** — `prometheus-alerts.yaml`

---

**Prepared for operations team handover and production deployment.**
