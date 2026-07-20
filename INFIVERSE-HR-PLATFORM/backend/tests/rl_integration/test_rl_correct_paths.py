#!/usr/bin/env python3
"""
RL Integration Test with Correct Paths
Tests RL endpoints using the correct /api/v1/rl/ prefix
"""
import requests
import json
from datetime import datetime

# Configuration
GATEWAY_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_rl_with_correct_paths():
    """Test RL integration using correct API paths"""
    print("RL Integration Test - Correct Paths")
    print("=" * 50)
    
    results = []
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Test 1: RL Analytics
    print("\n1. Testing RL Analytics...")
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
            results.append(("RL Analytics", True, data))
        else:
            print(f"   [FAIL] RL Analytics failed: {response.text}")
            results.append(("RL Analytics", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Analytics: {e}")
        results.append(("RL Analytics", False, str(e)))
    
    # Test 2: RL Performance
    print("\n2. Testing RL Performance...")
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
            results.append(("RL Performance", True, data))
        else:
            print(f"   [FAIL] RL Performance failed: {response.text}")
            results.append(("RL Performance", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Performance: {e}")
        results.append(("RL Performance", False, str(e)))
    
    # Test 3: RL Prediction with proper data
    print("\n3. Testing RL Prediction...")
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
            results.append(("RL Prediction", True, data))
        else:
            print(f"   [FAIL] RL Prediction failed: {response.text}")
            results.append(("RL Prediction", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Prediction: {e}")
        results.append(("RL Prediction", False, str(e)))
    
    # Test 4: RL Feedback
    print("\n4. Testing RL Feedback...")
    try:
        feedback_data = {
            "candidate_id": 1,
            "job_id": 1,
            "actual_outcome": "hired",
            "feedback_score": 4.5,
            "feedback_source": "hr",
            "feedback_notes": "Excellent technical skills"
        }
        
        response = requests.post(
            f"{GATEWAY_URL}/api/v1/rl/feedback",
            headers=headers,
            json=feedback_data,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] RL Feedback successful")
            print(f"   Response keys: {list(data.keys())}")
            results.append(("RL Feedback", True, data))
        else:
            print(f"   [FAIL] RL Feedback failed: {response.text}")
            results.append(("RL Feedback", False, response.text))
    except Exception as e:
        print(f"   [ERROR] RL Feedback: {e}")
        results.append(("RL Feedback", False, str(e)))
    
    # Summary
    print("\n" + "=" * 50)
    print("RL INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result, _ in results if result is True)
    total = len(results)
    
    for test_name, result, data in results:
        status = "[PASS]" if result is True else "[FAIL]"
        print(f"{test_name:20s}: {status}")
        
        # Show key information for successful tests
        if result is True and isinstance(data, dict):
            if "success" in data:
                print(f"                     Success: {data.get('success')}")
            if "data" in data and isinstance(data["data"], dict):
                inner_data = data["data"]
                if "rl_analytics" in inner_data:
                    analytics = inner_data["rl_analytics"]
                    print(f"                     Predictions: {analytics.get('total_predictions', 0)}")
                    print(f"                     Feedback: {analytics.get('total_feedback', 0)}")
    
    print(f"\nOverall: {passed}/{total} passed")
    success_rate = passed / total * 100 if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Save results
    with open("rl_correct_paths_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
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
    
    print(f"\nResults saved to: rl_correct_paths_results.json")
    
    if success_rate >= 50:
        print("\nRL Integration is FUNCTIONAL with correct paths!")
        return True
    else:
        print("\nRL Integration needs attention.")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = test_rl_with_correct_paths()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exit(0 if success else 1)