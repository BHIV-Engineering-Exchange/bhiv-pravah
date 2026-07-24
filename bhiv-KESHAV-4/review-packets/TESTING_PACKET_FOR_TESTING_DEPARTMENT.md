# TESTING PACKET FOR TESTING DEPARTMENT
## Phase 9 — Functional Verification

**Service Under Test:** KESHAV-4 Propagation Engine
**Canonical Owner:** Rajaryan
**Date:** 2026-05-26
**Estimated Testing Time:** 5-10 minutes

This document provides exact, copy-pasteable commands for a Black-Box QA Tester to verify the core functionality of KESHAV-4.

---

### Step 1: Health Check Verification (1 minute)

**Action:** Run the health check script.
```bash
python c:\blackhole\KESHAV-4\app\health.py
```

**Expected Output:**
A JSON dictionary with status "healthy" and three internal checks passing.
```json
{
  "status": "healthy",
  "service": "KESHAV-4-PropagationEngine",
  "checks": {
    "schema_import": "ok",
    "engine_computation": "ok",
    "latency_bound": "ok"
  },
  "elapsed_ms": <less than 500>
}
```

---

### Step 2: Automated Verification (3 minutes)

**Action:** Run the full integration and replay test suite.
```bash
pytest c:\blackhole\KESHAV-4\shared_tests\ -v --tb=short
```

**Expected Output:**
Exactly 38 tests should run. All 38 tests MUST pass (`PASSED`).
```text
============================= test session starts =============================
...
============================= 38 passed in XX.XXs =============================
```

---

### Step 3: Interactive Python Verification (3 minutes)

**Action:** Open an interactive Python shell and manually verify the engine.

1. Open python:
```bash
python
```

2. Paste the following block:
```python
import sys
sys.path.insert(0, r"c:\blackhole\KESHAV-4")
from app.engine import PropagationEngine

input_payload = {
    "blocked_task_id": "NODE_A",
    "root_cause": "RC_1",
    "trace_id": "qa-test-trace-001",
    "timestamp": "2026-05-26T12:00:00Z",
    "dependency_graph": {
        "RC_1": ["NODE_A"],
        "NODE_A": ["NODE_B", "NODE_C"],
        "NODE_B": ["NODE_D"],
        "NODE_C": ["NODE_D"],
        "NODE_D": []
    }
}

# Run the engine
output = PropagationEngine.compute_dependency_output(input_payload)

# Verify
import json
print(json.dumps(output, indent=2))
```

**Expected Output:**
```json
{
  "blocked_task_id": "NODE_A",
  "root_cause": "RC_1",
  "impacted_tasks": [
    "NODE_B",
    "NODE_C",
    "NODE_D"
  ],
  "impact_score": 3,
  "severity": "MEDIUM",
  "resolution_signal": "UNBLOCK_DEPENDENCY:RC_1",
  "trace_id": "qa-test-trace-001",
  "timestamp": "2026-05-26T12:00:00Z"
}
```

---

### Step 4: Failure Mode Verification (2 minutes)

**Action:** In the same python shell, attempt to submit a corrupted payload.

Paste the following block:
```python
bad_payload = input_payload.copy()
bad_payload["extra_field_injected"] = "MALICIOUS"

try:
    PropagationEngine.compute_dependency_output(bad_payload)
    print("TEST FAILED - Engine accepted bad payload!")
except Exception as e:
    print(f"TEST PASSED - Engine rejected payload. Error: {e}")
```

**Expected Output:**
```text
TEST PASSED - Engine rejected payload. Error: SCHEMA_MISMATCH: Input validation failed: 1 validation error for PropagationInput...
```

---

**SIGN-OFF CRITERIA:**
If Steps 1 through 4 match the expected outputs exactly, KESHAV-4 is functionally verified and ready for production deployment.
