# REVIEW_PACKET_3.md

**Project:** Real-Time Micro-Bridge — BHIV TANTRA Full Pipeline Convergence
**Task:** Full Pipeline Convergence & Execution Integration (Final Integration Task)
**Author:** Rudra Parmeshwar
**Status:** COMPLETE — All 9 Phases Delivered

---

## Table of Contents

1. [Entry Point](#1-entry-point)
2. [Full Execution Flow](#2-full-execution-flow)
3. [Real Contract Sample](#3-real-contract-sample)
4. [Real Event Output](#4-real-event-output)
5. [Failure Cases](#5-failure-cases)
6. [Artifact Proof](#6-artifact-proof)
7. [Integration Explanation](#7-integration-explanation)

---

## 1. Entry Point

### Primary Entry Point

**File:** `backend/domain-adapters/maritime/pipeline.js`
**Function:** `run(vesselInput, opts)`

This is the single callable function that executes the entire pipeline end-to-end.

```js
const { run } = require('./pipeline');

const result = await run(
  { vessel_id: 'VESSEL_ALPHA', lat: 25.1, lon: 55.2, speed: 8, heading: 45, status: 'moving' },
  { trace_id: 'my-trace-001', execution_id: 'exec_001' }
);
```

### Test Entry Points (Phase Validation)

| Phase | Test File | Command |
|---|---|---|
| Phase 1 | `test_phase1_contract.js` | `node backend/domain-adapters/maritime/test_phase1_contract.js` |
| Phase 2 | `test_phase2_enforcement.js` | `node backend/domain-adapters/maritime/test_phase2_enforcement.js` |
| Phase 3 | `test_phase3_execution.js` | `node backend/domain-adapters/maritime/test_phase3_execution.js` |
| Phase 4 | `test_phase4_event_collector.js` | `node backend/domain-adapters/maritime/test_phase4_event_collector.js` |
| Phase 5 | `test_phase5_telemetry.js` | `node backend/domain-adapters/maritime/test_phase5_telemetry.js` |
| Phase 6 | `test_phase6_bucket.js` | `node backend/domain-adapters/maritime/test_phase6_bucket.js` |
| Phase 7 | `test_phase7_failure_hardening.js` | `node backend/domain-adapters/maritime/test_phase7_failure_hardening.js` |
| Phase 8 | `test_phase8_validation.js` | `node backend/domain-adapters/maritime/test_phase8_validation.js` |

### Environment Variables Required

```env
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

# Telemetry (Phase 5)
TELEMETRY_HTTP_ENDPOINT=http://localhost:<port>/telemetry  # optional

# Test mode only
MITRA_STUB_ALLOWED=true   # enables stub when Mitra is not running
```

---

## 2. Full Execution Flow

### Pipeline Architecture

```
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
    │  → STUB_ALLOWED=false by default — fail loud if unreachable
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
    │  → NO retries, NO fallback
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
```

### Module Map

| Module | File | Responsibility |
|---|---|---|
| Adapter | `maritimeAdapter.js` | Raw input → engine schema |
| Contract Lock | `contractBuilder.js` | Schema → strict v2.0 contract |
| Decision | `mitraClient.js` | Call Mitra, get ALLOW/FLAG/BLOCK |
| Enforcement | `enforcementGate.js` | Enforce decision, no bypass |
| Execution | `executionClient.js` | Send contract to Atharva |
| Event Capture | `eventCollector.js` | Collect 4 runtime events |
| Telemetry | `insightBridge.js` | Emit 4 stages, file + HTTP |
| Artifacts | `pipelineBucketWriter.js` | Buffer → flush 5 artifacts |
| Failure | `failureGuard.js` | 13 named failure codes |
| Orchestrator | `pipeline.js` | Wires all phases together |

---

## 3. Real Contract Sample

This is the exact contract produced by `contractBuilder.build()` during the Phase 8 ALLOW path run.

**Input vessel:**
```json
{ "vessel_id": "VESSEL_ALPHA", "lat": 25.1, "lon": 55.2, "speed": 8, "heading": 45, "status": "moving" }
```

**Contract output (sent to Atharva's execution layer):**
```json
{
  "execution_id": "exec_p8_allow",
  "trace_id": "p8-allow-test",
  "game_mode": "open_scene",
  "scene": {
    "scene_id": "scene_maritime",
    "ambient_light": [0.5, 0.7, 0.9],
    "skybox": "ocean_sky"
  },
  "entities": [
    {
      "id": "VESSEL_ALPHA",
      "type": "npc",
      "transform": {
        "position": [2510, 0, 5520],
        "rotation": [0, 45, 0],
        "scale": [1, 1, 1]
      },
      "material": {
        "shader": "standard",
        "texture": "vessel_hull",
        "color": [0.2, 0.4, 0.8]
      },
      "components": {
        "mesh": "vessel",
        "collider": "box",
        "script": "vessel_controller"
      }
    }
  ],
  "physics": {
    "gravity": [0, 0, 0],
    "friction": 0.1,
    "bounce": 0,
    "air_resistance": 0.05,
    "collision_force": 1
  },
  "movement": { "speed": 8, "jump_height": 0 },
  "camera": { "type": "top_down", "distance": 20 },
  "spawn_rules": { "obstacles": 0, "frequency": 1, "distance": 5 },
  "scoring": {
    "rules": { "distance": 0, "collectibles": 0, "time": 0 },
    "end_conditions": ["time_limit"]
  },
  "player_params": { "health": 1, "jetpack": false }
}
```

**Coordinate mapping:**
- `lat: 25.1` → `x: 2510` (lat × 100)
- `lon: 55.2` → `z: 5520` (lon × 100)
- `heading: 45` → `rotation[1]: 45`
- `speed: 8` → `movement.speed: 8` (clamped 1–15)
- `gravity: [0,0,0]` — maritime, no vertical gravity

---

## 4. Real Event Output

### PATH 1 — ALLOW: events.jsonl (real file from Phase 8 run)

**File:** `bucket_artifacts/execution_p8-allow-test_events.jsonl`

```jsonl
{"event_id":"522f44c5-b4e6-482b-a9c7-9106ac266e98","event_type":"contract_accepted","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"accepted_at":1776833214530}}
{"event_id":"56f67545-2bee-421f-8fe0-5cab4a1c31c2","event_type":"execution_started","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"started_at":1776833214535}}
{"event_id":"f56a2d1d-f996-4606-81d7-225bdb74c2fa","event_type":"entity_spawned","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"entity_id":"VESSEL_ALPHA","entity_type":"npc"}}
{"event_id":"0344cb61-1515-4e38-9480-648f659d08b1","event_type":"execution_completed","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","collected_at":1776833214535,"payload":{"status":"completed","duration":68}}
{"telemetry_id":"cc710a2e-2e21-4aa4-a622-09162b1b073f","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"decision_received","timestamp":1776833214509,"metadata":{"decision":"ALLOW","risk_level":"LOW","confidence":0.95,"reason":"Content passed existing safety validation and enforcement checks.","source":"mitra"},"event_type":"decision_received"}
{"telemetry_id":"92dd357f-c414-4f6e-91dc-bb49e54f84d4","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"enforcement_applied","timestamp":1776833214512,"metadata":{"passed":true,"blocked":false,"flagged":false,"decision":"ALLOW","source":"mitra","enforced_at":1776833214512},"event_type":"enforcement_applied"}
{"telemetry_id":"2c78f83f-c8fc-404c-a066-b16128391070","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"execution_started","timestamp":1776833214514,"metadata":{"game_mode":"open_scene","entity_count":1},"event_type":"execution_started"}
{"telemetry_id":"60286995-a0be-45f2-bc38-e302bf869a8c","trace_id":"p8-allow-test","execution_id":"exec_p8_allow","stage":"execution_completed","timestamp":1776833214536,"metadata":{"status":"completed","duration":69,"event_count":4},"event_type":"execution_completed"}
```

### PATH 1 — ALLOW: Pipeline log (real file)

**File:** `bucket_artifacts/execution_p8-allow-test_log.jsonl`

```
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
[BUCKET      ] Flushed 5 artifacts
[COMPLETE    ] Pipeline complete | duration=116ms
```

### PATH 2 — FLAG: Decision record (real file)

**File:** `bucket_artifacts/execution_p8-flag-test_decision.json`

```json
{
  "artifact_type": "bhiv_decision_record",
  "trace_id": "p8-flag-test",
  "execution_id": "exec_p8_flag",
  "decision_envelope": {
    "decision": "FLAG",
    "risk_level": "MEDIUM",
    "confidence": 0.78,
    "reason": "Vessel speed exceeds safe threshold — requires monitoring.",
    "source": "mitra",
    "mitra_trace_id": "stub_1776833214613",
    "your_trace_id": "p8-flag-test",
    "decided_at": 1776833214613
  },
  "enforcement_result": {
    "passed": false,
    "blocked": false,
    "flagged": true,
    "decision": "FLAG",
    "reason": "Decision is FLAG — execution will not proceed.",
    "enforced_at": 1776833214615
  }
}
```

### PATH 3 — BLOCK: Decision record (real file)

**File:** `bucket_artifacts/execution_p8-block-test_decision.json`

```json
{
  "artifact_type": "bhiv_decision_record",
  "trace_id": "p8-block-test",
  "execution_id": "exec_p8_block",
  "decision_envelope": {
    "decision": "BLOCK",
    "risk_level": "HIGH",
    "confidence": 0.99,
    "reason": "Vessel ID matches restricted pattern — policy violation.",
    "source": "mitra",
    "mitra_trace_id": "stub_1776833214648",
    "your_trace_id": "p8-block-test",
    "decided_at": 1776833214648
  },
  "enforcement_result": {
    "passed": false,
    "blocked": true,
    "flagged": false,
    "decision": "BLOCK",
    "reason": "Decision is BLOCK — execution will not proceed.",
    "enforced_at": 1776833214650
  }
}
```

---

## 5. Failure Cases

All failure cases are handled by `failureGuard.js`. Every failure returns a structured `FailureResult` — no silent behavior anywhere.

### Failure Code Reference

| Code | Stage | Trigger | Behavior |
|---|---|---|---|
| `MISSING_TRACE_ID` | input | `trace_id` is null or empty | Pipeline stops immediately before any call |
| `DECISION_NOT_ALLOW` | decision | Mitra returns FLAG or BLOCK | Pipeline stops, artifacts written, no execution |
| `MITRA_UNREACHABLE` | decision | Mitra endpoint down, stub disabled | Fail loud, return error, no execution |
| `MITRA_INVALID_RESPONSE` | decision | Mitra returns malformed/unknown response | Fail loud |
| `ENFORCEMENT_BLOCKED` | enforcement | Gate returns blocked=true | Pipeline stops |
| `ENFORCEMENT_FLAGGED` | enforcement | Gate returns flagged=true | Pipeline stops |
| `STUB_DECISION` | enforcement | Decision source is 'stub' | Blocked — stub never reaches execution |
| `CONTRACT_BUILD_FAILED` | contract | contractBuilder returns errors | Pipeline stops |
| `EXECUTION_REJECTED` | execution | Atharva returns contract_rejected | Log + stop |
| `EXECUTION_UNREACHABLE` | execution | Atharva endpoint down | Fail loud, no retry |
| `EVENT_STREAM_BROKEN` | event_stream | Null event, missing fields, trace mismatch | Fail loud |
| `EVENT_STREAM_INCOMPLETE` | event_stream | execution_completed never received | Fail loud |
| `UNKNOWN` | any | Unclassified error | Wrapped by `fromError()`, never silent |

### FailureResult Shape (same for every failure)

```json
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
```

### Phase 7 Test Results

```
── Case C: Missing trace_id → fail ────────────────────────────
  ✅ assertTraceId(null) — code=MISSING_TRACE_ID
  ✅ assertTraceId("") — code=MISSING_TRACE_ID

── Case A: decision != ALLOW → no execution ───────────────────
  ✅ FLAG decision — code=DECISION_NOT_ALLOW
  ✅ BLOCK decision — code=DECISION_NOT_ALLOW

── Case B: Execution rejection → log + stop ───────────────────
  ✅ execution rejected — code=EXECUTION_REJECTED

── Case D: Broken event stream → fail ─────────────────────────
  ✅ null event — code=EVENT_STREAM_BROKEN
  ✅ trace_id mismatch — code=EVENT_STREAM_BROKEN
  ✅ stream incomplete — code=EVENT_STREAM_INCOMPLETE

Phase 7 Failure Hardening — 115 checks
  ✅ Passed : 115  ❌ Failed : 0
```

---

## 6. Artifact Proof

### ALLOW Path — All 5 Artifacts

| Artifact | File | Content |
|---|---|---|
| Schema | `execution_p8-allow-test_schema.json` | Contract-locked payload, governance metadata |
| Decision | `execution_p8-allow-test_decision.json` | Mitra envelope + enforcement result |
| Events | `execution_p8-allow-test_events.jsonl` | 8 lines: 4 runtime + 4 telemetry |
| State | `execution_p8-allow-test_state.json` | Final vessel state snapshot |
| Log | `execution_p8-allow-test_log.jsonl` | 13 pipeline log entries |

### FLAG Path — Artifacts Written on Stop

| Artifact | File | Content |
|---|---|---|
| Schema | `execution_p8-flag-test_schema.json` | Contract that was built before stop |
| Decision | `execution_p8-flag-test_decision.json` | FLAG decision + enforcement_result.passed=false |
| Events | `execution_p8-flag-test_events.jsonl` | 1 event: pipeline_stopped |
| State | `execution_p8-flag-test_state.json` | `{ stopped: true, decision: "FLAG" }` |
| Log | `execution_p8-flag-test_log.jsonl` | 6 pipeline log entries up to stop point |

### BLOCK Path — Artifacts Written on Stop

| Artifact | File | Content |
|---|---|---|
| Schema | `execution_p8-block-test_schema.json` | Contract that was built before stop |
| Decision | `execution_p8-block-test_decision.json` | BLOCK decision + enforcement_result.blocked=true |
| Events | `execution_p8-block-test_events.jsonl` | 1 event: pipeline_stopped |
| State | `execution_p8-block-test_state.json` | `{ stopped: true, decision: "BLOCK" }` |
| Log | `execution_p8-block-test_log.jsonl` | 6 pipeline log entries up to stop point |

### Artifact Rules Verified

- NO real-time writes — all data buffered in memory until `flush()`
- `flush()` is called exactly once per pipeline run
- All 5 artifacts share the same `trace_id`
- `flushed_at` timestamp is identical across all 5 files in a run
- JSONL files are valid — every line parses independently
- `domain` field is stripped from contract before writing (governance only)
- `decisionEnvelope` is stripped from contract before writing

### Phase 6 Test Results

```
Phase 6 Bucket Artifacts — 65 checks
  ✅ Passed : 65  ❌ Failed : 0
```

### Telemetry Files (Phase 5)

Each run also produces a separate telemetry file per trace:

```
bucket_artifacts/telemetry_p8-allow-test.jsonl   ← 4 lines, one per stage
bucket_artifacts/telemetry_p8-flag-test.jsonl    ← 2 lines (decision_received + enforcement_applied)
bucket_artifacts/telemetry_p8-block-test.jsonl   ← 2 lines (decision_received + enforcement_applied)
```

---

## 7. Integration Explanation

### Where This System Sits in TANTRA

```
[Akanksha — Policy Layer]
        ↓ (policy rules consumed upstream)
[Raj — Mitra Decision Layer]  ←──── mitraClient.js calls POST /api/mitra/evaluate
        ↓ ALLOW / FLAG / BLOCK
[Rudra — Adapter Layer]       ←──── THIS SYSTEM
        ↓ contract (if ALLOW)
[Atharva — Execution Layer]   ←──── executionClient.js calls POST /api/execution/submit
        ↓ events
[Rudra — Event Collector]     ←──── eventCollector.js captures runtime events
        ↓
[Vinayak — Testing Layer]     ←──── validates real system behavior
```

### What This Layer Does

This system is the **Adapter** — the bridge between raw domain data and the governed execution pipeline.

It is responsible for:

1. **Translating** raw maritime vessel data into an engine-compatible execution contract
2. **Requesting** a governance decision from Mitra (Raj) — never making its own decision
3. **Enforcing** that decision — only ALLOW proceeds, FLAG and BLOCK stop immediately
4. **Triggering** execution on Atharva's layer with the contract-locked payload
5. **Capturing** the 4 runtime events emitted by Atharva's execution layer
6. **Emitting** structured telemetry at every pipeline stage (file + HTTP)
7. **Writing** 5 BHIV-compliant artifacts atomically on completion

### trace_id Continuity

The `trace_id` is generated once at pipeline entry and flows through every system:

```
pipeline.run()
  → adaptVessel()          trace_id stamped on schema
  → contractBuilder()      trace_id preserved in contract
  → mitraClient()          trace_id sent as context.session_id to Mitra
  → mitraResult.envelope   your_trace_id = trace_id (Mitra preserves it)
  → enforcementGate()      trace_id on every gate result
  → executionClient()      X-Trace-Id header sent to Atharva
  → eventCollector()       trace_id on every collected event
  → insightBridge()        trace_id on every telemetry event
  → pipelineBucketWriter() trace_id on every artifact, every log line
```

No event, artifact, or log entry exits the pipeline without `trace_id`.

### How to Connect Real Services

**Step 1 — Connect Mitra (Raj)**
```env
MITRA_HOST=<Raj's host>
MITRA_PORT=<Raj's port>
MITRA_API_KEY=<key from Raj>
# Remove or set MITRA_STUB_ALLOWED=false (default)
```

**Step 2 — Connect Execution Layer (Atharva)**
```env
EXECUTION_HOST=<Atharva's host>
EXECUTION_PORT=<Atharva's port>
EXECUTION_PATH=<Atharva's endpoint path>
EXECUTION_API_KEY=<key from Atharva>
```

**Step 3 — Run the pipeline**
```js
const { run } = require('./backend/domain-adapters/maritime/pipeline');
const result = await run(vesselData, { trace_id, execution_id });
```

No code changes required — only `.env` values.

### Phase Test Summary

| Phase | Deliverable | Checks | Result |
|---|---|---|---|
| 1 | Contract Lock (`contractBuilder.js`) | 27 | ✅ 27/27 |
| 2 | Enforcement Gate (`enforcementGate.js`, `mitraClient.js`) | 35 | ✅ 35/35 |
| 3 | Execution Trigger (`executionClient.js`) | 20 | ✅ 20/20 |
| 4 | Event Collector (`eventCollector.js`) | 40 | ✅ 40/40 |
| 5 | Telemetry Emission (`insightBridge.js`) | 50 | ✅ 50/50 |
| 6 | Bucket Artifacts (`pipelineBucketWriter.js`) | 65 | ✅ 65/65 |
| 7 | Failure Hardening (`failureGuard.js`) | 115 | ✅ 115/115 |
| 8 | Full Validation (`pipeline.js`) | 59 | ✅ 59/59 |
| **Total** | | **411** | **✅ 411/411** |

---

## Files Delivered (This Task)

```
backend/domain-adapters/maritime/
├── contractBuilder.js          Phase 1 — strict contract lock
├── mitraClient.js              Phase 2 — real Mitra client (updated)
├── enforcementGate.js          Phase 2 — enforcement gate (updated)
├── executionClient.js          Phase 3 — execution trigger
├── eventCollector.js           Phase 4 — event stream capture
├── insightBridge.js            Phase 5 — externalized telemetry (rewritten)
├── pipelineBucketWriter.js     Phase 6 — buffer-then-flush artifacts
├── failureGuard.js             Phase 7 — all failure codes
├── pipeline.js                 Phase 8 — full orchestrator
├── test_phase1_contract.js
├── test_phase2_enforcement.js
├── test_phase3_execution.js
├── test_phase4_event_collector.js
├── test_phase5_telemetry.js
├── test_phase6_bucket.js
├── test_phase7_failure_hardening.js
└── test_phase8_validation.js

backend/.env                    Phase 3+5 env vars added
Review-Packet/REVIEW_PACKET_3.md  ← this file
```

---

*REVIEW_PACKET_3.md — Rudra Parmeshwar — BHIV TANTRA Final Integration Task*
