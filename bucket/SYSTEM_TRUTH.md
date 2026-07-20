# SYSTEM_TRUTH

Date: 2026-06-17  
Status: CANONICAL — Ecosystem Survivability Convergence

---

## One-Line Truth

**Bucket is append-only evidence storage with deterministic hashing, trace preservation, and replay — it is not an orchestrator, intelligence engine, or execution authority.**

---

## What Bucket IS

| Property | Description |
|----------|-------------|
| Evidence substrate | Stores validated artifact envelopes immutably |
| Truth anchor | Append-only log is source-of-record for artifacts and provenance |
| Hash authority | Server computes SHA256 deterministically; clients cannot supply authoritative hash |
| Trace participant | Preserves `trace_id` verbatim across write → storage → read-back |
| Lineage enforcer | Validates `parent_hash` against current chain head |
| Replay substrate | Full chain reconstructable from `artifact_log.jsonl` |
| Observability participant | Exposes read paths and audit records for InsightFlow and operators |

---

## What Bucket IS NOT

| Anti-role | Confirmed by |
|-----------|--------------|
| Orchestrator | No workflow scheduling, no cross-system coordination |
| Intelligence engine | No payload interpretation or business logic |
| Execution authority | No action execution or authorization for other systems |
| Governance authority | Namespace approval owned by Core; Bucket enforces envelope only |
| Transformation layer | Payloads stored exactly as produced |

---

## Ecosystem Participation (Proven)

| System | Role | Proof |
|--------|------|-------|
| SVACS | Independent producer | `MULTI_PRODUCER_RUNTIME_PROOF.md`, `SVACS_BUCKET_LIVE_PROOF.md` |
| NICAI | Independent producer | `MULTI_PRODUCT_CONTRACT_GUIDE.md`, `MULTI_PRODUCER_RUNTIME_PROOF.md` |
| Core | Producer + contract authority | `REVIEW_PACKET.md`, `TANTRA_TRACE_CONTINUITY_PROOF.md` |
| InsightFlow | Read-only observer | `INSIGHTFLOW_OBSERVABILITY_PROOF.md` |

**Benchmark answer:** Bucket survives simultaneous multi-producer participation without role drift. ✅

---

## Guarantees

1. **Immutability** — artifacts never modified or deleted by normal operations
2. **Deterministic hashing** — canonical JSON (`sort_keys=True`, `separators=(',',':')`) → reproducible SHA256
3. **Lineage integrity** — sequential `parent_hash` chain enforced at write time
4. **Trace preservation** — `trace_id` included in hash input; tampering detectable
5. **Replayability** — `POST /bucket/validate-replay` verifies full chain
6. **Schema contract** — unknown envelope fields rejected (schema drift detection)
7. **Failure visibility** — all rejections audit-logged with explicit error messages

---

## Canonical Persistence

| Environment | Path | Survives restart? |
|-------------|------|-------------------|
| Local | `data/artifacts/artifact_log.jsonl` | ✅ |
| Staging | `data/artifacts-staging/` (via `BHIV_ARTIFACT_PATH`) | ✅ |
| Production | `/data/artifacts/` (persistent disk required) | ✅ with disk mount |

Reference: `PRODUCTION_HARDENING_REPORT.md`, `DEPLOYMENT_PERSISTENCE_TRUTH_REPORT.md`

---

## Canonical Schema (v1.0.0)

Required envelope fields:
```
artifact_id, trace_id, timestamp_utc, schema_version,
source_module_id, product_namespace, artifact_type, payload
```

Optional: `parent_hash` (required when chain non-empty)

Reference: `MULTI_PRODUCT_CONTRACT_GUIDE.md`, `GET /bucket/schema-info`

---

## Authority Model

Hybrid bounded multi-producer with Core as coordinator. InsightFlow read-only.

Reference: `AUTHORITY_BOUNDARIES.md`, `BUCKET_CONTRACT_AUTHORITY_MODEL.md`

---

## Operator Bundle

| Document | Purpose |
|----------|---------|
| `ROLE.md` | What Bucket is and is not |
| `AUTHORITY_BOUNDARIES.md` | Who can read/write |
| `RECOVERY_GUIDE.md` | Restore after failure |
| `REPLAY_GUIDE.md` | Verify chain integrity |
| `INTEGRATION_GUIDE.md` | Connect new producers/observers |
| `SYSTEM_TRUTH.md` | This document |

---

## Evidence Index

| Phase | Document |
|-------|----------|
| Multi-producer runtime | `MULTI_PRODUCER_RUNTIME_PROOF.md` |
| Cross-product replay | `CROSS_PRODUCT_REPLAY_PROOF.md` |
| InsightFlow observability | `INSIGHTFLOW_OBSERVABILITY_PROOF.md` |
| Production hardening | `PRODUCTION_HARDENING_REPORT.md` |
| Review packet | `REVIEW_PACKET.md` |

---

## Responsible Owners

| Role | Owner |
|------|-------|
| System owner / contract authority | Raj Prajapati (BHIV Core) |
| Testing & validation | Vinayak Tiwari |
| InsightFlow alignment | Nupur |
| SVACS integration | SVACS Team |
| NICAI integration | NICAI Team |

---

## Success Condition (Met)

- [x] SVACS, NICAI, Core independently participate in same chain
- [x] InsightFlow observes without write authority
- [x] Replay reconstructs chain from append-only log
- [x] Production persistence path documented
- [x] Recovery and replay operator guides produced
- [x] Bucket remains evidence storage only — zero execution authority

---

*End of SYSTEM_TRUTH.md*
