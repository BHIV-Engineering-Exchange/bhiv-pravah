# Phase 8 — BHIV Testing Protocol
## TANTRA Ecosystem — Reproducible Validation Package

**Target:** 5–10 minute end-to-end validation  
**Systems Under Test:** Rudra (Real-Time Micro-Bridge) + TANTRA spine  
**Tester:** Run from `d:\Internship Task\Real-Time Micro-Bridge\backend`

---

## SETUP INSTRUCTIONS (2 minutes)

### Prerequisites
- Node.js v18+
- Python 3.10+
- All services from prior phases

### Step 1 — Start all services (separate terminals)

**Terminal A — Mitra (port 8000):**
```bash
cd "d:\Internship Task\Mitra\ai-assistant-backend"
venv_mitra\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Wait for: `Application startup complete`

**Terminal B — Atharva TTG (port 8080):**
```bash
cd "d:\Internship Task\ttg (1)\ttg"
uvicorn server:app --host 0.0.0.0 --port 8080
```
Wait for: `Uvicorn running on http://0.0.0.0:8080`

**Terminal C — Atharva browser renderer (port 8082):**
```bash
cd "d:\Internship Task\ttg (1)\ttg"
python -m http.server 8082
```
Open `http://localhost:8082` in browser.

**Terminal D — Rudra backend (port 3000):**
```bash
cd "d:\Internship Task\Real-Time Micro-Bridge\backend"
node index.js
```
Wait for: `server running at PORT : 3000`

**Terminal E — Rudra frontend (port 5173):**
```bash
cd "d:\Internship Task\Real-Time Micro-Bridge\frontend"
npm run dev
```
Open `http://localhost:5173` in browser.

### Step 2 — Verify all services healthy
```bash
cd "d:\Internship Task\Real-Time Micro-Bridge\backend"
curl http://localhost:3000/core/atharva-health
```
**Expected:**
```json
{
  "atharva": { "status": "ok" },
  "mitra":   { "status": "ok" },
  "prompt_runner": { "status": "healthy", "groq_available": true }
}
```

---

## EXECUTION STEPS (5–8 minutes)

Run each test script in Terminal D in order:

### Test 1 — Phase 1: Atharva Live Convergence
```bash
node test_phase1_atharva_real.js
```
**Time:** ~10 seconds

### Test 2 — Phase 3: SVACS End-to-End Proof
```bash
node test_phase3_svacs_e2e.js
```
**Time:** ~5 seconds

### Test 3 — Phase 4: Namami Gange Convergence
```bash
node test_phase4_namami_gange_e2e.js
```
**Time:** ~5 seconds

### Test 4 — Phase 5: NICAI + UICICS Compatibility
```bash
node test_phase5_nicai_uicics.js
```
**Time:** ~5 seconds

### Test 5 — Phase 6: Truth Layer Validation
```bash
node test_phase6_truth_layer.js
```
**Time:** ~3 seconds

### Test 6 — Phase 7: Ecosystem Demo (watch Samrachna panel)
```bash
node test_phase7_ecosystem_demo.js
```
**Time:** ~15 seconds (includes 800ms delays between systems)

---

## EXPECTED OUTPUTS

### Test 1 — Phase 1
```
✓ PHASE 1 LIVE CONVERGENCE PROOF: CONFIRMED
  trace_id         : tantra-p1-XXXXXXXXX
  contract accepted: ✓ YES
  game started     : ✓ YES
  trace intact     : ✓ YES
  status           : PROOF_CONFIRMED
```

### Test 2 — Phase 3
```
✓ upstream_trace_ownership         CONFIRMED
✓ contract_enforcement             PASSED
✓ execution_participation          CONFIRMED
✓ truth_persistence                LOCAL_ONLY
✓ visualization_continuity         ATHARVA_RENDERING
✓ PHASE 3 SVACS END-TO-END PROOF: CONFIRMED
```

### Test 3 — Phase 4
```
✓ Varanasi     BOD    risk=LOW    → Mitra(ALLOW) Atharva(runner)
✓ Patna        SILT   risk=MEDIUM → Mitra(ALLOW) Atharva(sidescroller)
✓ Kolkata      FLOW_RATE risk=HIGH → Mitra(ALLOW) Atharva(arena)
  domain_portability   : ✓ CONFIRMED
  core_spine_unchanged : ✓ CONFIRMED
✓ PHASE 4 NAMAMI GANGE CONVERGENCE PROOF: CONFIRMED
```

### Test 4 — Phase 5
```
  NICAI    ✓ CONFIRMED   ✓ CONFIRMED   ✓ CONFIRMED   2/2
  UICICS   ✓ CONFIRMED   ✓ CONFIRMED   ✓ CONFIRMED   3/3
  plug_and_play_model : ✓ CONFIRMED
✓ PHASE 5 NICAI + UICICS COMPATIBILITY PROOF: CONFIRMED
```

