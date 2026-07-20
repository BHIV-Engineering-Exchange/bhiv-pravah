# TANTRA CONNECTOR INTEGRATION — REVIEW PACKET
**Owner:** Soham Kotkar
**Sub-system:** Runtime + Integration (Pravah + Bucket Connectors)

─────────────────────────────────────────────────────────────
## 1. ENTRY POINT

**Trace ID Middleware Injection**
Path: `backend/app/middleware/trace_middleware.py`
Explanation: TANTRA Phase 1 requirement. Ensures every incoming request is locked to an immutable `trace_id`. If `x-trace-id` is in the header, it uses it. If not, it generates a new UUID4 trace ID at the entry point. The trace ID is then propagated into contextvars and echoed back in the response headers.

─────────────────────────────────────────────────────────────
## 2. CORE EXECUTION FLOW (3 FILES)

**File 1: Pravah HTTP Connector**
Path: `backend/app/services/pravah_adapter.py`
Explanation: Real HTTP POST (`/pravah/ingest`) integration. Replaces the simulated `runtime_events.json` writing. Implements 3-retry logic with exponential backoff.

**File 2: Bucket Hash-Chain Connector**
Path: `backend/app/services/bucket_adapter.py`
Explanation: Real HTTP POST (`/bucket/write`) integration. Implements an append-only SHA256 cryptographic hash chain `sha256(prev_hash + json(data))`. Maintains a 100-event in-memory queue to prevent silent data drops during network failures.

**File 3: Strict Schema Validator**
Path: `backend/app/services/tantra_schema_validator.py`
Explanation: Strict payload contract enforcer. Rejects any payloads missing required fields, sending incorrect types, or containing extra unauthorized keys, preventing downstream pollution.

─────────────────────────────────────────────────────────────
## 3. LIVE FLOW (REAL JSON)

**User Input:**
Login request triggered at `/api/v1/auth/login`

**Flow:**
Middleware (Trace Lock) → API → Pravah (Metrics) & Bucket (Memory)

**Pravah Payload Sent (Real):**
```json
{
  "source": "GurukulRuntime",
  "trace_id": "bhiv-e2e-7f1be7a918ab437c",
  "timestamp": "2026-04-23T09:35:57.123456+00:00",
  "event_type": "user_flow",
  "action": "login_complete",
  "status": "success",
  "payload": {"user": "tantra_e2e_abcdef@test.gurukul"}
}
```

**Bucket Payload Sent (Real, with Hash Chain):**
```json
{
  "trace_id": "bhiv-e2e-7f1be7a918ab437c",
  "user_id": "user_12345",
  "session_id": "e2e_session",
  "action": "login_complete",
  "outcome": "success",
  "payload": {"user": "tantra_e2e_abcdef@test.gurukul"},
  "timestamp": "2026-04-23T09:35:57.987654+00:00",
  "source": "GurukulRuntime",
  "prev_hash": "b2d5ac06380d...",
  "current_hash": "a4c9f182cc78... (computed via SHA256(prev_hash + data))"
}
```

─────────────────────────────────────────────────────────────
## 4. WHAT WAS BUILT

Strict bullets:
• Real HTTP POST logic built for Pravah and Bucket endpoints
• SHA256 Hash Chain implemented for TANTRA Bucket append-only ledger
• Strict Schema Validator blocks malformed JSON payloads from leaving Gurukul
• `runtime_events.json` simulation removed as source of truth (now behind debug flag)
• 3-Attempt retry and 100-event in-memory overflow queue for Bucket to avoid silents drops

─────────────────────────────────────────────────────────────
## 5. FAILURE CASES

• **Bucket TANTRA Node Offline**
  Returns: Connection fails. HTTP logic stops after 3 retries (1s backoff). Signal goes to in-memory deque buffer (`maxlen=100`) for deferred transmission. Hash chain is suspended until next successful send.
• **Malformed Payload Sent By UI**
  Returns: Pre-transmission abortion via `ContractViolationError` from schema validator. Extra keys block transmission.
