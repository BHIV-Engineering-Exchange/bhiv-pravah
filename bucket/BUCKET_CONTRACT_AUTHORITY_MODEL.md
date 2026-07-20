# BUCKET_CONTRACT_AUTHORITY_MODEL

Version: 1.0
Date: 2026-06-09
Status: CANONICAL — supersedes all prior conflicting wording
Prepared by: Integration Sprint — Phase 3 Convergence

---

## 1. PURPOSE

This document resolves the operational ambiguity between:
- "Core-exclusive write authority" (old contract spec)
- "multi-product ecosystem participation" (multi-product guide)

One model must be canonical. This document declares it.

---

## 2. CANONICAL MODEL — OPTION C: HYBRID AUTHORITY MODEL

**Bucket adopts Option C: Bounded Multi-Producer Contract Participation with Core as Authority Coordinator.**

This is NOT a relaxation of Bucket's role. Bucket remains:
- Immutable persistence substrate
- Deterministic replay participant
- Trace participant
- Truth anchoring substrate

The model change is at the **admission layer**, not at the storage layer.

---

## 3. AUTHORITY BOUNDARY DEFINITIONS

### 3.1 Allowed Writers

| Writer | Allowed? | Conditions |
|--------|----------|------------|
| BHIV Core (`bhiv_core`) | ✅ YES — always | No additional approval needed |
| SVACS (`svacs.*`) | ✅ YES — bounded | Must include valid `product_namespace: SVACS` and approved `source_module_id` |
| NICAI (`nicai.*`) | ✅ YES — bounded | Must include valid `product_namespace: NICAI` and approved `source_module_id` |
| Namami Gange (`namami.*`) | ✅ YES — bounded | Must include valid `product_namespace: NAMAMI` and approved `source_module_id` |
| InsightFlow | ❌ NO direct writes | InsightFlow is a read/observe participant only — it subscribes to audit events and telemetry. It does NOT write artifacts. |
| Unknown / unapproved callers | ❌ REJECTED | 400 — not an approved integration |

### 3.2 What Changes Per Writer

All writers — including Core — must conform to the **same artifact envelope**:
```
artifact_id, trace_id, timestamp_utc, schema_version,
source_module_id, product_namespace, artifact_type,
parent_hash (null for genesis), payload
```

There is **no special fast-path** for Core. Core is simply the most trusted and always-permitted writer.

### 3.3 Contract Ownership

| Contract Component | Owner |
|-------------------|-------|
| Envelope schema definition | Bucket (enforced at API boundary) |
| `product_namespace` registry | BHIV Core (governance authority) |
| `artifact_type` registry | BHIV Core (governance authority) |
| Per-product `source_module_id` approval | Respective product team, ratified by Core |
| Lineage chain integrity | Bucket (server-computed, non-negotiable) |
| Hash computation | Bucket (server-side, canonical, clients cannot supply authoritative hash) |

### 3.4 Validation Responsibility

| Validation Step | Responsible Party |
|----------------|-------------------|
| Envelope structural validation | Bucket API boundary |
| Schema version check | Bucket API boundary |
| `product_namespace` allowed-list | Bucket API boundary (sourced from governance registry) |
| Payload semantic correctness | Producing product (Bucket does NOT inspect payload) |
| Lineage (`parent_hash`) validity | Bucket — computed against current chain head |
| Trace ID preservation | Bucket — stored exactly as provided, never remapped |

---

## 4. AUTHORITY BOUNDARIES

### 4.1 What Bucket WILL enforce
- Structural envelope validation (required fields, no unknown top-level fields)
- `schema_version` must be in approved list
- `product_namespace` must be in governance-approved registry
- `parent_hash` must match current chain head (or null for genesis)
- Server-computed SHA256 hash — client-supplied hashes are ignored
- `trace_id` stored and returned exactly as received — zero mutation

### 4.2 What Bucket WILL NOT enforce
- Product-specific payload logic (e.g. vessel types, sensor readings)
- Cross-product correlation (Bucket does not join traces across products)
- Execution triggers or workflow orchestration
- Payload semantic validation (only structure is checked)

