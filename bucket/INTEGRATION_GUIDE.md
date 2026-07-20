# INTEGRATION_GUIDE

Date: 2026-06-17  
Status: OPERATOR-READY  
Full references: `MULTI_PRODUCT_CONTRACT_GUIDE.md`, `INTEGRATION_MAP.md`, `SVACS_BUCKET_INTEGRATION.md`

---

## Overview

This guide enables a new integrator to connect a BHIV product to Bucket as a producer or observer.

```
Producer (SVACS/NICAI/Core) ──POST──► Bucket ──GET──► Observer (InsightFlow)
```

---

## 1. Producer Integration

### Step 1 — Obtain namespace approval

Contact Raj Prajapati (BHIV Core) for:
- `product_namespace` token (e.g. `SVACS`, `NICAI`, `CORE`)
- Approved `source_module_id` (e.g. `svacs.perception`, `nicai.collector`)

### Step 2 — Get current chain head

```bash
curl http://<bucket-host>/bucket/latest-hash
```

Response:
```json
{
  "last_hash": "<sha256hex_or_null>",
  "artifact_count": 7
}
```

Use `last_hash` as `parent_hash`. Use `null` (omit field) if `artifact_count` is 0.

### Step 3 — Compose artifact envelope

```json
{
  "artifact_id": "<uuid>",
  "trace_id": "<cross-product-correlation-id>",
  "timestamp_utc": "2026-06-17T12:00:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "<approved-module-id>",
  "product_namespace": "<APPROVED_NAMESPACE>",
  "artifact_type": "<type>",
  "parent_hash": "<last_hash_from_step_2>",
  "payload": { }
}
```

### Step 4 — Write artifact

```bash
curl -X POST http://<bucket-host>/bucket/artifact \
  -H "Content-Type: application/json" \
  -d @artifact.json
```

**Success (HTTP 200):**
```json
{
  "success": true,
  "artifact_id": "<uuid>",
  "hash": "<server-computed-sha256>",
  "parent_hash": "<parent>",
  "storage_type": "append_only"
}
```

### Step 5 — Verify read-back

```bash
curl http://<bucket-host>/bucket/artifact/<artifact_id>
```

Confirm `chain_verified: true` and `trace_id` matches your input.

---

## 2. Core Contract Integration

For Core-mediated writes, use the contract path:

```bash
curl -X POST http://<bucket-host>/bucket/artifacts/write \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": "core_service",
    "integration_id": "bhiv_core",
    "artifact": { }
  }'
```

Requires `integration_id` matching Core. See `REVIEW_PACKET.md` for live request/response pairs.

---

## 3. Observer Integration (InsightFlow)

InsightFlow integrates as **read-only**:

| Path | Purpose |
|------|---------|
| `GET /bucket/artifact/{id}` | Single artifact with `chain_verified` |
| `GET /bucket/artifacts?trace_id=` | Trace correlation |
| `GET /bucket/artifacts?limit=&offset=` | Chronological listing |
| `GET /audit/recent` | Recent operations |
| `GET /audit/failed` | Rejection alerting |

**Do not** call write endpoints from InsightFlow.

Reference: `INSIGHTFLOW_BUCKET_ALIGNMENT.md`

---

## 4. Product-Specific Examples

### SVACS

```json
{
  "source_module_id": "svacs.perception",
  "product_namespace": "SVACS",
  "artifact_type": "perception",
  "payload": {
    "vessel_type": "cargo",
    "confidence_score": 0.94,
    "pipeline": "SVACS"
  }
}
```

Live proof: `SVACS_BUCKET_LIVE_PROOF.md`

### NICAI

```json
{
  "source_module_id": "nicai.collector",
  "product_namespace": "NICAI",
  "artifact_type": "ingestion",
  "payload": {
    "sensor": "lidar",
    "pipeline": "NICAI"
  }
}
```

Contract: `MULTI_PRODUCT_CONTRACT_GUIDE.md`

### Core

```json
{
  "source_module_id": "core_pipeline",
  "product_namespace": "CORE",
  "artifact_type": "integration_event",
  "payload": {
    "message": "contract ratification event"
  }
}
```

Live proof: `REVIEW_PACKET.md`

### Sarathi

```json
{
  "source_module_id": "sarathi.enforcement_adapter",
  "product_namespace": "SARATHI",
  "artifact_type": "enforcement_decision",
  "payload": {
    "decision_id": "<id>",
    "verdict": "ALLOW",
    "canonical_response_b64": "<base64>"
  }
}
```

Full spec: `SARATHI_BUCKET_INTEGRATION.md`

---

## 5. Validation Rules

| Rule | Enforced by |
|------|-------------|
| All required fields present | Bucket API |
| `schema_version` = `1.0.0` | Bucket API |
| No unknown top-level fields | Bucket API |
| `parent_hash` = current chain head | Bucket API |
| Payload ≤ 16 MB | Bucket API |
| Payload semantics | Producer (not Bucket) |
| `trace_id` preservation | Bucket (stored verbatim) |

---

## 6. Error Handling

| Error | HTTP | Fix |
|-------|------|-----|
| Missing field | 400 | Add required field |
| Unknown field | 400 | Remove extra field |
| Bad schema version | 400 | Set `1.0.0` |
| Parent hash mismatch | 400 | Re-fetch `/bucket/latest-hash` |
| Duplicate artifact_id | 400 | Use new UUID |

All errors are audit-logged. Check `GET /audit/failed`.

---

## 7. Staging vs Production

| Setting | Staging | Production |
|---------|---------|------------|
| `BHIV_ARTIFACT_PATH` | `data/artifacts-staging` | `/data/artifacts` |
| `ENVIRONMENT` | `staging` | `production` |
| Base URL | `http://127.0.0.1:8005` | `https://bhiv-bucket.onrender.com` |

**Never** point staging at production data directories.

---

## 8. Integration Checklist

- [ ] Namespace approved by Core
- [ ] `source_module_id` registered
- [ ] Envelope matches schema (`GET /bucket/schema-info`)
- [ ] Write + read-back succeeds on staging
- [ ] `trace_id` preserved on read-back
- [ ] `POST /bucket/validate-replay` returns `valid: true`
- [ ] Failure cases tested (bad parent_hash, bad schema)
- [ ] InsightFlow can observe artifacts (if applicable)
- [ ] Production persistent disk configured

---

## 9. Contacts

| Role | Contact |
|------|---------|
| Contract authority | Raj Prajapati (BHIV Core) |
| Testing | Vinayak Tiwari |
| InsightFlow | Nupur |
| SVACS | SVACS Team |
| NICAI | NICAI Team |

---

*End of INTEGRATION_GUIDE.md*
