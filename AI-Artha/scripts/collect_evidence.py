#!/usr/bin/env python3
"""
Evidence Collection Script — Generates runtime validation evidence for Phase IV convergence.
Run this script after the server is running to collect evidence.
"""

import os
import sys
import json
import time
import hashlib
import requests
from datetime import datetime, timezone

BASE_URL = os.getenv("PLATFORM_URL", "http://localhost:9000")
EVIDENCE_DIR = "evidence"

os.makedirs(EVIDENCE_DIR, exist_ok=True)


def save_evidence(name: str, data: dict):
    """Save evidence to file."""
    filepath = os.path.join(EVIDENCE_DIR, f"{name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    print(f"  [OK] Evidence saved: {filepath}")


def collect_day1a_evidence():
    """Day 1A: Platform Contract Lock evidence."""
    print("\n=== Day 1A: Platform Contract Lock ===")
    
    # 1. Contract validation
    try:
        resp = requests.post(f"{BASE_URL}/platform/validate-contract", json={
            "trace_id": "11111111-1111-1111-1111-111111111111",
            "schema_version": "1.0.0",
            "module": "platform",
            "action": "health",
            "payload": {},
            "metadata": {"source": "evidence_collector"}
        })
        save_evidence("day1a_contract_validation", resp.json())
    except Exception as e:
        save_evidence("day1a_contract_validation", {"error": str(e)})
    
    # 2. Module registry
    try:
        resp = requests.get(f"{BASE_URL}/platform/modules")
        save_evidence("day1a_platform_modules", resp.json())
    except Exception as e:
        save_evidence("day1a_platform_modules", {"error": str(e)})
    
    # 3. Schema version
    try:
        resp = requests.get(f"{BASE_URL}/platform/contract")
        save_evidence("day1a_platform_schema", resp.json())
    except Exception as e:
        save_evidence("day1a_platform_schema", {"error": str(e)})
    
    print("  Day 1A evidence collected.")


def collect_day1b_evidence():
    """Day 1B: Runtime Convergence evidence."""
    print("\n=== Day 1B: Runtime Convergence ===")
    
    flow_steps = []
    start_time = time.time()
    
    # Step 1: Health check
    try:
        resp = requests.get(f"{BASE_URL}/health")
        flow_steps.append({"step": "health_check", "status": "success", "response": resp.json()})
    except Exception as e:
        flow_steps.append({"step": "health_check", "status": "error", "error": str(e)})
    
    # Step 2: Platform health
    try:
        resp = requests.get(f"{BASE_URL}/health/platform")
        flow_steps.append({"step": "platform_health", "status": "success", "response": resp.json()})
    except Exception as e:
        flow_steps.append({"step": "platform_health", "status": "error", "error": str(e)})
    
    # Step 3: Platform execute with trace
    trace_id = f"trace_{int(time.time())}_{os.urandom(4).hex()}"
    try:
        resp = requests.post(f"{BASE_URL}/platform/execute", json={
            "trace_id": trace_id,
            "schema_version": "1.0.0",
            "module": "platform",
            "action": "echo",
            "payload": {"test": "runtime_convergence"},
            "metadata": {"source": "evidence_collector"}
        })
        flow_steps.append({"step": "platform_execute", "status": "success", "response": resp.json()})
    except Exception as e:
        flow_steps.append({"step": "platform_execute", "status": "error", "error": str(e)})
    
    # Step 4: Observability events
    try:
        resp = requests.get(f"{BASE_URL}/observability/events")
        flow_steps.append({"step": "observability_events", "status": "success", "response": resp.json()})
    except Exception as e:
        flow_steps.append({"step": "observability_events", "status": "error", "error": str(e)})
    
    # Step 5: Trace-specific events
    try:
        resp = requests.get(f"{BASE_URL}/observability/events/trace/{trace_id}")
        flow_steps.append({"step": "trace_events", "status": "success", "response": resp.json()})
    except Exception as e:
        flow_steps.append({"step": "trace_events", "status": "error", "error": str(e)})
    
    total_duration = (time.time() - start_time) * 1000
    
    evidence = {
        "test_name": "runtime_convergence",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "total_duration_ms": round(total_duration, 2),
        "steps": flow_steps,
        "all_steps_passed": all(s["status"] == "success" for s in flow_steps)
    }
    save_evidence("day1b_runtime_flow", evidence)
    print("  Day 1B evidence collected.")


def collect_day1c_evidence():
    """Day 1C: Observability evidence."""
    print("\n=== Day 1C: Observability ===")
    
    # 1. Observability events
    try:
        resp = requests.get(f"{BASE_URL}/observability/events?limit=10")
        save_evidence("day1c_observability_events", resp.json())
    except Exception as e:
        save_evidence("day1c_observability_events", {"error": str(e)})
    
    # 2. Observability health
    try:
        resp = requests.get(f"{BASE_URL}/observability/health")
        save_evidence("day1c_observability_health", resp.json())
    except Exception as e:
        save_evidence("day1c_observability_health", {"error": str(e)})
    
    # 3. Module stats
    try:
        resp = requests.get(f"{BASE_URL}/observability/stats/modules")
        save_evidence("day1c_module_stats", resp.json())
    except Exception as e:
        save_evidence("day1c_module_stats", {"error": str(e)})
    
    print("  Day 1C evidence collected.")


def collect_day2a_evidence():
    """Day 2A: Bucket Production Validation evidence."""
    print("\n=== Day 2A: Bucket Validation ===")
    
    # 1. Write and verify
    try:
        resp = requests.post(f"{BASE_URL}/bucket-validation/write-and-verify")
        save_evidence("day2a_bucket_write_verify", resp.json())
    except Exception as e:
        save_evidence("day2a_bucket_write_verify", {"error": str(e)})
    
    # 2. Bucket status
    try:
        resp = requests.get(f"{BASE_URL}/bucket-validation/status")
        save_evidence("day2a_bucket_status", resp.json())
    except Exception as e:
        save_evidence("day2a_bucket_status", {"error": str(e)})
    
    # 3. List artifacts
    try:
        resp = requests.get(f"{BASE_URL}/bucket-validation/list-artifacts")
        save_evidence("day2a_bucket_artifacts", resp.json())
    except Exception as e:
        save_evidence("day2a_bucket_artifacts", {"error": str(e)})
    
    print("  Day 2A evidence collected.")


def collect_day2b_evidence():
    """Day 2B: Production Hardening evidence."""
    print("\n=== Day 2B: Production Hardening ===")
    
    # 1. Health verification
    try:
        resp = requests.get(f"{BASE_URL}/health")
        save_evidence("day2b_health_verification", resp.json())
    except Exception as e:
        save_evidence("day2b_health_verification", {"error": str(e)})
    
    # 2. Platform health
    try:
        resp = requests.get(f"{BASE_URL}/health/platform")
        save_evidence("day2b_platform_health", resp.json())
    except Exception as e:
        save_evidence("day2b_platform_health", {"error": str(e)})
    
    # 3. Auth flow (demo login)
    try:
        resp = requests.post(f"{BASE_URL}/users/login", 
            data={"username": "demo", "password": "demo1234"})
        save_evidence("day2b_auth_flow", resp.json())
    except Exception as e:
        save_evidence("day2b_auth_flow", {"error": str(e)})
    
    # 4. Deterministic repeated execution
    results = []
    for i in range(3):
        try:
            resp = requests.get(f"{BASE_URL}/health")
            results.append({"attempt": i+1, "status": resp.json().get("status"), "status_code": resp.status_code})
        except Exception as e:
            results.append({"attempt": i+1, "error": str(e)})
    
    deterministic = all(r.get("status") == "healthy" for r in results)
    save_evidence("day2b_deterministic_execution", {
        "test": "deterministic_repeated_execution",
        "results": results,
        "deterministic": deterministic,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # 5. Graceful failure (invalid endpoint)
    try:
        resp = requests.get(f"{BASE_URL}/nonexistent-endpoint-12345")
        save_evidence("day2b_graceful_failure", {
            "test": "graceful_failure_handling",
            "status_code": resp.status_code,
            "handled_gracefully": resp.status_code in [404, 405],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        save_evidence("day2b_graceful_failure", {"error": str(e)})
    
    print("  Day 2B evidence collected.")


def collect_all_evidence():
    """Collect all Phase IV evidence."""
    print("=" * 60)
    print("Phase IV Evidence Collection")
    print(f"Server: {BASE_URL}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    # Verify server is running
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n[OK] Server is running (status: {resp.json().get('status')})")
    except Exception as e:
        print(f"\n[ERROR] Server not reachable at {BASE_URL}: {e}")
        print("Start the server first: python -m uvicorn app.main:app --host 127.0.0.1 --port 9000")
        return
    
    collect_day1a_evidence()
    collect_day1b_evidence()
    collect_day1c_evidence()
    collect_day2a_evidence()
    collect_day2b_evidence()
    
    print("\n" + "=" * 60)
    print("All evidence collected successfully!")
    print(f"Files saved to: {os.path.abspath(EVIDENCE_DIR)}/")
    print("=" * 60)


if __name__ == "__main__":
    collect_all_evidence()
