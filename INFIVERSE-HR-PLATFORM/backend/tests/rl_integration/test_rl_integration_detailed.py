#!/usr/bin/env python3
"""
BHIV HR Platform - Detailed RL Integration Test
Tests RL endpoints with proper input validation and comprehensive scenarios
"""
import requests
import json
import os
from datetime import datetime

# Configuration
GATEWAY_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_rl_integration_detailed():
    """Test RL integration with detailed scenarios and proper validation"""
    print("BHIV HR Platform - Detailed RL Integration Test")
    print("=" * 70)
    
    results = []
    
    # Test 1: RL Analytics (Gateway)
    print("\n1. Testing RL Analytics via Gateway...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/rl/analytics",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] RL Analytics - Status: {response.status_code}")
            print(f"       Data keys: {list(data.keys())}")
            results.append(("GW RL Analytics", True, data))
        else:
            print(f"[FAIL] RL Analytics - Status: {response.status_code}")
            results.append(("GW RL Analytics", False, response.text))
    except Exception as e:
        print(f"[ERROR] RL Analytics - {e}")
        results.append(("GW RL Analytics", False, str(e)))
    
    # Test 2: RL Performance (Gateway)
    print("\n2. Testing RL Performance via Gateway...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/rl/performance",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] RL Performance - Status: {response.status_code}")
            print(f"       Data keys: {list(data.keys())}")
            results.append(("GW RL Performance", True, data))
        else:
            print(f"[FAIL] RL Performance - Status: {response.status_code}")
            results.append(("GW RL Performance", False, response.text))
    except Exception as e:
        print(f"[ERROR] RL Performance - {e}")
        results.append(("GW RL Performance", False, str(e)))
    
    # Test 3: RL Prediction with proper data (Gateway)
    print("\n3. Testing RL Prediction with proper data via Gateway...")
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
            f"{GATEWAY_URL}/v1/rl/predict",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=prediction_data,
            timeout=30
        )
        
        print(f"       Request data: {json.dumps(prediction_data, indent=2)}")
        print(f"       Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] RL Prediction - Status: {response.status_code}")
            print(f"       Response keys: {list(data.keys())}")
            results.append(("GW RL Prediction", True, data))
        else:
            print(f"[FAIL] RL Prediction - Status: {response.status_code}")
            print(f"       Response: {response.text}")
            results.append(("GW RL Prediction", False, response.text))
    except Exception as e:
        print(f"[ERROR] RL Prediction - {e}")
        results.append(("GW RL Prediction", False, str(e)))
    
    # Test 4: RL Feedback with proper data (Gateway)
    print("\n4. Testing RL Feedback with proper data via Gateway...")
    try:
        feedback_data = {
            "candidate_id": 1,
            "job_id": 1,
            "actual_outcome": "hired",
            "feedback_score": 4.5,
            "feedback_source": "hr",
            "feedback_notes": "Excellent technical skills and cultural fit"
        }
        
        response = requests.post(
            f"{GATEWAY_URL}/v1/rl/feedback",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=feedback_data,
            timeout=30
        )
        
        print(f"       Request data: {json.dumps(feedback_data, indent=2)}")
        print(f"       Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] RL Feedback - Status: {response.status_code}")
            print(f"       Response keys: {list(data.keys())}")
            results.append(("GW RL Feedback", True, data))
        else:
            print(f"[FAIL] RL Feedback - Status: {response.status_code}")
            print(f"       Response: {response.text}")
            results.append(("GW RL Feedback", False, response.text))
    except Exception as e:
        print(f"[ERROR] RL Feedback - {e}")
        results.append(("GW RL Feedback", False, str(e)))
    
    # Test 5: Direct LangGraph RL Analytics
    print("\n5. Testing Direct LangGraph RL Analytics...")
    try:
        response = requests.get(
            f"{LANGGRAPH_URL}/rl/analytics",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] LG RL Analytics - Status: {response.status_code}")
            print(f"       Data keys: {list(data.keys())}")
            results.append(("LG RL Analytics", True, data))
        else:
            print(f"[FAIL] LG RL Analytics - Status: {response.status_code}")
            results.append(("LG RL Analytics", False, response.text))
    except Exception as e:
        print(f"[ERROR] LG RL Analytics - {e}")
        results.append(("LG RL Analytics", False, str(e)))
    
    # Test 6: Direct LangGraph RL History
    print("\n6. Testing Direct LangGraph RL History...")
    try:
        response = requests.get(
            f"{LANGGRAPH_URL}/rl/history/1",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] LG RL History - Status: {response.status_code}")
            print(f"       Data keys: {list(data.keys())}")
            results.append(("LG RL History", True, data))
        else:
            print(f"[FAIL] LG RL History - Status: {response.status_code}")
            results.append(("LG RL History", False, response.text))
    except Exception as e:
        print(f"[ERROR] LG RL History - {e}")
        results.append(("LG RL History", False, str(e)))
    
    # Test 7: Direct LangGraph RL Retrain
    print("\n7. Testing Direct LangGraph RL Retrain...")
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/rl/retrain",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] LG RL Retrain - Status: {response.status_code}")
            print(f"       Data keys: {list(data.keys())}")
            results.append(("LG RL Retrain", True, data))
        else:
            print(f"[FAIL] LG RL Retrain - Status: {response.status_code}")
            results.append(("LG RL Retrain", False, response.text))
    except Exception as e:
        print(f"[ERROR] LG RL Retrain - {e}")
        results.append(("LG RL Retrain", False, str(e)))
    
    # Test 8: Direct LangGraph RL Prediction with proper data
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
        
        print(f"       Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] LG RL Prediction - Status: {response.status_code}")
            print(f"       Response keys: {list(data.keys())}")
            results.append(("LG RL Prediction", True, data))
        else:
            print(f"[FAIL] LG RL Prediction - Status: {response.status_code}")
            print(f"       Response: {response.text}")
            results.append(("LG RL Prediction", False, response.text))
    except Exception as e:
        print(f"[ERROR] LG RL Prediction - {e}")
        results.append(("LG RL Prediction", False, str(e)))
    
    # Test 9: Database Schema Check for RL Tables
    print("\n9. Testing Database Schema for RL Tables...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/analytics/schema",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            rl_tables = [table for table in data.get("tables", []) if "rl_" in table.get("name", "")]
            print(f"[PASS] Database Schema - Status: {response.status_code}")
            print(f"       RL Tables found: {len(rl_tables)}")
            for table in rl_tables:
                print(f"       - {table.get('name', 'unknown')}")
            results.append(("Database RL Schema", True, {"rl_tables": len(rl_tables)}))
        else:
            print(f"[FAIL] Database Schema - Status: {response.status_code}")
            results.append(("Database RL Schema", False, response.text))
    except Exception as e:
        print(f"[ERROR] Database Schema - {e}")
        results.append(("Database RL Schema", False, str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print("DETAILED RL INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result, _ in results if result is True)
    total = len(results)
    
    for test_name, result, data in results:
        status = "[PASS]" if result is True else "[FAIL]"
        print(f"{test_name:25s}: {status}")
        if result is True and isinstance(data, dict):
            # Show key metrics for successful tests
            if "success" in data:
                print(f"                          Success: {data.get('success')}")
            if "data" in data and isinstance(data["data"], dict):
                inner_data = data["data"]
                if "rl_analytics" in inner_data:
                    analytics = inner_data["rl_analytics"]
                    print(f"                          Predictions: {analytics.get('total_predictions', 0)}")
                    print(f"                          Feedback: {analytics.get('total_feedback', 0)}")
                if "rl_prediction" in inner_data:
                    prediction = inner_data["rl_prediction"]
                    print(f"                          RL Score: {prediction.get('rl_score', 0)}")
                    print(f"                          Decision: {prediction.get('decision_type', 'unknown')}")
    
    print(f"\nOverall: {passed}/{total} passed")
    success_rate = passed / total * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Save detailed results
    with open("rl_integration_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "detailed_results": [
                {
                    "test_name": name,
                    "passed": result,
                    "data": data if isinstance(data, dict) else str(data)
                }
                for name, result, data in results
            ]
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: rl_integration_test_results.json")
    
    if success_rate >= 60:
        print("\nRL Integration is FUNCTIONAL and ready for automation sprint!")
        return True
    else:
        print("\nRL Integration needs attention before automation sprint.")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = test_rl_integration_detailed()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exit(0 if success else 1)