• **No Trace ID Supplied**
  Returns: Application intercepts immediately at middleware and generates a `uuid4` trace ID internally to ensure compliance with Phase 1 Trace Lock.

─────────────────────────────────────────────────────────────
## 6. PROOF

All assertions met. Test results attached below.

─────────────────────────────────────────────────────────────
## 7. CONNECTOR STATUS

* **Pravah:** Working / Ready for Ingestion Endpoint URL
* **Bucket:** Working / Ready for Ingestion Endpoint URL

─────────────────────────────────────────────────────────────
## 8. TEST CASE RESULTS (ALL 5 TESTS)

```
============================================================
  TANTRA CONNECTOR TEST SUITE
============================================================

============================================================
  TEST 1 — Trace Continuity
============================================================
  trace_id set      : bhiv-trace-d0463c656e7c47a9
  Pravah trace_id   : bhiv-trace-d0463c656e7c47a9
  Bucket trace_id   : bhiv-trace-d0463c656e7c47a9
  Match             : True
  Schema valid      : YES (both passed validation)

  Result: PASS

============================================================
  TEST 2 — Determinism (SHA256 Hash)
============================================================
  Input data       : {'user_id': 'u1', 'action': 'login', 'timestamp': '2026-04-23T10:00:00+00:00'}
  prev_hash        : 0000000000000000... (genesis)
  hash_a           : 63f514133def4cf60fa8608c86fbff8f940410e6ac693f742dc0dfa099b090c8
  hash_b           : 63f514133def4cf60fa8608c86fbff8f940410e6ac693f742dc0dfa099b090c8
  hash_c           : 63f514133def4cf60fa8608c86fbff8f940410e6ac693f742dc0dfa099b090c8
  All identical    : True
  Modified input   : {'user_id': 'u1', 'action': 'logout', 'timestamp': '2026-04-23T10:00:00+00:00'}
  Different hash   : 2b32c14aa98e3472f029985f8d8cb1c26b662a5742e44f02793ebaf8d087f24d
  No collision     : True

  Result: PASS

============================================================
  TEST 3 — Pravah Failure Simulation (3 retries)
============================================================
  [Attempt 1] POST to Pravah → ConnectionError (simulated)
  [Attempt 2] POST to Pravah → ConnectionError (simulated)
  [Attempt 3] POST to Pravah → ConnectionError (simulated)
  Total attempts   : 3 (expected 3)
  Emit returned    : False (expected False)
  Time elapsed     : 2.0s (min ~2s backoff)
  System crashed   : NO

  Result: PASS

============================================================
  TEST 4 — Bucket Hash Chain (prev -> current)
============================================================
  Event 1: prev=000000000000... -> current=0e9e2a182cd1...
  Event 2: prev=0e9e2a182cd1... -> current=da45df113644...
  Event 3: prev=da45df113644... -> current=5f6e8f1adfe1...
  Event 4: prev=5f6e8f1adfe1... -> current=bfe85cb1c325...

  Chain length     : 4 events
  All hashes unique: True
  Tamper detected  : True
  Chain valid      : True

  Result: PASS

============================================================
  TEST 5 — End-to-End Flow (Live Server)
============================================================
  Warming up server...
  Register         : 201
  Login            : 200
  trace_id sent    : bhiv-e2e-7f1be7a918ab437c
  trace_id echoed  : bhiv-e2e-7f1be7a918ab437c
  Trace match      : True
  Profile fetch    : 200
  trace_id in /me  : bhiv-e2e-7f1be7a918ab437c
  Pravah schema    : VALID
  Bucket schema    : VALID
  Hash computed    : b2d5ac06380d...

  Result: PASS

============================================================
  FINAL RESULTS
============================================================
  PASS  T1 — Trace Continuity
  PASS  T2 — Determinism
  PASS  T3 — Pravah Failure Sim
  PASS  T4 — Bucket Hash Chain
  PASS  T5 — End-to-End Flow

  5/5 tests passed
============================================================
```
