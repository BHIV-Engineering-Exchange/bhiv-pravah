#!/usr/bin/env python3
"""
Test all services with running Docker containers
"""

import requests
import json
import time

def test_service_health():
    """Test all service health endpoints"""
    print("=== TESTING SERVICE HEALTH ===")
    
    services = {
        "Gateway": "http://localhost:8000/health",
        "Agent": "http://localhost:9000/health", 
        "LangGraph": "http://localhost:9001/health",
        "HR Portal": "http://localhost:8501",
        "Client Portal": "http://localhost:8502",
        "Candidate Portal": "http://localhost:8503"
    }
    
    results = {}
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            status = "OK" if response.status_code == 200 else f"ERROR {response.status_code}"
            results[name] = status
            print(f"{name}: {status}")
        except Exception as e:
            results[name] = f"FAILED: {str(e)}"
            print(f"{name}: FAILED - {e}")
    
    return results

def test_langgraph_integration():
    """Test Gateway -> LangGraph integration (the main fix)"""
    print("\n=== TESTING LANGGRAPH INTEGRATION ===")
    
    # Test endpoints that were returning 404
    endpoints = [
        "/api/v1/workflow/health",
        "/api/v1/workflow/list", 
        "/api/v1/workflow/trigger",
        "/api/v1/webhooks/candidate-applied"
    ]
    
    base_url = "http://localhost:8000"
    results = {}
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            if "trigger" in endpoint or "webhooks" in endpoint:
                # POST endpoints need data
                data = {
                    "candidate_id": 1,
                    "job_id": 1,
                    "candidate_name": "Test User",
                    "candidate_email": "test@example.com",
                    "job_title": "Test Job"
                }
                response = requests.post(url, json=data, timeout=10)
            else:
                # GET endpoints
                response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                results[endpoint] = "STILL 404 - FIX FAILED"
            elif response.status_code in [200, 201]:
                results[endpoint] = "SUCCESS - FIX WORKED"
            else:
                results[endpoint] = f"STATUS {response.status_code}"
            
            print(f"{endpoint}: {results[endpoint]}")
            
        except Exception as e:
            results[endpoint] = f"ERROR: {str(e)}"
            print(f"{endpoint}: ERROR - {e}")
    
    return results

def test_gateway_routes():
    """Test Gateway service has all expected routes"""
    print("\n=== TESTING GATEWAY ROUTES ===")
    
    try:
        # Test OpenAPI docs endpoint to see all routes
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("Gateway OpenAPI docs accessible")
            
        # Test root endpoint
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"Gateway root: {data.get('message', 'OK')}")
            print(f"Total endpoints: {data.get('endpoints', 'unknown')}")
            
            # Check for LangGraph integration mention
            if 'langgraph_integration' in str(data):
                print("LangGraph integration: ACTIVE")
            else:
                print("LangGraph integration: NOT MENTIONED")
                
        return True
        
    except Exception as e:
        print(f"Gateway routes test failed: {e}")
        return False

def test_workflow_creation():
    """Test actual workflow creation"""
    print("\n=== TESTING WORKFLOW CREATION ===")
    
    try:
        url = "http://localhost:8000/api/v1/workflow/trigger"
        data = {
            "candidate_id": 1,
            "job_id": 1, 
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com",
            "candidate_phone": "+1234567890",
            "job_title": "Software Engineer",
            "trigger_type": "candidate_applied"
        }
        
        response = requests.post(url, json=data, timeout=15)
        
        if response.status_code == 404:
            print("Workflow creation: FAILED - Still getting 404")
            return False
        elif response.status_code in [200, 201]:
            result = response.json()
            print("Workflow creation: SUCCESS")
            print(f"Workflow ID: {result.get('workflow_id', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"Workflow creation: STATUS {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Workflow creation failed: {e}")
        return False

def main():
    print("BHIV HR Platform - Docker Integration Test")
    print("=" * 60)
    
    # Test service health
    health_results = test_service_health()
    
    # Test LangGraph integration (main fix)
    integration_results = test_langgraph_integration()
    
    # Test gateway routes
    routes_ok = test_gateway_routes()
    
    # Test workflow creation
    workflow_ok = test_workflow_creation()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Service health summary
    healthy_services = sum(1 for status in health_results.values() if "OK" in status)
    print(f"Services healthy: {healthy_services}/{len(health_results)}")
    
    # Integration summary
    fixed_endpoints = sum(1 for status in integration_results.values() if "SUCCESS" in status)
    total_endpoints = len(integration_results)
    print(f"LangGraph endpoints fixed: {fixed_endpoints}/{total_endpoints}")
    
    # Overall result
    if fixed_endpoints == total_endpoints and workflow_ok:
        print("\n🎉 ALL FIXES VERIFIED - INTEGRATION WORKING!")
        print("The 404 errors have been resolved.")
    elif fixed_endpoints > 0:
        print(f"\n✅ PARTIAL SUCCESS - {fixed_endpoints} endpoints working")
        print("Some fixes are working, check failed endpoints above.")
    else:
        print("\n❌ FIXES NOT WORKING - Still getting 404 errors")
        print("Check Docker containers and service logs.")

if __name__ == "__main__":
    main()