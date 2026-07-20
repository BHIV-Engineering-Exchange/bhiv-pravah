# DEMO_SCENARIOS.md
## Phase 5 — Demo Scenarios
**Project:** Real-Time Micro-Bridge / TANTRA Spine  
**Owner:** Rudra Parmeshwar  
**Generated:** 2026-06-13  
**Purpose:** Operator-runnable demo scenarios. No developer explanation required.

---

## Pre-Demo Checklist

Before running any scenario, verify the backend is running:

```bash
curl http://localhost:3000/health
```

Expected:
```json
{ "status": "ok", "uptime": 123.4, "timestamp": 1749799200000 }
```

Samrachna dashboard (optional, for live event visualization):
```
http://localhost:5173
```

Each scenario below is self-contained. Run them in any order. Every command produces a proof file in `backend/bucket_artifacts/`.

---

## Scenario 1 — NamamiGange Execution Path

### What This Proves
NamamiGange sends a marine sensor reading from waterway NW-1 at Varanasi. The TANTRA spine receives it, contacts Mitra for governance, attempts Atharva for rendering, writes a proof artifact, and emits a live event to Samrachna. The same spine then handles a higher-risk reading from Patna — producing a different game_mode — proving the mapping is dynamic, not hardcoded.

### Input

**Request 1 — Varanasi, LOW risk:**
```bash
curl -s -X POST http://localhost:3000/namami-gange/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id":     "ng_demo_varanasi_001",
    "execution_id": "ng_exec_varanasi_001",
    "waterway":     "NW-1",
    "location":     "Varanasi",
    "signal_type":  "BOD",
    "risk_level":   "LOW",
    "domain":       "marine",
    "sensor_data":  { "bod": 3.2, "do": 7.1, "flow_rate": 1200, "silt": 42 }
  }'
```

**Request 2 — Patna, MEDIUM risk:**
```bash
curl -s -X POST http://localhost:3000/namami-gange/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id":     "ng_demo_patna_001",
    "execution_id": "ng_exec_patna_001",
    "waterway":     "NW-1",
    "location":     "Patna",
    "signal_type":  "SILT",
    "risk_level":   "MEDIUM",
    "domain":       "marine",
    "sensor_data":  { "bod": 5.8, "do": 5.4, "flow_rate": 980, "silt": 78 }
  }'
```

### Execution

The backend route `POST /namami-gange/inbound` in `namamiGangeRoute.js`:
1. Validates `trace_id` and `execution_id` are present
2. Maps `risk_level` → `game_mode`: LOW→runner, MEDIUM→sidescroller, HIGH→arena
3. Contacts Mitra at `localhost:8000/api/mitra/evaluate` with category `marine_waterway`
4. Contacts Atharva at `localhost:8080/execute` with `game_mode`, `waterway`, `location`
5. Writes proof file to `backend/bucket_artifacts/`
6. Calls `emitToSamrachna()` → `io.emit('samrachna:event', {...})`

### Trace

| Field | Varanasi | Patna |
|---|---|---|
| trace_id | `ng_demo_varanasi_001` | `ng_demo_patna_001` |
| execution_id | `ng_exec_varanasi_001` | `ng_exec_patna_001` |
| Mitra receives | `session_id: "ng_demo_varanasi_001"` | `session_id: "ng_demo_patna_001"` |
| Atharva receives | `trace_id: "ng_demo_varanasi_001"` | `trace_id: "ng_demo_patna_001"` |
| Proof file | `namami_gange_phase4_ng_demo_varanasi_001_proof.json` | `namami_gange_phase4_ng_demo_patna_001_proof.json` |
| Samrachna event | `samrachna:event` with `trace_id`, `location: "Varanasi"` | `samrachna:event` with `location: "Patna"` |

### Expected Output

**Varanasi response (HTTP 200):**
```json
{
  "success": true,
  "phase": 4,
  "trace_id": "ng_demo_varanasi_001",
  "execution_id": "ng_exec_varanasi_001",
  "upstream_system": "NamamiGange",
  "domain": "marine",
  "domain_portability": "CONFIRMED",
  "core_spine_unchanged": true,
  "marine_compatibility": "CONFIRMED",
  "mitra_decision": "ALLOW",
  "game_mode": "runner",
  "waterway": "NW-1",
  "location": "Varanasi",
  "truth_persistence": "LOCAL_ONLY",
  "elapsed_ms": "<250ms typical>"
}
```

