1. ENTRY POINT

Frontend Entry:
Path:
frontend/src/contexts/PranaContext.jsx

Backend Entry:
Path:
backend/app/main.py

The frontend PRANA context initializes the browser-side PRANA client and points it at the Bucket ingest endpoint.
The backend starts in FastAPI, mounts the Bucket and PRANA routers, then routes packets into append-only integrity logging.
Deterministic replay validation runs through separate PRANA verify and replay endpoints against stored integrity events.

2. CORE EXECUTION FLOW (MAX 3 FILES)

File 1:
Path:
backend/app/main.py

What it does:
Defines the FastAPI application and registers PRANA-related routers.
Initializes middleware, database startup, and append-only guard installation.

File 2:
Path:
backend/app/routers/bucket.py

What it does:
Handles incoming frontend PRANA packets and validates packet schema.
Stores packet data, queues it for downstream processing, and emits a PRANA runtime event.

File 3:
Path:
backend/app/services/prana_runtime.py

What it does:
Writes append-only integrity events and computes deterministic payload hashes.
Records replay validation results and rejects update or delete mutations on the integrity log.

3. LIVE FLOW (REAL EXECUTION)

User Action:
User activity is captured by the frontend PRANA context and sent to the backend Bucket ingest endpoint.

System Flow:

Frontend -> API -> Backend -> Response -> UI

Frontend:
POST /api/v1/bucket/prana/ingest

Backend Flow:

Client Packet
-> Bucket Ingest API
-> Pydantic Packet Validator
-> Packet Store / Queue
-> PRANA Runtime Service
-> Append-only Integrity Log
-> Response Generator

Example JSON Response:

{
"status": "ingested",
"packet_id": "9b2f5f2a-7b85-4c60-8f0d-9e8b6d96fef5",
"received_at": "2026-04-07T11:00:00+00:00"
}

4. WHAT WAS BUILT IN YOUR TASKS

What I added:

- Append-only enforcement logic for PRANA integrity log
- Deterministic hashing and replay validation paths
- Structured event validation pipeline
- PRANA replay orchestration, load testing, and system health observability

What I modified:

- Existing logging flow to prevent mutation operations
- PRANA API validation logic to enforce registered contract validation

What I did NOT touch:

- Frontend UI components
- Speech pipeline
- TTS modules
- DevOps infrastructure

5. FAILURE CASES

What breaks:

- Invalid contract request to PRANA ingest
- Attempted UPDATE or DELETE on append-only log
- Replay hash mismatch

How system behaves:

- Invalid ingest is rejected before insert
- Append-only mutation is blocked with structured violation response
- Replay mismatch is recorded as MISMATCH in replay_validation_log

What user sees:

HTTP 409 / 422 response, or replay_status=MISMATCH on replay APIs

Example:

{
"status": "rejected",
"error": "APPEND_ONLY_VIOLATION"
}

6. PROOF

Provide:

Console Log Output

Example:

[Startup] [OK] SQL database tables initialized
[Startup] [OK] bucket router
[Startup] [OK] prana router
[Startup] [OK] Startup event complete! Server will bind to port now.
[Startup] Background tasks (routers, DB, MongoDB, Watchdog) are active.

7. INTEGRATION TOUCHPOINTS

Format:

Name - Module - Interaction

PranaContext - frontend/src/contexts/PranaContext.jsx - Initializes PRANA and sends packets to /api/v1/bucket/prana/ingest

Bucket Router - backend/app/routers/bucket.py - Persists packets and emits Bucket events into PRANA runtime

Karma Event Router - backend/app/routers/karma_tracker/v1/karma/event.py - Emits Karma-side events into PRANA runtime

8. CURRENT RISKS (HONEST)

- Replay queries may need index tuning as integrity volume grows
- Load testing exists but sustained production traffic is not characterized yet
- Observability is API-level only and does not include alerting
- Runtime log and append-only tables will grow without retention policy

9. HANDOVER READINESS

Yes, a new developer can understand the PRANA entry points, request flow, append-only enforcement, deterministic hashing,
replay validation, load-test path, and system health endpoint using this document.

The implemented backend scope is documented and testable through the current PRANA APIs.
