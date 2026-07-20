#!/usr/bin/env python3
"""
Final RL Integration Test - Correct Paths
"""
import requests
import json
from datetime import datetime

GATEWAY_URL = "http://localhost:8000"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_rl_final():
    """Test RL with correct paths"""
    print("RL Integration Test - Final Validation")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    results = []
    
    # Test 1: RL Analytics
    print("\n1. RL Analytics...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/rl/analytics", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("   [PASS] RL Analytics working")
            print(f"   Response: {json.dumps(data, indent=2)}")
            results.append(("RL Analytics", True))
        else:
            print(f"   [FAIL] Status: {response.status_code}")
            print(f"   Response: {response.text}")
            results.append(("RL Analytics", False))
    except Exception as e:
        print(f"   [ERROR] {e}")
        results.append(("RL Analytics", False))
    
    # Test 2: RL Performance
    print("\n2. RL Performance...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/rl/performance", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("   [PASS] RL Performance working")
            print(f"   Response: {json.dumps(data, indent=2)}")
            results.append(("RL Performance", True))
        else:
            print(f"   [FAIL] Status: {response.status_code}")
            results.append(("RL Performance", False))
    except Exception as e:
        print(f"   [ERROR] {e}")
        results.append(("RL Performance", False))
    
    # Test 3: RL Prediction
    print("\n3. RL Prediction...")
    try:
        prediction_data = {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_features": {
                "skills": ["Python", "FastAPI"],
                "experience_years": 5
            },
            "job_features": {
                "requirements": ["Python"],
                "title": "Developer"
            }
        }
        
        response = requests.post(
            f"{GATEWAY_URL}/v1/rl/predict", 
            headers=headers, 
            json=prediction_data, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   [PASS] RL Prediction working")
            print(f"   Response: {json.dumps(data, indent=2)}")
            results.append(("RL Prediction", True))
        else:
            print(f"   [FAIL] Status: {response.status_code}")
            print(f"   Response: {response.text}")
            results.append(("RL Prediction", False))
    except Exception as e:
        print(f"   [ERROR] {e}")
        results.append(("RL Prediction", False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"RL INTEGRATION RESULTS: {passed}/{total} passed")
    print(f"{'='*50}")
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:20s}: [{status}]")
    
    return passed >= 2

if __name__ == "__main__":
    success = test_rl_final()
    if success:
        print("\nRL Integration is FUNCTIONAL!")
    else:
        print("\nRL Integration needs attention.")