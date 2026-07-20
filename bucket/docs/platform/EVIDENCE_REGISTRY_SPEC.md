# Evidence Registry Specification

**Document ID:** BUCKET-REG-001  
**Version:** 1.0.0  
**Date:** 19 June 2026  
**Status:** CANONICAL  
**Owner:** Siddhesh Narkar — Bucket Custodian

---

## 1. Purpose

This specification defines the **ecosystem-wide Evidence Registry** — the logical model for artifact identity, metadata, indexing, integrity, and lifecycle across all BHIV products.

The registry is **product-agnostic**. No producer-specific assumptions are embedded. Product identity is expressed through standard envelope fields, not registry special cases.

### Implementation Mapping (v1)

| Registry concept | Physical implementation |
|----------------|-------------------------|
| Registry store | `data/artifacts/artifact_log.jsonl` |
| Index | `data/artifacts/artifact_index.json` |
| Chain head | `data/artifacts/chain_state.json` |
| Audit registry | `data/audit.log` or MongoDB `audit_logs` |

Future versions may add database-backed registry without changing the logical model.

---

## 2. Global Artifact Identity

### 2.1 Primary Identity

| Field | Type | Uniqueness | Purpose |
|-------|------|------------|---------|
| `artifact_id` | string (UUID recommended) | **Globally unique** within Bucket | Primary registry key |
| `trace_id` | string (UUID recommended) | Non-unique (many artifacts per trace) | Cross-system correlation |

### 2.2 Identity Rules

1. `artifact_id` is assigned by the **producer** before write
2. Bucket **rejects duplicates** — same `artifact_id` cannot be stored twice
3. Idempotent retries must send the **identical envelope** with the same `artifact_id`
4. `trace_id` links artifacts across systems and time; Bucket preserves it verbatim

### 2.3 Recommended ID Strategy

| Pattern | Use Case |
|---------|----------|
| `uuid4()` | General artifacts |
| `uuid5(namespace, decision_id)` | Deterministic idempotency (e.g. Sarathi enforcement) |
| `uuid5(namespace, transaction_id)` | Financial / transactional evidence |

---

## 3. Evidence Metadata Model

### 3.1 Envelope Metadata (Registry-Visible)

Every registry entry carries these fields at the envelope level:

```json
{
  "artifact_id": "string",
  "trace_id": "string",
  "timestamp_utc": "ISO8601",
  "schema_version": "1.0.0",
  "source_module_id": "string",
  "artifact_type": "string",
  "parent_hash": "string | null",
  "payload": {}
}
```

### 3.2 Storage Wrapper Metadata (Bucket-Owned)

Each log entry in the registry store includes:

```json
{
  "artifact": { "...envelope..." },
  "hash": "<server-sha256-hex>"
}
```

| Field | Owner | Mutable |
|-------|-------|---------|
| `artifact` | Producer (content), Bucket (storage) | Never after write |
| `hash` | Bucket (computed) | Never |

### 3.3 Payload Metadata (Producer-Owned, Opaque)

All domain semantics live inside `payload`. Bucket does not index payload fields in v1. Producers may include:

- Product-specific identifiers (`decision_id`, `vessel_type`, etc.)
- Producer-computed hashes (`decision_hash`, `response_hash`)
- Sealed byte references (`canonical_response_b64`)
- Trace echoes (`trace_id` in payload for producer convenience)

---

## 4. Namespace Ownership

### 4.1 Producer Identification

| Field | Registry Role | Governance Owner |
|-------|---------------|------------------|
| `source_module_id` | Primary producer identity | Product team, ratified by BHIV Core |
| `artifact_type` | Evidence classification | BHIV Core registry |

### 4.2 Approved Producer Namespaces (Governance Registry)

| Token | `source_module_id` pattern | Status |
|-------|---------------------------|--------|
| SVACS | `svacs.*` | ✅ Proven |
| NICAI | `nicai.*` | ✅ Contract ratified |
| CORE | `bhiv.core.*`, `core_pipeline` | ✅ Proven |
| SARATHI | `sarathi.enforcement_adapter` | ✅ Documented |
| NAMAMI | `namami.*` | ✅ Bounded |
| UNIGURU | `uniguru.*` | ⏳ Pending ratification |
| SAMRUDDHI | `samruddhi.*` | ⏳ Pending ratification |
| CYBER_DEFENCE | `cyber_defence.*` | ⏳ Pending ratification |
| CIP | `cip.*` | ⏳ Pending ratification |
| UCCIS | `uccis.*` | ⏳ Pending ratification |

