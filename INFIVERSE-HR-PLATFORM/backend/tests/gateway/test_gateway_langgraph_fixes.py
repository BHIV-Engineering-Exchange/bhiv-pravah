#!/usr/bin/env python3
"""
Test Gateway → LangGraph Integration Fixes
Verifies that the authentication and workflow issues have been resolved
"""

import requests
import json
import time
from datetime import datetime

# Configuration
GATEWAY_SERVICE_URL = "http://localhost:8000"
LANGGRAPH_SERVICE_URL = "http://localhost:9001"
API_KEY = "<YOUR_API_KEY>"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def test_gateway_langgraph_fixes():
    """Test ALL Gateway and LangGraph endpoints with workflow continuity"""
    print("Comprehensive Test: ALL Gateway + LangGraph Endpoints")
    print("=" * 70)
    print(f"Gateway URL: {GATEWAY_SERVICE_URL}")
    print(f"LangGraph URL: {LANGGRAPH_SERVICE_URL}")
    print(f"API Key: {API_KEY}")
    print()
    print("TESTING ALL 15 ENDPOINTS (8 LangGraph + 7 Gateway)")
    print("-" * 50)
    
    # LANGGRAPH SERVICE ENDPOINTS (8 total)
    print("\nLANGGRAPH SERVICE ENDPOINTS:")
    
    # LG-1: Root endpoint
    print("[LG-1] GET / - LangGraph Root...")
    try:
        response = requests.get(f"{LANGGRAPH_SERVICE_URL}/", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] {data.get('message')} v{data.get('version')} - {data.get('endpoints')} endpoints")
        else:
            print(f"[FAIL] Root failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Root error: {e}")
    
    # LG-2: Health check
    print("[LG-2] GET /health - LangGraph Health...")
    try:
        response = requests.get(f"{LANGGRAPH_SERVICE_URL}/health", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] {data.get('service')} - {data.get('status')}")
        else:
            print(f"[FAIL] Health failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Health error: {e}")
    
    # LG-3: Start workflow (maintain workflow ID for continuity)
    print("[LG-3] POST /workflows/application/start - Start Workflow...")
    workflow_payload = {
        "candidate_id": 1,
        "job_id": 1,
        "application_id": 1,
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "candidate_name": "Test User",
        "job_title": "Software Engineer",
        "job_description": "Test job description"
    }
    
    workflow_id = None
    try:
        response = requests.post(f"{LANGGRAPH_SERVICE_URL}/workflows/application/start", 
                               json=workflow_payload, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            workflow_id = data.get('workflow_id')
            print(f"[SUCCESS] Workflow Started: {workflow_id}")
        else:
            print(f"[FAIL] Workflow start failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Workflow start error: {e}")
    
    # LG-4: Get workflow status (using workflow_id from above)
    print("[LG-4] GET /workflows/{workflow_id}/status - Get Status...")
    if workflow_id:
        try:
            time.sleep(2)
            response = requests.get(f"{LANGGRAPH_SERVICE_URL}/workflows/{workflow_id}/status", 
                                  headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"[SUCCESS] Status: {data.get('application_status')} - {data.get('current_stage')}")
            else:
                print(f"[FAIL] Status failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Status error: {e}")
    else:
        print("[SKIP] No workflow ID available")
    
    # LG-5: Resume workflow
    print("[LG-5] POST /workflows/{workflow_id}/resume - Resume Workflow...")
    if workflow_id:
        try:
            response = requests.post(f"{LANGGRAPH_SERVICE_URL}/workflows/{workflow_id}/resume", 
                                   headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"[SUCCESS] Resume: {data.get('status')}")
            else:
                print(f"[FAIL] Resume failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Resume error: {e}")
    else:
        print("[SKIP] No workflow ID available")
    
    # LG-6: List workflows
    print("[LG-6] GET /workflows - List Workflows...")
    try:
        response = requests.get(f"{LANGGRAPH_SERVICE_URL}/workflows", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] List: {data.get('count')} workflows")
        else:
            print(f"[FAIL] List failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] List error: {e}")
    
    # LG-7: Send notification
    print("[LG-7] POST /tools/send-notification - Send Notification...")
    notification_payload = {
        "candidate_id": 1,
        "candidate_name": "Test User",
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "job_title": "Software Engineer",
        "message": "Test notification",
        "channels": ["email", "whatsapp"]
    }
    try:
        response = requests.post(f"{LANGGRAPH_SERVICE_URL}/tools/send-notification", 
                               json=notification_payload, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Notification: {len(data.get('channels_sent', []))} channels")
        else:
            print(f"[FAIL] Notification failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Notification error: {e}")
    
    # LG-8: Test integration
    print("[LG-8] GET /test-integration - Test Integration...")
    try:
        response = requests.get(f"{LANGGRAPH_SERVICE_URL}/test-integration", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Integration: {data.get('status')} - {data.get('endpoints_available')} endpoints")
        else:
            print(f"[FAIL] Integration failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Integration error: {e}")
    
    # GATEWAY LANGGRAPH ENDPOINTS (7 total)
    print("\nGATEWAY LANGGRAPH ENDPOINTS:")
    
    # GW-1: Gateway health check
    print("[GW-1] GET /api/v1/workflow/health - Gateway Health Check...")
    try:
        response = requests.get(f"{GATEWAY_SERVICE_URL}/api/v1/workflow/health", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"[SUCCESS] Gateway Health: {health_data.get('langgraph_status')} - {health_data.get('service_status')}")
        else:
            print(f"[FAIL] Gateway health failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Gateway health error: {e}")
    
    # GW-2: Gateway workflow trigger
    print("[GW-2] POST /api/v1/workflow/trigger - Gateway Trigger...")
    gateway_trigger_payload = {
        "candidate_id": 2,
        "job_id": 1,
        "candidate_name": "Gateway User",
        "candidate_email": "gateway@example.com",
        "candidate_phone": "+1987654321",
        "job_title": "Data Scientist",
        "trigger_type": "candidate_applied"
    }
    
    gateway_workflow_id = None
    try:
        response = requests.post(f"{GATEWAY_SERVICE_URL}/api/v1/workflow/trigger", 
                               json=gateway_trigger_payload, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            trigger_data = response.json()
            gateway_workflow_id = trigger_data.get('workflow_id')
            print(f"[SUCCESS] Gateway Trigger: {trigger_data.get('success')} - {gateway_workflow_id}")
        else:
            print(f"[FAIL] Gateway trigger failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Gateway trigger error: {e}")
    
    # GW-3: Gateway workflow status
    print("[GW-3] GET /api/v1/workflow/status/{workflow_id} - Gateway Status...")
    if gateway_workflow_id:
        try:
            time.sleep(2)
            response = requests.get(f"{GATEWAY_SERVICE_URL}/api/v1/workflow/status/{gateway_workflow_id}", 
                                  headers=HEADERS, timeout=10)
            if response.status_code == 200:
                status_data = response.json()
                print(f"[SUCCESS] Gateway Status: {status_data.get('status')} - {status_data.get('current_stage')}")
            else:
                print(f"[FAIL] Gateway status failed: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Gateway status error: {e}")
    else:
        print("[SKIP] No gateway workflow ID available")
    
    # GW-4: Gateway workflow list
    print("[GW-4] GET /api/v1/workflow/list - Gateway List...")
    try:
        response = requests.get(f"{GATEWAY_SERVICE_URL}/api/v1/workflow/list", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            list_data = response.json()
            print(f"[SUCCESS] Gateway List: {list_data.get('count')} workflows")
        else:
            print(f"[FAIL] Gateway list failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Gateway list error: {e}")
    
    # GW-5: Gateway webhook - candidate applied
    print("[GW-5] POST /api/v1/webhooks/candidate-applied - Webhook Applied...")
    webhook_payload = {
        "candidate_id": 3,
        "job_id": 1,
        "candidate_name": "Webhook User",
        "candidate_email": "webhook@example.com",
        "candidate_phone": "+1555666777",
        "job_title": "DevOps Engineer"
    }
    try:
        response = requests.post(f"{GATEWAY_SERVICE_URL}/api/v1/webhooks/candidate-applied", 
                               json=webhook_payload, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"[SUCCESS] Webhook Applied: {webhook_data.get('success')} - {webhook_data.get('status')}")
        else:
            print(f"[FAIL] Webhook applied failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Webhook applied error: {e}")
    
    # GW-6: Gateway webhook - candidate shortlisted
    print("[GW-6] POST /api/v1/webhooks/candidate-shortlisted - Webhook Shortlisted...")
    try:
        response = requests.post(f"{GATEWAY_SERVICE_URL}/api/v1/webhooks/candidate-shortlisted", 
                               json=webhook_payload, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"[SUCCESS] Webhook Shortlisted: {webhook_data.get('success')} - {webhook_data.get('status')}")
        else:
            print(f"[FAIL] Webhook shortlisted failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Webhook shortlisted error: {e}")
    
    # GW-7: Gateway webhook - interview scheduled
    print("[GW-7] POST /api/v1/webhooks/interview-scheduled - Webhook Interview...")
    try:
        response = requests.post(f"{GATEWAY_SERVICE_URL}/api/v1/webhooks/interview-scheduled", 
                               json=webhook_payload, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            webhook_data = response.json()
            print(f"[SUCCESS] Webhook Interview: {webhook_data.get('success')} - {webhook_data.get('status')}")
        else:
            print(f"[FAIL] Webhook interview failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Webhook interview error: {e}")
    

    
    print(f"\n" + "=" * 70)
    print("COMPREHENSIVE TEST COMPLETE")
    print("LangGraph Service: 8 endpoints tested")
    print("Gateway Service: 7 endpoints tested")
    print("Total: 15 endpoints tested with workflow continuity")

if __name__ == "__main__":
    test_gateway_langgraph_fixes()