### Test 5 — Phase 6
```
✓ trace_continuity_into_truth_layer   CONFIRMED
✓ replay_survives_restart             CONFIRMED
✓ append_only_integrity_preserved     CONFIRMED
✓ ecosystem_traces_recoverable        CONFIRMED
  total artifacts    : 429+
  unique trace IDs   : 100+
✓ PHASE 6 TRUTH LAYER VALIDATION: CONFIRMED
```

### Test 6 — Phase 7
```
✓ SVACS            1/1 contracts
✓ NamamiGange      2/2 contracts
✓ NICAI            2/2 contracts
✓ UICICS           2/2 contracts
  system_switchability : ✓ CONFIRMED
  one_tantra_spine     : ✓ CONFIRMED
  multiple_domains     : ✓ CONFIRMED
✓ PHASE 7 ECOSYSTEM DEMO: CONFIRMED
```

---

## FAILURE EXPECTATIONS

| Failure | Cause | Fix |
|---|---|---|
| `Cannot reach Rudra` | Backend not running | `node index.js` in backend dir |
| `Atharva timeout` | Atharva server not running | `uvicorn server:app --port 8080` |
| `Mitra unreachable` | Mitra not running on 8000 | Start Mitra, or ignore — defaults to ALLOW |
| `HTTP 404` on /nicai or /uicics | Old backend process running without new routes | Kill old process, restart `node index.js` |
| `EADDRINUSE :3000` | Old backend still running | Kill PID using port 3000 first |
| Phase 1 `game_start timeout` | Atharva browser tab not open | Open `http://localhost:8082` |
| Phase 3 `Invalid trace_id format` | trace_id doesn't start with `trace_` | Use real SVACS output or fallback contract |
| Phase 6 `0 artifacts` | Wrong working directory | Run from `backend/` directory |
| Phase 7 timeout on SVACS/NamamiGange | Live bucket slow | Timeout already set to 35s — wait |

---

## REPLAY VALIDATION STEPS

### Verify artifacts survive restart

1. Stop the backend (`Ctrl+C`)
2. Run:
```bash
node test_phase6_truth_layer.js
```
3. **Expected:** Same artifact count reported — proves replay survives restart

### Replay a specific trace

```bash
curl http://localhost:3000/svacs/proofs
```
Note a `trace_id` from the response, then:
```bash
curl http://localhost:3000/phase5/proofs
curl http://localhost:3000/namami-gange/proofs
```
All should return their respective proof artifacts — proves ecosystem traces are recoverable.

---

## TRACE VERIFICATION STEPS

### Verify trace_id continuity through the chain

**Step 1 — Fire a SVACS contract:**
```bash
curl -X POST http://localhost:3000/svacs/inbound \
  -H "Content-Type: application/json" \
  -d "{\"trace_id\":\"trace_verify_001\",\"execution_id\":\"exec_verify_001\",\"risk_level\":\"LOW\",\"pipeline_stages\":[\"SIGNAL\",\"CORE\"]}"
```

**Step 2 — Verify trace_id in response:**
```json
{ "trace_id": "trace_verify_001", "upstream_trace_ownership": "CONFIRMED" }
```

**Step 3 — Verify proof artifact written:**
```bash
dir bucket_artifacts\svacs_phase3_trace_verify_001_proof.json
```

**Step 4 — Verify trace_id inside artifact:**
```bash
node -e "const f=require('./bucket_artifacts/svacs_phase3_trace_verify_001_proof.json'); console.log(f.trace_id, f.upstream_trace_ownership)"
```
**Expected:** `trace_verify_001 CONFIRMED`

---

## QUICK HEALTH CHECK (30 seconds)

```bash
curl http://localhost:3000/health
curl http://localhost:3000/svacs/health
curl http://localhost:3000/namami-gange/health
curl http://localhost:3000/phase5/matrix
curl http://localhost:3000/core/atharva-health
```

All should return `200 OK` with status fields.

---

## PROOF ARTIFACTS LOCATION

All proof artifacts written to:
```
d:\Internship Task\Real-Time Micro-Bridge\backend\bucket_artifacts\
```

Key files:
| File Pattern | Phase |
|---|---|
| `phase1_atharva_*_proof.json` | Phase 1 |
| `phase3_svacs_proof_*.json` | Phase 3 |
| `phase4_namami_gange_proof_*.json` | Phase 4 |
| `phase5_compatibility_proof_*.json` | Phase 5 |
| `phase6_truth_chain_evidence_*.json` | Phase 6 |
| `phase7_ecosystem_demo_*.json` | Phase 7 |

---

## PASS CRITERIA

| Test | Pass Condition |
|---|---|
| Phase 1 | `status: PROOF_CONFIRMED` |
| Phase 3 | All 5 validations `CONFIRMED` |
| Phase 4 | `contracts_passed: 3/3` |
| Phase 5 | `total_passed: 5/5` |
| Phase 6 | All 4 validations `CONFIRMED`, 400+ artifacts intact |
| Phase 7 | `contracts_passed: 7/7`, `system_switchability: CONFIRMED` |
