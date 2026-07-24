# KESHAV Operator Runbook

**Owner:** Rajaryan Verma
**Date:** 2026-06-17
**On-Call Escalation:** See Escalation Matrix below

---

## Quick Reference

| Alert | Severity | Response Time | Section |
|-------|----------|---------------|---------|
| Service Down | Critical | Immediate | [1. Service Down](#1-service-down) |
| High Error Rate (>20%) | Critical | 5 minutes | [2. High Error Rate](#2-high-error-rate) |
| High Latency (>5s p99) | Critical | 5 minutes | [3. High Latency](#3-high-latency) |
| High Error Rate (>5%) | Warning | 15 minutes | [2. High Error Rate](#2-high-error-rate) |
| Pod Restarting | Warning | 15 minutes | [4. Pod Restarting](#4-pod-restarting) |
| Replay Inconsistency | Warning | 30 minutes | [5. Replay Inconsistency](#5-replay-inconsistency) |

---

## 1. Service Down

**Symptoms:** `GET /health` returns non-200 or times out.

**Diagnose:**
```bash
# Docker
docker ps | grep keshav
docker logs keshav-api --tail=100

# Kubernetes
kubectl get pods -n keshav
kubectl logs -n keshav -l app=keshav --tail=100
kubectl describe pod -n keshav -l app=keshav
```

**Fix:**
```bash
# Restart
docker restart keshav-api
# or
kubectl rollout restart deployment/keshav-api -n keshav

# If restart fails, rollback
kubectl rollout undo deployment/keshav-api -n keshav
```

---

## 2. High Error Rate

**Symptoms:** `keshav_request_success_rate < 0.95`

**Diagnose:**
```bash
# Check metrics
curl http://localhost:5000/metrics/json | python -m json.tool

# Check logs for error patterns
docker logs keshav-api --tail=500 | grep -E "ERROR|FAIL|WARNING"
```

**Common Causes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_INPUT_CONTRACT` | Upstream (SETU) sending bad payloads | Contact SETU team |
| `INVALID_JSON` | Malformed JSON body | Check upstream serialization |
| `UNSUPPORTED_MEDIA_TYPE` | Missing `Content-Type: application/json` | Fix upstream headers |
| Internal error | Code bug in new deployment | Rollback |

**Fix:**
```bash
# Rollback if error rate caused by new deployment
kubectl rollout undo deployment/keshav-api -n keshav
```

---

## 3. High Latency

**Symptoms:** `keshav_request_latency_seconds{quantile="0.95"} > 1.0`

**Diagnose:**
```bash
curl http://localhost:5000/metrics/json | python -c "import sys,json; d=json.load(sys.stdin); print(f'p95={d[\"p95_latency_seconds\"]}s p99={d[\"p99_latency_seconds\"]}s')"

# Check resource usage
docker stats keshav-api
# or
kubectl top pods -n keshav
```

**Fix:**
```bash
# Scale horizontally
kubectl scale deployment keshav-api -n keshav --replicas=10

# Or increase workers
kubectl set env deployment/keshav-api -n keshav WORKERS=8
```

---

## 4. Pod Restarting

**Symptoms:** Pods in `CrashLoopBackOff` or frequent restarts.

**Diagnose:**
```bash
kubectl get pods -n keshav
kubectl describe pod <pod-name> -n keshav
kubectl logs <pod-name> -n keshav --previous
```

**Common Causes:**

| Cause | Indicator | Fix |
|-------|-----------|-----|
| OOMKilled | `Reason: OOMKilled` in describe | Increase memory limit |
| Liveness probe failure | `Liveness probe failed` | Adjust probe timing |
| Application crash | Exception in logs | Rollback deployment |

---

## 5. Replay Inconsistency

**Symptoms:** Same input produces different output.

**Diagnose:**
```bash
# Run determinism tests
python -m pytest tests/test_phase8.py -v

# Run full replay proof
python replay_determinism_proof.py
```

**Root Causes to Check:**
- Non-deterministic code (random, uuid4, unsorted iteration)
- Global mutable state
- External dependency injection

**Fix:**
```bash
# Rollback to last known-good commit
git log --oneline -10
kubectl rollout undo deployment/keshav-api -n keshav
```

---

## Routine Operations

### Health Verification
```bash
curl http://localhost:5000/health
# Expected: {"status": "OK", "service": "KESHAV"}
```

### Run Full Validation
```bash
python -m pytest tests/ -q --tb=short        # 123 tests
python -m pytest --cov=analyzer --cov=tantra tests/  # 100% coverage
python run_proofs.py                          # End-to-end proofs
python tantra_wiring_proof.py                 # TANTRA chain (54 assertions)
python replay_determinism_proof.py            # Replay proof (34 assertions)
python production_hardening_proof.py          # Production proof (94 assertions)
```

### Deploy New Version
```bash
# 1. Run full validation on new code
python validate_production.py

# 2. Build image
docker build -t keshav:<version> .

# 3. Deploy
kubectl set image deployment/keshav-api -n keshav keshav-api=keshav:<version>

# 4. Monitor
kubectl rollout status deployment/keshav-api -n keshav
curl http://<service>/health
```

---

## Constitutional Boundaries

KESHAV is a **bounded dependency intelligence capability**. It does NOT own:

| Authority | Owner | KESHAV's Role |
|-----------|-------|---------------|
| Decision making | RAJYA | Emits signals; does not decide |
| Enforcement | Sarathi | Emits resolution; does not enforce |
| Execution | Core | Produces analysis; does not execute |
| Persistence | Bucket | Returns dicts; does not write to disk |
| Observability | InsightFlow | Emits data; InsightFlow reads it |

**Never add to KESHAV:** retry logic, database connections, file writes, external API calls, learning/adaptive mechanisms, execution authority.

---

## Escalation Matrix

| Level | Contact | Scope |
|-------|---------|-------|
| L1 | On-Call Engineer | Restart, scale, rollback |
| L2 | Rajaryan Verma (Owner) | Code review, architecture decisions |
| L3 | RAJYA/Core Team | Downstream execution issues |
| L3 | SETU Team | Upstream input issues |