Bucket enforces **structural** validity only. Namespace approval is a **governance** responsibility of BHIV Core.

### 4.3 Namespace Rules

1. Producers must use ratified `source_module_id` values
2. Cross-namespace impersonation is a **producer governance violation**, not a Bucket enforcement (v1)
3. Replay and query identify producers via `source_module_id` + `artifact_type`

---

## 5. Artifact Indexing

### 5.1 Primary Index

**File:** `artifact_index.json`

```json
{
  "<artifact_id>": <byte_offset_in_log>
}
```

- Updated on every successful write
- Enables O(1) retrieval by `artifact_id`

### 5.2 Secondary Indexes (v1 — Scan-Based)

| Index | Mechanism | API |
|-------|-----------|-----|
| By `trace_id` | Full log scan | `GET /bucket/artifacts?trace_id=` |
| By `artifact_type` | Contract query filter | `POST /bucket/artifacts/query` |
| By `source_module_id` | Contract query filter | `POST /bucket/artifacts/query` |
| Chronological | Log order + offset/limit | `GET /bucket/artifacts` |

### 5.3 Future Index Enhancements (Planned)

| Index | Status |
|-------|--------|
| Full-text payload search | Not implemented |
| Time-range index | Not implemented |
| Product namespace index | Not implemented |

Documented in API spec as `PLANNED` — not available in v1.

---

## 6. Version Discipline

### 6.1 Schema Version

| Field | Current Value | Rule |
|-------|---------------|------|
| `schema_version` | `"1.0.0"` | Must match exactly; other values rejected |

### 6.2 API Version

| Layer | Versioning Strategy |
|-------|---------------------|
| Envelope schema | `schema_version` field in artifact |
| HTTP API | Path-stable (`/bucket/*`); additive response fields only |
| Registry format | JSONL line format v1; new fields additive only |

### 6.3 Breaking Change Policy

1. Propose amendment to BHIV Core governance
2. 30-day comment period
3. Owner approval
4. 60-day transition window
5. Never break existing `schema_version: 1.0.0` entries

---

## 7. Replay Metadata

### 7.1 Chain State Record

**File:** `chain_state.json`

```json
{
  "last_hash": "<sha256-hex | null>",
  "artifact_count": <integer>
}
```

### 7.2 Per-Artifact Replay Fields

| Field | Replay Role |
|-------|-------------|
| `hash` (wrapper) | Integrity proof for this entry |
| `parent_hash` (envelope) | Lineage link to previous entry |
| `artifact_id` | Stable identity across replay |
| `timestamp_utc` | Temporal ordering reference |
| `trace_id` | Cross-artifact correlation |

### 7.3 Replay Validation Output

`POST /bucket/validate-replay` returns:

```json
{
  "valid": true,
  "artifact_count": 7,
  "last_hash": "<hex>",
  "errors": [],
  "storage_type": "append_only"
}
```

---

## 8. Provenance Metadata

### 8.1 Audit Record Schema

Each registry operation generates an audit entry:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | datetime UTC | Operation time |
| `operation_type` | enum | CREATE, READ, QUERY, AUDIT_READ |
| `artifact_id` | string | Target artifact |
| `requester_id` | string | Calling system/user |
| `integration_id` | string | Integration channel |
| `status` | enum | success, failure, blocked |
| `data_after` | object | Post-operation state summary |
| `error_message` | string | Present on failure/blocked |
| `immutable` | boolean | Always `true` |
| `audit_version` | string | `"1.0"` |

### 8.2 Provenance Queries

| Query | Endpoint |
|-------|----------|
| Recent operations | `POST /bucket/audit/read` |
| Failed operations | `GET /audit/failed` |

---

## 9. Integrity Metadata

### 9.1 Hash Specification

| Property | Value |
|----------|-------|
| Algorithm | SHA-256 |
| Authority | Server-only (Bucket) |
| Input fields | `artifact_id`, `trace_id`, `timestamp_utc`, `schema_version`, `source_module_id`, `artifact_type`, `parent_hash`, `payload` |
| Serialization | `json.dumps(sort_keys=True, separators=(',', ':'))` |
| Client hash | Ignored / stripped |

