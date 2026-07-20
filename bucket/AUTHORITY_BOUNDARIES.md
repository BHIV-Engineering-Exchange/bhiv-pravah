# AUTHORITY_BOUNDARIES

Date: 2026-06-17  
Status: CANONICAL  
Source: `BUCKET_CONTRACT_AUTHORITY_MODEL.md` (consolidated for operators)

---

## 1. Canonical Model

**Hybrid Authority Model:** Bounded multi-producer contract participation with Core as authority coordinator.

Bucket's role does **not** change under this model. Only the **admission layer** expands to multiple approved producers.

---

## 2. Writer Authority Matrix

| System | Write? | Conditions |
|--------|--------|------------|
| BHIV Core (`bhiv_core`, `core_pipeline`) | ✅ Always | Valid envelope + lineage |
| SVACS (`svacs.*`) | ✅ Bounded | `product_namespace: SVACS` + approved `source_module_id` |
| NICAI (`nicai.*`) | ✅ Bounded | `product_namespace: NICAI` + approved `source_module_id` |
| Namami Gange (`namami.*`) | ✅ Bounded | `product_namespace: NAMAMI` + approved `source_module_id` |
| Sarathi (`sarathi.*`) | ✅ Bounded | `product_namespace: SARATHI` + `sarathi.enforcement_adapter` — see `SARATHI_BUCKET_INTEGRATION.md` |
| InsightFlow | ❌ Never | Read/observe only |
| Unknown callers | ❌ Rejected | HTTP 400 |

---

## 3. Read Authority Matrix

| System | Read? | Paths |
|--------|-------|-------|
| InsightFlow | ✅ Yes | `GET /bucket/artifact/{id}`, `GET /bucket/artifacts`, audit reads |
| BHIV Core | ✅ Yes | Contract read/query + direct reads |
| Operators | ✅ Yes | Health, chain-state, validate-replay |
| Producers | ✅ Yes | Read-back of own artifacts |
| Unknown callers | ✅ Open reads* | *Read endpoints are open; write boundaries enforced |

---

## 4. What Each Party Owns

| Responsibility | Owner |
|----------------|-------|
| Envelope schema definition | Bucket (API boundary) |
| `product_namespace` registry | BHIV Core (governance) |
| `artifact_type` registry | BHIV Core (governance) |
| `source_module_id` approval per product | Product team, ratified by Core |
| Payload semantic correctness | Producing product |
| Hash computation | Bucket (server-side, non-negotiable) |
| Lineage (`parent_hash`) validation | Bucket (against chain head) |
| Trace ID preservation | Bucket (stored verbatim) |
| Audit trail | Bucket audit middleware |
| Observability dashboards | InsightFlow |

---

## 5. Bucket Enforcement Boundaries

Bucket **enforces** at the API boundary:

- Required envelope fields present
- No unknown top-level fields (schema drift rejection)
- `schema_version` matches `1.0.0`
- Payload size within limit (16 MB)
- `parent_hash` matches current chain head
- Server-computed hash (client hash ignored)

Bucket **does not enforce**:

- Business logic inside `payload`
- Producer authorization beyond structural validation
- Cross-product write ordering
- Downstream action permissions

---

## 6. Core Contract Endpoints (Privileged)

These endpoints require `integration_id` matching Core:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/bucket/artifacts/write` | POST | Core-mediated write |
| `/bucket/artifacts/read` | POST | Deterministic read |
| `/bucket/artifacts/query` | POST | Filtered query |
| `/bucket/audit/read` | POST | Audit record query |

Direct write path `POST /bucket/artifact` is used by SVACS, NICAI, and integration proofs.

---

## 7. Violation Responses

| Violation | HTTP | Audit status |
|-----------|------|--------------|
| Unknown envelope field | 400 | `blocked` |
| Invalid `schema_version` | 400 | `blocked` |
| `parent_hash` mismatch | 400 | `blocked` |
| Duplicate `artifact_id` | 400 | `blocked` |
| Payload too large | 400 | `blocked` |
| Missing required field | 400 | `blocked` |

All rejections are visible in audit (`GET /audit/failed`).

---

## 8. InsightFlow Boundary (Explicit)

InsightFlow **must not**:

- Call write endpoints in production observability mode
- Modify artifact envelopes
- Transform stored payloads
- Authorize or block producer writes
- Execute actions based on artifact content

InsightFlow **may**:

- Read artifacts and audit records
- Correlate by `trace_id`
- Surface `chain_verified` status
- Alert on rejection events

Proof: `INSIGHTFLOW_OBSERVABILITY_PROOF.md`

---

## 9. Cross-Product Rules

1. SVACS cannot write with `product_namespace: NICAI` — governance violation (producer responsibility)
2. All products share the **same append-only chain** — lineage is global
3. Each product's payload semantics are opaque to Bucket
4. Replay identifies producer via `source_module_id` + `product_namespace`

---

## 10. Sign-Off Status

| Item | Status |
|------|--------|
| Hybrid model documented | ✅ |
| SVACS bounded write proven | ✅ (`SVACS_BUCKET_LIVE_PROOF.md`) |
| NICAI contract ratified | ✅ (`MULTI_PRODUCT_CONTRACT_GUIDE.md`) |
| Core write proven | ✅ (`REVIEW_PACKET.md`) |
| InsightFlow read-only proven | ✅ (`INSIGHTFLOW_OBSERVABILITY_PROOF.md`) |
| Formal governance sign-off | ⚠️ Pending Raj Prajapati |

---

*End of AUTHORITY_BOUNDARIES.md*