**Patna response (HTTP 200) — note game_mode change:**
```json
{
  "mitra_decision": "ALLOW",
  "game_mode": "sidescroller",
  "location": "Patna",
  "domain_portability": "CONFIRMED"
}
```

`game_mode` changed from `runner` to `sidescroller` because `risk_level` changed from LOW to MEDIUM. This is the dynamic mapping proof.

**Verify proof files exist:**
```bash
curl http://localhost:3000/namami-gange/proofs
```
Expected: `count >= 2`, both trace IDs visible in the list.

**Existing proof on disk (from prior run):**  
File: `namami_gange_phase4_ng_mq1y96oq_varanasi_proof.json`
```json
{
  "upstream_system": "NamamiGange",
  "trace_id": "ng_mq1y96oq_varanasi",
  "status": "EXECUTION_COMPLETE",
  "marine_compatibility": "CONFIRMED",
  "elapsed_ms": 258,
  "timestamp": "2026-06-06T06:05:52.610Z"
}
```

### Replay

NamamiGange produces a single proof JSON per execution (not the 5-artifact maritime format). Replay of this proof means reading the file and confirming its fields match the HTTP response.

```bash
# Confirm proof file was written
ls backend/bucket_artifacts/namami_gange_phase4_ng_demo_varanasi_001_proof.json

# Read it back
cat backend/bucket_artifacts/namami_gange_phase4_ng_demo_varanasi_001_proof.json
```

Expected: `status: "EXECUTION_COMPLETE"`, `trace_id: "ng_demo_varanasi_001"`, `marine_compatibility: "CONFIRMED"`.

For the maritime pipeline replay (full 5-artifact replay engine):
```bash
# Maritime format traces can be replayed via the engine
curl -s -X POST http://localhost:3000/pipeline/replay/maritime_c9e761c9-2f30-4d29-9e00-5875ae6c6f0c
```

### Operator Narrative

> "NamamiGange monitors waterway NW-1. When sensor data arrives from Varanasi — BOD reading at 3.2, flow rate 1200 — it sends an execution contract to the TANTRA spine. Mitra evaluates it: risk is LOW, decision is ALLOW. The spine maps LOW risk to runner game mode and forwards to Atharva. A proof file is written locally. Samrachna shows a live event: upstream system NamamiGange, location Varanasi, mitra decision ALLOW.
>
> Now a second reading arrives from Patna. Silt level 78 — risk is MEDIUM. The same spine runs again. Mitra evaluates, ALLOW. But this time game_mode is sidescroller — not runner. The risk level drove a different mapping. No code change. Same spine, different domain signal, different output. That is what domain portability confirmed means.
>
> Both proof files are on disk. Call GET /namami-gange/proofs to see them listed."

---

## Scenario 2 — SVACS Execution Path

### What This Proves
SVACS sends a signal intelligence contract after completing its 7-stage internal pipeline. The TANTRA spine validates the trace format, routes through Mitra, forwards to Atharva, and writes a proof artifact with `upstream_trace_ownership: CONFIRMED` and `contract_enforcement: PASSED`. One existing proof shows `visualization_continuity: ATHARVA_RENDERING` — proving Atharva was live and accepted the execution.

### Input

```bash
curl -s -X POST http://localhost:3000/svacs/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id":         "trace_demo_svacs_001",
    "execution_id":     "exec_demo_svacs_001",
    "risk_level":       "LOW",
    "contract_version": "v1.0",
    "pipeline_stages":  ["SIGNAL","PERCEPTION","INTELLIGENCE","STATE","RAJYA","SARATHI","CORE"],
    "intelligence_event": {
      "risk_level":      "LOW",
      "risk_score":      0.14,
      "analysis":        "Vessel pattern nominal",
      "recommendation":  "MONITOR"
    },
    "signal_chunk": {
      "vessel_type":     "cargo",
      "signal_type":     "VESSEL_ALERT",
      "signal_strength": "LOW"
    }
  }'
```

