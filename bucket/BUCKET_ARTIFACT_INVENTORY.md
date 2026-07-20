# BUCKET_ARTIFACT_INVENTORY

Sprint: Evidence Persistence & Reconstruction  
Date: 2026-06-17  
Status: CANONICAL  
Prepared by: Bucket Integration Sprint

---

## 1. PURPOSE

Catalog all runtime artifacts entering Bucket by type, producer, storage location, trace participation, and reconstruction value.

---

## 2. STORAGE LOCATIONS (GLOBAL)

| Storage surface | Path | Role |
|-----------------|------|------|
| Append-only log | `data/artifacts/artifact_log.jsonl` | Canonical evidence record |
| Chain state | `data/artifacts/chain_state.json` | `last_hash`, `artifact_count` |
| Artifact index | `data/artifacts/artifact_index.json` | `artifact_id` → byte offset |
| Staging log | `data/artifacts-staging/artifact_log.jsonl` | Isolated integration tests |
| Audit fallback | `data/audit.log` | Operation audit trail |

---

## 3. ARTIFACT INVENTORY

### 3.1 Intelligence artifacts

| Artifact name | Producer system | Storage location | Trace participation | Reconstruction value |
|---------------|-----------------|------------------|---------------------|----------------------|
| SVACS perception output | SVACS (`svacs.perception`) — Ankita / SVACS Team | `artifact_log.jsonl` line for `03d80b5b-6dd3-42c5-a401-92be64a59656` | `trace_id: svacs-tantra-1780987983` | **HIGH** — vessel type, confidence, pipeline metadata recoverable |
| SVACS TANTRA perception | SVACS (`svacs.perception`) — Ankita / SVACS Team | `artifact_log.jsonl` line for `b314a074-c680-4568-add8-bd05d75baab5` | `trace_id: tantra-e2e-1780988334` | **HIGH** — intelligence layer tagged `SVACS_PRODUCER` |
| NICAI ingestion record | NICAI (`nicai.collector`) — contract only | Not yet in live log | `nicai-trace-0001` (contract example) | **MEDIUM** — envelope validated; live runtime pending |

### 3.2 Trace artifacts

| Artifact name | Producer system | Storage location | Trace participation | Reconstruction value |
|---------------|-----------------|------------------|---------------------|----------------------|
| SVACS trace envelope | SVACS | `03d80b5b-...` / `b314a074-...` | Top-level `trace_id` preserved | **HIGH** — cross-boundary correlation |
| Core relay trace link | BHIV Core (`bhiv.core.relay`) | `bcbebdd5-b27e-4f3f-8eae-98856fe7e8ec` | Same `tantra-e2e-1780988334` | **HIGH** — proves trace survives relay |
| Core contract event | BHIV Core (`core_pipeline`) | `artifact_log.jsonl` / review packet `rp-003` | Contract path | **MEDIUM** — integration event record |

### 3.3 Runtime artifacts

| Artifact name | Producer system | Storage location | Trace participation | Reconstruction value |
|---------------|-----------------|------------------|---------------------|----------------------|
| SVACS phase-1 live proof | SVACS runtime (`scripts/svacs_phase1_proof.py` executor) | `data/artifacts/artifact_log.jsonl` | `svacs-tantra-1780987983` | **HIGH** — full runtime payload |
| TANTRA E2E runtime chain | SVACS + Core (`scripts/tantra_phase2_proof.py`) | `data/artifacts/artifact_log.jsonl` | `tantra-e2e-1780988334` | **HIGH** — multi-layer runtime |

### 3.4 Provenance artifacts

| Artifact name | Producer system | Storage location | Trace participation | Reconstruction value |
|---------------|-----------------|------------------|---------------------|----------------------|
| Hash chain wrapper | Bucket (server authority) | JSONL wrapper `{ artifact, hash }` per line | Links via `parent_hash` | **CRITICAL** — tamper evidence |
| Parent lineage link | Bucket enforcement | `parent_hash` field per artifact | Chain-scoped | **CRITICAL** — ordering proof |
| Provenance manifest refs | Nupur / InsightFlow (read path) | Audit + read API metadata | `chain_verified: true` on GET | **HIGH** — lineage visibility for dashboards |

### 3.5 Replay artifacts

| Artifact name | Producer system | Storage location | Trace participation | Reconstruction value |
|---------------|-----------------|------------------|---------------------|----------------------|
| Chain replay validation | Bucket (`POST /bucket/validate-replay`) | API response + log scan | Full chain | **CRITICAL** — state reconstruction |
| Replay proof fixtures | `verification/replay_integrity/` | Offline test artifacts | Test traces | **LOW** — Bucket-generated; not ecosystem proof |
| Truth replay test | `tests/truth_replay_validation.py` | Test run output | Test trace | **LOW** — Bucket-generated; excluded from leadership proof |

---

## 4. PRODUCER SYSTEM SUMMARY

| Producer | Contact | Artifact types | Live in log? |
|----------|---------|----------------|--------------|
| SVACS | Ankita / SVACS Team | perception, intelligence | ✅ Yes |
| NICAI | NICAI Team | ingestion | ⚠️ Contract only |
| BHIV Core | Raj Prajapati | relay_event, integration_event | ✅ Yes |
| InsightFlow | Nupur / Nikhil | None (read-only) | N/A |
| Bucket test runners | Internal | test artifacts | ✅ Yes — **excluded from ecosystem proof** |

---

## 5. ARTIFACT TYPE REGISTRY

| `artifact_type` | Producer(s) | `source_module_id` | `product_namespace` |
|-----------------|-------------|-------------------|---------------------|
| `perception` | SVACS | `svacs.perception` | `SVACS` |
| `relay_event` | Core | `bhiv.core.relay` | `CORE` |
| `integration_event` | Core | `core_pipeline` | `CORE` |
| `ingestion` | NICAI | `nicai.collector` | `NICAI` |
| `enforcement_decision` | Sarathi | `sarathi.enforcement_adapter` | `SARATHI` |

---

## 6. RECONSTRUCTION VALUE KEY

| Rating | Meaning |
|--------|---------|
| **CRITICAL** | Required to answer "what happened" if runtime disappears |
| **HIGH** | Full payload + trace recoverable from Bucket alone |
| **MEDIUM** | Partial or contract-only; needs producer confirmation |
| **LOW** | Bucket-internal test; not valid for ecosystem leadership proof |

---

## 7. EVIDENCE SOURCES

| Source | Path |
|--------|------|
| SVACS live proof | `SVACS_BUCKET_LIVE_PROOF.md` |
| TANTRA trace proof | `TANTRA_TRACE_CONTINUITY_PROOF.md` |
| Multi-producer proof | `MULTI_PRODUCER_RUNTIME_PROOF.md` |
| Append-only log | `data/artifacts/artifact_log.jsonl` |
| Proof scripts | `scripts/svacs_phase1_proof.py`, `scripts/tantra_phase2_proof.py` |

---

*End of BUCKET_ARTIFACT_INVENTORY.md*
