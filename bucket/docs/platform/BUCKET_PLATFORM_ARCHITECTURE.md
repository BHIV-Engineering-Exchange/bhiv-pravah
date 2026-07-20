# Bucket Platform Architecture

**Document ID:** BUCKET-ARCH-001  
**Version:** 1.0.0  
**Date:** 19 June 2026  
**Status:** CANONICAL  
**Owner:** Siddhesh Narkar — Bucket Custodian  
**Phase:** IV Accepted — Evidence & Artifact Infrastructure Platform

---

## 1. Platform Vision

Bucket is the **canonical Evidence & Artifact Infrastructure Platform** for the BHIV ecosystem.

Following Phase IV reviews by TMS, GC, and MDU, Bucket is accepted as sovereign infrastructure — not a storage repository, but the **shared append-only evidence substrate** upon which every BHIV product can reliably persist, retrieve, and replay artifacts.

### Platform Principles

| Principle | Meaning |
|-----------|---------|
| **Memory, not decision** | Bucket stores evidence; it does not interpret, orchestrate, or execute |
| **One chain, many producers** | SVACS, NICAI, Core, Sarathi, and future products share a single tamper-evident hash chain |
| **Server hash authority** | All integrity hashes are computed by Bucket; client hashes are never trusted |
| **Constitutional discipline** | Platform boundaries are fixed; products adapt to Bucket, not the reverse |
| **Ecosystem participation** | Success is measured by integration breadth, replay reliability, and operational maturity |

### One-Line Truth

**Bucket is append-only evidence storage with deterministic replay — nothing more.**

---

## 2. Participation Model

```
                    ┌─────────────────────────────────────┐
                    │     BHIV Bucket Platform            │
                    │  Evidence & Artifact Infrastructure │
                    └─────────────────────────────────────┘
           write ▲                    ▲ write          ▲ write
                │                    │                │
         ┌──────┴──────┐    ┌───────┴──────┐  ┌─────┴──────┐
         │    SVACS     │    │    NICAI     │  │   Sarathi  │
         │  perception  │    │  inference   │  │ enforcement│
         └─────────────┘    └──────────────┘  └────────────┘
                │                    │                │
         ┌──────┴────────────────────┴────────────────┴──────┐
         │              BHIV Core (coordinator)                  │
         │         contract write / governance relay           │
         └─────────────────────────────────────────────────────┘
                                    │
                              read  ▼
                         ┌──────────────────┐
                         │   InsightFlow    │
                         │  (observe only)  │
                         └──────────────────┘
```

**Producers write. Consumers read. Bucket stores.**

---

## 3. Internal Service Architecture

