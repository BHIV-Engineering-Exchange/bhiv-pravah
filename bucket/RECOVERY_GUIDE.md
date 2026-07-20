# RECOVERY_GUIDE

Date: 2026-06-17  
Status: OPERATOR-READY  
Full reference: `BUCKET_RECOVERY_AND_RESTORATION_GUIDE.md`

---

## Quick Decision Tree

```
Bucket down?
  │
  ├─ Files intact? ──YES──► Scenario A: Cold Restart
  │
  ├─ chain_state.json missing? ──► Scenario B: Rebuild from log
  │
  ├─ Last log line corrupt? ──► Scenario C: Truncate + rebuild
  │
  └─ Render redeployed? ──► Scenario E: Restore from backup / persistent disk
```

---

## Scenario A — Cold Restart (Normal)

**When:** Process killed. Files intact.

```bash
cd /path/to/bucket
python main.py
```

**Verify:**
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/bucket/validate-replay
```

**Expected:** `status: healthy`, `valid: true`

---

## Scenario B — Rebuild chain_state.json

**When:** `chain_state.json` missing or corrupted. `artifact_log.jsonl` intact.

1. **Stop** the service (block writes)
2. Replay log to rebuild state:

```bash
# Manual verification: read each line of artifact_log.jsonl
# Recompute hash for each artifact envelope
# Verify parent_hash chain sequentially
# Write rebuilt chain_state.json
```

3. **Restart** service
4. **Verify** with `POST /bucket/validate-replay`

**Critical rule:** If any line fails hash verification → **STOP. Escalate.**

---

## Scenario C — Corrupted Last Log Line

**When:** Process crashed mid-write. Last JSONL line incomplete.

1. Stop service
2. Identify last valid line in `artifact_log.jsonl`
3. Truncate file to last valid line
4. Rebuild `chain_state.json` (Scenario B)
5. Restart service
6. Notify producer to retry dropped write

---

## Scenario D — Full Data Loss (Render Ephemeral)

**When:** Render container redeployed without persistent disk.

**Prevention (required for production):**
```bash
BHIV_ARTIFACT_PATH=/data/artifacts   # mounted persistent disk
```

**Recovery:**
1. Restore `artifact_log.jsonl` and `chain_state.json` from backup
2. Place in persistence root
3. Start service
4. Run `POST /bucket/validate-replay`

Without backup: chain starts from genesis (empty). **All prior artifacts lost.**

---

## Recovery Invariants (Never Violate)

1. Artifacts are never deleted during recovery
2. Hash algorithm never changes
3. `chain_state.json` never advances beyond last verified entry
4. No writes during recovery until verification passes
5. `trace_id` values are never remapped

---

## Verification Checklist (Post-Recovery)

| Step | Command | Expected |
|------|---------|----------|
| 1 | `GET /health` | `healthy` |
| 2 | `GET /bucket/chain-state` | `artifact_count` matches log |
| 3 | `POST /bucket/validate-replay` | `valid: true` |
| 4 | `GET /bucket/artifact/{known_id}` | `chain_verified: true` |
| 5 | `GET /audit/recent` | Audit trail intact |

---

## Minimum Files for Recovery

| File | Required |
|------|----------|
| `main.py` | ✅ |
| `requirements.txt` | ✅ |
| `.env` | ✅ |
| `data/artifacts/artifact_log.jsonl` | ✅ |
| `data/artifacts/chain_state.json` | ✅ (rebuildable from log) |
| `services/append_only_storage.py` | ✅ |
| `validators/` | ✅ |

---

## Escalation

| Situation | Contact |
|-----------|---------|
| Hash verification failure during rebuild | BHIV Core (Raj Prajapati) |
| Persistent disk not mounted on Render | Bucket custodian |
| Schema drift between environments | Core + Bucket custodian |
| Producer retry after truncated log | Respective product team |

---

## Environment-Specific Paths

| Environment | Artifact log | Chain state |
|-------------|-------------|-------------|
| Local | `data/artifacts/artifact_log.jsonl` | `data/artifacts/chain_state.json` |
| Staging | `data/artifacts-staging/artifact_log.jsonl` | `data/artifacts-staging/chain_state.json` |
| Production | `/data/artifacts/artifact_log.jsonl` | `/data/artifacts/chain_state.json` |

---

*End of RECOVERY_GUIDE.md*
