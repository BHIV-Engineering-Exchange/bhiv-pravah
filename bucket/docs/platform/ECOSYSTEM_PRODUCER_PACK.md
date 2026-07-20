# Ecosystem Producer Integration Pack

**Document ID:** BUCKET-PRODUCER-001  
**Version:** 1.0.0  
**Date:** 19 June 2026  
**Status:** CANONICAL  
**Owner:** Siddhesh Narkar — Bucket Custodian  
**Purpose:** Standard onboarding guide for all BHIV ecosystem producers

---

## 1. Universal Producer Contract

Every BHIV product integrates with Bucket using the **same evidence contract**. No product-specific Bucket code paths exist.

### 1.1 Standard Envelope

```json
{
  "artifact_id": "<uuid — producer-generated, globally unique>",
  "trace_id": "<uuid — cross-system correlation>",
  "timestamp_utc": "<ISO8601 UTC>",
  "schema_version": "1.0.0",
  "source_module_id": "<ratified module id>",
  "artifact_type": "<ratified type>",
  "parent_hash": "<from GET /bucket/latest-hash — omit for genesis>",
  "payload": { }
}
```

### 1.2 Universal Write Flow

```
1. GET  /bucket/latest-hash
2. POST /bucket/validate-structure  (optional dry-run)
3. POST /bucket/compute-hash        (optional preview)
4. POST /bucket/artifact
5. GET  /bucket/artifact/{artifact_id}  (read-back verify)
6. POST /bucket/validate-replay      (optional chain audit)
```

### 1.3 Universal Ownership Boundaries

| Responsibility | Owner |
|----------------|-------|
| Envelope structure | Bucket (validates) |
| Payload semantics | Producer |
| Hash computation | Bucket (server authority) |
| Lineage (`parent_hash`) | Bucket (validates against chain head) |
| Trace preservation | Bucket (stores verbatim) |
| Producer identity | Producer (`source_module_id`) |
| Read-back verification | Producer (recommended) |
| Signed receipts | Producer or Core (not Bucket) |

### 1.4 Universal Integration Checklist

- [ ] `source_module_id` ratified by BHIV Core
- [ ] `artifact_type` registered in governance registry
- [ ] Envelope passes `POST /bucket/validate-structure`
- [ ] `parent_hash` fetched fresh before each write
- [ ] `artifact_id` strategy defined (uuid4 or uuid5)
- [ ] Read-back verification implemented
- [ ] Duplicate `artifact_id` retry handling defined
- [ ] Staging test with `BHIV_ARTIFACT_PATH` override
- [ ] Live proof document produced

---

## 2. SVACS (Signal / Perception)

**Status:** ✅ PROVEN — `SVACS_BUCKET_LIVE_PROOF.md`  
**Team:** SVACS Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `svacs.perception` |
| `artifact_type` | `perception` |

### Required Metadata

**Envelope:**
```
artifact_id, trace_id, timestamp_utc, schema_version,
source_module_id, artifact_type, parent_hash, payload
```

**Payload (minimum):**
```json
{
  "trace_id": "<echo>",
  "vessel_type": "string",
  "confidence_score": 0.0,
  "pipeline": "SVACS",
  "stage": "perception"
}
```

### Trace Participation

- `trace_id` at envelope level: `svacs-tantra-{timestamp}` or product trace UUID
- Bucket preserves `trace_id` unchanged through write → storage → read-back

### Replay Expectations

- Read-back: `GET /bucket/artifact/{artifact_id}`
- Verify `trace_id` and payload fields unchanged
- Chain: `POST /bucket/validate-replay`

### Recovery Expectations

- On `parent_hash` mismatch (400): re-fetch `GET /bucket/latest-hash`, retry
- On duplicate `artifact_id` (400): treat as success if envelope identical
- On 500: exponential backoff, same `artifact_id`

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| SVACS | Perception semantics, confidence, vessel classification |
| Bucket | Structure, hash, chain, storage |

### Integration Checklist

- [x] Live proof executed (`scripts/svacs_phase1_proof.py`)
- [x] Hash proof PASS
- [x] Trace proof PASS
- [x] Lineage proof PASS
- [x] Failure visibility PASS (broken lineage → 400)

---

## 3. NICAI (AI Inference)

**Status:** ✅ CONTRACT RATIFIED — `MULTI_PRODUCT_CONTRACT_GUIDE.md`  
**Team:** NICAI Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `nicai.inference` (or ratified `nicai.*` module) |
| `artifact_type` | `inference_result` |

### Required Metadata

**Payload (minimum):**
```json
{
  "trace_id": "<echo>",
  "model_id": "string",
  "inference_output": {},
  "confidence": 0.0,
  "pipeline": "NICAI"
}
```

### Trace Participation

- Top-level `trace_id` required
- Correlate with SVACS/Core artifacts via shared `trace_id`

### Replay Expectations

- Same as universal flow
- Cross-product replay: NICAI artifacts appear in shared chain alongside SVACS

### Recovery Expectations

