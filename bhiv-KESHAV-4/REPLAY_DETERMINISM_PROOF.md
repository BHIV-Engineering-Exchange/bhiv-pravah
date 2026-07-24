# KESHAV Replay & Determinism Proof
**Generated:** 2026-06-17T11:14:20Z
**Replay Count:** 10 runs per input

---
## Test 1: Blocked Graph Replay (Input A)

### Input
```json
{
  "constraint_results": [
    {
      "is_valid": false,
      "task_id": "T1",
      "unsatisfied_dependencies": []
    },
    {
      "is_valid": false,
      "task_id": "T2",
      "unsatisfied_dependencies": [
        "T1"
      ]
    },
    {
      "is_valid": false,
      "task_id": "T3",
      "unsatisfied_dependencies": [
        "T1"
      ]
    },
    {
      "is_valid": false,
      "task_id": "T4",
      "unsatisfied_dependencies": [
        "T2",
        "T3"
      ]
    },
    {
      "is_valid": false,
      "task_id": "T5",
      "unsatisfied_dependencies": [
        "T4"
      ]
    }
  ],
  "execution_id": "replay-exec-A",
  "propagation_results": [
    {
      "affected_tasks": [
        "T2",
        "T3",
        "T4",
        "T5"
      ],
      "impact_score": 20,
      "task_id": "T1"
    },
    {
      "affected_tasks": [
        "T4",
        "T5"
      ],
      "impact_score": 8,
      "task_id": "T2"
    },
    {
      "affected_tasks": [
        "T4",
        "T5"
      ],
      "impact_score": 8,
      "task_id": "T3"
    }
  ],
  "tasks": [
    {
      "depends_on": [],
      "task_id": "T1"
    },
    {
      "depends_on": [
        "T1"
      ],
      "task_id": "T2"
    },
    {
      "depends_on": [
        "T1"
      ],
      "task_id": "T3"
    },
    {
      "depends_on": [
        "T2",
        "T3"
      ],
      "task_id": "T4"
    },
    {
      "depends_on": [
        "T4"
      ],
      "task_id": "T5"
    }
  ],
  "trace_id": "replay-trace-A"
}
```

### Output Comparison

| Run | SHA-256 Hash | Status | Root Cause | Resolution Signal |
|-----|-------------|--------|------------|-------------------|
|  1  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  2  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  3  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  4  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  5  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  6  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  7  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  8  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
|  9  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |
| 10  | `0166abbe307d5f1a...` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |

  PASS -- All 10 outputs are field-by-field identical
  PASS -- All 10 SHA-256 hashes are identical: 0166abbe307d5f1a34042637b9ce00e5...
  PASS -- Run 1: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 2: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 3: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 4: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 5: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 6: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 7: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 8: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 9: trace_id='replay-trace-A' preserved across all layers
  PASS -- Run 10: trace_id='replay-trace-A' preserved across all layers
  PASS -- All 10 bucket persistence records are identical

### Representative Output (Run 1)
```json
{
  "core_output": {
    "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1",
    "executed": true,
    "trace_id": "replay-trace-A"
  },
  "error": null,
  "keshav_output": {
    "execution_id": "replay-exec-A",
    "impact_score": 20,
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "root_cause": "T1",
    "severity": "HIGH",
    "trace_id": "replay-trace-A"
  },
  "rajya_output": {
    "execution_id": "replay-exec-A",
    "impact_score": 20,
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "root_cause": "T1",
    "severity": "HIGH",
    "trace_id": "replay-trace-A"
  },
  "sarathi_output": {
    "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1",
    "enforced": true,
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "trace_id": "replay-trace-A"
  },
  "status": "OK",
  "trace_id": "replay-trace-A"
}
```

### Representative Bucket Record (Run 1)
```json
{
  "core_output": {
    "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1",
    "executed": true,
    "trace_id": "replay-trace-A"
  },
  "keshav_output": {
    "execution_id": "replay-exec-A",
    "impact_score": 20,
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "root_cause": "T1",
    "severity": "HIGH",
    "trace_id": "replay-trace-A"
  },
  "trace_id": "replay-trace-A"
}
```

