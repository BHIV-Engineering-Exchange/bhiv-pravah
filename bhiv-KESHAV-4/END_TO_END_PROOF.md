# KESHAV End-to-End Proof
**Phase 4 — End-to-End Execution Proof**


## Scenario 1: Normal execution
### Input
```json
{
  "trace_id": "trace-normal-01",
  "execution_id": "exec-normal-01",
  "tasks": [
    {
      "task_id": "T1",
      "depends_on": []
    }
  ],
  "constraint_results": [
    {
      "task_id": "T1",
      "is_valid": true,
      "unsatisfied_dependencies": []
    }
  ],
  "propagation_results": [
    {
      "task_id": "T1",
      "affected_tasks": [],
      "impact_score": 0
    }
  ]
}
```
### Output
```json
{
  "trace_id": "trace-normal-01",
  "status": "OK",
  "keshav_output": {
    "trace_id": "trace-normal-01",
    "execution_id": "exec-normal-01",
    "root_cause": null,
    "resolution_signal": null,
    "impact_score": 0,
    "severity": "LOW",
    "timestamp": "2026-07-08T14:48:52Z"
  },
  "rajya_output": {
    "trace_id": "trace-normal-01",
    "execution_id": "exec-normal-01",
    "root_cause": null,
    "resolution_signal": null,
    "impact_score": 0,
    "severity": "LOW",
    "timestamp": "2026-07-08T14:48:52Z"
  },
  "sarathi_output": {
    "trace_id": "trace-normal-01",
    "enforced": true,
    "resolution_signal": null,
    "action": "NO_ACTION"
  },
  "core_output": {
    "trace_id": "trace-normal-01",
    "executed": true,
    "action": "NO_ACTION"
  },
  "error": null
}
```
### Bucket Result
```json
[
  {
    "trace_id": "trace-normal-01",
    "keshav_output": {
      "trace_id": "trace-normal-01",
      "execution_id": "exec-normal-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-normal-01",
      "executed": true,
      "action": "NO_ACTION"
    }
  }
]
```
### InsightFlow Result
```json
[
  {
    "type": "EXECUTION",
    "trace_id": "trace-normal-01",
    "root_cause": null,
    "impact_score": 0,
    "severity": "LOW",
    "resolution_signal": null
  }
]
```
### Logs
```text
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-normal-01 trace_id=trace-normal-01
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-normal-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-normal-01', 'root_cause': None, 'impact_score': 0, 'severity': 'LOW', 'resolution_signal': None}
INFO | bucket | bucket | write trace_id=trace-normal-01
```

---

## Scenario 2: Dependency blockage
### Input
```json
{
  "trace_id": "trace-block-01",
  "execution_id": "exec-block-01",
  "tasks": [
    {
      "task_id": "T1",
      "depends_on": []
    },
    {
      "task_id": "T2",
      "depends_on": [
        "T1"
      ]
    }
  ],
  "constraint_results": [
    {
      "task_id": "T1",
      "is_valid": false,
      "unsatisfied_dependencies": []
    },
    {
      "task_id": "T2",
      "is_valid": false,
      "unsatisfied_dependencies": [
        "T1"
      ]
    }
  ],
  "propagation_results": [
    {
      "task_id": "T1",
      "affected_tasks": [
        "T2"
      ],
      "impact_score": 10
    },
    {
      "task_id": "T2",
      "affected_tasks": [],
      "impact_score": 4
    }
  ]
}
```
### Output
```json
{
  "trace_id": "trace-block-01",
  "status": "OK",
  "keshav_output": {
    "trace_id": "trace-block-01",
    "execution_id": "exec-block-01",
    "root_cause": "T1",
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "impact_score": 10,
    "severity": "HIGH",
    "timestamp": "2026-07-08T14:48:52Z"
  },
  "rajya_output": {
    "trace_id": "trace-block-01",
    "execution_id": "exec-block-01",
    "root_cause": "T1",
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "impact_score": 10,
    "severity": "HIGH",
    "timestamp": "2026-07-08T14:48:52Z"
  },
  "sarathi_output": {
    "trace_id": "trace-block-01",
    "enforced": true,
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
    "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
  },
  "core_output": {
    "trace_id": "trace-block-01",
    "executed": true,
    "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
  },
  "error": null
}
```
### Bucket Result
```json
[
  {
    "trace_id": "trace-block-01",
    "keshav_output": {
      "trace_id": "trace-block-01",
      "execution_id": "exec-block-01",
      "root_cause": "T1",
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "impact_score": 10,
      "severity": "HIGH",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-block-01",
      "executed": true,
      "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
    }
  }
]
```
### InsightFlow Result
```json
[
  {
    "type": "EXECUTION",
    "trace_id": "trace-block-01",
    "root_cause": "T1",
    "impact_score": 10,
    "severity": "HIGH",
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1"
  }
]
```
### Logs
```text
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-block-01 trace_id=trace-block-01
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-block-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-block-01', 'root_cause': 'T1', 'impact_score': 10, 'severity': 'HIGH', 'resolution_signal': 'UNBLOCK_DEPENDENCY:T1'}
INFO | bucket | bucket | write trace_id=trace-block-01
```

