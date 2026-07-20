#!/usr/bin/env python3
"""
Test LangGraph Service Authorization - Simple Version
Tests LangGraph endpoints with API key authentication
"""

import requests
import json
import os
from datetime import datetime

# Configuration
LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
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

def main():
    print("Testing LangGraph Service Authorization")
    print("=" * 50)
    
    base_url = LANGGRAPH_URL
    print(f"Testing Production Environment: {base_url}")
    print("-" * 40)
    
    # Headers with API key
    headers_with_auth = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Headers without API key
    headers_no_auth = {
        "Content-Type": "application/json"
    }
    
    # Test endpoints
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/workflows", "List workflows"),
        ("GET", "/test-integration", "Test integration"),
    ]
    
    results = []
    
    for method, path, description in endpoints:
        url = f"{base_url}{path}"
        
        # Test without authentication (should fail)
        print(f"Testing {method} {path} (No Auth): ", end="")
        result_no_auth = test_endpoint(url, method, None, headers_no_auth)
        
        if result_no_auth["status_code"] == 401:
            print("PASS - Correctly rejected (401)")
            auth_working = True
        else:
            print(f"FAIL - Expected 401, got {result_no_auth['status_code']}")
            auth_working = False
        
        # Test with authentication (should succeed)
        print(f"Testing {method} {path} (With Auth): ", end="")
        result_with_auth = test_endpoint(url, method, None, headers_with_auth)
        
        if result_with_auth["success"]:
            print("PASS - Success")
            endpoint_working = True
        else:
            print(f"FAIL - Status {result_with_auth['status_code']}")
            endpoint_working = False
            if result_with_auth["error"]:
                print(f"  Error: {result_with_auth['error']}")
        
        results.append({
            "endpoint": f"{method} {path}",
            "description": description,
            "auth_working": auth_working,
            "endpoint_working": endpoint_working,
            "status_code": result_with_auth["status_code"]
        })
    
    # Summary
    print(f"\nSummary:")
    total_endpoints = len(results)
    auth_working_count = sum(1 for r in results if r["auth_working"])
    endpoint_working_count = sum(1 for r in results if r["endpoint_working"])
    
    print(f"Total Endpoints: {total_endpoints}")
    print(f"Authorization Working: {auth_working_count}/{total_endpoints}")
    print(f"Endpoints Functional: {endpoint_working_count}/{total_endpoints}")
    
    if auth_working_count == total_endpoints:
        print("SUCCESS: All endpoints properly protected!")
    else:
        print("WARNING: Some endpoints missing authorization!")
    
    if endpoint_working_count == total_endpoints:
        print("SUCCESS: All endpoints functional!")
    else:
        print("WARNING: Some endpoints not working!")

if __name__ == "__main__":
    main()