**Format validation test** — send a bad trace_id to prove validation fires:
```bash
curl -s -X POST http://localhost:3000/svacs/inbound \
  -H "Content-Type: application/json" \
  -d '{ "trace_id": "bad_id", "execution_id": "exec_001", "risk_level": "LOW" }'
```

Expected: HTTP 400, `error: "Invalid trace_id format: \"bad_id\" — SVACS trace_id must start with \"trace_\""`.

### Execution

The backend route `POST /svacs/inbound` in `svacsRoute.js`:
1. Validates `trace_id.startsWith('trace_')` — rejects with 400 otherwise
2. Validates `execution_id.startsWith('exec_')` — rejects with 400 otherwise
3. Maps `risk_level` → `game_mode`
4. Contacts Mitra with category `maritime_intelligence`
5. Contacts Atharva with `signal_source: signal_chunk.vessel_type`
6. Contacts Bucket at `bhiv-bucket.onrender.com`
7. Writes proof file
8. Calls `emitToSamrachna()`

### Trace

| Field | Value |
|---|---|
| trace_id | `trace_demo_svacs_001` |
| execution_id | `exec_demo_svacs_001` |
| Mitra receives | `content: "trace_id=trace_demo_svacs_001 risk_level=LOW execution_id=exec_demo_svacs_001"` |
| Atharva receives | `trace_id: "trace_demo_svacs_001"`, `parameters.upstream_system: "SVACS"` |
| Proof file | `svacs_phase3_trace_demo_svacs_001_proof.json` |
| Samrachna event | `samrachna:event` with `upstream_system: "SVACS"`, `trace_id`, `mitra_decision` |

### Expected Output

**HTTP 200 response:**
```json
{
  "success": true,
  "phase": 3,
  "trace_id": "trace_demo_svacs_001",
  "execution_id": "exec_demo_svacs_001",
  "upstream_system": "SVACS",
  "upstream_trace_ownership": "CONFIRMED",
  "contract_enforcement": "PASSED",
  "execution_participation": "CONFIRMED",
  "mitra_decision": "ALLOW",
  "game_mode": "runner",
  "truth_persistence": "LOCAL_ONLY",
  "message": "Phase 3 path: SVACS → Mitra(ALLOW) → Atharva(runner) → Bucket(local)"
}
```

**Existing proof showing Atharva ONLINE** (from prior run):  
File: `svacs_phase3_trace_verify_mq1xk3f7_proof.json`
```json
{
  "trace_id": "trace_verify_mq1xk3f7",
  "execution_id": "exec_verify_mq1xk3f7",
  "stages": {
    "atharva": {
      "status": 200,
      "accepted": true,
      "response": { "status": "accepted", "trace_id": "trace_verify_mq1xk3f7" },
      "trace_preserved": true
    }
  },
  "visualization_continuity": "ATHARVA_RENDERING",
  "elapsed_ms": 251,
  "timestamp": "2026-06-06T05:46:21.916Z"
}
```

This is the proof that when Atharva is running, `atharva_accepted: true` and `visualization_continuity: "ATHARVA_RENDERING"` — the trace was preserved through Atharva's acceptance response.

**List all SVACS proofs:**
```bash
curl http://localhost:3000/svacs/proofs
```

### Replay

```bash
# Read the proof file written during this run
cat backend/bucket_artifacts/svacs_phase3_trace_demo_svacs_001_proof.json

# Confirm trace_id matches what was sent
# Confirm execution_participation: "CONFIRMED"
# Confirm contract_enforcement: "PASSED"
```

### Operator Narrative

> "SVACS completes its 7-stage pipeline internally: SIGNAL → PERCEPTION → INTELLIGENCE → STATE → RAJYA → SARATHI → CORE. At the end, it sends a contract to the TANTRA spine. The trace ID must start with 'trace_' — if it doesn't, the spine rejects it with HTTP 400. That's contract enforcement.
>
> When the contract arrives, Mitra is contacted. Category: maritime intelligence. Decision: ALLOW, risk LOW. The spine maps LOW to runner game mode and sends to Atharva. A proof file is written. Samrachna shows: SVACS, ALLOW, runner, EXECUTION_COMPLETE.
>
> Look at the proof file for trace_verify_mq1xk3f7. This run had Atharva online. The stages section shows atharva.accepted: true, atharva.response.trace_id matches the original trace_id. visualization_continuity is ATHARVA_RENDERING. That means Atharva received this execution and confirmed the trace. That is what real system participation looks like."

