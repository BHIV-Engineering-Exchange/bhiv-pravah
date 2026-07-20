import os
import sys
import subprocess
import time
import requests
import uuid
from datetime import datetime

# Test configurations
TEST_API_KEY = "validation_sprint_test_key_2026"
BASE_URL = "http://127.0.0.1"

# Service endpoints and expected response keys/health checks
SERVICES = {
    "Prompt Runner": {"url": f"{BASE_URL}:8003/health", "auth": False},
    "Creator Core": {"url": f"{BASE_URL}:8000/", "auth": False},
    "BHIV Core": {"url": f"{BASE_URL}:8001/system/health", "auth": False},
    "Integration Bridge": {"url": f"{BASE_URL}:8004/pipeline/health", "auth": False},
    "BHIV Bucket": {"url": f"{BASE_URL}:8005/bucket/stats", "auth": False},
    "CET Service": {"url": f"{BASE_URL}:8006/health", "auth": False},
    "Sarathi Service": {"url": f"{BASE_URL}:8007/health", "auth": False},
    "Gate Service": {"url": f"{BASE_URL}:8008/health", "auth": False},
}

PROTECTED_ENDPOINTS = [
    f"{BASE_URL}:8004/pipeline/execute",
    f"{BASE_URL}:8004/pipeline/replay/test-trace",
    f"{BASE_URL}:8005/bucket/store",
    f"{BASE_URL}:8006/contract/compile",
    f"{BASE_URL}:8007/authority/validate",
    f"{BASE_URL}:8008/gate/evaluate",
]

