#!/usr/bin/env python3
"""
RL Integration Test - Localhost Version
Tests RL endpoints on local development environment
"""
import requests
import json
from datetime import datetime

# Localhost Configuration
GATEWAY_URL = "http://localhost:8000"
LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_rl_localhost():
    """Test RL integration on localhost"""
    print("RL Integration Test - Localhost Environment")
    print("=" * 60)
    
    results = []
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Test 1: Check Gateway Health
    print("\n1. Testing Gateway Health...")
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"   [PASS] Gateway is running: {response.status_code}")
            data = response.json()
            print(f"   Gateway version: {data.get('version', 'unknown')}")
        else:
            print(f"   [FAIL] Gateway health check failed: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Gateway not accessible: {e}")
        print("   Make sure the gateway service is running on localhost:8000")
        return False
    
    # Test 2: Check LangGraph Health
    print("\n2. Testing LangGraph Health...")
    try:
        response = requests.get(f"{LANGGRAPH_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"   [PASS] LangGraph is running: {response.status_code}")
        else:
            print(f"   [FAIL] LangGraph health check failed: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] LangGraph not accessible: {e}")
        print("   Make sure the langgraph service is running on localhost:9001")
    
    # Test 3: Check RL Routes in OpenAPI
    print("\n3. Checking RL Routes in OpenAPI Schema...")
    try:
        response = requests.get(f"{GATEWAY_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            rl_paths = [path for path in paths.keys() if "/rl/" in path]
            
            print(f"   Found {len(rl_paths)} RL paths:")
            for path in rl_paths:
                print(f"   - {path}")
            
            if rl_paths:
                print(f"   [PASS] RL routes are registered")
                results.append(("RL Routes Registration", True, {"paths": rl_paths}))
            else:
                print(f"   [FAIL] No RL routes found")
                results.append(("RL Routes Registration", False, "No RL routes"))
        else:
            print(f"   [FAIL] Could not fetch OpenAPI schema: {response.status_code}")
            results.append(("RL Routes Registration", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   [ERROR] OpenAPI check failed: {e}")
        results.append(("RL Routes Registration", False, str(e)))
    
    # Test 4: RL Analytics (Gateway Proxy)
    print("\n4. Testing RL Analytics via Gateway...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/api/v1/rl/analytics",
            headers=headers,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] RL Analytics successful")
            print(f"   Response keys: {list(data.keys())}")
            results.append(("Gateway RL Analytics", True, data))
        else:
            print(f"   [FAIL] RL Analytics failed")
            print(f"   Response: {response.text}")
            results.append(("Gateway RL Analytics", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Analytics: {e}")
        results.append(("Gateway RL Analytics", False, str(e)))
    
    # Test 5: RL Performance (Gateway Proxy)
    print("\n5. Testing RL Performance via Gateway...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/api/v1/rl/performance",
            headers=headers,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] RL Performance successful")
            print(f"   Response keys: {list(data.keys())}")
            results.append(("Gateway RL Performance", True, data))
        else:
            print(f"   [FAIL] RL Performance failed")
            print(f"   Response: {response.text}")
            results.append(("Gateway RL Performance", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Performance: {e}")
        results.append(("Gateway RL Performance", False, str(e)))
    
    # Test 6: Direct LangGraph RL Analytics
    print("\n6. Testing Direct LangGraph RL Analytics...")
    try:
        response = requests.get(f"{LANGGRAPH_URL}/rl/analytics", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] Direct LangGraph RL Analytics successful")
            print(f"   Response keys: {list(data.keys())}")
            results.append(("Direct LangGraph Analytics", True, data))
        else:
            print(f"   [FAIL] Direct LangGraph RL Analytics failed")
            print(f"   Response: {response.text}")
            results.append(("Direct LangGraph Analytics", False, response.text))
    except Exception as e:
        print(f"   [ERROR] Direct LangGraph RL Analytics: {e}")
        results.append(("Direct LangGraph Analytics", False, str(e)))
    
    # Test 7: RL Prediction with proper data (Gateway)
    print("\n7. Testing RL Prediction via Gateway...")
    try:
        prediction_data = {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_features": {
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "experience_years": 5,
                "education_level": "Bachelor's",
                "seniority_level": "Senior"
            },
            "job_features": {
                "requirements": ["Python", "API Development", "Database"],
                "experience_level": "Senior",
                "title": "Senior Python Developer"
            }
        }
        
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/rl/predict",
            headers=headers,
            json=prediction_data,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] RL Prediction successful")
            print(f"   Response keys: {list(data.keys())}")
            results.append(("Gateway RL Prediction", True, data))
        else:
            print(f"   [FAIL] RL Prediction failed")
            print(f"   Response: {response.text}")
            results.append(("Gateway RL Prediction", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Prediction: {e}")
        results.append(("Gateway RL Prediction", False, str(e)))
    
    # Test 8: Direct LangGraph RL Prediction
    print("\n8. Testing Direct LangGraph RL Prediction...")
    try:
        prediction_data = {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_features": {
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "experience_years": 5,
                "education_level": "Bachelor's",
                "seniority_level": "Senior"
            },
            "job_features": {
                "requirements": ["Python", "API Development", "Database"],
                "experience_level": "Senior",
                "title": "Senior Python Developer"
            }
        }
        
        response = requests.post(
            f"{LANGGRAPH_URL}/rl/predict",
            json=prediction_data,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] Direct LangGraph RL Prediction successful")
            print(f"   Response keys: {list(data.keys())}")
            results.append(("Direct LangGraph Prediction", True, data))
        else:
            print(f"   [FAIL] Direct LangGraph RL Prediction failed")
            print(f"   Response: {response.text}")
            results.append(("Direct LangGraph Prediction", False, response.text))
    except Exception as e:
        print(f"   [ERROR] Direct LangGraph RL Prediction: {e}")
        results.append(("Direct LangGraph Prediction", False, str(e)))
    
    # Test 9: Database Connection Test
    print("\n9. Testing Database Connection...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/candidates/stats",
            headers=headers,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] Database connection successful")
            print(f"   Total candidates: {data.get('total_candidates', 0)}")
            print(f"   Active jobs: {data.get('active_jobs', 0)}")
            results.append(("Database Connection", True, data))
        else:
            print(f"   [FAIL] Database connection failed")
            results.append(("Database Connection", False, response.text))
    except Exception as e:
        print(f"   [ERROR] Database connection: {e}")
        results.append(("Database Connection", False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("LOCALHOST RL INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result, _ in results if result is True)
    total = len(results)
    
    for test_name, result, data in results:
        status = "[PASS]" if result is True else "[FAIL]"
        print(f"{test_name:30s}: {status}")
        
        # Show key information for successful tests
        if result is True and isinstance(data, dict):
            if "success" in data:
                print(f"                               Success: {data.get('success')}")
            if "data" in data and isinstance(data["data"], dict):
                inner_data = data["data"]
                if "rl_analytics" in inner_data:
                    analytics = inner_data["rl_analytics"]
                    print(f"                               Predictions: {analytics.get('total_predictions', 0)}")
                    print(f"                               Feedback: {analytics.get('total_feedback', 0)}")
                if "rl_prediction" in inner_data:
                    prediction = inner_data["rl_prediction"]
                    print(f"                               RL Score: {prediction.get('rl_score', 0)}")
                    print(f"                               Decision: {prediction.get('decision_type', 'unknown')}")
    
    print(f"\nOverall: {passed}/{total} passed")
    success_rate = passed / total * 100 if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Save results
    with open("rl_localhost_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "environment": "localhost",
            "gateway_url": GATEWAY_URL,
            "langgraph_url": LANGGRAPH_URL,
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "results": [
                {
                    "test_name": name,
                    "passed": result,
                    "data": data if isinstance(data, dict) else str(data)
                }
                for name, result, data in results
            ]
        }, f, indent=2)
    
    print(f"\nResults saved to: rl_localhost_results.json")
    
    if success_rate >= 60:
        print("\nRL Integration is FUNCTIONAL on localhost!")
        return True
    else:
        print("\nRL Integration needs attention on localhost.")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Make sure the following services are running:")
    print("- Gateway: http://localhost:8000")
    print("- LangGraph: http://localhost:9001")
    print("- Database: PostgreSQL connection available")
    print()
    
    success = test_rl_localhost()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exit(0 if success else 1)