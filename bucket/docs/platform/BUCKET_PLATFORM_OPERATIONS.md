# Bucket Platform Operations

**Document ID:** BUCKET-OPS-001  
**Version:** 1.0.0  
**Date:** 19 June 2026  
**Status:** CANONICAL  
**Owner:** Siddhesh Narkar — Bucket Custodian  
**Purpose:** Operational handbook for Bucket in production

---

## 1. Operations Overview

Bucket operates as a **single-writer append-only evidence platform**. Production operations focus on:

- Evidence integrity (hash chain, replay validation)
- Storage durability (backup, recovery)
- Availability (health monitoring, restart procedures)
- Capacity (disk, artifact count, throughput)
- Constitutional discipline (no role creep)

**Primary persistence:** `data/artifacts/artifact_log.jsonl`  
**Override path:** `BHIV_ARTIFACT_PATH` environment variable

---

## 2. High Availability

### 2.1 Architecture Model (v1)

| Property | Value |
|----------|-------|
| Write model | Single-writer append-only |
| Consensus | None (no distributed consensus) |
| Replication | Manual backup / restore |
| Read scaling | Multiple read replicas possible (future) |

### 2.2 Availability Targets

| Metric | v1 Target | Notes |
|--------|-----------|-------|
| Uptime | 99.5% | Single-node deployment |
| Recovery Time (RTO) | < 15 minutes | Cold restart with intact files |
| Recovery Point (RPO) | Last successful fsync | No mid-write recovery |

### 2.3 HA Procedures

**Normal restart:**
```bash
# Stop
Ctrl+C or process kill

# Start
uvicorn main:app --host 0.0.0.0 --port 8000
# or
python main.py
```

On restart, Bucket auto-loads `chain_state.json` and opens `artifact_log.jsonl` in append mode. No manual steps if files intact.

**Health verification after restart:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/bucket/latest-hash
curl -X POST http://localhost:8000/bucket/validate-replay
```

### 2.4 Future HA (Not v1)

- Hot standby with shared persistent volume
- Read replica serving GET endpoints
- Automated failover with chain state sync

---

## 3. Backup Strategy

### 3.1 Critical Files

| File | Priority | Backup Frequency |
|------|----------|------------------|
| `data/artifacts/artifact_log.jsonl` | **CRITICAL** | Every write batch / hourly |
| `data/artifacts/chain_state.json` | HIGH | With log backup (rebuildable from log) |
| `data/artifacts/artifact_index.json` | MEDIUM | Rebuildable from log |
| `data/audit.log` | HIGH | Daily |
| `.env` | HIGH | On change (secrets redacted in shared backups) |

### 3.2 Backup Procedure

```bash
# 1. Pause writes (optional — append-only is crash-safe)
# 2. Copy artifacts directory
cp -r data/artifacts/ data/artifacts-backup-$(date +%Y%m%d-%H%M%S)/

# 3. Copy audit log
cp data/audit.log data/audit-backup-$(date +%Y%m%d).log

# 4. Verify backup integrity
wc -l data/artifacts-backup-*/artifact_log.jsonl
```

### 3.3 Off-Site Backup

- Upload `artifact_log.jsonl` to secure object storage (S3, Yotta bucket)
- Encrypt at rest
- Retain minimum 7 years for audit compliance (`ScaleLimits.AUDIT_RETENTION_YEARS`)

### 3.4 Backup Verification

After each backup:
```bash
curl -X POST http://localhost:8000/bucket/validate-replay
# Expect: "valid": true
```

---

## 4. Disaster Recovery

### 4.1 Recovery Invariants (Never Violate)

1. Artifacts are **never deleted** during recovery
2. Hashes are **never recomputed** with different logic
3. Chain state reflects **last verified** artifact only
4. **No writes** during recovery until verification passes
5. `trace_id` values are **never remapped**

### 4.2 Scenario Matrix

| Scenario | Trigger | Procedure | Reference |
|----------|---------|-----------|-----------|
| A — Cold restart | Process killed, files intact | Restart service | Auto-recovery |
| B — Missing chain_state | `chain_state.json` lost | Rebuild from log | `BUCKET_RECOVERY_AND_RESTORATION_GUIDE.md` §B |
| C — Corrupt last log line | Crash mid-write | Truncate corrupt line, rebuild chain | §C |
| D — Index divergence | Index out of sync | Restart (index rebuilds) | §D |
| E — Ephemeral disk loss | Container restart without persistent volume | Restore from backup or genesis | §E |
| F — Operator handover | Custodian change | Transfer log + verify + sign-off | §F |

### 4.3 Post-Recovery Verification

```bash
# 1. Chain validation
curl -X POST http://localhost:8000/bucket/validate-replay

# 2. Count check
curl http://localhost:8000/bucket/chain-state

# 3. Sample read-back
curl http://localhost:8000/bucket/artifact/<last-artifact-id>