---

## Scenario 3: Corrupted input
### Input
```json
{
  "execution_id": "exec-corrupt-01",
  "tasks": [
    {
      "task_id": "T1",
      "depends_on": []
    }
  ]
}
```
### Output
```json
{
  "trace_id": "",
  "status": "FAIL",
  "keshav_output": {
    "status": "FAIL",
    "reason": "INVALID_INPUT_CONTRACT",
    "trace_id": ""
  },
  "rajya_output": null,
  "sarathi_output": null,
  "core_output": null,
  "error": "KESHAV returned FAIL"
}
```
### Bucket Result
```json
[]
```
### InsightFlow Result
```json
[
  {
    "type": "FAILURE",
    "trace_id": "",
    "reason": "INVALID_INPUT_CONTRACT"
  }
]
```
### Logs
```text
WARNING | insightflow | insightflow | {'type': 'FAILURE', 'trace_id': '', 'reason': 'INVALID_INPUT_CONTRACT'}
```

---

## Scenario 4: Parallel traces
### Input
```json
{
  "execution_id": "exec-parallel-01",
  "tasks": [
    {
      "task_id": "T1",
      "depends_on": []
    }
  ],
  "constraint_results": [
    {
      "task_id": "T1",
      "is_valid": true,
      "unsatisfied_dependencies": []
    }
  ],
  "propagation_results": [
    {
      "task_id": "T1",
      "affected_tasks": [],
      "impact_score": 0
    }
  ]
}
```
### Output
```json
[
  {
    "trace_id": "trace-parallel-01",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-parallel-01",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-parallel-01",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-parallel-01",
      "enforced": true,
      "resolution_signal": null,
      "action": "NO_ACTION"
    },
    "core_output": {
      "trace_id": "trace-parallel-01",
      "executed": true,
      "action": "NO_ACTION"
    },
    "error": null
  },
  {
    "trace_id": "trace-parallel-02",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-parallel-02",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-parallel-02",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-parallel-02",
      "enforced": true,
      "resolution_signal": null,
      "action": "NO_ACTION"
    },
    "core_output": {
      "trace_id": "trace-parallel-02",
      "executed": true,
      "action": "NO_ACTION"
    },
    "error": null
  },
  {
    "trace_id": "trace-parallel-03",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-parallel-03",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-parallel-03",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-parallel-03",
      "enforced": true,
      "resolution_signal": null,
      "action": "NO_ACTION"
    },
    "core_output": {
      "trace_id": "trace-parallel-03",
      "executed": true,
      "action": "NO_ACTION"
    },
    "error": null
  },
  {
    "trace_id": "trace-parallel-04",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-parallel-04",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-parallel-04",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-parallel-04",
      "enforced": true,
      "resolution_signal": null,
      "action": "NO_ACTION"
    },
    "core_output": {
      "trace_id": "trace-parallel-04",
      "executed": true,
      "action": "NO_ACTION"
    },
    "error": null
  },
  {
    "trace_id": "trace-parallel-05",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-parallel-05",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-parallel-05",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-parallel-05",
      "enforced": true,
      "resolution_signal": null,
      "action": "NO_ACTION"
    },
    "core_output": {
      "trace_id": "trace-parallel-05",
      "executed": true,
      "action": "NO_ACTION"
    },
    "error": null
  }
]
```
### Bucket Result
```json
[
  {
    "trace_id": "trace-parallel-01",
    "keshav_output": {
      "trace_id": "trace-parallel-01",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-parallel-01",
      "executed": true,
      "action": "NO_ACTION"
    }
  },
  {
    "trace_id": "trace-parallel-02",
    "keshav_output": {
      "trace_id": "trace-parallel-02",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-parallel-02",
      "executed": true,
      "action": "NO_ACTION"
    }
  },
  {
    "trace_id": "trace-parallel-03",
    "keshav_output": {
      "trace_id": "trace-parallel-03",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-parallel-03",
      "executed": true,
      "action": "NO_ACTION"
    }
  },
  {
    "trace_id": "trace-parallel-04",
    "keshav_output": {
      "trace_id": "trace-parallel-04",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-parallel-04",
      "executed": true,
      "action": "NO_ACTION"
    }
  },
  {
    "trace_id": "trace-parallel-05",
    "keshav_output": {
      "trace_id": "trace-parallel-05",
      "execution_id": "exec-parallel-01",
      "root_cause": null,
      "resolution_signal": null,
      "impact_score": 0,
      "severity": "LOW",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-parallel-05",
      "executed": true,
      "action": "NO_ACTION"
    }
  }
]
```
### InsightFlow Result
```json
[
  {
    "type": "EXECUTION",
    "trace_id": "trace-parallel-01",
    "root_cause": null,
    "impact_score": 0,
    "severity": "LOW",
    "resolution_signal": null
  },
  {
    "type": "EXECUTION",
    "trace_id": "trace-parallel-02",
    "root_cause": null,
    "impact_score": 0,
    "severity": "LOW",
    "resolution_signal": null
  },
  {
    "type": "EXECUTION",
    "trace_id": "trace-parallel-03",
    "root_cause": null,
    "impact_score": 0,
    "severity": "LOW",
    "resolution_signal": null
  },
  {
    "type": "EXECUTION",
    "trace_id": "trace-parallel-04",
    "root_cause": null,
    "impact_score": 0,
    "severity": "LOW",
    "resolution_signal": null
  },
  {
    "type": "EXECUTION",
    "trace_id": "trace-parallel-05",
    "root_cause": null,
    "impact_score": 0,
    "severity": "LOW",
    "resolution_signal": null
  }
]
```
### Logs
```text
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-parallel-01 trace_id=trace-parallel-01
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-parallel-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-parallel-01', 'root_cause': None, 'impact_score': 0, 'severity': 'LOW', 'resolution_signal': None}
INFO | bucket | bucket | write trace_id=trace-parallel-01
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-parallel-01 trace_id=trace-parallel-02
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-parallel-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-parallel-02', 'root_cause': None, 'impact_score': 0, 'severity': 'LOW', 'resolution_signal': None}
INFO | bucket | bucket | write trace_id=trace-parallel-02
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-parallel-01 trace_id=trace-parallel-03
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-parallel-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-parallel-03', 'root_cause': None, 'impact_score': 0, 'severity': 'LOW', 'resolution_signal': None}
INFO | bucket | bucket | write trace_id=trace-parallel-03
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-parallel-01 trace_id=trace-parallel-04
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-parallel-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-parallel-04', 'root_cause': None, 'impact_score': 0, 'severity': 'LOW', 'resolution_signal': None}
INFO | bucket | bucket | write trace_id=trace-parallel-04
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-parallel-01 trace_id=trace-parallel-05
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-parallel-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-parallel-05', 'root_cause': None, 'impact_score': 0, 'severity': 'LOW', 'resolution_signal': None}
INFO | bucket | bucket | write trace_id=trace-parallel-05
```

