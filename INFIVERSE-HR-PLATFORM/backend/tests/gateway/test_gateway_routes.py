#!/usr/bin/env python3
"""
Test Gateway Routes to Debug LangGraph Integration
"""

import requests
import json

GATEWAY_SERVICE_URL = "http://localhost:8000"
API_KEY = "test-api-key-12345"

def test_routes():
    """Test specific routes to debug integration"""
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    print("Testing Gateway Routes...")
    
    # Test root endpoint
    try:
        resp = requests.get(f"{GATEWAY_SERVICE_URL}/")
        data = resp.json()
        print(f"Root endpoint: {resp.status_code}")
        print(f"Endpoints count: {data.get('endpoints', 'unknown')}")
        print(f"LangGraph integration: {data.get('langgraph_integration', 'unknown')}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test specific LangGraph routes
    langgraph_routes = [
        "/api/v1/workflow/health",
        "/api/v1/workflow/trigger", 
        "/api/v1/workflow/list",
        "/api/v1/webhooks/candidate-applied"
    ]
    
    for route in langgraph_routes:
        try:
            if "trigger" in route or "webhooks" in route:
                # POST endpoints
                test_data = {
                    "candidate_id": 1,
                    "job_id": 1,
                    "candidate_name": "Test",
                    "candidate_email": "test@example.com",
                    "job_title": "Engineer"
                }
                resp = requests.post(f"{GATEWAY_SERVICE_URL}{route}", json=test_data, headers=headers)
            else:
                # GET endpoints
                resp = requests.get(f"{GATEWAY_SERVICE_URL}{route}", headers=headers)
            
            print(f"{route}: {resp.status_code}")
            if resp.status_code != 404:
                try:
                    data = resp.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"  Response: {resp.text[:100]}...")
        except Exception as e:
            print(f"{route}: ERROR - {e}")

if __name__ == "__main__":
    test_routes()