# Sarathi → Bucket Integration Guide

**Audience:** Sarathi team (enforcement adapter)  
**Bucket owner:** Siddhesh Narkar  
**Status:** CANONICAL — Sarathi adapts to Bucket; no Bucket code changes required  
**Date:** 2026-06-17

---

## Purpose

This document defines how Sarathi integrates with BHIV Bucket using the **existing** Bucket contract. Sarathi owns hash verification and receipt posting. Bucket remains the central append-only evidence store and **server hash authority**.

**Out of scope:** Sarathi internal implementation details.

---

## Integration model

```
Sarathi                          Bucket (authority)                 Sarathi ack pipeline
   │                                    │                                    │
   │ 1. GET /bucket/latest-hash         │                                    │
   │ 2. POST /bucket/validate-structure │                                    │
   │ 3. POST /bucket/compute-hash       │                                    │
   │ 4. POST /bucket/artifact           │                                    │
   │───────────────────────────────────►│ validate + store + authority hash  │
   │◄────────────── sync 200 ─────────────│                                    │
   │ 5. GET /bucket/artifact/{id}       │                                    │
   │ 6. Verify hashes (Sarathi-side)    │                                    │
   │──────────────────────────────────────────────────────────────────────────►│
   │                         POST receipt (Sarathi or Core relay)             │
```

Bucket does **not**:
- Read `X-Sarathi-*` headers
- Compare `body_hash` / `response_hash` from Sarathi
- POST to `/v1/downstream-ack`
- Persist raw wire bytes verbatim

---

## 1. BHIV envelope (required)

**Endpoint:** `POST https://<bucket-url>/bucket/artifact`  
**Content-Type:** `application/json`

### Request body

```json
{
  "artifact_id": "<uuid — Sarathi generates, must be unique>",
  "trace_id": "<uuid>",
  "timestamp_utc": "2026-06-17T12:00:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "sarathi.enforcement_adapter",
  "product_namespace": "SARATHI",
  "artifact_type": "enforcement_decision",
  "parent_hash": "<from GET /bucket/latest-hash last_hash>",
  "payload": {
    "decision_id": "<id>",
    "verdict": "ALLOW",
    "evaluator_id": "bhiv.sovereign.decision.prod.v1",
    "decision_hash": "<64-hex>",
    "decision_core_hash": "<64-hex>",
    "enforcement_hash": "<64-hex>",
    "response_hash": "<64-hex>",
    "chain_binding_hash": "<64-hex>",
    "policy_reference": "<policy_pack_id@version>",
    "input_hash": "<64-hex>",
    "agent_id": "<id>",
    "resource_id": "<id>",
    "action": "execute",
    "obligations": [],
    "enforced_at": "2026-06-17T12:00:00.000000000Z",
    "sealed_at": "2026-06-17T12:00:00.000000000Z",
    "canonical_response_b64": "<base64-std of sealed 20-field response bytes>"
  }
}
```

### Schema mapping (Sarathi spec → Bucket)

| Sarathi v15.12 spec | Required for Bucket |
|---------------------|---------------------|
| `schema_version: "bhiv.bucket.artifact/v1.0"` | → `"1.0.0"` |
| `artifact_id = sha256(payload)` | → **UUID** (unique per write) |
| No `product_namespace` | → `"product_namespace": "SARATHI"` |
| No top-level `trace_id` | → Add `trace_id` at envelope level |
| `X-Sarathi-*` headers required | → Optional metadata only (Bucket ignores today) |

### Genesis write (empty chain)

When `GET /bucket/latest-hash` returns `"last_hash": null` and `"artifact_count": 0`:
- Omit `parent_hash` or set to `null`
- Do not send a parent hash for the first artifact

---

## 2. Hash verification (Sarathi-side)

Bucket computes the **authority hash** over the canonical envelope. Sarathi mints and verifies **transport** and **decision** hashes locally.

### Before send (Sarathi)

```python
import base64
import hashlib
import json

def sarathi_mint_hashes(envelope: dict) -> dict:
    # Transport: canonical JSON of envelope you will POST
    wire = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    minted_body_hash = hashlib.sha256(wire).hexdigest()

    # Decision: sealed canonical response bytes
    canonical_bytes = base64.b64decode(envelope["payload"]["canonical_response_b64"])
    minted_response_hash = hashlib.sha256(canonical_bytes).hexdigest()

    return {
        "minted_body_hash": minted_body_hash,
        "minted_response_hash": minted_response_hash,
    }
```