### 9.2 Integrity Verification Methods

| Method | When | Endpoint |
|--------|------|----------|
| Pre-write preview | Before persist | `POST /bucket/compute-hash` |
| Post-write confirm | After persist | Compare write response `hash` |
| Read-back verify | After retrieve | Recompute via `compute-hash` on read-back envelope |
| Full chain audit | Scheduled / on-demand | `POST /bucket/validate-replay` |

### 9.3 Integrity Metadata on Write Response

```json
{
  "success": true,
  "artifact_id": "<id>",
  "hash": "<server-sha256>",
  "parent_hash": "<chain-parent>",
  "timestamp": "<timestamp_utc>",
  "storage_type": "append_only"
}
```

---

## 10. Lifecycle States

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│ COMPOSED  │────►│ VALIDATED │────►│ PERSISTED │────►│ INDEXED   │
│ (producer)│     │ (bucket)  │     │ (bucket)  │     │ (bucket)  │
└───────────┘     └───────────┘     └───────────┘     └─────┬─────┘
                                                            │
                         ┌───────────┐     ┌───────────┐    │
                         │ REPLAY_   │◄────│ READABLE  │◄───┘
                         │ VERIFIED  │     │ (bucket)  │
                         │(operator) │     └───────────┘
                         └───────────┘
```

| State | Description | Transition Trigger |
|-------|-------------|-------------------|
| `COMPOSED` | Producer has envelope ready | Producer action |
| `VALIDATED` | Structure passes Bucket checks | `validate_artifact_structure()` success |
| `PERSISTED` | Written to JSONL with hash | `store_artifact()` success |
| `INDEXED` | Lookup entry created | Index update after persist |
| `READABLE` | Retrievable by ID | Index + log consistent |
| `REPLAY_VERIFIED` | Chain integrity confirmed | `validate_chain_integrity()` pass |

**Terminal state:** `PERSISTED` artifacts are immutable. No UPDATE or DELETE states exist.

---

## 11. Cross-Product Relationships

### 11.1 Shared Chain Model

All BHIV products write to the **same append-only chain**. Lineage is global:

```
SVACS artifact → NICAI artifact → Core artifact → Sarathi artifact
     hash₁            hash₂           hash₃            hash₄
```

### 11.2 Correlation Patterns

| Relationship | Mechanism |
|--------------|-----------|
| Same trace | Shared `trace_id` across artifacts |
| Sequential causality | Chain order + `parent_hash` (global, not per-product) |
| Product attribution | `source_module_id` + `artifact_type` |
| Payload cross-reference | Producer-defined IDs inside `payload` |

### 11.3 Cross-Product Rules

1. Products do not get separate chains
2. Products do not get separate storage paths (unless `BHIV_ARTIFACT_PATH` env for staging)
3. Replay validates the **entire** chain, not per-product segments
4. Product payload semantics never leak into Bucket validation

---

## 12. Registry Query Model

### 12.1 Supported Queries (v1)

| Query | Parameters | Endpoint |
|-------|------------|----------|
| By ID | `artifact_id` | `GET /bucket/artifact/{id}` |
| By trace | `trace_id` | `GET /bucket/artifacts?trace_id=` |
| Paginated list | `limit`, `offset` | `GET /bucket/artifacts` |
| Filtered query | `artifact_type`, `source_module_id`, `limit`, `offset` | `POST /bucket/artifacts/query` |
| Chain head | — | `GET /bucket/latest-hash` |
| Chain state | — | `GET /bucket/chain-state` |

### 12.2 Unsupported Queries (v1)

- Full-text search across payloads
- Graph traversal beyond `trace_id`
- Time-range queries without scan
- Cross-registry federation

---

## 13. Related Documents

| Document | Purpose |
|----------|---------|
| `BUCKET_PLATFORM_ARCHITECTURE.md` | Platform architecture |
| `EVIDENCE_PLATFORM_API.md` | API reference |
| `ECOSYSTEM_PRODUCER_PACK.md` | Producer contracts |
| `docs/HASH_AUTHORITY_POLICY.md` | Hash rules |
| `AUTHORITY_BOUNDARIES.md` | Writer/reader matrix |

---

*End of EVIDENCE_REGISTRY_SPEC.md*
