#!/usr/bin/env python3
"""
Test LangGraph Service Authorization
Tests all LangGraph endpoints with API key authentication
"""

import requests
import json
import os
from datetime import datetime

# Configuration
LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"  # Production URL
LOCAL_URL = "http://localhost:9001"  # Local URL
API_KEY = os.getenv("API_KEY_SECRET", "bhiv-hr-2024-secure-api-key-v2")

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
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
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
    print("🔐 Testing LangGraph Service Authorization")
    print("=" * 50)
    
    # Test both production and local URLs
    urls_to_test = [
        ("Production", LANGGRAPH_URL),
        ("Local", LOCAL_URL)
    ]
    
    for env_name, base_url in urls_to_test:
        print(f"\n🌐 Testing {env_name} Environment: {base_url}")
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
            
            # Test without authentication (should fail)
            print(f"  🔓 Testing {method} {path} (No Auth): ", end="")
            result_no_auth = test_endpoint(url, method, data, headers_no_auth)
            
            if result_no_auth["status_code"] == 401:
                print("✅ Correctly rejected (401)")
                auth_working = True
            else:
                print(f"❌ Expected 401, got {result_no_auth['status_code']}")
                auth_working = False
            
            # Test with authentication (should succeed)
            print(f"  🔐 Testing {method} {path} (With Auth): ", end="")
            result_with_auth = test_endpoint(url, method, data, headers_with_auth)
            
            if result_with_auth["success"]:
                print("✅ Success")
                endpoint_working = True
            else:
                print(f"❌ Failed ({result_with_auth['status_code']})")
                endpoint_working = False
                if result_with_auth["error"]:
                    print(f"    Error: {result_with_auth['error']}")
            
            results.append({
                "endpoint": f"{method} {path}",
                "description": description,
                "auth_working": auth_working,
                "endpoint_working": endpoint_working,
                "status_code": result_with_auth["status_code"]
            })
        
        # Summary for this environment
        print(f"\n📊 {env_name} Summary:")
        total_endpoints = len(results)
        auth_working_count = sum(1 for r in results if r["auth_working"])
        endpoint_working_count = sum(1 for r in results if r["endpoint_working"])
        
        print(f"  Total Endpoints: {total_endpoints}")
        print(f"  Authorization Working: {auth_working_count}/{total_endpoints}")
        print(f"  Endpoints Functional: {endpoint_working_count}/{total_endpoints}")
        
        if auth_working_count == total_endpoints:
            print("  🎉 All endpoints properly protected!")
        else:
            print("  ⚠️  Some endpoints missing authorization!")
        
        if endpoint_working_count == total_endpoints:
            print("  🎉 All endpoints functional!")
        else:
            print("  ⚠️  Some endpoints not working!")

if __name__ == "__main__":
    main()