Store both keyed by `payload.decision_id`.

### Bucket authority hash (preview before write)

```http
POST /bucket/compute-hash
Content-Type: application/json

<same envelope as write>
```

**Response:**
```json
{
  "artifact_id": "<uuid>",
  "computed_hash": "<64-hex>",
  "algorithm": "SHA256",
  "deterministic": true
}
```

Bucket hash input fields: `artifact_id`, `trace_id`, `timestamp_utc`, `schema_version`, `source_module_id`, `product_namespace`, `artifact_type`, `parent_hash`, `payload` — serialized with `sort_keys=True`, `separators=(',', ':')`.

### After Bucket 200 response

```http
GET /bucket/artifact/{artifact_id}
```

Confirm:
- HTTP 200
- `chain_verified: true`
- `trace_id` and `payload.decision_id` match what Sarathi sent
- Re-run Sarathi minted hash checks against read-back payload

**Do not expect HTTP 412** from Bucket. Schema/lineage failures return **400**.

---

## 3. Persistence expectations

Bucket parses JSON and appends to `artifact_log.jsonl`. Stored bytes may differ from Sarathi wire bytes (field order, whitespace).

| Proof type | Owner | Method |
|------------|-------|--------|
| Chain / custody | Bucket | `hash` in 200 response + `chain_verified` on read |
| Transport integrity | Sarathi | `minted_body_hash` vs local copy of sent envelope |
| Decision integrity | Sarathi | `minted_response_hash` vs `canonical_response_b64` after read-back |

---

## 4. Receipt / downstream-ack (Sarathi-owned)

Bucket does **not** POST to `https://<sarathi-url>/v1/downstream-ack`.

### Option A — Sarathi posts receipt (recommended)

After successful Bucket write + read-back verification:

```json
POST <sarathi-internal-ack-endpoint>
{
  "schema_version": "sarathi.live.receipt/v1.0",
  "peer": "sarathi",
  "execution_id": "<execution id>",
  "decision_id": "<id>",
  "response_hash": "<minted_response_hash>",
  "received_body_hash": "<minted_body_hash>",
  "observed_response_hash": "<sha256 of canonical_response bytes>",
  "chain_binding_hash": "<from payload>",
  "persisted_at": "<RFC3339Nano UTC>",
  "storage_path": "bucket://artifact/<artifact_id>",
  "bucket_hash": "<hash from Bucket 200 response>",
  "bucket_artifact_id": "<artifact_id from Bucket 200 response>"
}
```

### Option B — Core relay

BHIV Core receives Bucket sync response, signs Ed25519 receipt, POSTs to Sarathi `/v1/downstream-ack` with `"peer": "core"` if Sarathi gate accepts Core.

**Sarathi must remove:**
- Dependency on Bucket async receipt within 300s
- Dependency on Bucket `peer_public_key_hex` / `receipt_signature` (unless Core relay)

---

## 5. Idempotency

| Sarathi spec | Bucket behavior |
|--------------|-----------------|
| Idempotent on `decision_id` | Idempotent on **`artifact_id`** only |
| Same `decision_id`, different body → 409 | Same `artifact_id` → **400 duplicate** |

**Sarathi implementation:**

```python
import uuid

NAMESPACE_SARATHI = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # register with Core

def artifact_id_for_decision(decision_id: str) -> str:
    return str(uuid.uuid5(NAMESPACE_SARATHI, decision_id))
```

On retry: send the **same** `artifact_id` and identical envelope.

---

## 6. Chain / lineage

```http
GET https://<bucket-url>/bucket/latest-hash
```

```json
{
  "last_hash": "<64-hex or null>",
  "artifact_count": 7
}
```

Use `last_hash` as `parent_hash` on every write. Always fetch before POST — do not hardcode genesis hash.

---

## 7. Bucket success response

```json
{
  "success": true,
  "artifact_id": "<uuid>",
  "hash": "<bucket-authority-sha256>",
  "parent_hash": "<chain parent or null>",
  "timestamp": "<timestamp_utc>",
  "storage_type": "append_only",
  "message": "Artifact stored successfully in append-only log"
}
```

