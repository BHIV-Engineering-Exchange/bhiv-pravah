#!/usr/bin/env python3
"""
Test script for InsightFlow API endpoints
Run this after starting the server to test all endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, url, data=None, headers=None, expected_status=200):
    """Test an API endpoint"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data, headers=headers)
        
        print(f"{method.upper()} {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
            print(f"Response: {response.text}")
        
        print("-" * 50)
        return response
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("-" * 50)
        return None

def main():
    print("🚀 Testing InsightFlow API Endpoints")
    print("=" * 50)
    
    # Test 1: Health check (no auth required)
    print("1. Testing Health Check")
    test_endpoint("GET", f"{BASE_URL}/health")
    
    # Test 2: Test endpoint (no auth required)
    print("2. Testing Simple Test Endpoint")
    test_endpoint("GET", f"{BASE_URL}/test")
    
    # Test 3: Generate token
    print("3. Testing Token Generation")
    token_response = test_endpoint("POST", f"{BASE_URL}/api/v1/auth/quick-token")
    
    if token_response and token_response.status_code == 200:
        token_data = token_response.json()
        token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        print("4. Testing Agents Endpoints")
        # Test agents list
        test_endpoint("GET", f"{BASE_URL}/api/v1/agents/", headers=headers)
        
        print("5. Testing Analytics Endpoints")
        # Test analytics overview
        test_endpoint("GET", f"{BASE_URL}/api/v1/analytics/overview", headers=headers)
        
        # Test agent performance
        test_endpoint("GET", f"{BASE_URL}/api/v1/analytics/agent-performance", headers=headers)
        
        print("6. Testing Routing Endpoints")
        # Test routing (this might fail if no agents exist)
        routing_data = {
            "input_data": {"text": "Hello world"},
            "input_type": "text",
            "strategy": "rule_based"
        }
        test_endpoint("POST", f"{BASE_URL}/api/v1/routing/route", 
                     data=routing_data, headers=headers, expected_status=400)  # Expect 400 if no agents
        
    else:
        print("❌ Could not get token, skipping authenticated tests")
    
    print("\n🏁 Testing Complete!")
    print("If you see database errors, make sure you've created the Supabase tables.")

if __name__ == "__main__":
    main()