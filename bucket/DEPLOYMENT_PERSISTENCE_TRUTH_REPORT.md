# DEPLOYMENT_PERSISTENCE_TRUTH_REPORT

Version: 1.0
Date: 2026-06-09
Status: CANONICAL
Prepared by: Integration Sprint — Phase 4 Convergence

---

## 1. PURPOSE

Close the operational ambiguity between local, staging, and deployed persistence states.
Answer exactly: Where is canonical truth? What survives? What restores first?

---

## 2. ENVIRONMENT INVENTORY

| Environment | Base URL | Persistence Root | Status |
|-------------|----------|-----------------|--------|
| **Local** | `http://127.0.0.1:8005` | `data/artifacts/artifact_log.jsonl` + `data/chain_state.json` | Active (dev/test) |
| **Staging** | `http://127.0.0.1:8005` (separate instance) | `data/artifacts-staging/artifact_log.jsonl` | Active (integration tests) |
| **Deployed (Render)** | `https://bhiv-bucket.onrender.com` | Render ephemeral filesystem (see Section 4) | Active (production) |

---

## 3. CANONICAL PERSISTENCE ANSWER

**Q: Where is canonical Bucket persistence?**

> **A: The deployed Render instance (`https://bhiv-bucket.onrender.com`) is the canonical persistence environment for TANTRA integration.**

However, as documented in `TRACE_CONTINUITY_PROOF.md`, the deployed instance had a schema mismatch (rejected `trace_id` as an unknown envelope field). Until this divergence is resolved, **staging is the operational truth surface for integration testing**.

### Environment authority hierarchy:
```
Deployed (Render) — canonical for production TANTRA traffic
       ↓
Staging (local, mirrored schema) — canonical for integration test validation
       ↓
Local dev — canonical for development and feature iteration
```

**Cross-environment rule:** Artifacts written in one environment DO NOT appear in another. Each environment maintains an independent append-only log and chain state.

---

## 4. STORAGE PATH AUTHORITY

### 4.1 Local / Staging — File-based Storage

| Artifact | Path |
|----------|------|
| Artifact log (append-only) | `data/artifacts/artifact_log.jsonl` |
| Chain state | `data/chain_state.json` |
| Audit log (file fallback) | `data/audit.log` |
| Staging artifact log | `data/artifacts-staging/artifact_log.jsonl` |

Chain state file structure:
```json
{
  "artifact_count": <integer>,
  "last_hash": "<sha256hex>",
  "last_artifact_id": "<artifact_id>",
  "last_timestamp": "<ISO8601>"
}
```

### 4.2 Deployed (Render) — Persistence Considerations

**CRITICAL:** Render free/hobby tier runs on **ephemeral filesystem**. This means:
- The `data/` directory is **not persistent across deploys or restarts**
- If Render restarted the container, `artifact_log.jsonl` and `chain_state.json` are **lost**
- MongoDB is configured in `.env` (`MONGODB_URI`) but is currently pointing to `localhost` — this does NOT work on Render

**Current deployed persistence risk:** 🔴 HIGH — no persistent volume configured, no working remote MongoDB.

### Recommended fix for production:
Option A — Mount Render Persistent Disk to `/data` path
Option B — Replace file-based storage with Supabase or cloud MongoDB (Atlas)

Until resolved, **production Bucket cannot guarantee artifact survival across deploys**.

---

## 5. WHAT SURVIVES NODE LOSS

| Item | Local | Staging | Deployed (current) |
|------|-------|---------|-------------------|
| `artifact_log.jsonl` | ✅ Survives restart | ✅ Survives restart | ❌ Lost on redeploy (ephemeral) |
| `chain_state.json` | ✅ Survives restart | ✅ Survives restart | ❌ Lost on redeploy (ephemeral) |
| `audit.log` | ✅ Survives restart | ✅ Survives restart | ❌ Lost on redeploy (ephemeral) |
| MongoDB audit records | Only if Mongo running locally | Only if Mongo running | ❌ Not working (localhost URI) |
| In-memory state | ❌ Lost on process restart | ❌ Lost on process restart | ❌ Lost on restart |

---

## 6. WHAT RESTORES FIRST

On cold start (process restart with existing files), the restore order is:

1. **`chain_state.json`** — loaded first; sets `artifact_count` and `last_hash`
2. **`artifact_log.jsonl`** — opened in append mode; not re-read unless recovery mode
3. **`audit.log`** — opened in append mode; prior records remain
4. **In-memory index** — rebuilt from `artifact_log.jsonl` scan on startup (if implemented)