- Same as universal flow
- Producer must not hardcode `parent_hash`

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| NICAI | Model output, inference semantics |
| Bucket | Storage and chain only |

### Integration Checklist

- [x] Contract ratified in `MULTI_PRODUCT_CONTRACT_GUIDE.md`
- [x] Multi-producer runtime proof (`MULTI_PRODUCER_RUNTIME_PROOF.md`)
- [ ] Dedicated NICAI live proof script (recommended)
- [ ] Staging integration test

---

## 4. Sarathi (Enforcement)

**Status:** ✅ DOCUMENTED — `docs/SARATHI_INTEGRATION_WITHOUT_CONFLICT.md`  
**Team:** Sarathi Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `sarathi.enforcement_adapter` |
| `artifact_type` | `enforcement_decision` |

### Required Metadata

**Payload (minimum):**
```json
{
  "decision_id": "string",
  "verdict": "ALLOW | DENY",
  "decision_hash": "<64-hex>",
  "response_hash": "<64-hex>",
  "canonical_response_b64": "<base64 sealed bytes>",
  "enforced_at": "ISO8601",
  "sealed_at": "ISO8601"
}
```

### Trace Participation

- Top-level `trace_id` links enforcement to upstream perception/inference traces
- `artifact_id`: `uuid5(SARATHI_NAMESPACE, decision_id)` for idempotency

### Replay Expectations

- Sarathi **owns** transport and decision hash verification after read-back
- Bucket provides chain custody (`hash`, `artifact_id`)
- Sarathi issues Ed25519 custody receipt after verification (not Bucket)

### Recovery Expectations

- Same as universal flow
- Sarathi must not expect Bucket Ed25519 signing or downstream-ack POST

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| Sarathi | Sealed bytes, enforcement semantics, custody receipt |
| Bucket | Chain storage only |
| Core (optional) | Co-sign witness receipt |

### Integration Checklist

- [x] Integration guide published
- [x] Conflict-free model documented
- [ ] Adapter wired to staging
- [ ] Read-back verification proven
- [ ] Custody receipt pipeline active

---

## 5. UniGuru

**Status:** ⏳ PENDING RATIFICATION — Template contract  
**Team:** UniGuru Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `uniguru.learning_adapter` *(pending Core ratification)* |
| `artifact_type` | `learning_event` *(pending registry)* |

### Required Metadata

**Payload (proposed minimum):**
```json
{
  "trace_id": "<echo>",
  "learner_id": "string",
  "session_id": "string",
  "learning_outcome": {},
  "pipeline": "UNIGURU"
}
```

### Trace Participation

- Standard `trace_id` at envelope level
- Correlate learning sessions across BHIV products

### Replay Expectations

- Universal flow
- Producer verifies payload semantics after read-back

### Recovery Expectations

- Universal flow

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| UniGuru | Learning semantics, pedagogy data |
| Bucket | Storage and chain |

### Integration Checklist

- [ ] `source_module_id` ratified by BHIV Core
- [ ] `artifact_type` registered
- [ ] Payload schema documented by UniGuru team
- [ ] Staging write + read-back test
- [ ] Live proof document

---

## 6. Samruddhi

**Status:** ⏳ PENDING RATIFICATION — Template contract  
**Team:** Samruddhi Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `samruddhi.prosperity_adapter` *(pending)* |
| `artifact_type` | `prosperity_assessment` *(pending)* |

### Required Metadata

**Payload (proposed minimum):**
```json
{
  "trace_id": "<echo>",
  "assessment_id": "string",
  "subject_id": "string",
  "assessment_result": {},
  "pipeline": "SAMRUDDHI"
}
```

### Trace Participation

- Standard envelope `trace_id`

### Replay Expectations

- Universal flow

### Recovery Expectations

- Universal flow

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| Samruddhi | Prosperity/assessment semantics |
| Bucket | Storage and chain |

### Integration Checklist

- [ ] Core ratification of `source_module_id`
- [ ] Artifact type registration
- [ ] Payload schema from Samruddhi team
- [ ] Staging integration test
- [ ] Live proof document

---

## 7. Cyber Defence

**Status:** ⏳ PENDING RATIFICATION — Template contract  
**Team:** Cyber Defence Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `cyber_defence.threat_adapter` *(pending)* |
| `artifact_type` | `threat_event` *(pending)* |

### Required Metadata

**Payload (proposed minimum):**
```json
{
  "trace_id": "<echo>",
  "threat_id": "string",
  "severity": "LOW | MEDIUM | HIGH | CRITICAL",
  "threat_indicators": [],
  "pipeline": "CYBER_DEFENCE"
}
```

### Trace Participation

- Link threat events to upstream perception/inference via `trace_id`

### Replay Expectations

- Universal flow
- Threat timeline reconstructable from chain order + `trace_id` queries

### Recovery Expectations

- Universal flow
- High-severity events: producer should implement retry with same `artifact_id`

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| Cyber Defence | Threat semantics, severity, indicators |
| Bucket | Immutable evidence storage |

### Integration Checklist

