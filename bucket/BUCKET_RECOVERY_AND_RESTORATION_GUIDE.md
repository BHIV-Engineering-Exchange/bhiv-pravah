# BUCKET_RECOVERY_AND_RESTORATION_GUIDE

Version: 1.0
Date: 2026-06-09
Status: CANONICAL
Prepared by: Integration Sprint — Phase 5 Convergence

---

## 1. PURPOSE

Document the deterministic recovery and restoration workflows for Bucket so any operator can bring Bucket back to a verified, trustworthy state after failure, corruption, or node loss.

This does NOT add distributed blockchain behavior. Bucket remains a bounded, append-only, file-based persistence layer.

---

## 2. CORE INVARIANTS (NEVER VIOLATE DURING RECOVERY)

1. **Artifacts are never deleted.** Recovery does not remove artifacts.
2. **Hashes are never recomputed with different logic.** Canonical SHA256 over sorted JSON envelope — always.
3. **Chain state reflects last verified artifact.** Never advance `chain_state.json` beyond the last hash-verified entry.
4. **No writes during recovery.** Block all incoming writes until recovery is complete and verified.
5. **Trace IDs are preserved.** Recovery does not remap or alter `trace_id` values.

---

## 3. RECOVERY SCENARIOS AND WORKFLOWS

### SCENARIO A — Cold Restart (Normal)

**Trigger:** Process killed and restarted. Files intact.

**Steps:**
```
1. Start process: python main.py (or uvicorn main:app --port <PORT>)
2. Service auto-loads chain_state.json → sets last_hash and artifact_count
3. Service opens artifact_log.jsonl in append mode
4. Service is ready — no manual steps required
```

**Verification after restart:**
```
GET /bucket/health  → expect {"status": "ok"}
POST /bucket/artifacts/query (integration_id: bhiv_core, limit: 1)
  → expect artifact_count matches chain_state.json
```

**Success condition:** First query returns artifacts consistent with `chain_state.json`.

---

### SCENARIO B — Missing chain_state.json (Rebuild)

**Trigger:** `chain_state.json` deleted, corrupted, or absent. `artifact_log.jsonl` intact.

**Steps:**
```
1. STOP the service immediately (block all writes)
2. Run chain state rebuild:
   python scripts/rebuild_chain_state.py --log data/artifacts/artifact_log.jsonl
   (or equivalent recovery script)
3. Script reads artifact_log.jsonl line by line, recomputes hash chain:
   - For each line: parse artifact, compute SHA256 over canonical envelope
   - Verify hash matches stored hash field
   - Advance chain head
4. Script writes rebuilt chain_state.json:
   { "artifact_count": N, "last_hash": "<hash>", "last_artifact_id": "...", "last_timestamp": "..." }
5. Operator manually reviews output — confirm artifact_count and last_hash look correct
6. RESTART the service
7. Run verification (see Section 5)
```

**Failure condition:** If any line in `artifact_log.jsonl` fails hash verification → **STOP. Do not proceed. Escalate immediately.**

---

### SCENARIO C — Corrupted artifact_log.jsonl (Partial Write)

**Trigger:** Process crashed mid-write. Last line of `artifact_log.jsonl` is incomplete or malformed JSON.

**Steps:**
```
1. STOP the service
2. Open artifact_log.jsonl in a text editor or run:
   python scripts/validate_log.py --log data/artifacts/artifact_log.jsonl
3. Identify last complete valid JSON line (N-1 if last line is corrupt)
4. Truncate artifact_log.jsonl to remove the corrupted last line:
   python scripts/truncate_log.py --log data/artifacts/artifact_log.jsonl --last-valid-line <N-1>
5. Rebuild chain_state.json from truncated log (see Scenario B)
6. RESTART service
7. Notify the producer of the dropped artifact (they must retry the write)
8. Run verification (see Section 5)
```

**Key rule:** The dropped artifact was never successfully committed. The producer's retry with the same payload is safe because the chain head reverted to the pre-write state.

---

### SCENARIO D — Corrupted Index / In-Memory Inconsistency

**Trigger:** In-memory artifact index diverges from `artifact_log.jsonl` (bug, OOM kill, etc.)

**Steps:**
```
1. STOP the service
2. The in-memory index is ephemeral — it is not recoverable
3. Restart the service (the in-memory index is rebuilt from artifact_log.jsonl on startup)
4. If startup rebuild fails → fall back to Scenario B or C
```

---

### SCENARIO E — Deployed Node Loss (Render Ephemeral Disk)

**Trigger:** Render container restarted. `data/` directory lost (ephemeral filesystem).

> ⚠ This scenario results in **data loss** unless a Persistent Disk or remote storage backend is configured. This is a known open risk (see DEPLOYMENT_PERSISTENCE_TRUTH_REPORT.md).