### Recovery bootstrap sequence:
```
Process start
  → Load chain_state.json (sets chain head)
  → Open artifact_log.jsonl (append mode)
  → Service ready to accept writes
```

If `chain_state.json` is missing but `artifact_log.jsonl` exists:
→ Rebuild `chain_state.json` by replaying `artifact_log.jsonl` from line 1 to last line
→ Recompute `artifact_count`, `last_hash`, `last_artifact_id`
→ Write rebuilt `chain_state.json`

If both are missing: chain starts from genesis (empty, `artifact_count: 0`).

---

## 7. MINIMUM ARTIFACT SET REQUIRED FOR OPERATION

| File | Required? | Notes |
|------|-----------|-------|
| `main.py` | ✅ YES | Service entry point |
| `data/` directory | ✅ YES | Created automatically on first write |
| `data/artifact_log.jsonl` | AUTO-CREATED | Created on first successful artifact write |
| `data/chain_state.json` | AUTO-CREATED | Created/updated on every write |
| `.env` | ✅ YES | Must have `FASTAPI_PORT` set |
| `requirements.txt` | ✅ YES | All deps must be installed |
| `validators/` | ✅ YES | Validation layer |
| `services/append_only_storage.py` | ✅ YES | Core storage logic |

**Minimum restore set**: `main.py` + `requirements.txt` + `.env` + `data/artifact_log.jsonl` + `data/chain_state.json`

---

## 8. ENVIRONMENT SEPARATION RULES

| Rule | Description |
|------|-------------|
| **Never share data directories** | Local and staging must use different `data/` paths |
| **Never run staging against production chain** | Staging writes corrupt production lineage |
| **Schema must match across environments** | The deployed instance rejected `trace_id` because envelope schema diverged — this must be synchronized before live integration |
| **No cross-environment artifact reads** | An `artifact_id` written locally cannot be read from deployed — chains are independent |
| **Environment variable enforcement** | Use `ENVIRONMENT=local`, `ENVIRONMENT=staging`, `ENVIRONMENT=production` to explicitly label runtime |

---

## 9. DEGRADED NODE EXPECTATIONS

| Degraded Scenario | Expected Behavior |
|-------------------|------------------|
| MongoDB unavailable | Audit falls back to `data/audit.log` file — artifact writes continue |
| Redis unavailable | Redis is not currently in the critical write path — no impact |
| `chain_state.json` corrupted | Refuse writes; trigger recovery replay from `artifact_log.jsonl` |
| `artifact_log.jsonl` partially written (crash mid-write) | Last line may be incomplete; truncate and rebuild chain state from last valid line |
| Render container restart (ephemeral disk) | All in-flight and stored artifacts lost unless persistent volume is mounted |
| Network partition (client timeout) | Write either committed or not — no partial commits; client must retry with same `artifact_id` |

---

## 10. OPEN ACTIONS TO CLOSE PRODUCTION AMBIGUITY

| Action | Owner | Priority |
|--------|-------|----------|
| Mount Render Persistent Disk (`/data`) | Siddhesh (Bucket custodian) | 🔴 CRITICAL |
| Update `MONGODB_URI` to Atlas or remote Mongo | Siddhesh | 🔴 CRITICAL |
| Synchronize envelope schema between local and deployed (add `trace_id` to allowed fields) | Siddhesh + Raj | 🔴 CRITICAL |
| Add `ENVIRONMENT` env var to distinguish runtime context | Siddhesh | 🟡 HIGH |
| Add startup chain verification log line | Siddhesh | 🟡 HIGH |

---

## 11. SUCCESS CONDITION

This report resolves all ambiguity between environments.

**No ambiguity remains** on these questions:

| Question | Answer |
|----------|--------|
| Where is canonical persistence? | Deployed Render (production); staging for integration test validation |
| What survives node loss? | Nothing on deployed (ephemeral) without persistent disk; everything on local with files present |
| What restores first? | `chain_state.json`, then `artifact_log.jsonl` |
| What minimum artifact set is required? | `main.py` + `requirements.txt` + `.env` + `data/artifact_log.jsonl` + `data/chain_state.json` |
| How are environments separated? | Independent data directories; no shared state; schema must be synchronized |

---

*End of DEPLOYMENT_PERSISTENCE_TRUTH_REPORT.md*
