# CORRUPTION INJECTION PROOF — KESHAV

**Status:** Operational Freeze Preparation  
**Last Updated:** 2025-01-XX  
**Authority:** Pritesh (Architect) → Rajaryan Verma (Incoming Steward)

---

## 1. Executive Summary

KESHAV guarantees **fail-closed corruption resistance**:
- ✅ Malformed payloads rejected
- ✅ Trace mutation attempts rejected
- ✅ Schema corruption rejected
- ✅ No silent repair
- ✅ No partial truth persistence
- ✅ Visible rejection reasoning
- ✅ Deterministic rejection signatures

---

## 2. Corruption Injection Scope

### Attack Vectors Tested
1. Missing `trace_id`
2. Missing `execution_id`
3. Wrong type `trace_id` (non-string)
4. Wrong type `execution_id` (non-string)
5. Non-dict input
6. Malformed `tasks` (non-list)
7. Malformed `constraint_results` (non-list)
8. Malformed `propagation_results` (non-list)
9. Trace mutation (changing `trace_id` mid-pipeline)
10. Downstream schema corruption (Sarathi failure)
11. Partial execution interruption (Core failure)
12. Bucket write inconsistency (write-on-success violation)

---

## 3. Corruption Test 1 — Missing trace_id

### Test: `test_failure_missing_trace_id_fail_closed`

**Input:**
```json
{
  "execution_id": "exec-no-trace"
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution
- ❌ No Bucket write
- ✅ InsightFlow FAILURE event

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": ""
}
```

**Downstream State:**
- `rajya_output`: None
- `sarathi_output`: None
- `core_output`: None
- Bucket entries: 0
- InsightFlow events: 1 FAILURE event

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed, no partial execution**

---

## 4. Corruption Test 2 — Missing execution_id

### Test: `test_validation_missing_execution_id`

