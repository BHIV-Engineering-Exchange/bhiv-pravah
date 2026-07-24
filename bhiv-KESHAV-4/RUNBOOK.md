# KESHAV Production Runbook

**Maintainer:** Rajaryan Verma  
**Last Updated:** 2025-01-XX  
**On-Call:** [Contact Information]

---

## Quick Reference

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| Service Down | Critical | Immediate | [Incident 1](#incident-1-service-down) |
| High Error Rate (>20%) | Critical | 5 minutes | [Incident 2](#incident-2-high-error-rate) |
| High Latency (>5s) | Critical | 5 minutes | [Incident 3](#incident-3-high-latency) |
| High Error Rate (>5%) | Warning | 15 minutes | [Incident 2](#incident-2-high-error-rate) |
| High Latency (>1s) | Warning | 15 minutes | [Incident 3](#incident-3-high-latency) |
| Pod Restarting | Warning | 15 minutes | [Incident 4](#incident-4-pod-restarting) |
| High Memory/CPU | Warning | 30 minutes | [Incident 5](#incident-5-high-resource-usage) |

---

## Incident 1: Service Down

### Symptoms
- Alert: `KeshavServiceDown`
- Health check failing: `GET /health` returns non-200

### Diagnosis

**Step 1: Check service status**
```bash
# Docker
docker ps | grep keshav
docker logs keshav-api --tail=100

# Kubernetes
kubectl get pods -n keshav
kubectl logs -n keshav -l app=keshav --tail=100
```

**Step 2: Check recent deployments**
```bash
# Kubernetes
kubectl rollout history deployment/keshav-api -n keshav
```

**Step 3: Check resource availability**
```bash
# Kubernetes
kubectl describe pod -n keshav -l app=keshav
```

### Resolution

**Option 1: Restart service**
```bash
# Docker
docker restart keshav-api

# Kubernetes
kubectl rollout restart deployment/keshav-api -n keshav
```

**Option 2: Rollback deployment**
```bash
# Kubernetes
kubectl rollout undo deployment/keshav-api -n keshav
```

**Option 3: Scale up replicas**
```bash
# Kubernetes
kubectl scale deployment keshav-api -n keshav --replicas=5
```

### Post-Incident
- [ ] Review logs for root cause
- [ ] Update incident log
- [ ] Create post-mortem if downtime >5 minutes

---

## Incident 2: High Error Rate

### Symptoms
- Alert: `KeshavHighErrorRate` or `KeshavCriticalErrorRate`
- Metrics: `keshav_request_success_rate < 0.95`

### Diagnosis

**Step 1: Check error distribution**
```bash
curl http://localhost:5000/metrics/json | jq '.request_errors, .request_count'
```

**Step 2: Check logs for error patterns**
```bash
# Docker
docker logs keshav-api --tail=500 | grep ERROR

# Kubernetes
kubectl logs -n keshav -l app=keshav --tail=500 | grep ERROR
```

**Step 3: Check InsightFlow FAILURE events**
```bash
# Via API (if exposed)
curl http://localhost:5000/metrics/json | jq '.severity_distribution'
```

### Common Causes

**Invalid Input (INVALID_INPUT_CONTRACT)**
- Missing `trace_id` or `execution_id`
- Wrong type fields
- Malformed JSON

**Action:** Investigate upstream SETU input source

**Downstream Failure (SARATHI_FAILURE, CORE_FAILURE)**
- Sarathi or Core layer exception

**Action:** Check downstream service health

**Trace Mutation (RAJYA_TRACE_MISMATCH)**
- Trace ID changed mid-pipeline

**Action:** Investigate RAJYA layer

### Resolution

**Option 1: Fix upstream input**
- Contact SETU team
- Validate input contract

**Option 2: Rollback deployment**
```bash
kubectl rollout undo deployment/keshav-api -n keshav
```

**Option 3: Scale up for load**
```bash
kubectl scale deployment keshav-api -n keshav --replicas=10
```

### Post-Incident
- [ ] Identify root cause (upstream vs downstream)
- [ ] Update validation tests if new failure mode
- [ ] Document in CORRUPTION_INJECTION_PROOF.md

---

## Incident 3: High Latency

### Symptoms
- Alert: `KeshavHighLatency` or `KeshavCriticalLatency`
- Metrics: `keshav_request_latency_seconds{quantile="0.95"} > 1.0`

### Diagnosis

**Step 1: Check current latency**
```bash
curl http://localhost:5000/metrics/json | jq '.p95_latency_seconds, .p99_latency_seconds'
```

**Step 2: Check resource usage**
```bash
# Docker
docker stats keshav-api

# Kubernetes
kubectl top pods -n keshav
```

**Step 3: Check worker count**
```bash
# Docker
docker exec keshav-api ps aux | grep gunicorn | wc -l

# Kubernetes
kubectl get pods -n keshav | wc -l
```

### Common Causes

**Insufficient Workers**
- Too few Gunicorn workers for load

**Action:** Increase worker count

**High CPU/Memory**
- Resource exhaustion

**Action:** Scale horizontally or increase limits

**Large Input Payloads**
- Input exceeds `MAX_CONTENT_MB`

**Action:** Increase limit or reject large payloads

### Resolution

**Option 1: Increase workers**
```bash
# Update deployment with more workers
kubectl set env deployment/keshav-api -n keshav WORKERS=8
```

**Option 2: Scale horizontally**
```bash
kubectl scale deployment keshav-api -n keshav --replicas=10
```

**Option 3: Increase resource limits**
```yaml
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Post-Incident
- [ ] Review latency trends
- [ ] Adjust autoscaling thresholds
- [ ] Load test to validate capacity

---

## Incident 4: Pod Restarting

### Symptoms
- Alert: `KeshavPodRestarting`
- Pods in `CrashLoopBackOff` or frequent restarts

### Diagnosis

**Step 1: Check pod status**
```bash
kubectl get pods -n keshav
kubectl describe pod <pod-name> -n keshav
```

**Step 2: Check logs**
```bash
kubectl logs <pod-name> -n keshav --previous
```

**Step 3: Check events**
```bash
kubectl get events -n keshav --sort-by='.lastTimestamp'
```

### Common Causes

**OOMKilled (Out of Memory)**
- Memory limit too low

**Action:** Increase memory limit

**Liveness Probe Failure**
- Health check timing out

**Action:** Adjust probe settings

**Application Crash**
- Unhandled exception

**Action:** Review logs, rollback if needed

### Resolution

**Option 1: Increase memory limit**
```yaml
resources:
  limits:
    memory: "1Gi"
```

**Option 2: Adjust liveness probe**
```yaml
livenessProbe:
  initialDelaySeconds: 30
  timeoutSeconds: 10
```

**Option 3: Rollback deployment**
```bash
kubectl rollout undo deployment/keshav-api -n keshav
```

### Post-Incident
- [ ] Analyze memory usage patterns
- [ ] Review for memory leaks
- [ ] Update resource requests/limits

---

## Incident 5: High Resource Usage

### Symptoms
- Alert: `KeshavHighMemoryUsage` or `KeshavHighCPUUsage`
- Metrics: Memory/CPU >85% of limit

### Diagnosis

**Step 1: Check current usage**
```bash
kubectl top pods -n keshav
```

**Step 2: Check historical trends**
```bash
# Via Grafana dashboard
# Or Prometheus query
```

**Step 3: Check request rate**
```bash
curl http://localhost:5000/metrics/json | jq '.request_count'
```

### Common Causes

**High Load**
- Request rate exceeds capacity

**Action:** Scale horizontally

**Memory Leak**
- Unbounded growth in Bucket or InsightFlow

**Action:** Restart workers, investigate leak

**Inefficient Code**
- New deployment introduced performance regression

**Action:** Rollback, investigate

### Resolution

**Option 1: Scale horizontally**
```bash
kubectl scale deployment keshav-api -n keshav --replicas=10
```

**Option 2: Increase resource limits**
```yaml
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

**Option 3: Enable worker restart**
```bash
# Gunicorn max-requests to prevent memory leaks
gunicorn "api:app" --max-requests 1000 --max-requests-jitter 100
```

### Post-Incident
- [ ] Review Bucket/InsightFlow bounded storage
- [ ] Profile memory usage
- [ ] Adjust autoscaling thresholds

---

## Incident 6: Replay Inconsistency

### Symptoms
- Different outputs for same input
- Determinism tests failing

### Diagnosis

**Step 1: Run determinism tests**
```bash
pytest tests/test_phase8.py -v
```

**Step 2: Check for non-deterministic code**
- Random number generation
- System time (excluding timestamp)
- Network calls
- File I/O

**Step 3: Review recent PRs**
```bash
git log --oneline -10
```

### Resolution

**Option 1: Rollback deployment**
```bash
kubectl rollout undo deployment/keshav-api -n keshav
```

**Option 2: Revert offending commit**
```bash
git revert <commit-hash>
```

### Post-Incident
- [ ] Identify non-deterministic code
- [ ] Add test coverage
- [ ] Update DISTRIBUTED_REPLAY_VALIDATION.md

---

## Escalation

### Level 1: On-Call Engineer
- Restart services
- Scale resources
- Rollback deployments

### Level 2: Rajaryan Verma (Maintainer)
- Code review
- Architectural decisions
- Convergence boundary violations

### Level 3: Integration Partners
- **Kanishk Singh** — Replay governance issues
- **Akanksha Parab** — Sarathi enforcement issues
- **RAJYA/Core Team** — Downstream execution issues

---

## Monitoring Dashboards

- **Grafana:** `grafana-dashboard.json`
- **Prometheus:** `http://prometheus:9090`
- **Metrics:** `http://keshav-service:5000/metrics`

---

## Contact Information

| Role | Name | Contact |
|------|------|---------|
| Maintainer | Rajaryan Verma | [Email/Slack] |
| Architect | Pritesh | [Email/Slack] |
| Replay Governance | Kanishk Singh | [Email/Slack] |
| Sarathi Enforcement | Akanksha Parab | [Email/Slack] |

---

## Post-Incident Template

```markdown
# Incident Report: [Title]

**Date:** YYYY-MM-DD  
**Duration:** X minutes  
**Severity:** Critical/Warning/Info  
**Responder:** [Name]

## Summary
[Brief description]

## Timeline
- HH:MM - Alert triggered
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Resolution applied
- HH:MM - Service restored

## Root Cause
[Detailed explanation]

## Resolution
[What was done]

## Prevention
[How to prevent recurrence]

## Action Items
- [ ] Item 1
- [ ] Item 2
```

---

**Keep this runbook updated. Review quarterly.**