# 4. Re-enable writes only after all checks pass
```

### 4.4 Restore from Backup

```bash
# 1. STOP service
# 2. Replace data/artifacts/ with backup copy
# 3. START service
# 4. Run post-recovery verification
# 5. Notify producers of restoration complete
```

---

## 5. Integrity Monitoring

### 5.1 Scheduled Checks

| Check | Frequency | Endpoint / Command |
|-------|-----------|-------------------|
| Full chain replay | Daily | `POST /bucket/validate-replay` |
| Chain head consistency | Hourly | `GET /bucket/latest-hash` vs log tail |
| Storage stats | Hourly | `GET /bucket/storage-stats` |
| Health | Every 1 min | `GET /health` |

### 5.2 Integrity Failure Response

```
1. IMMEDIATELY block new writes (stop service or network ACL)
2. Capture artifact_log.jsonl snapshot
3. Run validate-replay to identify first broken line
4. Escalate to Bucket custodian + BHIV Core
5. Follow recovery scenario B or C
6. Do NOT advance chain_state beyond last valid entry
```

### 5.3 Hash Mismatch Alert

**Severity:** CRITICAL  
**Trigger:** `validate-replay` returns `"valid": false`  
**Action:** Halt writes, begin recovery, notify all producers

---

## 6. Storage Health

### 6.1 Monitoring Metrics

| Metric | Source | Warning | Critical |
|--------|--------|---------|----------|
| Log file size (bytes) | `GET /bucket/storage-stats` | > 80% disk | > 95% disk |
| Artifact count | `chain-state` | > 70% of 100M limit | > 90% |
| Payload rejections (400) | Audit log | > 10/hour | > 100/hour |
| Write failures (500) | Audit log | Any sustained | > 5/minute |

### 6.2 Limits (from `config/scale_limits.py`)

| Limit | Value |
|-------|-------|
| Max artifact size | 16 MB |
| Max total storage | 1 TB |
| Max total artifacts | 100M |
| Max artifacts per product | 10M |
| Max products | 100 |
| Storage warning threshold | 90% |
| Storage critical threshold | 99% |

### 6.3 Disk Space Procedure

```
1. Check GET /bucket/storage-stats
2. If > 90%: alert operators
3. If > 99%: block writes, expand volume or archive old logs (governance approval required)
4. Never delete artifacts without governance-approved retention policy
```

---

## 7. Capacity Planning

### 7.1 Growth Estimation

```
daily_growth_bytes = avg_artifact_size × daily_write_count
days_to_limit = (MAX_TOTAL_STORAGE_GB × 1e9) / daily_growth_bytes
```

### 7.2 Throughput Limits

| Operation | Safe Rate | Max Rate |
|-----------|-----------|----------|
| Writes/sec | 500 | 1000 |
| Reads/sec | 50 | 100 |
| Concurrent writes | 50 | 100 |
| Concurrent reads | 20 | 50 |

### 7.3 What Does Not Scale (v1)

- Real-time cross-product queries
- Full-text search
- Multi-region replication
- Distributed read-heavy (>100 reads/sec)

Plan capacity accordingly. Do not assume unlimited scale.

---

## 8. Replay Monitoring

### 8.1 Automated Replay Job

```bash
#!/bin/bash
# replay_monitor.sh — run via cron daily
RESULT=$(curl -s -X POST http://localhost:8000/bucket/validate-replay)
VALID=$(echo $RESULT | jq -r '.valid')

if [ "$VALID" != "true" ]; then
  echo "CRITICAL: Chain integrity failure"
  echo $RESULT
  # Trigger alert (email, webhook, InsightFlow)
  exit 1
fi

echo "OK: Chain valid, count=$(echo $RESULT | jq -r '.artifact_count')"
```

### 8.2 Replay Metrics to Track

| Metric | Description |
|--------|-------------|
| `replay_valid` | Boolean — last replay result |
| `artifact_count` | Total artifacts in chain |
| `last_hash` | Current chain head |
| `replay_duration_ms` | Time to complete full scan |
| `replay_errors_count` | Number of integrity errors |

---

## 9. Production Dashboards

### 9.1 Recommended Panels

| Panel | Data Source |
|-------|-------------|
| Service health | `GET /health` → `status` |
| Artifact count | `GET /bucket/chain-state` |
| Chain head hash | `GET /bucket/latest-hash` |
| Log file size | `GET /bucket/storage-stats` |
| Replay status | `POST /bucket/validate-replay` |
| Write rate | Audit log CREATE count/minute |
| Rejection rate | Audit log `status: blocked` count |
| MongoDB/Redis status | `GET /health` → `services` |

### 9.2 InsightFlow Integration

InsightFlow reads Bucket artifacts and audit records for observability dashboards. InsightFlow **must not** write to Bucket in production.

Proof: `INSIGHTFLOW_OBSERVABILITY_PROOF.md`

---

## 10. Alerting

### 10.1 Alert Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Chain integrity failure | `validate-replay.valid == false` | CRITICAL | Halt writes, begin recovery |
| Service unhealthy | `health.status == unhealthy` | HIGH | Restart, check dependencies |
| Disk space critical | `storage > 99%` | CRITICAL | Expand volume |
| Sustained write failures | `500 rate > 5/min` | HIGH | Check logs, disk, permissions |
| parent_hash rejections spike | `400 parent_hash > 50/hour` | MEDIUM | Check producer coordination |
| MongoDB disconnected | `health.mongodb != connected` | MEDIUM | Audit falls back to file |

### 10.2 Notification Channels

- Operator email / Slack
- InsightFlow alert feed
- BHIV Core escalation for CRITICAL integrity failures

---

## 11. Production Deployment

### 11.1 Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `MONGODB_URI` | Recommended | Audit + agent logs |
| `REDIS_HOST/PORT/PASSWORD` | Optional | Agent orchestration only |
| `BHIV_ARTIFACT_PATH` | Optional | Override artifact storage path |
| `FASTAPI_PORT` | Optional | Default 8000 |

### 11.2 Deployment Checklist

- [ ] Persistent volume mounted for `data/artifacts/`
- [ ] `BHIV_ARTIFACT_PATH` points to persistent path
- [ ] MongoDB Atlas or remote Mongo configured (not localhost on cloud)
- [ ] Health endpoint reachable
- [ ] `validate-replay` passes on deploy
- [ ] Backup job scheduled
- [ ] Replay monitor cron configured
- [ ] CORS restricted to known origins (production)
- [ ] TLS terminated at load balancer or reverse proxy
- [ ] Producers notified of production URL

### 11.3 Render Deployment Notes

From `DEPLOYMENT_PERSISTENCE_TRUTH_REPORT.md`:

- Ephemeral disk = **data loss on restart**
- **Must** mount Render Persistent Disk to `/data`
- Update `MONGODB_URI` to Atlas (localhost does not work on Render)

---

## 12. Yotta Deployment Readiness

### 12.1 Sovereign Hosting Requirements

| Requirement | Status | Action |
|-------------|--------|--------|
| Persistent storage for JSONL | Required | Mount sovereign volume |
| Network isolation | Required | Private VPC / firewall |
| Backup to sovereign object store | Required | Configure off-site backup |
| TLS encryption in transit | Required | Certificate management |
| Access control | Required | RBAC for operator access |
| Audit log retention (7 years) | Required | Retention policy + backup |
| No external data egress | Recommended | Air-gapped or controlled egress |

### 12.2 Yotta Readiness Checklist

- [ ] Sovereign compute instance provisioned
- [ ] Persistent volume attached (`BHIV_ARTIFACT_PATH`)
- [ ] MongoDB on sovereign infrastructure (or file-only audit mode)
- [ ] Backup to Yotta object storage configured
- [ ] Network ACL: producers only, no public write
- [ ] TLS certificates installed
- [ ] Operator runbook (this document) distributed
- [ ] Recovery drill executed on Yotta environment
- [ ] `validate-replay` passes post-deploy
- [ ] BHIV Core notified of sovereign endpoint

### 12.3 Yotta-Specific Considerations

- Single-writer model aligns with sovereign deployment (no multi-region complexity)
- Append-only JSONL is portable — migrate by copying log file
- No dependency on external cloud services if MongoDB/Redis run locally or audit uses file fallback

---

## 13. Operational Runbook Quick Reference

| Task | Command |
|------|---------|
| Health check | `curl /health` |
| Chain head | `curl /bucket/latest-hash` |
| Full replay | `curl -X POST /bucket/validate-replay` |
| Storage stats | `curl /bucket/storage-stats` |
| Start service | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| Backup artifacts | `cp -r data/artifacts/ <backup-path>/` |
| Staging path | `BHIV_ARTIFACT_PATH=data/artifacts-staging` |

---

## 14. Escalation Matrix

| Severity | Contact | Response Time |
|----------|---------|---------------|
| CRITICAL (integrity failure) | Bucket custodian + BHIV Core | Immediate |
| HIGH (service down) | Bucket custodian | < 1 hour |
| MEDIUM (degraded) | Bucket custodian | < 4 hours |
| LOW (capacity warning) | Bucket custodian | < 24 hours |

Governance escalation: Raj Prajapati (BHIV Core contract authority)

---

## 15. Related Documents

| Document | Purpose |
|----------|---------|
| `BUCKET_RECOVERY_AND_RESTORATION_GUIDE.md` | Detailed recovery scenarios |
| `BUCKET_PLATFORM_ARCHITECTURE.md` | Platform architecture |
| `config/scale_limits.py` | Scale limit constants |
| `docs/15_scale_readiness.md` | Scale certification |
| `DEPLOYMENT_PERSISTENCE_TRUTH_REPORT.md` | Deployment risks |
| `governance/RETENTION_POSTURE.md` | Retention policy |

---

*End of BUCKET_PLATFORM_OPERATIONS.md*
