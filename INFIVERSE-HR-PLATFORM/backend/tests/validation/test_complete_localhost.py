#!/usr/bin/env python3
"""
Complete Localhost Test Suite
Tests all major endpoints and RL integration on localhost
"""
import requests
import json
import time
from datetime import datetime

# Localhost Configuration
BASE_URLS = {
    "gw": "http://localhost:8000",
    "ag": "http://localhost:9000", 
    "lg": "http://localhost:9001"
}
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

results = []

def test(name, method, url, headers=None, data=None, exp=200):
    """Execute a single test"""
    try:
        start = time.time()
        r = requests.request(method, url, headers=headers, json=data, timeout=30)
        t = time.time() - start
        ok = r.status_code == exp
        results.append({
            "name": name, 
            "ok": ok, 
            "time": f"{t:.2f}s", 
            "code": r.status_code,
            "response": r.json() if r.headers.get('content-type', '').startswith('application/json') else r.text[:200]
        })
        return ok, f"{'PASS' if ok else 'FAIL'} {r.status_code}", t
    except Exception as e:
        results.append({
            "name": name, 
            "ok": False, 
            "time": "ERR", 
            "code": 0,
            "response": str(e)[:200]
        })
        return False, f"FAIL ERR", 0

def run_localhost_tests():
    """Run comprehensive localhost tests"""
    gw, ag, lg = BASE_URLS["gw"], BASE_URLS["ag"], BASE_URLS["lg"]
    auth = {"Authorization": f"Bearer {API_KEY}"}
    
    print("BHIV HR Platform - Complete Localhost Test Suite")
    print("=" * 60)
    print(f"Gateway: {gw}")
    print(f"Agent: {ag}")
    print(f"LangGraph: {lg}")
    print("=" * 60)
    
    tests = [
        # Core Gateway Tests (5)
        ("GW-Root", "GET", f"{gw}/", None, None, 200),
        ("GW-Health", "GET", f"{gw}/health", None, None, 200),
        ("GW-OpenAPI", "GET", f"{gw}/openapi.json", None, None, 200),
        ("GW-Docs", "GET", f"{gw}/docs", None, None, 200),
        ("GW-CandidateStats", "GET", f"{gw}/v1/candidates/stats", auth, None, 200),
        
        # Database & Jobs (3)
        ("GW-ListJobs", "GET", f"{gw}/v1/jobs", auth, None, 200),
        ("GW-ListCandidates", "GET", f"{gw}/v1/candidates", auth, None, 200),
        ("GW-DatabaseSchema", "GET", f"{gw}/v1/analytics/schema", auth, None, 200),
        
        # Authentication Tests (4)
        ("GW-ClientLogin", "POST", f"{gw}/v1/client/login", None, {"client_id": "TECH001", "password": "demo123"}, 200),
        ("GW-2FASetup", "POST", f"{gw}/v1/auth/2fa/setup", auth, {"user_id": "test_user"}, 200),
        ("GW-PasswordValidate", "POST", f"{gw}/v1/password/validate", None, {"password": "Test123!"}, 200),
        ("GW-SecurityRateLimit", "GET", f"{gw}/v1/security/rate-limit-status", auth, None, 200),
        
        # AI Matching (2)
        ("GW-TopMatches", "GET", f"{gw}/v1/match/1/top", auth, None, 200),
        ("GW-BatchMatch", "POST", f"{gw}/v1/match/batch", auth, {"job_ids": [1, 2]}, 200),
        
        # RL Integration Tests (4) - Using correct /api/v1/rl/ prefix
        ("GW-RLAnalytics", "GET", f"{gw}/api/v1/rl/analytics", auth, None, 200),
        ("GW-RLPerformance", "GET", f"{gw}/api/v1/rl/performance", auth, None, 200),
        ("GW-RLPredict", "POST", f"{gw}/api/v1/rl/predict", auth, {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_features": {
                "skills": ["Python", "FastAPI"],
                "experience_years": 5,
                "education_level": "Bachelor's",
                "seniority_level": "Senior"
            },
            "job_features": {
                "requirements": ["Python", "API Development"],
                "experience_level": "Senior",
                "title": "Senior Developer"
            }
        }, 200),
        ("GW-RLFeedback", "POST", f"{gw}/api/v1/rl/feedback", auth, {
            "candidate_id": 1,
            "job_id": 1,
            "actual_outcome": "hired",
            "feedback_score": 4.5,
            "feedback_source": "hr"
        }, 200),
        
        # Agent Service Tests (3)
        ("AG-Root", "GET", f"{ag}/", None, None, 200),
        ("AG-Health", "GET", f"{ag}/health", None, None, 200),
        ("AG-Match", "POST", f"{ag}/match", None, {"job_id": 1}, 200),
        
        # LangGraph Service Tests (5)
        ("LG-Root", "GET", f"{lg}/", None, None, 200),
        ("LG-Health", "GET", f"{lg}/health", None, None, 200),
        ("LG-RLAnalytics", "GET", f"{lg}/rl/analytics", None, None, 200),
        ("LG-RLHistory", "GET", f"{lg}/rl/history/1", None, None, 200),
        ("LG-RLRetrain", "POST", f"{lg}/rl/retrain", None, None, 200),
        
        # Workflow Tests (2)
        ("GW-WorkflowStatus", "GET", f"{gw}/api/v1/workflow/status/test", auth, None, 200),
        ("LG-WorkflowStats", "GET", f"{lg}/workflows/stats", None, None, 200),
    ]
    
    print(f"\nRunning {len(tests)} tests...\n")
    
    for i, (name, method, url, headers, data, exp) in enumerate(tests, 1):
        ok, msg, t = test(name, method, url, headers, data, exp)
        status_icon = "✅" if ok else "❌"
        print(f"{i:2d}. {status_icon} {msg} {name:25s} ({t:.2f}s)")
        time.sleep(0.1)  # Small delay between tests
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed
    
    print(f"\n{'='*60}")
    print(f"LOCALHOST TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    # Show failed tests
    if failed > 0:
        print(f"\nFailed Tests:")
        for r in results:
            if not r["ok"]:
                print(f"❌ {r['name']} - HTTP {r['code']} - {r['response'][:100]}")
    
    # Show RL-specific results
    rl_tests = [r for r in results if "RL" in r["name"]]
    if rl_tests:
        rl_passed = sum(1 for r in rl_tests if r["ok"])
        print(f"\nRL Integration Results:")
        print(f"RL Tests: {len(rl_tests)}")
        print(f"RL Passed: {rl_passed}")
        print(f"RL Success Rate: {rl_passed/len(rl_tests)*100:.1f}%")
        
        for r in rl_tests:
            status = "✅" if r["ok"] else "❌"
            print(f"{status} {r['name']} - HTTP {r['code']}")
    
    # Save detailed results
    with open("localhost_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "environment": "localhost",
            "base_urls": BASE_URLS,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "success_rate": passed/total*100,
            "rl_tests": len(rl_tests),
            "rl_passed": rl_passed if rl_tests else 0,
            "rl_success_rate": rl_passed/len(rl_tests)*100 if rl_tests else 0,
            "results": results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: localhost_test_results.json")
    
    # Final assessment
    if passed/total >= 0.7:  # 70% success rate
        print(f"\n🎉 LOCALHOST SYSTEM IS READY FOR DEVELOPMENT!")
        if rl_tests and rl_passed/len(rl_tests) >= 0.5:
            print(f"🤖 RL INTEGRATION IS FUNCTIONAL!")
        return True
    else:
        print(f"\n⚠️  LOCALHOST SYSTEM NEEDS ATTENTION")
        print(f"   - Start missing services")
        print(f"   - Check database connection")
        print(f"   - Verify environment configuration")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nPrerequisites:")
    print("1. Gateway service running on localhost:8000")
    print("2. Agent service running on localhost:9000") 
    print("3. LangGraph service running on localhost:9001")
    print("4. PostgreSQL database accessible")
    print("5. Environment variables configured")
    print()
    
    success = run_localhost_tests()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exit(0 if success else 1)