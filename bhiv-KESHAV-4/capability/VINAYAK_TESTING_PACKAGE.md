# KESHAV Testing Package for Vinayak

**To:** Vinayak (Testing & Validation Department)
**From:** Rajaryan Verma (BHIV Operational Chariot)
**Subject:** KESHAV Capability Certification & Sovereign Verification

Vinayak, 
The objective of this testing package is to validate KESHAV not as a localized feature, but as a sovereign, reusable capability that strengthens the BHIV ecosystem through stable contracts, bounded authority, deterministic behavior, and long-term interoperability.

Please execute the following tests strictly in the provided sequence.

---

## 1. Capability Publication Validation

**Objective:** Validate that KESHAV's identity, metadata, and boundaries are properly registered.
**Instructions:**
1. Open `capability/KESHAV_CAPABILITY.md` and `capability/CAPABILITY_REGISTRY.md`.
2. Verify the `Capability ID` is `bhiv-keshav-dependency-intelligence`.
3. Verify that KESHAV possesses NO physical execution rights outside its own compute sandbox.
**Expected Result:** The documentation cleanly defines a pure intelligence capability without state-mutation or enforcement authority.

---

## 2. Consumer Compatibility Tests

**Objective:** Verify that KESHAV can be simultaneously integrated by multiple diverse consumers without modification to its internal code.
**Instructions:**
1. Navigate to the workspace root: `c:\blackhole\KESHAV-4`
2. Run the multi-consumer simulation script: 
   ```bash
   python multi_consumer_proof.py
   ```
**Expected Result:** 
- The console outputs results for Sarathi, SETU, and AIAIC.
- The script asserts `True` that all consumers received the exact same deterministic output payload, despite interpreting it for different actions.
- The console explicitly prints: `Proof Successful: KESHAV was consumed through stable contracts by multiple simulated participants without modifying internal logic.`

---

## 3. Schema Compatibility Tests

**Objective:** Validate that KESHAV conforms strictly to the canonical terminologies defined in the semantic and schema registries.
**Instructions:**
1. Open `capability/SEMANTIC_REGISTRY.md` and `capability/SCHEMA_REGISTRY.md`.
2. Execute a test request to the running API (ensure `python api.py` is running in another terminal):
   ```bash
   curl -X POST http://localhost:5000/analyze -H "Content-Type: application/json" -d @sample_input.json
   ```
3. Inspect the returned JSON payload.
**Expected Result:** 
- The keys returned must perfectly match the `SEMANTIC_REGISTRY.md` (e.g., `root_cause`, `resolution_signal`, `impact_score`).
- The payload must contain a `trace_id` and an execution timestamp.

---

## 4. Contract Stability Tests

**Objective:** Prove KESHAV safely handles structurally invalid payloads by failing closed.
**Instructions:**
1. Send an invalid, empty JSON payload to the API:
   ```bash
   curl -X POST http://localhost:5000/analyze -H "Content-Type: application/json" -d "{}"
   ```
2. Send a request with the wrong content type:
   ```bash
   curl -X POST http://localhost:5000/analyze -H "Content-Type: text/plain" -d "not-json"
   ```
**Expected Result:**
- The first request returns a strict HTTP 400 with: `{"status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": ""}`
- The second request returns HTTP 415 with: `{"status": "FAIL", "reason": "UNSUPPORTED_MEDIA_TYPE", "trace_id": ""}`
- The execution pipeline does NOT crash and does not enter an unknown state.

---

## 5. Replay Verification

**Objective:** Prove that KESHAV acts as a perfectly deterministic 10/10 replay engine.
**Instructions:**
1. From the root directory, run the deterministic proof harness:
   ```bash
   python replay_determinism_proof.py
   ```
**Expected Result:**
- The harness successfully runs the replay tests and outputs a success banner indicating that 34/34 assertions passed.
- No divergence signatures or entropy violations are logged.

---

## 6. Version Compatibility Verification

**Objective:** Validate forward compatibility guarantees outlined in the Service Contract.
**Instructions:**
1. Open `capability/SERVICE_CONTRACT.md`.
2. Review the `Compatibility Policy` and `Breaking Change Policy` sections.
**Expected Result:**
- The document formally guarantees that output schemas are append-only.
- The contract mandates that any breaking change (removing a field) requires a `MAJOR` SemVer bump and a 90-day deprecation notice for downstream consumers.

---

**Conclusion**: If all expected results hold true, KESHAV is fully certified as a robust, sovereign, reusable ecosystem capability for the BHIV Operational Chariot.