**Sarathi must not expect:**
- `X-Sarathi-Ack-Hash` response header
- Body shape `{ peer, ack_hash, storage_path, endpoint }`

Use `hash` + `artifact_id` as persistence proof.

---

## 8. Pre-send validation checklist

```bash
# 1. Schema info
curl https://<bucket-url>/bucket/schema-info

# 2. Dry-run structure
curl -X POST https://<bucket-url>/bucket/validate-structure \
  -H "Content-Type: application/json" \
  -d @envelope.json

# 3. Preview authority hash
curl -X POST https://<bucket-url>/bucket/compute-hash \
  -H "Content-Type: application/json" \
  -d @envelope.json

# 4. Chain head
curl https://<bucket-url>/bucket/latest-hash

# 5. Write
curl -X POST https://<bucket-url>/bucket/artifact \
  -H "Content-Type: application/json" \
  -d @envelope.json

# 6. Read-back
curl https://<bucket-url>/bucket/artifact/<artifact_id>

# 7. Chain integrity (optional)
curl -X POST https://<bucket-url>/bucket/validate-replay
```

---

## 9. Payload fields (unchanged inside `payload`)

Sarathi keeps all enforcement semantics inside `payload`. Bucket stores opaque:

- `decision_id`, `verdict`, `evaluator_id`
- `decision_hash`, `decision_core_hash`, `enforcement_hash`, `response_hash`, `chain_binding_hash`
- `policy_reference`, `input_hash`, `agent_id`, `resource_id`, `action`, `obligations`
- `enforced_at`, `sealed_at`, `canonical_response_b64`

---

## 10. Error handling

| HTTP | Cause | Sarathi action |
|------|-------|----------------|
| 400 | Missing field, unknown envelope field, bad schema version | Fix envelope; check `GET /bucket/schema-info` |
| 400 | `parent_hash` mismatch | Re-fetch `GET /bucket/latest-hash` and retry |
| 400 | Duplicate `artifact_id` | Treat as success if body identical; else escalate |
| 404 | Read-back before propagation | Retry with backoff |
| 500 | Server error | Retry with exponential backoff; same `artifact_id` |

---

## 11. Registration (out-of-band)

| Item | Direction | Notes |
|------|-----------|-------|
| `source_module_id` | Sarathi → Core | `sarathi.enforcement_adapter` ratified by Raj Prajapati |
| `product_namespace` | Sarathi → Core | `SARATHI` |
| Bucket POST URL | Bucket → Sarathi | `https://<bucket-host>/bucket/artifact` |
| Bucket GET URL | Bucket → Sarathi | `https://<bucket-host>/bucket/artifact/{artifact_id}` |
| Sarathi ack URL | Sarathi → Core | Internal or `/v1/downstream-ack` (Sarathi posts, not Bucket) |

---

## 12. Quick reference — Sarathi change list

| # | Change in Sarathi |
|---|-------------------|
| 1 | Use BHIV envelope: `schema_version: "1.0.0"`, `product_namespace: "SARATHI"`, UUID `artifact_id`, top-level `trace_id` |
| 2 | Stop requiring Bucket to read `X-Sarathi-*` headers |
| 3 | Run body + response hash verification on Sarathi side after Bucket 200 + read-back |
| 4 | POST receipt from Sarathi (or Core relay) — not from Bucket |
| 5 | Idempotency on `artifact_id`; map from `decision_id` via UUID5 |
| 6 | Fetch `parent_hash` from `GET /bucket/latest-hash` before each write |
| 7 | Parse Bucket's actual 200 response; use `hash` + `artifact_id` as proof |
| 8 | Call `validate-structure` and `compute-hash` before live writes |
| 9 | Keep enforcement fields inside `payload` unchanged |

---

## 13. Related documents

| Document | Purpose |
|----------|---------|
| `MULTI_PRODUCT_CONTRACT_GUIDE.md` | Multi-product envelope rules |
| `INTEGRATION_GUIDE.md` | General producer integration |
| `AUTHORITY_BOUNDARIES.md` | Who reads/writes |
| `docs/HASH_AUTHORITY_POLICY.md` | Server hash authority policy |
| `governance/INTEGRATION_BOUNDARY.md` | Bucket one-way data flow |

---

*End of SARATHI_BUCKET_INTEGRATION.md*
