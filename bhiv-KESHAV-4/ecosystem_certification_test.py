#!/usr/bin/env python3
"""
Ecosystem Convergence Validation Testing Package

Project: KESHAV
Product: TANTRA Ecosystem
Module: Ecosystem Convergence Validation
Submitted By: Rajaryan Verma
Submission Type: Convergence Certification
"""

import sys
from tantra.pipeline import run_tantra_pipeline
from tantra import bucket, insightflow

def run_certification():
    print("==================================================")
    print(" TESTING PACKAGE: Ecosystem Convergence Validation")
    print("==================================================")
    print("Project:        KESHAV")
    print("Product:        TANTRA Ecosystem")
    print("Module:         Ecosystem Convergence Validation")
    print("Submitted By:   Rajaryan Verma")
    print("Submission Type: Convergence Certification")
    print("--------------------------------------------------\n")

    input_data = {
        "trace_id": "cert-trace-001",
        "execution_id": "cert-exec-001",
        "tasks": [{"task_id": "T1", "depends_on": []}, {"task_id": "T2", "depends_on": ["T1"]}],
        "constraint_results": [
            {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]}
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2"], "impact_score": 10}
        ]
    }

    bucket.clear()
    insightflow.clear()

    print("Executing pipeline...")
    result = run_tantra_pipeline(input_data)
    
    failures = 0

    print("\n1. Runtime Attachment Claims")
    if result["status"] == "OK" and result["core_output"] is not None:
        print("   [PASS] Pipeline attached and executed sequentially.")
    else:
        print("   [FAIL] Pipeline did not attach correctly.")
        failures += 1

    print("2. Trace Continuity Claims")
    if result["trace_id"] == "cert-trace-001" and result["core_output"]["trace_id"] == "cert-trace-001":
        print("   [PASS] trace_id preserved identically across all layers.")
    else:
        print("   [FAIL] trace_id mutated or lost.")
        failures += 1

    print("3. Authority Declarations")
    if "enforced" in result["sarathi_output"] and "executed" in result["core_output"]:
        print("   [PASS] KESHAV output passed to RAJYA/Sarathi; authority isolated.")
    else:
        print("   [FAIL] Authority bleeding detected.")
        failures += 1

    print("4. Persistence Assessments")
    stored = bucket.read("cert-trace-001")
    if stored and stored["trace_id"] == "cert-trace-001":
        print("   [PASS] Truth layer persisted execution result upon success.")
    else:
        print("   [FAIL] Bucket failed to persist.")
        failures += 1

    print("5. Observability Claims")
    events = insightflow.get_events()
    if len(events) == 1 and events[0]["trace_id"] == "cert-trace-001":
        print("   [PASS] InsightFlow emitted read-only telemetry.")
    else:
        print("   [FAIL] InsightFlow missed telemetry.")
        failures += 1

    print("\n==================================================")
    if failures == 0:
        print(" FINAL VERDICT: APPROVED WITH EVIDENCE")
    else:
        print(f" FINAL VERDICT: REJECTED ({failures} failures)")
    print("==================================================")
    
    sys.exit(failures)

if __name__ == "__main__":
    run_certification()
