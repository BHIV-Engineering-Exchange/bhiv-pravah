import json
import copy
from tantra.pipeline import run_tantra_pipeline

def main():
    print("==========================================================")
    print(" PHASE 5: MULTI-CONSUMER INTEGRATION PROOF")
    print("==========================================================\n")

    # The canonical TANTRA input contract payload
    base_payload = {
        "trace_id": "multi-consumer-trace-001",
        "execution_id": "exec-demo",
        "tasks": [
            { "task_id": "T1", "depends_on": [] },
            { "task_id": "T2", "depends_on": ["T1"] },
            { "task_id": "T3", "depends_on": ["T2"] }
        ],
        "constraint_results": [
            { "task_id": "T1", "is_valid": False, "unsatisfied_dependencies": [] },
            { "task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"] },
            { "task_id": "T3", "is_valid": True,  "unsatisfied_dependencies": [] }
        ],
        "propagation_results": [
            { "task_id": "T1", "affected_tasks": ["T2", "T3"], "impact_score": 10 },
            { "task_id": "T2", "affected_tasks": ["T3"],       "impact_score": 4  }
        ]
    }

    # Simulate three distinct consumers
    print("--- Consumer A (Sarathi Runtime) ---")
    payload_a = copy.deepcopy(base_payload)
    result_a = run_tantra_pipeline(payload_a)["keshav_output"]
    print(f"Received Output: root_cause={result_a['root_cause']}, resolution={result_a['resolution_signal']}")
    print("Action Taken: Instructed Core Engine to halt and await T1 unblock.\n")

    print("--- Consumer B (SETU Planning Engine) ---")
    payload_b = copy.deepcopy(base_payload)
    result_b = run_tantra_pipeline(payload_b)["keshav_output"]
    print(f"Received Output: root_cause={result_b['root_cause']}, resolution={result_b['resolution_signal']}")
    print("Action Taken: Re-routed upcoming deployment DAG around T1 bottleneck.\n")

    print("--- Consumer C (AIAIC Analysis Engine) ---")
    payload_c = copy.deepcopy(base_payload)
    result_c = run_tantra_pipeline(payload_c)["keshav_output"]
    print(f"Received Output: root_cause={result_c['root_cause']}, resolution={result_c['resolution_signal']}")
    print("Action Taken: Aggregated incident into global impact report.\n")

    print("--- Verification of Interface Stability ---")
    is_identical = (result_a == result_b == result_c)
    print(f"Are all outputs bit-for-bit identical? {is_identical}")
    
    # Assert there's no consumer-specific state bleeding
    assert is_identical, "Deterministic output violated across consumers!"
    print("Proof Successful: KESHAV was consumed through stable contracts by multiple simulated participants without modifying internal logic.")

if __name__ == "__main__":
    main()