**Input:**
```json
{
  "trace_id": "trace-no-exec"
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution
- ❌ No Bucket write
- ✅ InsightFlow FAILURE event

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": "trace-no-exec"
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 5. Corruption Test 3 — Wrong Type trace_id

### Test: `test_validation_trace_id_wrong_type`

**Input:**
```json
{
  "trace_id": 12345,
  "execution_id": "exec-001"
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": ""
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 6. Corruption Test 4 — Wrong Type execution_id

### Test: `test_validation_execution_id_wrong_type`

**Input:**
```json
{
  "trace_id": "trace-001",
  "execution_id": 12345
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": "trace-001"
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 7. Corruption Test 5 — Non-Dict Input

### Test: `test_failure_invalid_schema_fail_closed`

**Input:**
```python
"not-a-dict"
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution
- ❌ No Bucket write
- ✅ InsightFlow FAILURE event

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": ""
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 8. Corruption Test 6 — Malformed tasks (Non-List)

### Test: `test_validation_tasks_not_list`

**Input:**
```json
{
  "trace_id": "trace-001",
  "execution_id": "exec-001",
  "tasks": "not-a-list"
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": "trace-001"
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 9. Corruption Test 7 — Malformed constraint_results (Non-List)

### Test: `test_validation_constraint_results_not_list`

**Input:**
```json
{
  "trace_id": "trace-001",
  "execution_id": "exec-001",
  "tasks": [],
  "constraint_results": "not-a-list"
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": "trace-001"
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 10. Corruption Test 8 — Malformed propagation_results (Non-List)

### Test: `test_validation_propagation_results_not_list`

**Input:**
```json
{
  "trace_id": "trace-001",
  "execution_id": "exec-001",
  "tasks": [],
  "constraint_results": [],
  "propagation_results": "not-a-list"
}
```

**Expected Behavior:**
- ❌ Fail closed
- ❌ No downstream execution

**Result:**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": "trace-001"
}
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — Fail closed**

---

## 11. Corruption Test 9 — Trace Mutation Attempt

### Test: `test_pipeline_rajya_trace_mismatch_is_fail_closed`

**Scenario:** RAJYA output has different `trace_id` than KESHAV output

**Method:**
1. Inject trace mutation in RAJYA layer
2. Assert pipeline fails closed
3. Assert no Bucket write

**Result:**
```json
{
  "status": "FAIL",
  "reason": "RAJYA_TRACE_MISMATCH"
}
```

**Downstream State:**
- `sarathi_output`: None
- `core_output`: None
- Bucket entries: 0

**Rejection Signature:** `RAJYA_TRACE_MISMATCH`

**Result:** ✅ **PASS — Trace mutation rejected**

---

## 12. Corruption Test 10 — Downstream Schema Corruption (Sarathi Failure)

### Test: `test_pipeline_sarathi_failure_is_fail_closed`

**Scenario:** Sarathi raises exception during enforcement

**Method:**
1. Inject Sarathi failure (raise exception)
2. Assert pipeline fails closed
3. Assert no Bucket write
4. Assert InsightFlow emits FAILURE event

**Result:**
```json
{
  "status": "FAIL",
  "reason": "SARATHI_FAILURE"
}
```

**Downstream State:**
- `core_output`: None
- Bucket entries: 0
- InsightFlow events: 1 FAILURE event

**Rejection Signature:** `SARATHI_FAILURE`

**Result:** ✅ **PASS — Sarathi failure is fail-closed**

---

## 13. Corruption Test 11 — Partial Execution Interruption (Core Failure)

### Test: `test_pipeline_core_failure_is_fail_closed`

**Scenario:** Core raises exception during execution

**Method:**
1. Inject Core failure (raise exception)
2. Assert pipeline fails closed
3. Assert no Bucket write
4. Assert InsightFlow emits FAILURE event

**Result:**
```json
{
  "status": "FAIL",
  "reason": "CORE_FAILURE"
}
```

**Downstream State:**
- Bucket entries: 0
- InsightFlow events: 1 FAILURE event

**Rejection Signature:** `CORE_FAILURE`

**Result:** ✅ **PASS — Core failure is fail-closed**

---

## 14. Corruption Test 12 — Bucket Write Inconsistency

### Test: `test_failed_runs_not_in_bucket`

**Scenario:** Failed runs must NOT be written to Bucket

**Method:**
1. Run TANTRA pipeline with invalid input (missing `trace_id`)
2. Assert pipeline fails closed
3. Assert Bucket has 0 entries

**Result:**
```python
assert bucket.read("trace-missing") is None
```

**Rejection Signature:** `INVALID_INPUT_CONTRACT`

**Result:** ✅ **PASS — No partial truth persistence**

---

## 15. Corruption Injection Summary

| Corruption Type | Test | Rejection Signature | Result |
|-----------------|------|---------------------|--------|
| Missing `trace_id` | `test_failure_missing_trace_id_fail_closed` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Missing `execution_id` | `test_validation_missing_execution_id` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Wrong type `trace_id` | `test_validation_trace_id_wrong_type` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Wrong type `execution_id` | `test_validation_execution_id_wrong_type` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Non-dict input | `test_failure_invalid_schema_fail_closed` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Malformed `tasks` | `test_validation_tasks_not_list` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Malformed `constraint_results` | `test_validation_constraint_results_not_list` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Malformed `propagation_results` | `test_validation_propagation_results_not_list` | `INVALID_INPUT_CONTRACT` | ✅ PASS |
| Trace mutation | `test_pipeline_rajya_trace_mismatch_is_fail_closed` | `RAJYA_TRACE_MISMATCH` | ✅ PASS |
| Sarathi failure | `test_pipeline_sarathi_failure_is_fail_closed` | `SARATHI_FAILURE` | ✅ PASS |
| Core failure | `test_pipeline_core_failure_is_fail_closed` | `CORE_FAILURE` | ✅ PASS |
| Bucket write inconsistency | `test_failed_runs_not_in_bucket` | `INVALID_INPUT_CONTRACT` | ✅ PASS |

**Total:** ✅ **12/12 corruption tests passing**

---

## 16. Deterministic Rejection Proof

### Same Corruption → Same Rejection

**Method:**
1. Run corrupted input 10 times
2. Assert all 10 rejections are identical

**Test:** `test_deterministic_rejection`

**Input (Run 1-10):**
```json
{
  "execution_id": "exec-no-trace"
}
```

**Output (Run 1-10):**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": ""
}
```

**Result:** ✅ **10/10 identical rejections**

---

## 17. Visible Rejection Reasoning

All rejections emit:
- **Status:** `FAIL`
- **Reason:** Structured rejection signature
- **Trace ID:** Passthrough (or empty if missing)

### InsightFlow Failure Events

**Test:** `test_failures_visible_in_insightflow`

**Method:**
1. Run 3 corrupted inputs
2. Assert InsightFlow emits 3 FAILURE events

**InsightFlow Events:**
```json
[
  {"type": "FAILURE", "trace_id": "", "reason": "INVALID_INPUT_CONTRACT"},
  {"type": "FAILURE", "trace_id": "", "reason": "INVALID_INPUT_CONTRACT"},
  {"type": "FAILURE", "trace_id": "", "reason": "INVALID_INPUT_CONTRACT"}
]
```

**Result:** ✅ **3/3 FAILURE events visible**

---

## 18. No Silent Repair

KESHAV **DOES NOT**:
- Auto-correct malformed input
- Generate missing `trace_id`
- Coerce wrong types
- Substitute default values
- Retry failed operations

**All corruption is rejected immediately.**

---

## 19. Operational Stewardship Expectations

Rajaryan Verma (incoming maintainer) must:
- **Reject** any PR that introduces silent repair
- **Reject** any PR that allows partial execution on failure
- **Reject** any PR that bypasses fail-closed validation
- **Monitor** for corruption injection attempts in production
- **Validate** rejection signatures remain deterministic

---

## 20. Convergence Freeze Status

**KESHAV corruption resistance is proven.**

All corruption injection tests pass:
- ✅ Fail closed
- ✅ No silent repair
- ✅ No partial truth persistence
- ✅ Visible rejection reasoning
- ✅ Deterministic rejection signatures

**Status:** READY FOR OPERATIONAL HANDOVER