- [ ] Core ratification
- [ ] Artifact type registration
- [ ] Payload schema documented
- [ ] Staging test
- [ ] Live proof document

---

## 8. Commercial Intelligence Platform (CIP)

**Status:** ⏳ PENDING RATIFICATION — Template contract  
**Team:** CIP Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `cip.intelligence_adapter` *(pending)* |
| `artifact_type` | `intelligence_report` *(pending)* |

### Required Metadata

**Payload (proposed minimum):**
```json
{
  "trace_id": "<echo>",
  "report_id": "string",
  "domain": "string",
  "intelligence_summary": {},
  "pipeline": "CIP"
}
```

### Trace Participation

- Standard envelope `trace_id`
- Cross-correlate with SVACS/NICAI artifacts on shared traces

### Replay Expectations

- Universal flow

### Recovery Expectations

- Universal flow

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| CIP | Intelligence semantics, report content |
| Bucket | Storage and chain |

### Integration Checklist

- [ ] Core ratification
- [ ] Artifact type registration
- [ ] Payload schema documented
- [ ] Staging test
- [ ] Live proof document

---

## 9. UCCIS

**Status:** ⏳ PENDING RATIFICATION — Template contract  
**Team:** UCCIS Team

### Evidence Contract

| Field | Value |
|-------|-------|
| Endpoint | `POST /bucket/artifact` |
| `source_module_id` | `uccis.compliance_adapter` *(pending)* |
| `artifact_type` | `compliance_record` *(pending)* |

### Required Metadata

**Payload (proposed minimum):**
```json
{
  "trace_id": "<echo>",
  "record_id": "string",
  "compliance_framework": "string",
  "compliance_status": "COMPLIANT | NON_COMPLIANT | PENDING",
  "evidence_refs": [],
  "pipeline": "UCCIS"
}
```

### Trace Participation

- Link compliance records to upstream evidence via `trace_id`
- `evidence_refs` may reference other `artifact_id` values in payload

### Replay Expectations

- Universal flow
- Compliance audit trail reconstructable from chain + trace queries

### Recovery Expectations

- Universal flow

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| UCCIS | Compliance semantics, framework mapping |
| Bucket | Immutable evidence storage |

### Integration Checklist

- [ ] Core ratification
- [ ] Artifact type registration
- [ ] Payload schema documented
- [ ] Staging test
- [ ] Live proof document

---

## 10. BHIV Core (Coordinator)

**Status:** ✅ PROVEN — `REVIEW_PACKET.md`, `MULTI_PRODUCER_RUNTIME_PROOF.md`  
**Team:** BHIV Core (Raj Prajapati)

### Evidence Contract

| Field | Value |
|-------|-------|
| Direct write | `POST /bucket/artifact` |
| Contract write | `POST /bucket/artifacts/write` (requires `integration_id`) |
| `source_module_id` | `bhiv.core.relay` |
| `artifact_type` | `core_relay` |

### Privileged Endpoints

Core may additionally use:
- `POST /bucket/artifacts/read`
- `POST /bucket/artifacts/query`
- `POST /bucket/audit/read`

### Ownership Boundaries

| Owner | Scope |
|-------|-------|
| Core | Coordination, namespace ratification, optional witness signing |
| Bucket | Storage, hash, chain |

---

## 11. Onboarding Process for New Producers

```
Step 1: Request source_module_id ratification from BHIV Core
Step 2: Register artifact_type in governance registry
Step 3: Define payload schema (producer-owned)
Step 4: Implement standard write flow (Section 1.2)
Step 5: Test in staging (BHIV_ARTIFACT_PATH override)
Step 6: Execute read-back verification
Step 7: Produce live proof document
Step 8: Core sign-off
Step 9: Production write enabled
```

**No Bucket code changes required for any new producer.**

---

## 12. Error Handling (All Producers)

| HTTP | Cause | Producer Action |
|------|-------|-----------------|
| 400 | Missing field, unknown envelope field, bad schema | Fix envelope; check `GET /bucket/schema-info` |
| 400 | `parent_hash` mismatch | Re-fetch `GET /bucket/latest-hash`, retry |
| 400 | Duplicate `artifact_id` | Success if identical; else escalate |
| 404 | Artifact not found on read-back | Retry with backoff |
| 500 | Server error | Retry with exponential backoff; same `artifact_id` |

---

## 13. Related Documents

| Document | Purpose |
|----------|---------|
| `BUCKET_PLATFORM_ARCHITECTURE.md` | Platform architecture |
| `EVIDENCE_REGISTRY_SPEC.md` | Registry model |
| `EVIDENCE_PLATFORM_API.md` | API reference |
| `INTEGRATION_GUIDE.md` | General integration guide |
| `MULTI_PRODUCT_CONTRACT_GUIDE.md` | Multi-product rules |
| `docs/SARATHI_INTEGRATION_WITHOUT_CONFLICT.md` | Sarathi-specific guidance |

---

*End of ECOSYSTEM_PRODUCER_PACK.md*