**Steps (current state — no persistent disk):**
```
1. Accept: artifacts written to deployed instance before restart are lost
2. Notify all producers: chain head has reset to genesis
3. All producers must re-submit artifacts with parent_hash: null (genesis write)
   OR coordinate an artifact log restore from backup
4. Restore from backup if available (see Section 4)
5. Restart service normally
```

**Mitigation (recommended):** Mount Render Persistent Disk to `/data`. This eliminates this scenario.

---

### SCENARIO F — Handover / Operator Change

**Trigger:** Bucket custodian changes. New operator takes over.

**Steps:**
```
1. Outgoing operator provides:
   - data/artifacts/artifact_log.jsonl (full log)
   - data/chain_state.json
   - .env (secrets redacted)
   - This recovery guide
2. New operator runs chain verification (see Section 5)
3. New operator confirms last_hash matches top of artifact_log.jsonl
4. New operator takes custody and updates SYSTEM_TRUTH.md with new owner name
5. Notify BHIV Core (Raj Prajapati) of handover completion
```

---

## 4. REPLAY RESTORATION WORKFLOW

Replay is used to verify that a rebuilt or restored chain is consistent.

**Replay command (reference):**
```bash
python tests/truth_replay_validation.py --log data/artifacts/artifact_log.jsonl
```

**What replay does:**
1. Reads `artifact_log.jsonl` line by line
2. For each artifact: recomputes SHA256 over canonical JSON (deterministic sort + separators)
3. Compares recomputed hash to stored `hash` field
4. Verifies `parent_hash` links to previous artifact's hash (or null for genesis)
5. Reports: PASS (chain intact) or FAIL (first broken link identified)

**Replay success criteria:**
- All hashes match
- All parent links are valid
- Final artifact hash matches `chain_state.json → last_hash`
- Artifact count matches `chain_state.json → artifact_count`

---

## 5. CHAIN VERIFICATION (POST-RECOVERY)

Run after every recovery scenario before accepting new writes:

```bash
# Step 1: Verify chain integrity
python tests/truth_replay_validation.py --log data/artifacts/artifact_log.jsonl

# Step 2: Confirm service health
curl http://127.0.0.1:8005/bucket/health

# Step 3: Read back last known artifact
curl -X POST http://127.0.0.1:8005/bucket/artifacts/read \
  -H "Content-Type: application/json" \
  -d '{"requester_id":"operator","integration_id":"bhiv_core","artifact_id":"<last_artifact_id>"}'

# Step 4: Confirm chain_state.json matches read-back response
# last_hash in chain_state.json must equal hash in read response
```

---

## 6. INTEGRITY REVALIDATION

For periodic integrity checks (not just post-recovery):

```bash
# Run full chain hash revalidation
python tests/truth_replay_validation.py --log data/artifacts/artifact_log.jsonl --full

# Expected output:
# Chain replay: PASS
# Artifacts verified: N
# Last hash: <sha256>
# Matches chain_state.json: YES
```

Schedule this check: at minimum after every deploy, after every schema change, and before any major integration milestone.

---

## 7. OPERATOR RECOVERY CHECKLIST

Use this checklist for any recovery event:

```
Pre-recovery:
[ ] STOP service — block all writes before recovery
[ ] Identify scenario (A, B, C, D, E, or F above)
[ ] Back up current data/ directory before any modification

Recovery:
[ ] Follow scenario-specific steps exactly
[ ] Do not skip chain rebuild if chain_state.json was affected
[ ] Do not truncate log without verifying the last valid line

Post-recovery:
[ ] Run chain verification (Section 5)
[ ] Confirm artifact_count and last_hash are consistent
[ ] Confirm health endpoint responds OK
[ ] Notify producers of any dropped artifacts (they must retry)
[ ] Log recovery event in audit log with timestamp and description
[ ] Update SYSTEM_TRUTH.md if ownership or configuration changed
[ ] Notify BHIV Core (Raj Prajapati) that recovery is complete
```

---

## 8. WHAT THIS GUIDE DOES NOT COVER

- Distributed consensus between multiple Bucket nodes (out of scope — Bucket is single-node)
- Database migration for schema changes (see MULTI_PRODUCT_CONTRACT_GUIDE.md)
- Active replication or hot standby (not implemented)
- Automated recovery pipelines (operator-driven by design)

---

## 9. CIVILIZATIONAL SURVIVABILITY STATEMENT

> Bucket's append-only log is the ground truth. As long as `artifact_log.jsonl` exists and is intact, all other state (chain_state.json, in-memory index, audit log) can be deterministically reconstructed. The log is the artifact. Protect the log.

---

*End of BUCKET_RECOVERY_AND_RESTORATION_GUIDE.md*
