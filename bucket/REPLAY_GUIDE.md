# REPLAY_GUIDE

Date: 2026-06-17  
Status: OPERATOR-READY  
Full reference: `REPLAY_PROOF_VALIDATION.md`, `CROSS_PRODUCT_REPLAY_PROOF.md`

---

## What Replay Means

Replay reconstructs the full artifact chain from the append-only log (`artifact_log.jsonl`) and verifies:

1. Each stored hash matches server recomputation
2. Each `parent_hash` links to the prior artifact's hash
3. Ordering is deterministic (line order = chain order)
4. Producer identity (`source_module_id`, `product_namespace`) is recoverable

Bucket does **not** re-execute payload semantics during replay. Replay validates **evidence integrity**, not business outcomes.

---

## When to Run Replay

| Trigger | Action |
|---------|--------|
| After cold restart | `POST /bucket/validate-replay` |
| After recovery (Scenario B/C) | Full replay before accepting writes |
| Scheduled audit (weekly) | Full replay + log result |
| Suspected tampering | Full replay + compare errors |
| Pre-production deploy | Replay on staging instance |

---

## API Replay (Live)

### Full chain validation

```bash
curl -X POST http://localhost:8000/bucket/validate-replay
```

**Success:**
```json
{
  "valid": true,
  "chain_valid": true,
  "message": "Replay validation passed - chain integrity verified"
}
```

**Failure:**
```json
{
  "valid": false,
  "errors": ["Line 3: Hash mismatch for <artifact_id>"],
  "message": "Replay validation failed"
}
```

### Single artifact chain walk

```bash
curl -X POST http://localhost:8000/bucket/validate-chain/{artifact_id}
```

### Chain state inspection

```bash
curl http://localhost:8000/bucket/chain-state
curl http://localhost:8000/bucket/latest-hash
```

---

## Manual Replay (Offline)

1. Open `data/artifacts/artifact_log.jsonl`
2. For each line:
   - Parse JSON wrapper: `{"artifact": {...}, "hash": "..."}`
   - Extract envelope fields
   - Recompute SHA256 over canonical JSON:

```python
import json, hashlib

fields = ["artifact_id","trace_id","timestamp_utc","schema_version",
          "source_module_id","product_namespace","artifact_type",
          "parent_hash","payload"]
h = {k: artifact.get(k) for k in fields}
computed = hashlib.sha256(
    json.dumps(h, sort_keys=True, separators=(',',':')).encode()
).hexdigest()
assert computed == stored_hash
```

3. Verify `parent_hash` of artifact N equals `hash` of artifact N-1
4. Compare final hash to `chain_state.json` → `last_hash`

---

## Cross-Product Replay

All producers (SVACS, NICAI, Core) share one log. Replay does not segregate by product — it walks the entire chain sequentially.

| Replay output | How to identify producer |
|---------------|-------------------------|
| `source_module_id` | e.g. `svacs.perception`, `nicai.collector`, `core_pipeline` |
| `product_namespace` | e.g. `SVACS`, `NICAI`, `CORE` |
| `artifact_type` | e.g. `perception`, `ingestion`, `relay_event` |

Proof: `CROSS_PRODUCT_REPLAY_PROOF.md`

---

## Replay Proof Artifacts

`artifact_type: replay_proof` entries (legacy path) capture validation runs:

```json
{
  "artifact_type": "replay_proof",
  "input_hash": "<hash_of_validation_input>",
  "payload": {
    "validation_result": "passed",
    "artifacts_validated": 100
  }
}
```

Fixtures: `verification/replay_integrity/test_artifacts/`

---

## Automated Replay Scripts

| Script | Command |
|--------|---------|
| TANTRA E2E proof | `python scripts/tantra_phase2_proof.py http://127.0.0.1:8005` |
| SVACS proof | `python scripts/svacs_phase1_proof.py http://127.0.0.1:8005` |
| Truth replay test | `python tests/truth_replay_validation.py http://127.0.0.1:8000` |
| Offline verifier | `python verification/replay_integrity/verify_integrity.py` |

---

## Interpreting Failures

| Error | Meaning | Action |
|-------|---------|--------|
| Hash mismatch at line N | Tampering or schema change | Stop writes. Investigate line N. |
| Parent hash mismatch | Broken lineage | Stop writes. Rebuild from last valid entry. |
| First artifact has parent_hash | Genesis violation | Reject chain. Manual review. |
| Invalid JSON at line N | Crash mid-write | Truncate to N-1. Rebuild state. |

---

## Performance Expectations

| Chain size | Expected replay time |
|------------|---------------------|
| < 1,000 artifacts | < 1 second |
| < 10,000 artifacts | < 10 seconds |
| > 100,000 artifacts | Schedule off-peak; consider log rotation policy |

---

## Guarantees

- **Deterministic:** Same log → same validation result every time
- **Tamper-evident:** Any modification detected at hash recompute
- **Complete:** Every line in the log is validated
- **Producer-neutral:** Replay does not interpret payload content

---

*End of REPLAY_GUIDE.md*