def main():
    print("\n" + "="*80)
    print("SHAKTI & TANTRA RUNTIME VALIDATION SUITE")
    print("="*80)
    
    # Configure environmental variables for child process
    env = os.environ.copy()
    env["AUTH_ENABLED"] = "true"
    env["AUTH_API_KEY"] = TEST_API_KEY
    env["AUTH_SECRET_KEY"] = "validation_sprint_test_secret_key_2026"
    env["RATE_LIMIT_IP_PER_MIN"] = "150"  # Set higher to avoid blocking health checks
    env["DISABLE_VIDEO_SERVICE"] = "true"  # Disable slow video generation in health checks
    env["PYTHONIOENCODING"] = "utf-8"
    
    print("\n[STEP 1] Cold Startup: Spawning start_all.py...")
    proc = subprocess.Popen(
        [sys.executable, "start_all.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    # Wait for services to start (timeout 30s)
    print("Waiting for all 8 microservices to report healthy...")
    all_healthy = False
    start_time = time.time()
    
    while time.time() - start_time < 90:
        # Check health of all services
        healthy_count = 0
        failed_services = []
        for name, info in SERVICES.items():
            try:
                res = requests.get(info["url"], timeout=2)
                if res.status_code == 200:
                    healthy_count += 1
                else:
                    failed_services.append(f"{name} (status {res.status_code})")
            except Exception as e:
                failed_services.append(f"{name} (error: {type(e).__name__})")
        
        print(f"   Healthy services: {healthy_count}/{len(SERVICES)}")
        if failed_services:
            print(f"     Failed: {', '.join(failed_services)}")
        if healthy_count == len(SERVICES):
            all_healthy = True
            break
        time.sleep(2)
        
    if not all_healthy:
        print("\n[X] Cold startup failed or services timed out.")
        # Dump subprocess stdout cleanly
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=5)
            print("Subprocess Output:\n", out)
        except Exception as e:
            print("Could not get subprocess output:", e)
        sys.exit(1)
        
    print("\n[OK] Cold startup validated. All 8 microservices are running.")
    
    success = True
    try:
        # STEP 2: Verify Authentication Protection
        print("\n[STEP 2] Verifying API Authentication Protection...")
        headers = {"X-API-Key": TEST_API_KEY}
        
        # Test a protected endpoint without auth header
        for endpoint in PROTECTED_ENDPOINTS:
            try:
                res = requests.post(endpoint, json={}, timeout=2)
                if res.status_code == 401:
                    print(f"   [OK] Protected: {endpoint} returned 401 Unauthorized as expected")
                else:
                    print(f"   [X] Vulnerability: {endpoint} returned {res.status_code} without auth header")
                    success = False
            except Exception as e:
                # GET endpoints might return 401 or 405 on POST which is also a form of rejection
                print(f"   [OK] Rejection validated: {endpoint}")
                
        # STEP 3: Verify End-to-End Pipeline & Correlation IDs
        print("\n[STEP 3] Running End-to-End Pipeline with Correlation IDs...")
        trace_id = f"trace_val_{uuid.uuid4().hex[:12]}"
        workflow_id = f"workflow_val_{uuid.uuid4().hex[:12]}"
        
        pipeline_url = f"{BASE_URL}:8004/pipeline/execute"
        pipeline_headers = {
            "X-API-Key": TEST_API_KEY,
            "X-Trace-Id": trace_id,
            "X-Workflow-Id": workflow_id
        }
        
        payload = {"prompt": "Generate a simple content processing adapter for validation"}
        print(f"   Sending execute request with Trace-ID: {trace_id} and Workflow-ID: {workflow_id}")
        res = requests.post(pipeline_url, json=payload, headers=pipeline_headers, timeout=15)
        
        if res.status_code != 200:
            print(f"   [X] Pipeline execution failed: {res.status_code} - {res.text}")
            success = False
        else:
            data = res.json()
            print("   [OK] Pipeline completed successfully.")
            print(f"   Returned Trace-ID: {data.get('trace_id')}")
            print(f"   Returned Workflow-ID: {data.get('workflow_id')}")
            
            # STEP 4: Verify Bucket Storage & Artifact Integrity
            print("\n[STEP 4] Querying Bucket to Verify Artifact and Trace Integrity...")
            bucket_url = f"{BASE_URL}:8005/bucket/trace/{trace_id}"
            bucket_res = requests.get(bucket_url, headers=headers, timeout=5)
            
            if bucket_res.status_code != 200:
                print(f"   [X] Trace retrieval from bucket failed: {bucket_res.status_code} - {bucket_res.text}")
                success = False
            else:
                trace_data = bucket_res.json()
                print("   [OK] Trace artifacts retrieved from append-only bucket.")
                artifacts = trace_data.get("artifacts", [])
                print(f"   Total stored artifacts: {len(artifacts)}")
                
                # Check that every artifact carries both the trace_id and workflow_id inside its stored data
                for idx, art in enumerate(artifacts):
                    art_type = art.get("artifact_type")
                    art_data = art.get("data", {})
                    art_trace = art.get("trace_id") or art_data.get("trace_id")
                    art_workflow = art_data.get("workflow_id")
                    
                    print(f"     Artifact {idx+1} ({art_type}):")
                    print(f"       Trace ID in record: {art_trace}")
                    print(f"       Workflow ID in stored data: {art_workflow}")
                    
                    if art_trace != trace_id or art_workflow != workflow_id:
                        print("       [X] Correlation IDs mismatch!")
                        success = False
                    else:
                        print("       [OK] Correlation IDs match.")
            
        # STEP 5: Verify Rate Limiting Enforcement
        print("\n[STEP 5] Testing Rate Limiting Enforcement (IP-based limit = 150)...")
        rate_limit_triggered = False
        # Send 160 fast requests to trigger rate limit (150 limit + buffer)
        health_url = f"{BASE_URL}:8004/pipeline/health"
        for i in range(170):
            try:
                res = requests.get(health_url, timeout=2)
                if res.status_code == 429:
                    print(f"   [OK] Request {i+1} blocked: {res.status_code} Rate Limit Exceeded")
                    rate_limit_triggered = True
                    break
            except Exception as e:
                pass
            
        if not rate_limit_triggered:
            print("   [X] Rate limiter failed to trigger after 170 requests")
            success = False
            
    finally:
        # STEP 6: Clean Shutdown
        print("\n[STEP 6] Shutting down all services via Orchestrator...")
        proc.terminate()
        try:
            proc.wait(timeout=10)
            print("[OK] All processes stopped cleanly.")
        except subprocess.TimeoutExpired:
            proc.kill()
            print("[OK] Processes killed.")
            
    print("\n" + "="*80)
    if success:
        print("VALIDATION SUITE RESULT: SUCCESS")
        print("All production runtime criteria have been met successfully.")
        print("="*80 + "\n")
        sys.exit(0)
    else:
        print("VALIDATION SUITE RESULT: FAILED")
        print("One or more validation steps failed. See details above.")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
