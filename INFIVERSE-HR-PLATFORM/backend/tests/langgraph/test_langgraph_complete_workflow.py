#!/usr/bin/env python3
"""
Complete LangGraph Workflow Implementation Test
Tests actual workflow creation -> status -> resume flow
"""

import requests
import json
import time
from datetime import datetime

# Configuration
LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "<YOUR_API_KEY>"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def test_complete_workflow():
    """Test complete workflow implementation"""
    print("LangGraph Complete Workflow Implementation Test")
    print("=" * 60)
    print(f"Service URL: {LANGGRAPH_URL}")
    print(f"API Key: {API_KEY}")
    print()
    
    # Step 1: Create workflow
    print("[STEP 1] Creating workflow...")
    workflow_payload = {
        "candidate_id": 1,
        "job_id": 1,
        "application_id": 1,
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "candidate_name": "Test Candidate",
        "job_title": "Software Engineer",
        "job_description": "Test job description"
    }
    
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/workflows/application/start",
            json=workflow_payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            workflow_data = response.json()
            workflow_id = workflow_data.get('workflow_id')
            print(f"[SUCCESS] Workflow created: {workflow_id}")
            print(f"Status: {workflow_data.get('status')}")
            print(f"Message: {workflow_data.get('message')}")
        else:
            print(f"[FAIL] Workflow creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Workflow creation error: {e}")
        return False
    
    # Step 2: Wait for workflow to process
    print(f"\n[STEP 2] Waiting 3 seconds for workflow processing...")
    time.sleep(3)
    
    # Step 3: Check workflow status
    print(f"[STEP 3] Checking workflow status...")
    try:
        status_response = requests.get(
            f"{LANGGRAPH_URL}/workflows/{workflow_id}/status",
            headers=HEADERS,
            timeout=10
        )
        
        print(f"Status Code: {status_response.status_code}")
        print(f"Response: {status_response.text}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"[SUCCESS] Workflow Status Retrieved:")
            print(f"  Workflow ID: {status_data.get('workflow_id')}")
            print(f"  Current Stage: {status_data.get('current_stage')}")
            print(f"  Application Status: {status_data.get('application_status')}")
            print(f"  Matching Score: {status_data.get('matching_score')}")
            print(f"  Last Action: {status_data.get('last_action')}")
            print(f"  Completed: {status_data.get('completed')}")
        else:
            print(f"[FAIL] Status check failed: {status_response.status_code}")
            print(f"Error: {status_response.text}")
            
    except Exception as e:
        print(f"[ERROR] Status check error: {e}")
    
    # Step 4: Test resume workflow
    print(f"\n[STEP 4] Testing workflow resume...")
    try:
        resume_response = requests.post(
            f"{LANGGRAPH_URL}/workflows/{workflow_id}/resume",
            headers=HEADERS,
            timeout=10
        )
        
        print(f"Resume Code: {resume_response.status_code}")
        print(f"Resume Response: {resume_response.text}")
        
        if resume_response.status_code == 200:
            resume_data = resume_response.json()
            print(f"[SUCCESS] Workflow Resumed:")
            print(f"  Status: {resume_data.get('status')}")
        else:
            print(f"[FAIL] Resume failed: {resume_response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Resume error: {e}")
    
    # Step 5: Test other endpoints with same workflow context
    print(f"\n[STEP 5] Testing notification with workflow context...")
    notification_payload = {
        "candidate_name": "Test Candidate",
        "job_title": "Software Engineer",
        "message": f"Workflow {workflow_id} notification test",
        "channels": ["email"]
    }
    
    try:
        notify_response = requests.post(
            f"{LANGGRAPH_URL}/tools/send-notification",
            json=notification_payload,
            headers=HEADERS,
            timeout=10
        )
        
        if notify_response.status_code == 200:
            notify_data = notify_response.json()
            print(f"[SUCCESS] Notification sent:")
            print(f"  Success: {notify_data.get('success')}")
            print(f"  Message: {notify_data.get('message')}")
            print(f"  Channels: {notify_data.get('channels_sent')}")
        else:
            print(f"[FAIL] Notification failed: {notify_response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Notification error: {e}")
    
    # Step 6: Test workflows list
    print(f"\n[STEP 6] Testing workflows list...")
    try:
        list_response = requests.get(
            f"{LANGGRAPH_URL}/workflows",
            headers=HEADERS,
            timeout=10
        )
        
        if list_response.status_code == 200:
            list_data = list_response.json()
            print(f"[SUCCESS] Workflows list:")
            print(f"  Count: {list_data.get('count')}")
            print(f"  Status: {list_data.get('status')}")
        else:
            print(f"[FAIL] List failed: {list_response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] List error: {e}")
    
    # Step 7: Test integration
    print(f"\n[STEP 7] Testing integration endpoint...")
    try:
        integration_response = requests.get(
            f"{LANGGRAPH_URL}/test-integration",
            headers=HEADERS,
            timeout=10
        )
        
        if integration_response.status_code == 200:
            integration_data = integration_response.json()
            print(f"[SUCCESS] Integration test:")
            print(f"  Service: {integration_data.get('service')}")
            print(f"  Status: {integration_data.get('status')}")
            print(f"  Test Result: {integration_data.get('integration_test')}")
        else:
            print(f"[FAIL] Integration failed: {integration_response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Integration error: {e}")
    
    print(f"\n" + "=" * 60)
    print("COMPLETE WORKFLOW TEST FINISHED")
    print(f"Workflow ID used throughout: {workflow_id}")
    print("Check above results for endpoint functionality")
    
    return workflow_id

def test_health_endpoints():
    """Test basic health endpoints"""
    print(f"\n[HEALTH] Testing basic endpoints...")
    
    # Root endpoint
    try:
        root_response = requests.get(f"{LANGGRAPH_URL}/", timeout=5)
        if root_response.status_code == 200:
            root_data = root_response.json()
            print(f"[SUCCESS] Root: {root_data.get('message')}")
        else:
            print(f"[FAIL] Root failed: {root_response.status_code}")
    except Exception as e:
        print(f"[ERROR] Root error: {e}")
    
    # Health endpoint
    try:
        health_response = requests.get(f"{LANGGRAPH_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"[SUCCESS] Health: {health_data.get('status')}")
        else:
            print(f"[FAIL] Health failed: {health_response.status_code}")
    except Exception as e:
        print(f"[ERROR] Health error: {e}")

if __name__ == "__main__":
    # Test health first
    test_health_endpoints()
    
    # Run complete workflow test
    workflow_id = test_complete_workflow()
    
    print(f"\nTest completed with workflow ID: {workflow_id}")
    print("Check the detailed output above for each endpoint's actual behavior")