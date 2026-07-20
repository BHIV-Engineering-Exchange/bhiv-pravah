# PRANA External API Validation Report

## Execution Summary
We executed a complete API surface testing suite against `http://localhost:3000/api/v1/bucket/prana/ingest` under simulated real-world conditions. The goal was to verify canonical guarantees about PRANA's boundary behavior.

## Key Findings

### 1. Deterministic Submission IDs
**Verification Failed.** 
- When identical payloads were submitted consecutively, PRANA assigned entirely random IDs (`uuid4` on ingest) instead of deterministically hashing the payload. 
- *Impact:* PRANA has zero idempotency out of the box. Duplicate transmissions from external systems will lead to duplicate ingestion records and corrupted analytics.

### 2. High-Frequency Rate Limiting
**Verification Failed.**
- Repeated high-frequency calls (10 contiguous rapid requests) succeeded completely (10 success, 0 failures). 
- *Impact:* The ingest endpoint lacks any built-in rate-limiting or throttling, making the system highly vulnerable to external flooding attacks or runaway AI assistant loops.

### 3. Boundary-Limit Payloads
**Verification Failed.**
- Missing required fields correctly throw `422 Unprocessable Entity` due to standard validation schemas.
- However, logical boundary limits (e.g. `active_seconds > 5` or negative time bounds) caused unhandled `500 Internal Server Error` responses, exposing internal tracebacks instead of clean API fail-closed errors.
- Oversized payloads (1MB+ nested `raw_signals`) were **silently accepted** with a `200 OK`, allowing malicious or malfunctioning external systems to bloat the backend storage without limits.

### 4. Lifecycle Transitions & State Regression
**Verification Failed.**
- A simulated student transition from `ON_TASK` abruptly to `AWAY` (skipping intermediate logical states or reverting states) was silently ingested with `200 OK`. 
- *Impact:* The ingest API acts as a structural schema checker (a "dumb pipe") without authenticating state-machine validity or preventing unauthorized state regression.

## Conclusion
PRANA behaves as a structurally-valid but completely un-guarded data pipe under external pressure. Canonical claims of ingestion resistance to misuse are completely falsified.

## Final Output & Explicit Statement

**Does PRANA behave exactly as canon states under external pressure?**
**No.**

**Why:**
While basic structural schema validation works successfully, PRANA fundamentally violates critical canonical claims:
1. **Lack of Determinism**: `packet_id` logic simply invokes `uuid4()` on ingestion rather than hashing payloads, exposing it to undetected duplicate spam flows and replay attacks.
2. **Hidden System Coupling**: Despite the asynchronous client bridge acting independently, the backend ingest endpoint acts synchronously across PostgreSQL database inserts for its hashed-chain ledgers. Temporary database strain triggers a 500 loop.
3. **Failing Cryptographic Integrity**: The append-only ledger `add_packet()` mechanism fails immediately under concurrent external pressure. Parallel database saves will forge duplicate identical `previous_hash` nodes, forging a chain conflict that subsequently shatters the `verify_packet_chain` process loop.
4. **Adversarial Silence**: Disconnected from verification engines, the border ingest silently accepts structurally sound non-sequiturs (e.g., direct state skipping from `DEEP_FOCUS` to `FAKING`, payloads reordered, or oversized objects > 1MB).

PRANA behaves as a structurally-valid dumb pipe, breaking several key safety bounds assumed in canon when interacting out in the wild.