### 4.3 What requires Core coordination
- Adding a new `product_namespace` to the approved list
- Adding new `artifact_type` values to the registry
- Deprecating or migrating schema versions
- Any change to Bucket's `ALLOWED_ENVELOPE_FIELDS`

---

## 5. REPLAY IMPLICATIONS

The hybrid model does NOT change replay behavior:
- Replay reconstructs the **full append-only log** deterministically
- Each artifact can be identified by `product_namespace` and `source_module_id` during replay
- Hash chain is product-agnostic — one chain, all products contribute to it in append order
- Replay verification recomputes SHA256 over canonical envelope and compares to stored hash — same logic regardless of producer

### Per-product replay filter (read-only, non-mutating):
```
GET /bucket/artifacts/query?product_namespace=SVACS
```
This enables product-scoped replay validation without breaking chain integrity.

---

## 6. MULTI-PRODUCT PARTICIPATION RULES

1. **One shared chain.** All products write to the same append-only chain. There are no per-product sub-chains.
2. **Trace IDs are product-owned.** Each product generates and owns its `trace_id`. Bucket preserves it verbatim.
3. **Payload is opaque.** Bucket stores `payload` as-is. Products are responsible for payload structure.
4. **No cross-product writes.** SVACS cannot write an artifact with `product_namespace: NICAI`. Violation → 400 rejected.
5. **Genesis writes.** First artifact from any product must have `parent_hash: null` only if it is also the chain genesis. Otherwise it must link to the current chain head.
6. **InsightFlow participation.** InsightFlow observes via audit event stream and telemetry — never via direct artifact write.

---

## 7. FAILURE / REJECTION BEHAVIOR

| Violation | HTTP Code | Behavior |
|-----------|-----------|----------|
| Unknown `product_namespace` | 400 | Rejected, audit log: `blocked` |
| Unknown envelope field | 422 | Pydantic validation error |
| Wrong `schema_version` | 400 | Rejected with expected version |
| Broken lineage | 400 | Rejected with expected `parent_hash` |
| Oversized payload (>16MB) | 400 | Rejected |
| Non-approved `source_module_id` | 400 | Rejected (if governance strict mode enabled) |

All rejections are **visible** — they appear in audit log with `status: blocked` and `error_message`.

---

## 8. REMOVAL OF OLD AMBIGUITY

The following previously conflicting statements are now resolved:

| Old Conflict | Resolution |
|-------------|------------|
| `CONTRACT_SPEC.md`: "Only Core integration is allowed on contract endpoints." | **SUPERSEDED** — Core is always allowed; other approved products are also allowed under bounded rules. |
| `MULTI_PRODUCT_CONTRACT_GUIDE.md`: "multi-product participation" without authority boundary | **CLARIFIED** — participation is bounded by this model. Governance approval required per product namespace. |
| Confusion about InsightFlow writing vs observing | **RESOLVED** — InsightFlow is read/observe only. Zero write authority. |

---

## 9. SIGN-OFF REQUIREMENT

This model becomes operational only after:
- [ ] BHIV Core (Raj Prajapati) ratifies Section 3.3 (contract ownership)
- [ ] Each product team (SVACS, NICAI, Namami) confirms their `source_module_id` list
- [ ] Governance registry updated with approved `product_namespace` tokens
- [ ] `CONTRACT_SPEC.md` updated to reference this document as canonical

Until sign-off, **current behavior (Core-only) remains the operative default**.

---

## 10. ONE-LINE AUTHORITY STATEMENT

> Bucket enforces a shared, product-neutral append-only contract where BHIV Core is always permitted and bounded multi-producer participation is allowed for governance-approved products (SVACS, NICAI, Namami) — InsightFlow observes only — hash chain integrity, trace preservation, and payload immutability are unconditional.

---

*End of BUCKET_CONTRACT_AUTHORITY_MODEL.md*