---

## Scenario 5: Replay execution
### Input
```json
{
  "trace_id": "trace-replay-01",
  "execution_id": "exec-block-01",
  "tasks": [
    {
      "task_id": "T1",
      "depends_on": []
    },
    {
      "task_id": "T2",
      "depends_on": [
        "T1"
      ]
    }
  ],
  "constraint_results": [
    {
      "task_id": "T1",
      "is_valid": false,
      "unsatisfied_dependencies": []
    },
    {
      "task_id": "T2",
      "is_valid": false,
      "unsatisfied_dependencies": [
        "T1"
      ]
    }
  ],
  "propagation_results": [
    {
      "task_id": "T1",
      "affected_tasks": [
        "T2"
      ],
      "impact_score": 10
    },
    {
      "task_id": "T2",
      "affected_tasks": [],
      "impact_score": 4
    }
  ]
}
```
### Output
```json
{
  "run_1": {
    "trace_id": "trace-replay-01",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-replay-01",
      "execution_id": "exec-block-01",
      "root_cause": "T1",
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "impact_score": 10,
      "severity": "HIGH",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-replay-01",
      "execution_id": "exec-block-01",
      "root_cause": "T1",
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "impact_score": 10,
      "severity": "HIGH",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-replay-01",
      "enforced": true,
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
    },
    "core_output": {
      "trace_id": "trace-replay-01",
      "executed": true,
      "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
    },
    "error": null
  },
  "run_2_replay": {
    "trace_id": "trace-replay-01",
    "status": "OK",
    "keshav_output": {
      "trace_id": "trace-replay-01",
      "execution_id": "exec-block-01",
      "root_cause": "T1",
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "impact_score": 10,
      "severity": "HIGH",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "rajya_output": {
      "trace_id": "trace-replay-01",
      "execution_id": "exec-block-01",
      "root_cause": "T1",
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "impact_score": 10,
      "severity": "HIGH",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "sarathi_output": {
      "trace_id": "trace-replay-01",
      "enforced": true,
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
    },
    "core_output": {
      "trace_id": "trace-replay-01",
      "executed": true,
      "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
    },
    "error": null
  }
}
```
### Bucket Result
```json
[
  {
    "trace_id": "trace-replay-01",
    "keshav_output": {
      "trace_id": "trace-replay-01",
      "execution_id": "exec-block-01",
      "root_cause": "T1",
      "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
      "impact_score": 10,
      "severity": "HIGH",
      "timestamp": "2026-07-08T14:48:52Z"
    },
    "core_output": {
      "trace_id": "trace-replay-01",
      "executed": true,
      "action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"
    }
  }
]
```
### InsightFlow Result
```json
[
  {
    "type": "EXECUTION",
    "trace_id": "trace-replay-01",
    "root_cause": "T1",
    "impact_score": 10,
    "severity": "HIGH",
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1"
  },
  {
    "type": "EXECUTION",
    "trace_id": "trace-replay-01",
    "root_cause": "T1",
    "impact_score": 10,
    "severity": "HIGH",
    "resolution_signal": "UNBLOCK_DEPENDENCY:T1"
  }
]
```
### Logs
```text
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-block-01 trace_id=trace-replay-01
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-block-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-replay-01', 'root_cause': 'T1', 'impact_score': 10, 'severity': 'HIGH', 'resolution_signal': 'UNBLOCK_DEPENDENCY:T1'}
INFO | bucket | bucket | write trace_id=trace-replay-01
INFO | analyzer.analyze_blockage | analyze_and_recommend started | execution_id=exec-block-01 trace_id=trace-replay-01
INFO | analyzer.analyze_blockage | analyze_and_recommend complete | execution_id=exec-block-01
INFO | insightflow | insightflow | {'type': 'EXECUTION', 'trace_id': 'trace-replay-01', 'root_cause': 'T1', 'impact_score': 10, 'severity': 'HIGH', 'resolution_signal': 'UNBLOCK_DEPENDENCY:T1'}
INFO | bucket | bucket | write trace_id=trace-replay-01
```

---
