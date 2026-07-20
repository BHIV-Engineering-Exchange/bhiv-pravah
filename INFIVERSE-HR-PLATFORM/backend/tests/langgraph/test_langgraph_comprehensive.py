#!/usr/bin/env python3
"""
Comprehensive LangGraph Service Test
Tests routes, configuration, authorization, and functionality
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration
LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
LOCAL_URL = "http://localhost:9001"
API_KEY = "bhiv-hr-2024-secure-api-key-v2"

def test_endpoint(url, method="GET", data=None, headers=None):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        return {
            "status_code": response.status_code,
            "success": response.status_code in [200, 201],
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
            "error": None
        }
    except Exception as e:
        return {
            "status_code": None,
            "success": False,
            "response": None,
            "error": str(e)
        }

def test_local_import():
    """Test if dependencies can be imported locally"""
    try:
        sys.path.append(os.path.join(os.getcwd(), 'services', 'langgraph'))
        from dependencies import validate_api_key, get_api_key
        print("OK Dependencies import: SUCCESS")
        
        # Test API key validation
        test_result = validate_api_key(API_KEY)
        print(f"OK API key validation: {'SUCCESS' if test_result else 'FAIL'}")
        
        return True
    except Exception as e:
        print(f"FAIL Dependencies import: FAIL - {str(e)}")
        return False

def test_configuration():
    """Test configuration files"""
    config_files = [
        "services/langgraph/config.py",
        "services/langgraph/dependencies.py", 
        "services/langgraph/.env.example",
        "services/langgraph/Dockerfile",
        "services/langgraph/requirements.txt",
        "services/langgraph/render.yaml"
    ]
    
    print("\nConfiguration Files Check:")
    print("-" * 30)
    
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"OK {file_path}: EXISTS")
        else:
            print(f"FAIL {file_path}: MISSING")

def test_docker_structure():
    """Test Docker and deployment structure"""
    print("\nDocker & Deployment Structure:")
    print("-" * 35)
    
    # Check Dockerfile
    dockerfile_path = "services/langgraph/Dockerfile"
    if os.path.exists(dockerfile_path):
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            if "uvicorn app.main:app" in content:
                print("OK Dockerfile: Correct startup command")
            else:
                print("FAIL Dockerfile: Missing or incorrect startup command")
            
            if "EXPOSE 9001" in content:
                print("OK Dockerfile: Correct port exposure")
            else:
                print("FAIL Dockerfile: Missing or incorrect port")
    else:
        print("FAIL Dockerfile: MISSING")
    
    # Check render.yaml
    render_path = "services/langgraph/render.yaml"
    if os.path.exists(render_path):
        with open(render_path, 'r') as f:
            content = f.read()
            if "API_KEY_SECRET" in content:
                print("OK render.yaml: API_KEY_SECRET configured")
            else:
                print("FAIL render.yaml: API_KEY_SECRET missing")
    else:
        print("FAIL render.yaml: MISSING")

def test_routes_authorization():
    """Test all routes with and without authorization"""
    print("\nRoutes & Authorization Test:")
    print("-" * 32)
    
    base_url = LANGGRAPH_URL
    
    # Headers
    headers_with_auth = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    headers_no_auth = {"Content-Type": "application/json"}
    
    # Test endpoints
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/workflows", "List workflows"),
        ("GET", "/test-integration", "Test integration"),
        ("POST", "/workflows/application/start", "Start workflow", {
            "candidate_id": 1,
            "job_id": 1,
            "application_id": 1,
            "candidate_email": "test@example.com",
            "candidate_phone": "+1234567890",
            "candidate_name": "Test Candidate",
            "job_title": "Software Engineer"
        }),
        ("GET", "/workflows/test-123/status", "Get workflow status"),
        ("POST", "/tools/send-notification", "Send notification", {
            "candidate_id": 1,
            "candidate_name": "Test Candidate",
            "candidate_email": "test@example.com",
            "job_title": "Software Engineer",
            "message": "Test notification",
            "channels": ["email"]
        })
    ]
    
    results = []
    
    for endpoint_info in endpoints:
        method = endpoint_info[0]
        path = endpoint_info[1]
        description = endpoint_info[2]
        data = endpoint_info[3] if len(endpoint_info) > 3 else None
        
        url = f"{base_url}{path}"
        
        # Test without auth
        result_no_auth = test_endpoint(url, method, data, headers_no_auth)
        auth_working = result_no_auth["status_code"] == 401
        
        # Test with auth
        result_with_auth = test_endpoint(url, method, data, headers_with_auth)
        endpoint_working = result_with_auth["success"]
        
        status = "OK" if auth_working and endpoint_working else "FAIL"
        print(f"{status} {method} {path}: Auth={auth_working}, Func={endpoint_working}")
        
        if not auth_working and result_no_auth["status_code"]:
            print(f"    No Auth: {result_no_auth['status_code']} (expected 401)")
        if not endpoint_working and result_with_auth["status_code"]:
            print(f"    With Auth: {result_with_auth['status_code']} (expected 200)")
        
        results.append({
            "endpoint": f"{method} {path}",
            "auth_working": auth_working,
            "endpoint_working": endpoint_working
        })
    
    return results

def test_gateway_integration():
    """Test Gateway → LangGraph integration"""
    print("\nGateway Integration Test:")
    print("-" * 27)
    
    gateway_url = "https://bhiv-hr-gateway-ltg0.onrender.com"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test Gateway LangGraph endpoints
    gateway_endpoints = [
        ("GET", "/api/v1/workflow/health", "LangGraph health check"),
        ("GET", "/api/v1/workflow/list", "List workflows"),
        ("POST", "/api/v1/workflow/trigger", "Trigger workflow", {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_name": "Test Candidate",
            "candidate_email": "test@example.com",
            "job_title": "Software Engineer"
        })
    ]
    
    for method, path, description, *data in gateway_endpoints:
        url = f"{gateway_url}{path}"
        payload = data[0] if data else None
        
        result = test_endpoint(url, method, payload, headers)
        status = "OK" if result["success"] else "FAIL"
        print(f"{status} {method} {path}: {result['status_code']}")

def main():
    print("COMPREHENSIVE LANGGRAPH SERVICE TEST")
    print("=" * 50)
    
    # Test 1: Local imports and configuration
    test_local_import()
    
    # Test 2: Configuration files
    test_configuration()
    
    # Test 3: Docker structure
    test_docker_structure()
    
    # Test 4: Routes and authorization
    results = test_routes_authorization()
    
    # Test 5: Gateway integration
    test_gateway_integration()
    
    # Summary
    print("\nSUMMARY:")
    print("-" * 15)
    
    if results:
        total = len(results)
        auth_working = sum(1 for r in results if r["auth_working"])
        func_working = sum(1 for r in results if r["endpoint_working"])
        
        print(f"Total Endpoints: {total}")
        print(f"Authorization Working: {auth_working}/{total}")
        print(f"Endpoints Functional: {func_working}/{total}")
        
        if auth_working == total and func_working == total:
            print("ALL TESTS PASSED!")
        else:
            print("Some tests failed - check deployment")
    else:
        print("No endpoint tests completed")

if __name__ == "__main__":
    main()