---
## Test 2: Clean Graph Replay (Input B)

### Input
```json
{
  "constraint_results": [
    {
      "is_valid": true,
      "task_id": "X1",
      "unsatisfied_dependencies": []
    },
    {
      "is_valid": true,
      "task_id": "X2",
      "unsatisfied_dependencies": []
    }
  ],
  "execution_id": "replay-exec-B",
  "propagation_results": [],
  "tasks": [
    {
      "depends_on": [],
      "task_id": "X1"
    },
    {
      "depends_on": [
        "X1"
      ],
      "task_id": "X2"
    }
  ],
  "trace_id": "replay-trace-B"
}
```

### Output Comparison

| Run | SHA-256 Hash | Status | Root Cause | Sarathi Action |
|-----|-------------|--------|------------|----------------|
|  1  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  2  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  3  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  4  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  5  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  6  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  7  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  8  | `e75610c4bd013850...` | OK | None | NO_ACTION |
|  9  | `e75610c4bd013850...` | OK | None | NO_ACTION |
| 10  | `e75610c4bd013850...` | OK | None | NO_ACTION |

  PASS -- All 10 clean graph outputs are field-by-field identical
  PASS -- All 10 clean graph SHA-256 hashes are identical: e75610c4bd013850d41431e72677e8b2...

---
## Test 3: Fail-Closed Replay (Input C -- corrupted)

### Input
```json
{
  "execution_id": "corrupt-001",
  "tasks": "not-a-list"
}
```

  PASS -- Run 1: Bucket empty after corrupted input
  PASS -- Run 2: Bucket empty after corrupted input
  PASS -- Run 3: Bucket empty after corrupted input
  PASS -- Run 4: Bucket empty after corrupted input
  PASS -- Run 5: Bucket empty after corrupted input
  PASS -- Run 6: Bucket empty after corrupted input
  PASS -- Run 7: Bucket empty after corrupted input
  PASS -- Run 8: Bucket empty after corrupted input
  PASS -- Run 9: Bucket empty after corrupted input
  PASS -- Run 10: Bucket empty after corrupted input
### Output Comparison

| Run | SHA-256 Hash | Status | Reason |
|-----|-------------|--------|--------|
|  1  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  2  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  3  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  4  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  5  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  6  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  7  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  8  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
|  9  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |
| 10  | `9000de7535a531f5...` | FAIL | INVALID_INPUT_CONTRACT |

  PASS -- All 10 fail-closed outputs are field-by-field identical
  PASS -- All 10 fail-closed SHA-256 hashes are identical: 9000de7535a531f56ab834ed41b9d15e...

---
## Test 4: Cross-Input Hash Isolation

  PASS -- Input A hash != Input B hash (different inputs produce different outputs)
  PASS -- Input A hash != Input C hash (valid vs corrupted)
  PASS -- Input B hash != Input C hash (clean vs corrupted)

---
## Test 5: InsightFlow Event Determinism

  PASS -- InsightFlow recorded exactly 3 EXECUTION events across 3 replays
  PASS -- InsightFlow event 1: trace_id, root_cause, severity, resolution_signal all match
  PASS -- InsightFlow event 2: trace_id, root_cause, severity, resolution_signal all match
  PASS -- InsightFlow event 3: trace_id, root_cause, severity, resolution_signal all match

---
## FINAL VERDICT

**Total Assertions:** 34
**Passed:** 34
**Failed:** 0

### ALL ASSERTIONS PASSED

KESHAV replay-safe operation is **fully proven**.

**Proven:**
- 10 identical runs per input produce byte-identical outputs
- SHA-256 hash equality verified across all 10 runs for 3 input classes
- Trace artifacts (trace_id, root_cause, resolution_signal) are identical across replays
- Bucket persistence records are identical across replays
- Fail-closed replays produce identical FAIL outputs with zero Bucket writes
- Cross-input hash isolation verified (different inputs -> different hashes)
- InsightFlow observability events are deterministic across replays