---

## Scenario 3 — NICAI Execution Path

### What This Proves
NICAI submits two intelligence missions — a border patrol at low threat and a threat assessment at high threat. The spine maps threat level to risk level and then to game mode: low→runner, high→arena. Both produce proof artifacts with `structured_contract_participation: CONFIRMED`, `trace_continuity: CONFIRMED`, `deterministic_stream_compatibility: CONFIRMED`. The `GET /phase5/matrix` endpoint returns the cumulative proof count across all NICAI runs.

### Input

**Mission 1 — border_patrol, low threat:**
```bash
curl -s -X POST http://localhost:3000/nicai/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id":     "nicai_demo_patrol_001",
    "execution_id": "nicai_exec_patrol_001",
    "mission":      "border_patrol",
    "threat_level": "low",
    "domain":       "intelligence",
    "agents": [
      { "id": "agent_alpha", "role": "observer",  "position": [0,0,0] },
      { "id": "agent_beta",  "role": "tracker",   "position": [10,0,0] },
      { "id": "agent_gamma", "role": "sentinel",  "position": [5,0,5] }
    ]
  }'
```

**Mission 2 — threat_assessment, high threat:**
```bash
curl -s -X POST http://localhost:3000/nicai/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id":     "nicai_demo_threat_001",
    "execution_id": "nicai_exec_threat_001",
    "mission":      "threat_assessment",
    "threat_level": "high",
    "domain":       "intelligence",
    "agents": [
      { "id": "agent_delta", "role": "coordinator", "position": [0,0,0] }
    ]
  }'
```

### Execution

The backend route `POST /nicai/inbound` in `phase5Route.js`:
1. Receives mission contract with `mission`, `agents[]`, `threat_level`
2. Counts `agent_count` from the agents array
3. Maps `threat_level` → `risk_level` → `game_mode`
4. Calls `runSpine(trace_id, execution_id, 'NICAI', 'intelligence', risk_level, 'mission=border_patrol')`
5. Inside `runSpine`: contacts Mitra → contacts Atharva
6. Writes proof file `phase5_nicai_{trace_id}_proof.json`
7. Calls `emitToSamrachna()` with `upstream_system: 'NICAI'`

### Trace

| Field | Mission 1 | Mission 2 |
|---|---|---|
| trace_id | `nicai_demo_patrol_001` | `nicai_demo_threat_001` |
| execution_id | `nicai_exec_patrol_001` | `nicai_exec_threat_001` |
| threat_level | low | high |
| risk_level (mapped) | LOW | HIGH |
| game_mode (mapped) | runner | arena |
| Proof file | `phase5_nicai_nicai_demo_patrol_001_proof.json` | `phase5_nicai_nicai_demo_threat_001_proof.json` |
| Samrachna event | `upstream_system: "NICAI"`, `mission: "border_patrol"` | `upstream_system: "NICAI"`, `mission: "threat_assessment"` |

### Expected Output

**Mission 1 response (HTTP 200):**
```json
{
  "success": true,
  "phase": 5,
  "system": "NICAI",
  "trace_id": "nicai_demo_patrol_001",
  "execution_id": "nicai_exec_patrol_001",
  "domain": "intelligence",
  "mission": "border_patrol",
  "agent_count": 3,
  "threat_level": "low",
  "structured_contract_participation": "CONFIRMED",
  "trace_continuity": "CONFIRMED",
  "deterministic_stream_compatibility": "CONFIRMED",
  "mitra_decision": "ALLOW",
  "game_mode": "runner",
  "status": "EXECUTION_COMPLETE"
}
```

**Mission 2 response — note game_mode is arena:**
```json
{
  "game_mode": "arena",
  "mission": "threat_assessment",
  "threat_level": "high",
  "structured_contract_participation": "CONFIRMED"
}
```

**Cumulative compatibility matrix:**
```bash
curl http://localhost:3000/phase5/matrix
```

Expected:
```json
{
  "NICAI": {
    "structured_contract_participation": "CONFIRMED",
    "trace_continuity": "CONFIRMED",
    "deterministic_stream_compatibility": "CONFIRMED",
    "proofs_count": 26
  }
}
```

