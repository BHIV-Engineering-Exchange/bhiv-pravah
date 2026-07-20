#!/usr/bin/env python3
"""
RL Integration Test Suite
Tests the complete RL integration in LangGraph service
"""

import requests
import json
import time
from datetime import datetime

# Configuration
LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def print_test(name, status, details=""):
    symbol = "PASS" if status == "PASS" else "FAIL"
    print(f"[{symbol}] {name}: {status}")
    if details:
        print(f"   {details}")

def test_rl_predict():
    """Test RL prediction endpoint"""
    print("\nTesting RL Prediction...")
    
    payload = {
        "candidate_id": 1,
        "job_id": 1,
        "candidate_features": {
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "experience_years": 5,
            "education_level": "Bachelor",
            "seniority_level": "Senior"
        },
        "job_features": {
            "requirements": ["Python", "FastAPI", "Docker"],
            "experience_required": 5,
            "department": "Engineering"
        }
    }
    
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/rl/predict",
            headers=HEADERS,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                rl_data = data.get("data", {}).get("rl_prediction", {})
                print_test(
                    "RL Predict",
                    "PASS",
                    f"Score: {rl_data.get('rl_score')}, Decision: {rl_data.get('decision_type')}, Confidence: {rl_data.get('confidence_level')}"
                )
                return True, data
            else:
                print_test("RL Predict", "FAIL", f"Success=False: {data}")
                return False, None
        else:
            print_test("RL Predict", "FAIL", f"Status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test("RL Predict", "FAIL", str(e))
        return False, None

def test_rl_feedback(prediction_id=None):
    """Test RL feedback submission"""
    print("\nTesting RL Feedback...")
    
    payload = {
        "prediction_id": prediction_id,
        "candidate_id": 1,
        "job_id": 1,
        "actual_outcome": "hired",
        "feedback_score": 4.5,
        "feedback_source": "hr",
        "feedback_notes": "Excellent candidate, strong technical skills"
    }
    
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/rl/feedback",
            headers=HEADERS,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                feedback_data = data.get("data", {})
                print_test(
                    "RL Feedback",
                    "PASS",
                    f"Feedback ID: {feedback_data.get('feedback_id')}, Reward: {feedback_data.get('reward_signal')}"
                )
                return True, data
            else:
                print_test("RL Feedback", "FAIL", f"Success=False: {data}")
                return False, None
        else:
            print_test("RL Feedback", "FAIL", f"Status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test("RL Feedback", "FAIL", str(e))
        return False, None

def test_rl_analytics():
    """Test RL analytics endpoint"""
    print("\nTesting RL Analytics...")
    
    try:
        response = requests.get(
            f"{LANGGRAPH_URL}/rl/analytics",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                analytics = data.get("data", {}).get("rl_analytics", {})
                print_test(
                    "RL Analytics",
                    "PASS",
                    f"Predictions: {analytics.get('total_predictions')}, Feedback: {analytics.get('total_feedback')}, Rate: {analytics.get('feedback_rate', 0):.1f}%"
                )
                return True, data
            else:
                print_test("RL Analytics", "FAIL", f"Success=False: {data}")
                return False, None
        else:
            print_test("RL Analytics", "FAIL", f"Status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test("RL Analytics", "FAIL", str(e))
        return False, None

def test_rl_performance():
    """Test RL performance endpoint"""
    print("\nTesting RL Performance...")
    
    try:
        response = requests.get(
            f"{LANGGRAPH_URL}/rl/performance/v1.0.0",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                perf_data = data.get("data", {})
                print_test(
                    "RL Performance",
                    "PASS",
                    f"Model: {perf_data.get('model_version')}, Status: {perf_data.get('status')}"
                )
                return True, data
            else:
                print_test("RL Performance", "FAIL", f"Success=False: {data}")
                return False, None
        else:
            print_test("RL Performance", "FAIL", f"Status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test("RL Performance", "FAIL", str(e))
        return False, None

def test_rl_history():
    """Test RL history endpoint"""
    print("\nTesting RL History...")
    
    try:
        response = requests.get(
            f"{LANGGRAPH_URL}/rl/history/1",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                history_data = data.get("data", {})
                print_test(
                    "RL History",
                    "PASS",
                    f"Candidate: {history_data.get('candidate_id')}, Decisions: {history_data.get('total_decisions')}"
                )
                return True, data
            else:
                print_test("RL History", "FAIL", f"Success=False: {data}")
                return False, None
        else:
            print_test("RL History", "FAIL", f"Status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test("RL History", "FAIL", str(e))
        return False, None

def test_rl_retrain():
    """Test RL retrain endpoint"""
    print("\nTesting RL Retrain...")
    
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/rl/retrain",
            headers=HEADERS,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                retrain_data = data.get("data", {})
                print_test(
                    "RL Retrain",
                    "PASS",
                    f"New Model: {retrain_data.get('new_model_version')}, Samples: {retrain_data.get('training_samples')}, Accuracy: {retrain_data.get('accuracy')}%"
                )
                return True, data
            else:
                print_test("RL Retrain", "FAIL", f"Success=False: {data.get('message')}")
                return False, None
        else:
            print_test("RL Retrain", "FAIL", f"Status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print_test("RL Retrain", "FAIL", str(e))
        return False, None

def test_service_health():
    """Test LangGraph service health"""
    print("\nTesting Service Health...")
    
    try:
        response = requests.get(f"{LANGGRAPH_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_test(
                "Service Health",
                "PASS",
                f"Service: {data.get('service')}, Version: {data.get('version')}"
            )
            return True
        else:
            print_test("Service Health", "FAIL", f"Status {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Service Health", "FAIL", str(e))
        return False

def test_integration():
    """Test integration endpoint"""
    print("\nTesting Integration...")
    
    try:
        response = requests.get(
            f"{LANGGRAPH_URL}/test-integration",
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_test(
                "Integration Test",
                "PASS",
                f"RL Engine: {data.get('rl_engine')}, RL DB: {data.get('rl_database')}"
            )
            return True
        else:
            print_test("Integration Test", "FAIL", f"Status {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Integration Test", "FAIL", str(e))
        return False

def run_complete_test_suite():
    """Run complete RL integration test suite"""
    print("\n" + "="*60)
    print("RL INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Target: {LANGGRAPH_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Service Health
    results.append(("Service Health", test_service_health()))
    time.sleep(0.5)
    
    # Test 2: Integration
    results.append(("Integration", test_integration()))
    time.sleep(0.5)
    
    # Test 3: RL Predict
    predict_success, predict_data = test_rl_predict()
    results.append(("RL Predict", predict_success))
    prediction_id = None
    if predict_success and predict_data:
        prediction_id = predict_data.get("data", {}).get("prediction_id")
    time.sleep(0.5)
    
    # Test 4: RL Feedback
    feedback_success, _ = test_rl_feedback(prediction_id)
    results.append(("RL Feedback", feedback_success))
    time.sleep(0.5)
    
    # Test 5: RL Analytics
    analytics_success, _ = test_rl_analytics()
    results.append(("RL Analytics", analytics_success))
    time.sleep(0.5)
    
    # Test 6: RL Performance
    perf_success, _ = test_rl_performance()
    results.append(("RL Performance", perf_success))
    time.sleep(0.5)
    
    # Test 7: RL History
    history_success, _ = test_rl_history()
    results.append(("RL History", history_success))
    time.sleep(0.5)
    
    # Test 8: RL Retrain
    retrain_success, _ = test_rl_retrain()
    results.append(("RL Retrain", retrain_success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\nFailed Tests:")
        for name, success in results:
            if not success:
                print(f"  - {name}")
    
    print("\n" + "="*60)
    
    if passed_tests == total_tests:
        print("ALL TESTS PASSED - RL INTEGRATION VERIFIED")
        return True
    else:
        print("SOME TESTS FAILED - CHECK IMPLEMENTATION")
        return False

if __name__ == "__main__":
    success = run_complete_test_suite()
    exit(0 if success else 1)
