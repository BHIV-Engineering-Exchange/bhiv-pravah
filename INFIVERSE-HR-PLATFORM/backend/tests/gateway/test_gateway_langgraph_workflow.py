#!/usr/bin/env python3
"""
Complete Gateway → LangGraph Workflow Integration Test
Tests the full workflow from Gateway endpoints to LangGraph service
"""

import requests
import json
import time
from datetime import datetime

# Configuration
GATEWAY_SERVICE_URL = "http://localhost:8000"
LANGGRAPH_SERVICE_URL = "http://localhost:9001"  # For local testing, use 9001
API_KEY = "<YOUR_API_KEY>"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def test_complete_gateway_langgraph_workflow():
    """Test complete Gateway → LangGraph workflow integration"""
    print("Gateway -> LangGraph Complete Workflow Integration Test")
    print("=" * 70)
    print(f"Gateway URL: {GATEWAY_SERVICE_URL}")
    print(f"LangGraph URL: {LANGGRAPH_SERVICE_URL}")
    print(f"API Key: {API_KEY}")
    print()
    
    # Step 1: Test Gateway LangGraph Health Check
    print("[STEP 1] Testing Gateway -> LangGraph Health Check...")
    try:
        response = requests.get(
            f"{GATEWAY_SERVICE_URL}/api/v1/workflow/health",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"[SUCCESS] LangGraph Health via Gateway:")
            print(f"  Status: {health_data.get('langgraph_status')}")
            print(f"  Service Status: {health_data.get('service_status')}")
            print(f"  Version: {health_data.get('version')}")
        else:
            print(f"[FAIL] Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Health check error: {e}")
    
    # Step 2: Test Gateway Workflow Trigger
    print(f"\n[STEP 2] Testing Gateway Workflow Trigger...")
    workflow_payload = {
        "candidate_id": 1,
        "job_id": 1,
        "candidate_name": "John Doe",
        "candidate_email": "john.doe@example.com",
        "candidate_phone": "+1234567890",
        "job_title": "Software Engineer",
        "trigger_type": "candidate_applied"
    }
    
    workflow_id = None
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE_URL}/api/v1/workflow/trigger",
            json=workflow_payload,
            headers=HEADERS,
            timeout=30
        )
        
        print(f"Trigger Status Code: {response.status_code}")
        print(f"Trigger Response: {response.text}")
        
        if response.status_code == 200:
            trigger_data = response.json()
            workflow_id = trigger_data.get('workflow_id')
            print(f"[SUCCESS] Workflow triggered via Gateway:")
            print(f"  Success: {trigger_data.get('success')}")
            print(f"  Workflow ID: {workflow_id}")
            print(f"  Status: {trigger_data.get('status')}")
            print(f"  Message: {trigger_data.get('message')}")
        else:
            print(f"[FAIL] Workflow trigger failed: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Workflow trigger error: {e}")
    
    # Step 3: Test Gateway Workflow Status (if workflow was created)
    if workflow_id:
        print(f"\n[STEP 3] Testing Gateway Workflow Status...")
        time.sleep(2)  # Wait for workflow to process
        
        try:
            response = requests.get(
                f"{GATEWAY_SERVICE_URL}/api/v1/workflow/status/{workflow_id}",
                headers=HEADERS,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Status Response: {response.text}")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"[SUCCESS] Workflow status via Gateway:")
                print(f"  Workflow ID: {status_data.get('workflow_id')}")
                print(f"  Status: {status_data.get('status')}")
                print(f"  Current Stage: {status_data.get('current_stage')}")
            else:
                print(f"[FAIL] Status check failed: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Status check error: {e}")
    
    # Step 4: Test Gateway Workflow List
    print(f"\n[STEP 4] Testing Gateway Workflow List...")
    try:
        response = requests.get(
            f"{GATEWAY_SERVICE_URL}/api/v1/workflow/list",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            list_data = response.json()
            print(f"[SUCCESS] Workflow list via Gateway:")
            print(f"  Count: {list_data.get('count')}")
            print(f"  Workflows: {len(list_data.get('workflows', []))}")
        else:
            print(f"[FAIL] List failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] List error: {e}")
    
    # Step 5: Test Webhook - Candidate Applied
    print(f"\n[STEP 5] Testing Webhook - Candidate Applied...")
    webhook_payload = {
        "candidate_id": 2,
        "job_id": 1,
        "candidate_name": "Jane Smith",
        "candidate_email": "jane.smith@example.com",
        "candidate_phone": "+1987654321",
        "job_title": "Data Scientist"
    }
    
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE_URL}/api/v1/webhooks/candidate-applied",
            json=webhook_payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"[SUCCESS] Candidate Applied Webhook:")
            print(f"  Success: {webhook_data.get('success')}")
            print(f"  Workflow ID: {webhook_data.get('workflow_id')}")
            print(f"  Status: {webhook_data.get('status')}")
            print(f"  Trigger Type: {webhook_data.get('trigger_type')}")
        else:
            print(f"[FAIL] Webhook failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Webhook error: {e}")
    
    # Step 6: Test Webhook - Candidate Shortlisted
    print(f"\n[STEP 6] Testing Webhook - Candidate Shortlisted...")
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE_URL}/api/v1/webhooks/candidate-shortlisted",
            json=webhook_payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"[SUCCESS] Candidate Shortlisted Webhook:")
            print(f"  Success: {webhook_data.get('success')}")
            print(f"  Message: {webhook_data.get('message')}")
            print(f"  Status: {webhook_data.get('status')}")
        else:
            print(f"[FAIL] Shortlist webhook failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Shortlist webhook error: {e}")
    
    # Step 7: Test Webhook - Interview Scheduled
    print(f"\n[STEP 7] Testing Webhook - Interview Scheduled...")
    try:
        response = requests.post(
            f"{GATEWAY_SERVICE_URL}/api/v1/webhooks/interview-scheduled",
            json=webhook_payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"[SUCCESS] Interview Scheduled Webhook:")
            print(f"  Success: {webhook_data.get('success')}")
            print(f"  Message: {webhook_data.get('message')}")
            print(f"  Status: {webhook_data.get('status')}")
        else:
            print(f"[FAIL] Interview webhook failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Interview webhook error: {e}")
    
    # Step 8: Direct LangGraph Service Test (for comparison)
    print(f"\n[STEP 8] Direct LangGraph Service Test (for comparison)...")
    direct_payload = {
        "candidate_id": 3,
        "job_id": 1,
        "application_id": 3,
        "candidate_email": "direct@example.com",
        "candidate_phone": "+1555666777",
        "candidate_name": "Direct Test",
        "job_title": "DevOps Engineer",
        "job_description": "Direct test job"
    }
    
    try:
        response = requests.post(
            f"{LANGGRAPH_SERVICE_URL}/workflows/application/start",
            json=direct_payload,
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            direct_data = response.json()
            print(f"[SUCCESS] Direct LangGraph Test:")
            print(f"  Workflow ID: {direct_data.get('workflow_id')}")
            print(f"  Status: {direct_data.get('status')}")
            print(f"  Message: {direct_data.get('message')}")
        else:
            print(f"[FAIL] Direct LangGraph failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Direct LangGraph error: {e}")
    
    print(f"\n" + "=" * 70)
    print("COMPLETE GATEWAY -> LANGGRAPH WORKFLOW TEST FINISHED")
    print("Check above results for full integration functionality")
    
    return workflow_id

def test_gateway_health():
    """Test Gateway health endpoints"""
    print(f"\n[HEALTH] Testing Gateway endpoints...")
    
    # Gateway root
    try:
        response = requests.get(f"{GATEWAY_SERVICE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Gateway Root: {data.get('message')}")
            print(f"  LangGraph Integration: {data.get('langgraph_integration')}")
            print(f"  AI Workflows: {data.get('ai_workflows')}")
        else:
            print(f"[FAIL] Gateway root failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Gateway root error: {e}")
    
    # Gateway health
    try:
        response = requests.get(f"{GATEWAY_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Gateway Health: {data.get('status')}")
        else:
            print(f"[FAIL] Gateway health failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Gateway health error: {e}")

if __name__ == "__main__":
    # Test Gateway health first
    test_gateway_health()
    
    # Run complete workflow test
    workflow_id = test_complete_gateway_langgraph_workflow()
    
    print(f"\nIntegration test completed.")
    print("This test verifies the complete Gateway -> LangGraph workflow integration")
    print("including workflow triggers, status checks, and webhook automation.")