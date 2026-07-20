#!/usr/bin/env python3
"""
Deployment Verification Script — Validates all Phase IV requirements.
Run this script to verify deployment health.
"""

import os
import sys
import json
import time
import hashlib
import requests
from datetime import datetime, timezone

BASE_URL = os.getenv("PLATFORM_URL", "http://localhost:9000")

class DeploymentVerifier:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def check(self, name: str, test_fn):
        """Run a verification check."""
        try:
            result = test_fn()
            status = "PASS" if result else "FAIL"
            if result:
                self.passed += 1
            else:
                self.failed += 1
            self.results.append({"name": name, "status": status})
            print(f"  [{status}] {name}")
            return result
        except Exception as e:
            self.failed += 1
            self.results.append({"name": name, "status": "FAIL", "error": str(e)})
            print(f"  [FAIL] {name}: {e}")
            return False
    
    def run_all(self):
        """Run all deployment verification checks."""
        print("=" * 60)
        print("Deployment Verification — Phase IV")
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)
        
        # === Pre-Deployment ===
        print("\n--- Pre-Deployment ---")
        self.check("MongoDB configured", lambda: self._check_env("MONGO_URI"))
        self.check("JWT secret configured", lambda: self._check_env("JWT_SECRET_KEY"))
        
        # === Startup ===
        print("\n--- Startup Validation ---")
        self.check("Health endpoint responds", self._check_health)
        self.check("Health status is healthy", self._check_health_status)
        
        # === Authentication ===
        print("\n--- Authentication ---")
        self.check("Login endpoint accessible", self._check_login_accessible)
        
        # === Platform Contract ===
        print("\n--- Platform Contract ---")
        self.check("Platform execute accepts valid contract", self._check_platform_execute)
        self.check("Platform validate-contract works", self._check_platform_validate)
        self.check("Platform modules listed", self._check_platform_modules)
        self.check("Platform contract spec available", self._check_platform_contract)
        
        # === Trace Propagation ===
        print("\n--- Trace Propagation ---")
        self.check("Trace headers in response", self._check_trace_headers)
        self.check("Schema version in response", self._check_schema_version_header)
        self.check("Execution ID in response", self._check_execution_id_header)
        
        # === Observability ===
        print("\n--- Observability ---")
        self.check("Observability events endpoint", self._check_observability_events)
        self.check("Observability health endpoint", self._check_observability_health)
        self.check("Module stats endpoint", self._check_module_stats)
        
        # === Bucket Validation ===
        print("\n--- Bucket Validation ---")
        self.check("Bucket write-and-verify", self._check_bucket_write_verify)
        self.check("Bucket status endpoint", self._check_bucket_status)
        self.check("Bucket list-artifacts endpoint", self._check_bucket_list)
        
        # === Health Variants ===
        print("\n--- Health Variants ---")
        self.check("Platform health endpoint", self._check_platform_health)
        self.check("Detailed health endpoint", self._check_detailed_health)
        
        # === Backward Compatibility ===
        print("\n--- Backward Compatibility ---")
        self.check("Root endpoint responds", self._check_root)
        self.check("Test endpoint responds", self._check_test)
        
        # === Deterministic Execution ===
        print("\n--- Deterministic Execution ---")
        self.check("Repeated health checks are deterministic", self._check_deterministic)
        
        # === Failure Handling ===
        print("\n--- Failure Handling ---")
        self.check("Invalid endpoint returns 404/405", self._check_404_handling)
        self.check("Invalid method returns proper error", self._check_405_handling)
        
        # === Summary ===
        print("\n" + "=" * 60)
        total = self.passed + self.failed
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        
        if self.failed == 0:
            print("STATUS: ALL CHECKS PASSED — Deployment verified!")
        else:
            print(f"STATUS: {self.failed} CHECKS FAILED — Review required")
        
        print("=" * 60)
        
        # Save results
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_url": self.base_url,
            "total_checks": total,
            "passed": self.passed,
            "failed": self.failed,
            "status": "verified" if self.failed == 0 else "needs_attention",
            "results": self.results
        }
        
        os.makedirs("evidence", exist_ok=True)
        with open("evidence/deployment_verification.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: evidence/deployment_verification.json")
        
        return self.failed == 0
    
    # === Check implementations ===
    
    def _check_env(self, var_name):
        return bool(os.getenv(var_name))
    
    def _check_health(self):
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        return resp.status_code == 200
    
    def _check_health_status(self):
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        return resp.json().get("status") == "healthy"
    
    def _check_login_accessible(self):
        resp = requests.post(f"{self.base_url}/users/login", 
            data={"username": "nonexistent", "password": "test"}, timeout=5)
        return resp.status_code in [401, 422]
    
    def _check_platform_execute(self):
        trace_id = f"verify_{int(time.time())}"
        resp = requests.post(f"{self.base_url}/platform/execute", json={
            "trace_id": trace_id,
            "schema_version": "1.0.0",
            "module": "platform",
            "action": "echo",
            "payload": {"test": True}
        }, timeout=10)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return (data.get("trace_id") == trace_id and 
                data.get("status") in ["success", "error", "partial"] and
                data.get("schema_version") == "1.0.0")
    
    def _check_platform_validate(self):
        resp = requests.post(f"{self.base_url}/platform/validate-contract", json={
            "trace_id": "11111111-1111-1111-1111-111111111111",
            "schema_version": "1.0.0",
            "module": "platform",
            "action": "health"
        }, timeout=5)
        return resp.status_code == 200 and "data" in resp.json()
    
    def _check_platform_modules(self):
        resp = requests.get(f"{self.base_url}/platform/modules", timeout=5)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return "data" in data and "modules" in data["data"]
    
    def _check_platform_contract(self):
        resp = requests.get(f"{self.base_url}/platform/contract", timeout=5)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return data.get("schema_version") == "1.0.0"
    
    def _check_trace_headers(self):
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        return "X-Trace-ID" in resp.headers
    
    def _check_schema_version_header(self):
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        return "X-Schema-Version" in resp.headers
    
    def _check_execution_id_header(self):
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        return "X-Execution-ID" in resp.headers
    
    def _check_observability_events(self):
        resp = requests.get(f"{self.base_url}/observability/events?limit=5", timeout=5)
        return resp.status_code == 200 and "data" in resp.json()
    
    def _check_observability_health(self):
        resp = requests.get(f"{self.base_url}/observability/health", timeout=5)
        return resp.status_code == 200
    
    def _check_module_stats(self):
        resp = requests.get(f"{self.base_url}/observability/stats/modules", timeout=5)
        return resp.status_code == 200 and "data" in resp.json()
    
    def _check_bucket_write_verify(self):
        resp = requests.post(f"{self.base_url}/bucket-validation/write-and-verify", timeout=10)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return (data.get("status") == "success" and 
                data.get("data", {}).get("integrity", {}).get("verified") == True)
    
    def _check_bucket_status(self):
        resp = requests.get(f"{self.base_url}/bucket-validation/status", timeout=5)
        return resp.status_code == 200
    
    def _check_bucket_list(self):
        resp = requests.get(f"{self.base_url}/bucket-validation/list-artifacts", timeout=5)
        return resp.status_code == 200 and "data" in resp.json()
    
    def _check_platform_health(self):
        resp = requests.get(f"{self.base_url}/health/platform", timeout=5)
        return resp.status_code == 200
    
    def _check_detailed_health(self):
        resp = requests.get(f"{self.base_url}/health/detailed", timeout=5)
        return resp.status_code == 200
    
    def _check_root(self):
        resp = requests.get(f"{self.base_url}/", timeout=5)
        return resp.status_code == 200
    
    def _check_test(self):
        resp = requests.get(f"{self.base_url}/test", timeout=5)
        return resp.status_code == 200
    
    def _check_deterministic(self):
        results = []
        for _ in range(3):
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            results.append(resp.json().get("status"))
        return all(r == "healthy" for r in results)
    
    def _check_404_handling(self):
        resp = requests.get(f"{self.base_url}/nonexistent-endpoint-xyz", timeout=5)
        return resp.status_code in [404, 405]
    
    def _check_405_handling(self):
        resp = requests.delete(f"{self.base_url}/health", timeout=5)
        return resp.status_code in [404, 405]


if __name__ == "__main__":
    verifier = DeploymentVerifier(BASE_URL)
    success = verifier.run_all()
    sys.exit(0 if success else 1)
