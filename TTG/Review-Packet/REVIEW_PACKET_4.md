Here's the full updated content for REVIEW_PACKET_4.md — copy this exactly:

# REVIEW_PACKET_4.md

**Project:** Real-Time Micro-Bridge — BHIV TANTRA Sovereign Pipeline Node
**Task:** Convert Pipeline into Auditable, Replayable, Service-Exposed, Queryable System Node
**Author:** Rudra Parmeshwar
**Status:** COMPLETE — All 8 Phases Delivered

---

## Table of Contents

1. [Entry Point](#1-entry-point)
2. [Full Execution Flow](#2-full-execution-flow)
3. [Replay Engine](#3-replay-engine)
4. [API Endpoints](#4-api-endpoints)
5. [Determinism Proof](#5-determinism-proof)
6. [Failure Cases](#6-failure-cases)
7. [Artifact Proof](#7-artifact-proof)
8. [Telemetry Query Output](#8-telemetry-query-output)

---

## 1. Entry Point

### Primary Entry Point

**File:** `backend/domain-adapters/maritime/pipeline.js`
**Function:** `run(vesselInput, opts)`

Single callable function that executes the entire governed pipeline end-to-end.

```js
const { run } = require('./pipeline');

const result = await run(
  { vessel_id: 'VESSEL_ALPHA', lat: 25.1, lon: 55.2, speed: 8, heading: 45, status: 'moving' },
  { trace_id: 'my-trace-001', execution_id: 'exec_001' }
);


Copy
Replay Entry Point
File: backend/domain-adapters/maritime/replayEngine.js
Function: replay(trace_id)

Pure artifact-driven replay — reads 5 artifacts from bucket_artifacts/, runs 7 validation steps, returns ReplayResult.

const { replay } = require('./replayEngine');
const result = await replay('p8-allow-test');

Copy
js
Service Entry Points (API)
File: backend/routes/pipeline.js
Mounted at: /pipeline

Method	Endpoint	Description
POST	/pipeline/run	Run full pipeline from raw vessel signal
GET	/pipeline/result/:trace_id	Fetch all 5 artifacts for a trace
POST	/pipeline/replay/:trace_id	Run replay engine against stored artifacts
GET	/pipeline/telemetry/:trace_id	Query telemetry stages for a trace
GET	/pipeline/health	Service status + bucket health
Test Entry Points
Phase	Test File	Command
Phase 1	test_phase1_contract.js	node backend/domain-adapters/maritime/test_phase1_contract.js
Phase 2	test_phase2_enforcement.js	node backend/domain-adapters/maritime/test_phase2_enforcement.js
Phase 3	test_phase3_execution.js	node backend/domain-adapters/maritime/test_phase3_execution.js
Phase 4	test_phase4_event_collector.js	node backend/domain-adapters/maritime/test_phase4_event_collector.js
Phase 5	test_phase5_telemetry.js	node backend/domain-adapters/maritime/test_phase5_telemetry.js
Phase 6	test_phase6_bucket.js	node backend/domain-adapters/maritime/test_phase6_bucket.js
Phase 7	test_phase7_failure_hardening.js	node backend/domain-adapters/maritime/test_phase7_failure_hardening.js
Phase 8	test_phase8_validation.js	node backend/domain-adapters/maritime/test_phase8_validation.js
Replay	test_replay_engine.js	node backend/domain-adapters/maritime/test_replay_engine.js
Environment Variables Required
# Mitra (Raj — Decision Layer)
MITRA_HOST=localhost
MITRA_PORT=8000
MITRA_API_KEY=<key from Raj>
MITRA_TIMEOUT_MS=5000

# Execution Layer (Atharva)
EXECUTION_HOST=localhost
EXECUTION_PORT=9000
EXECUTION_PATH=/api/execution/submit
EXECUTION_API_KEY=<key from Atharva>

# Telemetry (optional)
TELEMETRY_HTTP_ENDPOINT=http://localhost:<port>/telemetry

# Stub — Phase 8 tests only (NEVER in production)
MITRA_STUB_ALLOWED=true

Copy
env
2. Full Execution Flow
Pipeline Architecture
Raw Input (vessel data)
    │
    ▼
[Phase 1] maritimeAdapter.adaptVessel()
    │  → parse, validate, normalize, map lat/lon → x/z
    │  → output: adapter schema with trace_id + execution_id
    │
    ▼
[Phase 1] contractBuilder.build()
    │  → strict schema lock against engineExecutionContract.json v2.0
    │  → strips domain + decisionEnvelope (governance only)
    │  → fails loud on missing required fields
    │
    ▼
[Phase 2] mitraClient.evaluate()
    │  → POST to Raj's Mitra endpoint
    │  → returns decisionEnvelope { decision, risk_level, confidence, source }
    │  → STUB_ALLOWED=false by default — FAIL LOUD if unreachable
    │
    ▼
[Phase 7] failureGuard.checkMitraResult()
    │  → decision != ALLOW → STOP, write artifacts, return FailureResult
    │  → FLAG  → DECISION_NOT_ALLOW, pipeline stops
    │  → BLOCK → DECISION_NOT_ALLOW, pipeline stops
    │
    ▼  (only if ALLOW)
[Phase 2] enforcementGate.enforce()
    │  → reads decisionEnvelope, makes NO decisions
    │  → ALLOW  → passed=true
    │  → FLAG   → passed=false, logged
    │  → BLOCK  → passed=false, terminated
    │  → stub source → BLOCK (STUB_DECISION)
    │
    ▼
[Phase 5] insightBridge.emitDecisionReceived()
         insightBridge.emitEnforcementApplied()
    │  → writes to in-memory stream + telemetry_<trace_id>.jsonl + HTTP endpoint
    │
    ▼  (only if gate passed)
[Phase 3] executionClient.submit()
    │  → POST contract to Atharva's execution layer
    │  → returns contract_accepted OR contract_rejected
    │  → NO retries, NO fallback — FAIL LOUD
    │
    ▼
[Phase 5] insightBridge.emitExecutionStarted()
    │
    ▼
[Phase 4] eventCollector.collect() × 4
    │  → contract_accepted
    │  → execution_started
    │  → entity_spawned
    │  → execution_completed
    │  → each stamped with trace_id + execution_id
    │
    ▼
[Phase 5] insightBridge.emitExecutionCompleted()
    │
    ▼
[Phase 6] pipelineBucketWriter.flush()
    │  → buffer → flush atomically (NO real-time writes)
    │  → writes all 5 artifacts in one pass
    │
    ▼
PipelineResult { success, path, trace_id, artifacts, telemetry_events, log }


Copy
Module Map
Module	File	Responsibility
Adapter	maritimeAdapter.js	Raw input → engine schema
Contract Lock	contractBuilder.js	Schema → strict v2.0 contract
Decision	mitraClient.js	Call Mitra, get ALLOW/FLAG/BLOCK
Enforcement	enforcementGate.js	Enforce decision, no bypass
Execution	executionClient.js	Send contract to Atharva
Event Capture	eventCollector.js	Collect 4 runtime events
Telemetry	insightBridge.js	Emit 4 stages, file + HTTP + query
Artifacts	pipelineBucketWriter.js	Buffer → flush 5 artifacts
Failure	failureGuard.js	13 named failure codes
Replay	replayEngine.js	Artifact-driven replay, 7 validation steps
Determinism	determinismValidator.js	Run N times, compare outputs
Orchestrator	pipeline.js	Wires all phases together
Service Layer	backend/routes/pipeline.js	5 HTTP endpoints, no business logic
3. Replay Engine
File: backend/domain-adapters/maritime/replayEngine.js
Test: node backend/domain-adapters/maritime/test_replay_engine.js
API: POST /pipeline/replay/:trace_id

What the Replay Engine Does
Reads all 5 artifacts from bucket_artifacts/ for a given trace_id and runs 7 validation steps:

Step 1 — Load all 5 artifacts (schema, decision, events, state, log)
Step 2 — Validate trace_id consistency across every artifact and every line
Step 3 — Reconstruct execution path (ALLOW / FLAG / BLOCK) from decision artifact
Step 4 — Re-emit all events in timestamp order
Step 5 — Validate pipeline stage sequence
Step 6 — Validate decision correctness (schema governance matches decision artifact)
Step 7 — Validate final state

Copy
Live Replay Output (trace: p8-allow-test)
[REPLAY:START         ] Replaying trace_id=p8-allow-test
[REPLAY:LOAD          ] Loading artifacts from bucket
[REPLAY:LOAD          ] All 5 artifacts loaded
[REPLAY:VALIDATE      ] Checking trace_id consistency across all artifacts
[REPLAY:VALIDATE      ] trace_id consistent across all artifacts
[REPLAY:PATH          ] Reconstructing execution path from decision artifact
[REPLAY:PATH          ] Execution path: ALLOW | decision=ALLOW | passed=true
[REPLAY:EVENTS        ] Re-emitting 8 events in timestamp order
[REPLAY:EVENTS        ] Re-emitted 8 events
[REPLAY:SEQUENCE      ] Validating pipeline stage sequence
[REPLAY:SEQUENCE      ] Sequence valid — stages: decision_received → enforcement_applied → execution_started → execution_completed
[REPLAY:DECISION      ] Validating decision correctness against schema
[REPLAY:DECISION      ] Decision correct: ALLOW | risk=LOW
[REPLAY:STATE         ] Validating final state
[REPLAY:STATE         ] State valid | execution_id=exec_p8_allow
[REPLAY:COMPLETE      ] Replay complete | path=ALLOW | events=8

Copy
ReplayResult Shape
{
  "success": true,
  "trace_id": "p8-allow-test",
  "execution_id": "exec_p8_allow",
  "path": "ALLOW",
  "decision": "ALLOW",
  "risk_level": "LOW",
  "event_count": 8,
  "sequence": [
    "decision_received",
    "enforcement_applied",
    "execution_started",
    "execution_completed"
  ],
  "state_summary": {
    "execution_id": "exec_p8_allow",
    "stopped": false,
    "decision": "ALLOW"
  },
  "failure": null
}

Copy
json
Replay Failure Codes
Code	Trigger
MISSING_TRACE_ID	trace_id not provided
ARTIFACT_LOAD_FAILED	one or more of the 5 artifacts missing or unreadable
TRACE_MISMATCH	trace_id inconsistent across artifacts or event lines
SEQUENCE_INVALID	required pipeline stages missing or out of order
DECISION_MISMATCH	schema governance decision ≠ decision artifact decision
STATE_INVALID	state.trace_id mismatch or ALLOW path with stopped=true
4. API Endpoints
File: backend/routes/pipeline.js
Mounted at: /pipeline

No business logic in controllers — all logic lives in modules.

POST /pipeline/run
Accepts a raw vessel signal, runs the full governance pipeline, returns PipelineResult.

curl -X POST http://localhost:3000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "vessel_id": "VESSEL_ALPHA",
    "lat": 25.1,
    "lon": 55.2,
    "speed": 8,
    "heading": 45,
    "status": "moving"
  }'

Copy
bash
Response (ALLOW — HTTP 200):

{
  "success": true,
  "path": "ALLOW",
  "trace_id": "maritime_c9e761c9-2f30-4d29-9e00-5875ae6c6f0c",
  "execution_id": "exec_maritime_...",
  "duration": 116,
  "artifacts": ["schema.json", "decision.json", "events.jsonl", "state.json", "log.jsonl"],
  "failure": null
}

Copy
json
Response (FLAG/BLOCK — HTTP 422):

{
  "success": false,
  "path": "DECISION_NOT_ALLOW",
  "trace_id": "...",
  "failure": {
    "failed": true,
    "failure_code": "DECISION_NOT_ALLOW",
    "stage": "decision",
    "reason": "Decision is FLAG — execution will not proceed."
  }
}

Copy
json
GET /pipeline/result/:trace_id
Returns all 5 artifacts for a completed execution.

curl http://localhost:3000/pipeline/result/p8-allow-test

Copy
bash
Response:

{
  "success": true,
  "trace_id": "p8-allow-test",
  "artifacts": {
    "schema":   { "artifact_type": "bhiv_execution_schema", "..." : "..." },
    "decision": { "artifact_type": "bhiv_decision_record",  "..." : "..." },
    "events":   [ "..." ],
    "state":    { "artifact_type": "bhiv_final_state",      "..." : "..." },
    "log":      [ "..." ]
  }
}

Copy
json
POST /pipeline/replay/:trace_id
Runs replayEngine.replay() against stored artifacts.

curl -X POST http://localhost:3000/pipeline/replay/p8-allow-test

Copy
bash
Response: ReplayResult shape — see Section 3.

GET /pipeline/telemetry/:trace_id
Queries in-memory + file telemetry for a trace. Supports optional ?stage= filter.

# All stages
curl http://localhost:3000/pipeline/telemetry/p8-allow-test

# Single stage
curl "http://localhost:3000/pipeline/telemetry/p8-allow-test?stage=decision_received"

Copy
bash
Response:

{
  "success": true,
  "trace_id": "p8-allow-test",
  "source": "file",
  "total": 4,
  "filtered": 4,
  "stage_filter": null,
  "stages_present": ["decision_received", "enforcement_applied", "execution_started", "execution_completed"],
  "trace_consistent": true,
  "events": [ "..." ]
}

Copy
json
GET /pipeline/health
curl http://localhost:3000/pipeline/health

Copy
bash
Response:

{
  "success": true,
  "service": "pipeline",
  "status": "ok",
  "bucket_accessible": true,
  "artifact_count": 172,
  "checked_at": 1776833214535
}

Copy
json
5. Determinism Proof
File: backend/domain-adapters/maritime/determinismValidator.js

Same vessel input run through the pipeline 3 times. These fields must be identical across all runs:

Field	Why It Must Be Deterministic
path	ALLOW/FLAG/BLOCK determined by vessel data + policy — not time
decision	Mitra returns the same decision for the same input
risk_level	Mitra risk assessment is deterministic for the same signal
enforcement.passed/blocked/flagged	Gate result follows directly from decision
contract.game_mode	Adapter mapping is a pure function of vessel fields
contract.entities	Position/rotation derived from lat/lon/heading — no randomness
contract.physics	Maritime constants — always gravity: [0,0,0]
contract.movement	Speed clamped deterministically (1–15)
contract.scoring	Fixed schema defaults
contract.spawn_rules	Fixed schema defaults
contract.player_params	Fixed schema defaults
contract.scene	Fixed maritime scene constants
event_sequence	Pre-runtime stages always fire in the same order
artifact_keys	All 5 artifacts always written regardless of path
failure_code	Same input always produces the same failure code
failure_stage	Same input always fails at the same stage
What Is Allowed to Vary
trace_id, execution_id, telemetry_id, event_id,
timestamp, logged_at, decided_at, enforced_at,
buffered_at, flushed_at, collected_at, accepted_at,
started_at, completed_at, stopped_at,
duration, mitra_trace_id, your_trace_id

Copy
Wall-clock times and UUIDs — vary by design, do not affect pipeline behavior.

Determinism Checks (19/19 passed)
✅ path                    — ALLOW identical across 3 runs
✅ failure_code            — null identical across 3 runs
✅ failure_stage           — null identical across 3 runs
✅ decision                — ALLOW identical across 3 runs
✅ risk_level              — LOW identical across 3 runs
✅ enforcement.passed      — true identical across 3 runs
✅ enforcement.blocked     — false identical across 3 runs
✅ enforcement.flagged     — false identical across 3 runs
✅ enforcement.decision    — ALLOW identical across 3 runs
✅ contract.game_mode      — open_scene identical across 3 runs
✅ contract.entities       — [{"id":"VESSEL_ALPHA","type":"npc",...}] identical
✅ contract.physics        — {"gravity":[0,0,0],"friction":0.1,...} identical
✅ contract.movement       — {"speed":8,"jump_height":0} identical
✅ contract.scoring        — identical across 3 runs
✅ contract.spawn_rules    — identical across 3 runs
✅ contract.player_params  — identical across 3 runs
✅ contract.scene          — identical across 3 runs
✅ event_sequence          — ["decision_received","enforcement_applied","execution_started"] identical
✅ artifact_keys           — ["decision","events","log","schema","state"] identical

Determinism: CONFIRMED — 19/19 checks passed

Copy
Coordinate Mapping (Pure Function)
lat: 25.1   → x: 2510   (lat × 100, deterministic)
lon: 55.2   → z: 5520   (lon × 100, deterministic)
heading: 45 → rotation[1]: 45  (direct mapping)
speed: 8    → movement.speed: 8 (clamped 1–15, deterministic)
gravity     → [0,0,0]   (maritime constant, always)

Copy
Same input → same contract. No randomness anywhere in the adapter or contract builder.

6. Failure Cases
File: backend/domain-adapters/maritime/failureGuard.js

All failures return a structured FailureResult — no silent behavior anywhere.

All 13 Failure Codes
Code	Stage	Trigger	Behavior
MISSING_TRACE_ID	input	trace_id is null or empty	Pipeline stops immediately before any call
DECISION_NOT_ALLOW	decision	Mitra returns FLAG or BLOCK	Pipeline stops, artifacts written, no execution
MITRA_UNREACHABLE	decision	Mitra endpoint down, stub disabled	FAIL LOUD — no execution
MITRA_INVALID_RESPONSE	decision	Mitra returns malformed response	FAIL LOUD
ENFORCEMENT_BLOCKED	enforcement	Gate returns blocked=true	Pipeline stops
ENFORCEMENT_FLAGGED	enforcement	Gate returns flagged=true	Pipeline stops
STUB_DECISION	enforcement	Decision source is 'stub'	Blocked — stub never reaches execution
CONTRACT_BUILD_FAILED	contract	contractBuilder returns errors	Pipeline stops
EXECUTION_REJECTED	execution	Atharva returns contract_rejected	Log + stop
EXECUTION_UNREACHABLE	execution	Atharva endpoint down	FAIL LOUD, no retry
EVENT_STREAM_BROKEN	event_stream	Null event, missing fields, trace mismatch	FAIL LOUD
EVENT_STREAM_INCOMPLETE	event_stream	execution_completed never received	FAIL LOUD
UNKNOWN	any	Unclassified error	Wrapped by fromError(), never silent
FailureResult Shape (same for every failure)
{
  "failed": true,
  "failure_code": "DECISION_NOT_ALLOW",
  "stage": "decision",
  "reason": "Decision is FLAG — execution will not proceed.",
  "trace_id": "p8-flag-test",
  "execution_id": "exec_p8_flag",
  "stopped_at": 1776833214615,
  "meta": {
    "decision": "FLAG",
    "risk_level": "MEDIUM",
    "reason": "Vessel speed exceeds safe threshold"
  }
}

Copy
json
Phase 7 Test Results (115 checks)
── Case C: Missing trace_id → fail ────────────────────────────
  ✅ assertTraceId(null) — code=MISSING_TRACE_ID
  ✅ assertTraceId("")   — code=MISSING_TRACE_ID

── Case A: decision != ALLOW → no execution ───────────────────
  ✅ FLAG decision  — code=DECISION_NOT_ALLOW
  ✅ BLOCK decision — code=DECISION_NOT_ALLOW

── Case B: Execution rejection → log + stop ───────────────────
  ✅ execution rejected — code=EXECUTION_REJECTED

── Case D: Broken event stream → fail ─────────────────────────
  ✅ null event          — code=EVENT_STREAM_BROKEN
  ✅ trace_id mismatch   — code=EVENT_STREAM_BROKEN
  ✅ stream incomplete   — code=EVENT_STREAM_INCOMPLETE

Phase 7 Failure Hardening — 115 checks
  ✅ Passed : 115  ❌ Failed : 0

Copy
7. Artifact Proof
ALLOW Path — All 5 Artifacts
Artifact	File	Content
Schema	execution_p8-allow-test_schema.json	Contract-locked payload, governance metadata
Decision	execution_p8-allow-test_decision.json	Mitra envelope + enforcement result
Events	execution_p8-allow-test_events.jsonl	8 lines: 4 runtime + 4 telemetry
State	execution_p8-allow-test_state.json	Final vessel state snapshot
Log	execution_p8-allow-test_log.jsonl	13 pipeline log entries
FLAG Path — Artifacts Written on Stop
Artifact	File	Content
Schema	execution_p8-flag-test_schema.json	Contract built before stop
Decision	execution_p8-flag-test_decision.json	FLAG decision + enforcement_result.passed=false
Events	execution_p8-flag-test_events.jsonl	1 event: pipeline_stopped
State	execution_p8-flag-test_state.json	{ stopped: true, decision: "FLAG" }
Log	execution_p8-flag-test_log.jsonl	6 log entries up to stop point
BLOCK Path — Artifacts Written on Stop
Artifact	File	Content
Schema	execution_p8-block-test_schema.json	Contract built before stop
Decision	execution_p8-block-test_decision.json	BLOCK decision + enforcement_result.blocked=true
Events	execution_p8-block-test_events.jsonl	1 event: pipeline_stopped
State	execution_p8-block-test_state.json	{ stopped: true, decision: "BLOCK" }
Log	execution_p8-block-test_log.jsonl	6 log entries up to stop point
Artifact Rules Verified
NO real-time writes — all data buffered in memory until flush()

flush() called exactly once per pipeline run

All 5 artifacts share the same trace_id

flushed_at timestamp identical across all 5 files in a run

JSONL files are valid — every line parses independently

domain field stripped from contract before writing

decisionEnvelope stripped from contract before writing

Real Events File — ALLOW Path
File: bucket_artifacts/execution_p8-allow-test_events.jsonl

{"event_id":"522f44c5-...","event_type":"contract_accepted","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"accepted_at":1776833214530}}
{"event_id":"56f67545-...","event_type":"execution_started","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"started_at":1776833214535}}
{"event_id":"f56a2d1d-...","event_type":"entity_spawned","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"entity_id":"VESSEL_ALPHA","entity_type":"npc"}}
{"event_id":"0344cb61-...","event_type":"execution_completed","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"status":"completed","duration":68}}
{"telemetry_id":"cc710a2e-...","trace_id":"p8-allow-test","stage":"decision_received","timestamp":1776833214509,"metadata":{"decision":"ALLOW","risk_level":"LOW","confidence":0.95,"source":"mitra"}}
{"telemetry_id":"92dd357f-...","trace_id":"p8-allow-test","stage":"enforcement_applied","timestamp":1776833214512,"metadata":{"passed":true,"blocked":false,"flagged":false,"decision":"ALLOW"}}
{"telemetry_id":"2c78f83f-...","trace_id":"p8-allow-test","stage":"execution_started","timestamp":1776833214514,"metadata":{"game_mode":"open_scene","entity_count":1}}
{"telemetry_id":"60286995-...","trace_id":"p8-allow-test","stage":"execution_completed","timestamp":1776833214536,"metadata":{"status":"completed","duration":69,"event_count":4}}

Copy
jsonl
Real Pipeline Log — ALLOW Path
File: bucket_artifacts/execution_p8-allow-test_log.jsonl

[START       ] Pipeline started | trace=p8-allow-test | vessel=VESSEL_ALPHA
[ADAPTER     ] Building execution schema
[ADAPTER     ] Contract locked | execution_id=exec_p8_allow
[MITRA       ] Requesting governance decision
[MITRA       ] Decision: ALLOW | risk=LOW | source=mitra
[ENFORCEMENT ] Applying governance decision
[ENFORCEMENT ] Gate result: passed=true | decision=ALLOW
[EXECUTION   ] Submitting contract to execution layer
[EXECUTION   ] Contract accepted | accepted_at=1776833214530
[EVENTS      ] Collecting runtime events
[EVENTS      ] Stream complete | 4 events collected
[TELEMETRY   ] Emitted 4 telemetry stages
[BUCKET      ] Flushing artifacts
[COMPLETE    ] Pipeline complete | duration=116ms

Copy
Phase 6 Test Results
Phase 6 Bucket Artifacts — 65 checks
  ✅ Passed : 65  ❌ Failed : 0

Copy
8. Telemetry Query Output
File: backend/domain-adapters/maritime/insightBridge.js
API: GET /pipeline/telemetry/:trace_id

Transports
Transport	Behavior
In-memory stream	Keyed by trace_id, replayable, cleared per test run
File	Appends to bucket_artifacts/telemetry_<trace_id>.jsonl
HTTP	POSTs to TELEMETRY_HTTP_ENDPOINT if set (non-blocking, non-fatal)
ALLOW Path — 4 Telemetry Events
{"telemetry_id":"cc710a2e-...","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"decision_received","timestamp":1776833214509,"metadata":{"decision":"ALLOW","risk_level":"LOW","confidence":0.95,"reason":"Content passed existing safety validation and enforcement checks.","source":"mitra"}}
{"telemetry_id":"92dd357f-...","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"enforcement_applied","timestamp":1776833214512,"metadata":{"passed":true,"blocked":false,"flagged":false,"decision":"ALLOW","source":"mitra","enforced_at":1776833214512}}
{"telemetry_id":"2c78f83f-...","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"execution_started","timestamp":1776833214514,"metadata":{"game_mode":"open_scene","entity_count":1}}
{"telemetry_id":"60286995-...","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"execution_completed","timestamp":1776833214536,"metadata":{"status":"completed","duration":69,"event_count":4}}

Copy
jsonl
FLAG Path — 2 Telemetry Events (stopped at enforcement)
{"telemetry_id":"...","trace_id":"p8-flag-test","stage":"decision_received","timestamp":1776833214613,"metadata":{"decision":"FLAG","risk_level":"MEDIUM","confidence":0.78,"reason":"Vessel speed exceeds safe threshold — requires monitoring.","source":"mitra"}}
{"telemetry_id":"...","trace_id":"p8-flag-test","stage":"enforcement_applied","timestamp":1776833214615,"metadata":{"passed":false,"blocked":false,"flagged":true,"decision":"FLAG"}}

Copy
jsonl
execution_started and execution_completed NOT emitted — pipeline stopped before execution.

BLOCK Path — 2 Telemetry Events (stopped at enforcement)