**Existing proof on disk:**  
File: `phase5_nicai_nicai_mq1y97ts_patrol_proof.json`
```json
{
  "system": "NICAI",
  "trace_id": "nicai_mq1y97ts_patrol",
  "mission": "border_patrol",
  "agent_count": 3,
  "structured_contract_participation": "CONFIRMED",
  "trace_continuity": "CONFIRMED",
  "deterministic_stream_compatibility": "CONFIRMED",
  "mitra_decision": "ALLOW",
  "game_mode": "runner",
  "status": "EXECUTION_COMPLETE",
  "elapsed_ms": 5,
  "timestamp": "2026-06-06T06:05:54.076Z"
}
```

### Replay

```bash
# List all NICAI proof files
curl http://localhost:3000/phase5/proofs | python -m json.tool

# Read a specific proof
cat "backend/bucket_artifacts/phase5_nicai_nicai_demo_patrol_001_proof.json"
```

Confirm: `trace_id`, `mission`, `agent_count`, `structured_contract_participation: "CONFIRMED"` all match what was sent.

### Operator Narrative

> "NICAI runs intelligence missions. It sends each mission as a contract to the TANTRA spine. A border patrol mission comes in with 3 agents, threat level low. The spine receives it, maps low threat to LOW risk, LOW risk to runner game mode. Mitra evaluates the content — ALLOW. Atharva is called with game_mode runner. A proof file is written for this trace.
>
> Next a threat assessment mission comes in. One agent, threat level high. Same spine. But high maps to HIGH risk, HIGH risk to arena. Different game mode. Same execution path. Proof file is written.
>
> Call GET /phase5/matrix. It shows NICAI with structured_contract_participation: CONFIRMED, trace_continuity: CONFIRMED, deterministic_stream_compatibility: CONFIRMED — and a proofs_count that has just increased by 2 from this demo run.
>
> That count is built from real proof files in bucket_artifacts/. Every file was written by a real HTTP request. Nothing is simulated."

---

## Scenario 4 — Cross-System Execution Path

### What This Proves
All 4 systems fire sequentially through the same backend in one demo run. The same TANTRA spine handles SVACS (maritime intelligence), NamamiGange (marine waterway), NICAI (intelligence), and UICICS (compliance) without any architecture change between them. `phase7_ecosystem_demo_*.json` is written as a combined proof artifact showing 7/7 executions passed.

### Input — One Command

```bash
node backend/test_phase7_ecosystem_demo.js
```

This runs 7 contracts sequentially with 800ms delay between each (for visible Samrachna updates):
1. SVACS — `trace_demo7_svacs_[ts]`, risk LOW
2. NamamiGange / Varanasi — `ng_demo7_[ts]_varanasi`, BOD LOW
3. NamamiGange / Patna — `ng_demo7_[ts]_patna`, SILT MEDIUM
4. NICAI / border_patrol — `nicai_demo7_[ts]`, threat low
5. NICAI / threat_assessment — `nicai_demo7_[ts]_t`, threat high
6. UICICS / structured_validation — `uicics_demo7_[ts]`, risk LOW
7. UICICS / audit_trace — `uicics_demo7_[ts]_a`, risk HIGH

### Execution

Each contract hits a different endpoint on the same backend (`localhost:3000`):

```
SVACS       → POST /svacs/inbound
NamamiGange → POST /namami-gange/inbound  (×2 locations)
NICAI       → POST /nicai/inbound          (×2 missions)
UICICS      → POST /uicics/inbound         (×2 contract types)
```

The backend processes each through the same spine: Mitra governance → Atharva forwarding → proof write → Samrachna emit. No code path changes between systems.

### Trace — All 7 Executions

This table is taken directly from `phase7_ecosystem_demo_1780725963097.json` (generated 2026-06-06T06:06:03.098Z):

