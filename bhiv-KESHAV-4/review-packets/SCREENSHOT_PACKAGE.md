# SCREENSHOT PACKAGE
*(Textual Terminal Output Logs)*

## 1. Environment Setup & Execution
```text
C:\blackhole\KESHAV-4> pip install pydantic pytest
Requirement already satisfied: pydantic in C:\Users\rajar\AppData\Local\...
Requirement already satisfied: pytest in C:\Users\rajar\AppData\Local\...
```

## 2. Health Check Validation (Entry-point)
```json
C:\blackhole\KESHAV-4> python c:\blackhole\KESHAV-4\app\health.py
{
  "status": "healthy",
  "service": "KESHAV-4-PropagationEngine",
  "checks": {
    "schema_import": "ok",
    "engine_computation": "ok",
    "latency_bound": "ok"
  },
  "elapsed_ms": 0.07
}
```

## 3. Full Test Suite Execution
```text
C:\blackhole\KESHAV-4> pytest shared_tests\ -v --tb=short
============================= test session starts =============================
platform win32 -- Python 3.13.4, pytest-8.3.3, pluggy-1.6.0
collected 38 items

shared_tests/test_adversarial_failures.py::test_trace_corruption_attempt PASSED [  2%]
shared_tests/test_adversarial_failures.py::test_parallel_failure_pressure PASSED [  5%]
...
shared_tests/test_deep_failures.py::test_downstream_service_outage_503 PASSED [ 15%]
shared_tests/test_deep_failures.py::test_schema_version_mismatch_extra_field PASSED [ 18%]
...
shared_tests/test_distributed_determinism.py::test_distributed_determinism PASSED [ 34%]
...
shared_tests/test_replay_hardening.py::test_restart_replay_validation PASSED [ 89%]
shared_tests/test_replay_hardening.py::test_cross_process_deterministic_replay PASSED [ 92%]
shared_tests/test_replay_hardening.py::test_reconstruction_after_interruption PASSED [ 94%]
shared_tests/test_replay_hardening.py::test_trace_continuity_after_restart PASSED [ 97%]
shared_tests/test_replay_hardening.py::test_corruption_injection_replay PASSED [100%]

============================= 38 passed in 22.17s =============================
```

## 4. Interactive Payload Execution (Success)
```json
C:\blackhole\KESHAV-4> python -c "..."
Executing interactive validation...
{
  "blocked_task_id": "A",
  "root_cause": "A",
  "impacted_tasks": [
    "B",
    "C",
    "D"
  ],
  "impact_score": 3,
  "severity": "MEDIUM",
  "resolution_signal": "UNBLOCK_DEPENDENCY:A",
  "trace_id": "trace-123",
  "timestamp": "2026-05-30T10:00:00Z"
}
```

## 5. Interactive Payload Execution (Failure/Malformed)
```text
C:\blackhole\KESHAV-4> python -c "..."
Executing interactive failure validation...
Exception caught: PropagationContractViolation
SCHEMA_MISMATCH: Input validation failed: 1 validation error for PropagationInput
root_cause
  Field required [type=missing, input_value={'blocked_task_id': 'A', ...'D'], 'C': [], 'D': []}}, input_type=dict]
```
