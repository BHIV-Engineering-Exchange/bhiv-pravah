# KESHAV-4 Testing Packet
**Target Audience:** QA & Testing Department
**Objective:** Complete Operational Validation of KESHAV-4 in under 10 minutes.

This document contains explicit, copy-paste instructions for a Tester to independently verify KESHAV's deterministic output, fail-closed boundaries, and API compliance. 

> [!IMPORTANT]  
> All tests must currently be executed from the validated canonical payload directory, as the root workspace integration is pending overwrite.

## Pre-requisites
Open your terminal and navigate to the canonical intake directory:
```powershell
cd c:\rajaryan\KESHAV-4\intake\Pritesh_transfer
```

---

## Step 1: Environment Setup (2 Minutes)
Initialize the Python environment and install the core dependencies.

```powershell
# Install the application and development dependencies
pip install -e ".[dev]"
```

---

## Step 2: Run the Comprehensive Test Suite (1 Minute)
Run the automated test suite to instantly verify 100% of the core graph traversal logic and constitutional boundaries.

```powershell
# Run all 123 tests
pytest tests/ -q --tb=short

# Verify code coverage (must be 100%)
pytest --cov=analyzer --cov=tantra tests/
```
**Expected Output:**
* You should see `123 passed` in under 1 second.
* The coverage report should output `TOTAL 100%`.

---

## Step 3: Start the KESHAV API Server (1 Minute)
Start the KESHAV Flask server to validate live HTTP interactions.

```powershell
# Start the server (leave this terminal running and open a new one for steps 4-6)
python api.py
```
**Expected Output:**                   
* `* Running on http://127.0.0.1:5000`

---

## Step 4: Liveness Health Check (1 Minute)
Verify the server is live and responsive.

```powershell
curl -X GET http://localhost:5000/health
```
**Expected Output:**
```json
{
  "service": "KESHAV",
  "status": "OK"
}
```

---

## Step 5: Valid TANTRA Payload Test (2 Minutes)
Send a valid, structurally correct payload with a blocked task to ensure KESHAV emits the correct TANTRA-compliant resolution signal.

```powershell
curl -X POST http://localhost:5000/analyze `
  -H "Content-Type: application/json" `
  -d @sample_input.json
```
**Expected Output:**
```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "root_cause": "T1",
  "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
  "impact_score": 10,
  "severity": "HIGH",
  "timestamp": "<Current UTC Time>"
}
```

---

## Step 6: Fail-Closed Corruption Test (2 Minutes)
Send a completely malformed payload (missing the mandatory `trace_id` and violating schema arrays) to verify KESHAV's strict fail-closed boundary prevents propagation.

```powershell
curl -X POST http://localhost:5000/analyze `
  -H "Content-Type: application/json" `
  -d '{"execution_id": "bad-exec-001", "tasks": []}'
```
**Expected Output:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": ""
}
```

---

## Sign-off & Final Verdict
If all 6 steps produce the exact **Expected Output** listed above, the KESHAV-4 subsystem is fully validated and operationally sound. No further internal unit testing of the BFS graph algorithms or layer isolation is required.