| # | System | trace_id | Mitra | game_mode | elapsed | pass |
|---|---|---|---|---|---|---|
| 1 | SVACS | `trace_demo7_svacs_mq1y98sw` | ALLOW | runner | 245ms | ✓ |
| 2 | NamamiGange (Varanasi) | `ng_demo7_mq1y98sw_varanasi` | ALLOW | runner | 252ms | ✓ |
| 3 | NamamiGange (Patna) | `ng_demo7_mq1y98sw_patna` | ALLOW | sidescroller | 245ms | ✓ |
| 4 | NICAI (border_patrol) | `nicai_demo7_mq1y98sw` | ALLOW | runner | 5ms | ✓ |
| 5 | NICAI (threat_assessment) | `nicai_demo7_mq1y98sw_t` | ALLOW | arena | 5ms | ✓ |
| 6 | UICICS (structured_validation) | `uicics_demo7_mq1y98sw` | ALLOW | runner | 5ms | ✓ |
| 7 | UICICS (audit_trace) | `uicics_demo7_mq1y98sw_a` | ALLOW | arena | 7ms | ✓ |

**7/7 passed. Generated at: 2026-06-06T06:06:03.098Z.**

### Expected Console Output

```
╔══════════════════════════════════════════════════════╗
║   PHASE 7 — ECOSYSTEM DEMO RUN (MANDATORY)          ║
╚══════════════════════════════════════════════════════╝

[DEMO] Open http://localhost:5173 — watch Samrachna panel for live events

[DEMO] 1/7 ▶ SVACS
[DEMO]      ✓ trace=trace_demo7_svacs_... Mitra(ALLOW) Atharva(runner) [Xms]
[DEMO] 2/7 ▶ NamamiGange / Varanasi
[DEMO]      ✓ trace=ng_demo7_..._varanasi Mitra(ALLOW) Atharva(runner) [Xms]
[DEMO] 3/7 ▶ NamamiGange / Patna
[DEMO]      ✓ trace=ng_demo7_..._patna    Mitra(ALLOW) Atharva(sidescroller) [Xms]
[DEMO] 4/7 ▶ NICAI / border_patrol
[DEMO]      ✓ trace=nicai_demo7_...       Mitra(ALLOW) Atharva(runner) [Xms]
[DEMO] 5/7 ▶ NICAI / threat_assessment
[DEMO]      ✓ trace=nicai_demo7_..._t     Mitra(ALLOW) Atharva(arena) [Xms]
[DEMO] 6/7 ▶ UICICS / structured_validation
[DEMO]      ✓ trace=uicics_demo7_...      Mitra(ALLOW) Atharva(runner) [Xms]
[DEMO] 7/7 ▶ UICICS / audit_trace
[DEMO]      ✓ trace=uicics_demo7_..._a    Mitra(ALLOW) Atharva(arena) [Xms]

╔══════════════════════════════════════════════════════╗
║              PHASE 7 DEMO RESULTS                   ║
╚══════════════════════════════════════════════════════╝

  ✓ SVACS             1/1 contracts
  ✓ NamamiGange       2/2 contracts
  ✓ NICAI             2/2 contracts
  ✓ UICICS            2/2 contracts

  system_switchability : ✓ CONFIRMED
  one_tantra_spine     : ✓ CONFIRMED
  multiple_domains     : ✓ CONFIRMED (maritime, marine, intelligence, compliance)
  contracts_passed     : 7/7

✓ PHASE 7 ECOSYSTEM DEMO: CONFIRMED
```

### Output — Proof Files Written

After this run, 7 new proof files appear in `backend/bucket_artifacts/`:

```
svacs_phase3_trace_demo7_svacs_[ts]_proof.json
namami_gange_phase4_ng_demo7_[ts]_varanasi_proof.json
namami_gange_phase4_ng_demo7_[ts]_patna_proof.json
phase5_nicai_nicai_demo7_[ts]_proof.json
phase5_nicai_nicai_demo7_[ts]_t_proof.json
phase5_uicics_uicics_demo7_[ts]_proof.json
phase5_uicics_uicics_demo7_[ts]_a_proof.json
```

Plus one combined proof:
```
phase7_ecosystem_demo_[timestamp].json
```

This combined file contains all 7 results with trace IDs, decisions, game modes, elapsed times, and pass status.

**Read the combined proof:**
```bash
cat backend/bucket_artifacts/phase7_ecosystem_demo_[timestamp].json
```

Or list all Phase 7 proofs:
```bash
ls backend/bucket_artifacts/phase7_ecosystem_demo_*.json
```

### Replay