### 3.1 Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│  API Layer          main.py (FastAPI)                       │
│  /bucket/*          Contract endpoints, health, governance  │
├─────────────────────────────────────────────────────────────┤
│  Validation Layer   append_only_storage.validate_*          │
│                     validators/bucket_contract_validator.py │
├─────────────────────────────────────────────────────────────┤
│  Evidence Core      AppendOnlyStorage (services/)           │
│                     compute_hash → append → index → chain   │
├─────────────────────────────────────────────────────────────┤
│  Audit Layer        middleware/audit_middleware.py          │
│                     services/file_audit_store.py            │
├─────────────────────────────────────────────────────────────┤
│  Persistence        data/artifacts/                         │
│                     artifact_log.jsonl (primary)            │
│                     artifact_index.json, chain_state.json   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  SEPARATE — NOT EVIDENCE PATH                               │
│  Agent/Basket Orchestration  agents/, baskets/              │
│  State: Redis (execution)    Logs: MongoDB (workflow_ai)    │
└─────────────────────────────────────────────────────────────┘
```

Agent and basket execution (`POST /run-agent`, `POST /run-basket`) is **architecturally separate** from artifact evidence storage. No agent code path writes to `append_only_storage`.

### 3.2 Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| Append-Only Storage | `services/append_only_storage.py` | Validate, hash, append, index, chain state |
| HTTP API | `main.py` | Platform endpoints, contract boundary |
| Contract Validator | `validators/bucket_contract_validator.py` | Core integration gate, lineage, payload size |
| Audit Middleware | `middleware/audit_middleware.py` | Immutable operation log (CREATE, READ, QUERY) |
| File Audit Store | `services/file_audit_store.py` | JSONL fallback at `data/audit.log` |
| Scale Limits | `config/scale_limits.py` | Capacity constants and validation helpers |
| Threat Model | `utils/threat_validator.py` | Governance scanning (not wired to write path) |

### 3.3 Legacy Stack (Fallback Only)

| Component | File | When Used |
|-----------|------|-----------|
| Legacy bucket service | `services/bucket_service.py` | Fallback if append-only write fails |
| Legacy store | `services/bucket_store.py` | `data/bucket_artifacts.json` |
| Legacy hash | `services/hash_service.py` | Client `artifact_hash` verification (legacy scheme) |

Primary path is always append-only. Legacy exists for backward compatibility only.

---

## 4. External Ecosystem Interfaces

### 4.1 Producer Interface (Write)

| Interface | Endpoint | Users |
|-----------|----------|-------|
| Direct write | `POST /bucket/artifact` | SVACS, NICAI, Sarathi, integration proofs |
| Core contract write | `POST /bucket/artifacts/write` | BHIV Core (requires `integration_id`) |
| Pre-write helpers | `GET /bucket/latest-hash`, `POST /bucket/validate-structure`, `POST /bucket/compute-hash` | All producers |

### 4.2 Consumer Interface (Read)

| Interface | Endpoint | Users |
|-----------|----------|-------|
| Single artifact | `GET /bucket/artifact/{id}` | Producers, Core, InsightFlow |
| List / trace filter | `GET /bucket/artifacts?trace_id=` | InsightFlow, operators |
| Contract read | `POST /bucket/artifacts/read` | BHIV Core |
| Contract query | `POST /bucket/artifacts/query` | BHIV Core |
| Audit read | `POST /bucket/audit/read` | Core, operators |

### 4.3 Integrity Interface

| Interface | Endpoint | Purpose |
|-----------|----------|---------|
| Chain replay | `POST /bucket/validate-replay` | Full chain integrity validation |
| Chain state | `GET /bucket/chain-state`, `GET /bucket/latest-hash` | Head lookup, lineage prep |
| Schema info | `GET /bucket/schema-info` | Envelope contract discovery |

### 4.4 Observability Interface

| Interface | Endpoint | Purpose |
|-----------|----------|---------|
| Health | `GET /health` | Service and dependency status |
| Storage stats | `GET /bucket/storage-stats` | Capacity monitoring |
| Certification | `GET /bucket/certification` | Platform certification metadata |

---

## 5. Evidence Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Originate│───►│ Validate │───►│   Hash   │───►│  Persist │───►│  Audit   │
│ (Producer)│    │(Bucket)  │    │ (Bucket) │    │ (Bucket) │    │ (Bucket) │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                                      │
     ┌──────────┐    ┌──────────┐    ┌──────────┐                    │
     │  Replay  │◄───│  Retrieve│◄───│  Index   │◄───────────────────┘
     │(Operator)│    │(Consumer)│    │ (Bucket) │
     └──────────┘    └──────────┘    └──────────┘
```

| Stage | Owner | Action |
|-------|-------|--------|
| **Originate** | Producer | Compose envelope + opaque payload |
| **Validate** | Bucket | Structure, schema version, lineage, size, duplicates |
| **Hash** | Bucket | SHA-256 over canonical envelope (server authority) |
| **Persist** | Bucket | Atomic append to JSONL + fsync |
| **Index** | Bucket | Update `artifact_index.json` |
| **Chain** | Bucket | Advance `chain_state.json` |
| **Audit** | Bucket | Log CREATE to audit trail |
| **Retrieve** | Consumer | Read by `artifact_id` or `trace_id` |
| **Replay** | Operator | `validate-replay` — full chain scan |

---

## 6. Artifact Lifecycle

### 6.1 States

| State | Description | Enforced In Code |
|-------|-------------|----------------|
| `composed` | Producer has envelope ready | Producer-side |
| `validated` | Structure passes Bucket checks | `validate_artifact_structure()` |
| `persisted` | Appended to log with hash | `store_artifact()` |
| `indexed` | Lookup entry exists | `artifact_index.json` |
| `readable` | Retrievable by ID | `get_artifact()` |
| `replay_verified` | Chain integrity confirmed | `validate_chain_integrity()` |

### 6.2 Immutability Rules

- Artifacts are **never modified** after write
- Artifacts are **never deleted** in normal operations
- Each `artifact_id` may be written **once only**
- Payload semantics are **opaque** to Bucket

### 6.3 Envelope Contract (v1.0.0)

Required fields (from `append_only_storage.py`):

```
artifact_id, trace_id, timestamp_utc, schema_version,
source_module_id, artifact_type, payload
```

Conditional: `parent_hash` (required after genesis artifact)

Allowed envelope fields: above + `hash` (ignored on write, stripped by server)

---

## 7. Replay Architecture

### 7.1 Storage Model

```
data/artifacts/
├── artifact_log.jsonl      # Append-only log (one JSON record per line)
├── artifact_index.json     # artifact_id → file position
└── chain_state.json        # { last_hash, artifact_count }
```

Each log line:

```json
{
  "artifact": { "...envelope..." },
  "hash": "<server-computed-sha256>"
}
```

### 7.2 Replay Process

1. Scan `artifact_log.jsonl` sequentially
2. For each entry: recompute hash, compare to stored hash
3. Verify parent chain: artifact N's `parent_hash` == hash of artifact N-1
4. Report errors with line numbers

Implementation: `AppendOnlyStorage.validate_chain_integrity()`

API: `POST /bucket/validate-replay`

### 7.3 Cross-Product Replay

All products share one chain. Replay identifies producers via `source_module_id` and payload content. Proof: `CROSS_PRODUCT_REPLAY_PROOF.md`, `MULTI_PRODUCER_RUNTIME_PROOF.md`.

---

## 8. Provenance Architecture

### 8.1 What Is Guaranteed

| Guarantee | Mechanism |
|-----------|-----------|
| Server hash authority | `compute_hash()` — SHA-256, canonical JSON |
| Lineage chain | `parent_hash` links to previous artifact hash |
| Trace preservation | `trace_id` stored verbatim |
| Operation audit | CREATE/READ/QUERY logged with timestamp |
| Deterministic replay | Full log reconstructable |

### 8.2 Honest Gaps (Documented)

From `governance/provenance.py`:

| Gap | Status |
|-----|--------|
| Cryptographic signing (Ed25519, HMAC) | `not_guaranteed` |
| Non-repudiation | `not_guaranteed` |
| Blockchain immutability | `not_guaranteed` |

Producers requiring signed receipts (e.g. Sarathi) must implement verification on the producer side. See `docs/SARATHI_INTEGRATION_WITHOUT_CONFLICT.md`.

### 8.3 Audit Trail

| Store | Location | Content |
|-------|----------|---------|
| Primary | MongoDB `audit_logs` | When DB connected |
| Fallback | `data/audit.log` | JSONL, immutable flag |

Fields: `operation_type`, `artifact_id`, `requester_id`, `integration_id`, `status`, `timestamp`

---

## 9. Storage Architecture

### 9.1 Primary Store

| Property | Value |
|----------|-------|
| Format | JSONL (one record per line) |
| Path | `data/artifacts/artifact_log.jsonl` |
| Override | `BHIV_ARTIFACT_PATH` environment variable |
| Write semantics | Append-only, atomic, fsync |
| Max payload | 16 MB per artifact |

### 9.2 Index Store

| File | Purpose |
|------|---------|
| `artifact_index.json` | O(1) lookup: artifact_id → byte offset |
| `chain_state.json` | Current chain head and count |

### 9.3 What Bucket Does NOT Store

- Raw HTTP wire bytes
- Product-specific derived fields outside envelope
- Orchestration state (Redis/Mongo handle that separately)

---

## 10. Platform Deployment Model

### 10.1 Runtime

| Component | Technology |
|-----------|------------|
| API server | FastAPI + uvicorn |
| Evidence store | Local filesystem (JSONL) |
| Optional audit | MongoDB or file fallback |
| Optional orchestration | Redis + MongoDB (agents only) |

### 10.2 Deployment Targets

| Environment | Configuration |
|-------------|---------------|
| Local development | `python main.py` or `uvicorn main:app --port 8000` |
| Staging | `BHIV_ARTIFACT_PATH=data/artifacts-staging` |
| Production (current) | Render / cloud host with persistent volume |
| Yotta (sovereign) | See `BUCKET_PLATFORM_OPERATIONS.md` — Yotta readiness checklist |

### 10.3 High-Level Topology

```
                    ┌─────────────┐
  Producers ───────►│   Bucket    │──────► InsightFlow (read)
                    │   FastAPI   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        artifact_log   audit.log    chain_state
         (JSONL)       (JSONL)       (JSON)
```

Single-writer append-only model. No distributed consensus in v1.

---

## 11. Service Boundaries

| System | Relationship to Bucket |
|--------|------------------------|
| **BHIV Core** | Coordinator; may use contract endpoints; does not own storage |
| **SVACS** | Producer; writes perception artifacts |
| **NICAI** | Producer; writes inference artifacts |
| **Sarathi** | Producer; writes enforcement decisions; owns custody verification |
| **InsightFlow** | Consumer only; never writes |
| **Agents/Baskets** | Separate execution layer; not evidence path |

---

## 12. Constitutional Boundaries (Unchanged)

Bucket **is**:

- Append-only evidence substrate
- Server hash authority
- Tamper-evident hash chain
- Trace and lineage preserver
- Replay engine

Bucket **is not**:

| Forbidden Role | Reason |
|----------------|--------|
| Orchestrator | Core owns workflows |
| Intelligence engine | Products own semantics |
| Execution authority | Products execute; Bucket stores |
| Governance authority | Core ratifies namespaces |
| Transformation layer | Payloads stored as received (JSON canonicalization only) |
| Signing authority | No Ed25519/HMAC in platform v1 |
| Product-specific adapter | All products use same envelope contract |

**These boundaries must not change without BHIV-wide constitutional amendment.**

---

## 13. Related Documents

| Document | Purpose |
|----------|---------|
| `ROLE.md` | Canonical role definition |
| `EVIDENCE_REGISTRY_SPEC.md` | Registry metadata model |
| `EVIDENCE_PLATFORM_API.md` | API reference |
| `ECOSYSTEM_PRODUCER_PACK.md` | Producer onboarding |
| `BUCKET_PLATFORM_OPERATIONS.md` | Production operations |
| `docs/APPEND_LOG_STORAGE.md` | Storage implementation detail |
| `docs/HASH_AUTHORITY_POLICY.md` | Hash authority policy |

---

*End of BUCKET_PLATFORM_ARCHITECTURE.md*