```bash
# After the demo run, verify the combined proof file
node -e "
const fs = require('fs');
const files = fs.readdirSync('backend/bucket_artifacts').filter(f => f.startsWith('phase7_ecosystem_demo_'));
const latest = files.sort().reverse()[0];
const data = JSON.parse(fs.readFileSync('backend/bucket_artifacts/' + latest, 'utf8'));
console.log('traces_fired:', data.systems_fired);
console.log('passed:', data.passed, '/', data.total_runs);
console.log('system_switchability:', data.system_switchability);
console.log('generated_at:', data.generated_at);
"
```

Expected output:
```
traces_fired: [ 'SVACS', 'NamamiGange', 'NICAI', 'UICICS' ]
passed: 7 / 7
system_switchability: CONFIRMED
generated_at: 2026-06-13T...
```

For maritime-format replay (full artifact-driven replay engine):
```bash
# Replay a prior maritime execution
curl -s -X POST http://localhost:3000/pipeline/replay/p8-allow-test | python -m json.tool
```

Expected: `success: true`, `9/9` checks in the replay log, `decision: "ALLOW"`.

### Operator Narrative

> "This is the full ecosystem demo. Four systems. One spine. No architecture changes.
>
> SVACS sends maritime intelligence. NamamiGange sends Ganga waterway readings from two locations. NICAI sends two intelligence missions — one routine patrol, one high-threat assessment. UICICS sends a compliance validation and an audit trace.
>
> Every one of these goes through the same backend. Same Mitra call. Same Atharva forward. Same proof file write. Same Samrachna emit.
>
> Watch the Samrachna panel at localhost:5173. As each system fires, a new event appears: upstream_system, trace_id, mitra_decision, game_mode, status. Seven events in total. All live. All different trace IDs. All from real HTTP requests made 800 milliseconds apart.
>
> When it finishes, the console shows 7/7 passed, system_switchability: CONFIRMED. A phase7_ecosystem_demo file is written to bucket_artifacts with every result inside it. That file is the evidence.
>
> No developer explanation needed. The file is there. The trace IDs are in it. The timestamps are real. Open it."

---

## Quick Reference — All Endpoints Used

| Scenario | Method | Endpoint | Proof Location |
|---|---|---|---|
| NamamiGange | POST | `/namami-gange/inbound` | `namami_gange_phase4_{trace_id}_proof.json` |
| NamamiGange list | GET | `/namami-gange/proofs` | — |
| SVACS | POST | `/svacs/inbound` | `svacs_phase3_{trace_id}_proof.json` |
| SVACS list | GET | `/svacs/proofs` | — |
| NICAI | POST | `/nicai/inbound` | `phase5_nicai_{trace_id}_proof.json` |
| UICICS | POST | `/uicics/inbound` | `phase5_uicics_{trace_id}_proof.json` |
| Phase 5 matrix | GET | `/phase5/matrix` | — |
| Phase 5 proofs | GET | `/phase5/proofs` | — |
| Cross-system demo | node script | `test_phase7_ecosystem_demo.js` | `phase7_ecosystem_demo_{ts}.json` |
| Maritime replay | POST | `/pipeline/replay/{trace_id}` | console output + `REPLAY_RESULT.json` |
| Health | GET | `/health` | — |

## Quick Reference — Existing Proof Files (Already on Disk)

These can be shown to the reviewer without running any new commands:

| System | Proof File | Key Fields |
|---|---|---|
| SVACS (Atharva online) | `svacs_phase3_trace_verify_mq1xk3f7_proof.json` | `atharva.accepted: true`, `visualization_continuity: "ATHARVA_RENDERING"` |
| NamamiGange | `namami_gange_phase4_ng_mq1y96oq_varanasi_proof.json` | `marine_compatibility: "CONFIRMED"`, `elapsed_ms: 258` |
| NICAI | `phase5_nicai_nicai_mq1y97ts_patrol_proof.json` | `structured_contract_participation: "CONFIRMED"`, `agent_count: 3` |
| Cross-system | `phase7_ecosystem_demo_1780725963097.json` | `7/7 passed`, all 4 systems, `generated_at: 2026-06-06T06:06:03.098Z` |
| Maritime replay | `REPLAY_RESULT.json` | `2/2 traces fully matched`, `18/18 checks passed` |
