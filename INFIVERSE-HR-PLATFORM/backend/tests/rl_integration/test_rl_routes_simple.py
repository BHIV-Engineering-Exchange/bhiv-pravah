#!/usr/bin/env python3
"""
Simple RL Routes Test - Check if RL routes are properly registered
"""
import requests
import json
from datetime import datetime

# Configuration
GATEWAY_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_rl_routes():
    """Test RL routes registration and basic functionality"""
    print("Testing RL Routes Registration")
    print("=" * 50)
    
    # Test 1: Check OpenAPI schema for RL routes
    print("\n1. Checking OpenAPI schema for RL routes...")
    try:
        response = requests.get(f"{GATEWAY_URL}/openapi.json", timeout=30)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            rl_paths = [path for path in paths.keys() if "/rl/" in path]
            print(f"   Found {len(rl_paths)} RL paths in OpenAPI schema:")
            for path in rl_paths:
                print(f"   - {path}")
            
            if rl_paths:
                print("   [PASS] RL routes are registered in OpenAPI schema")
            else:
                print("   [FAIL] No RL routes found in OpenAPI schema")
        else:
            print(f"   [FAIL] Could not fetch OpenAPI schema: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] OpenAPI check failed: {e}")
    
    # Test 2: Try different RL route patterns
    print("\n2. Testing different RL route patterns...")
    
    test_routes = [
        ("/v1/rl/analytics", "GET"),
        ("/v1/rl/performance", "GET"),
        ("/api/v1/rl/analytics", "GET"),
        ("/api/v1/rl/performance", "GET"),
        ("/rl/analytics", "GET"),
        ("/rl/performance", "GET")
    ]
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    for route, method in test_routes:
        try:
            url = f"{GATEWAY_URL}{route}"
            response = requests.request(method, url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   [PASS] {method} {route} -> {response.status_code}")
            elif response.status_code == 404:
                print(f"   [FAIL] {method} {route} -> {response.status_code} (Not Found)")
            else:
                print(f"   [INFO] {method} {route} -> {response.status_code}")
        except Exception as e:
            print(f"   [ERROR] {method} {route} -> {str(e)[:50]}")
    
    # Test 3: Check if LangGraph service is accessible
    print("\n3. Testing LangGraph service accessibility...")
    try:
        response = requests.get("https://bhiv-hr-langgraph.onrender.com/", timeout=10)
        if response.status_code == 200:
            print(f"   [PASS] LangGraph service is accessible: {response.status_code}")
        else:
            print(f"   [FAIL] LangGraph service error: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] LangGraph service: {str(e)[:50]}")
    
    # Test 4: Check gateway health and service info
    print("\n4. Checking gateway service information...")
    try:
        response = requests.get(f"{GATEWAY_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   Gateway version: {data.get('version', 'unknown')}")
            print(f"   Total endpoints: {data.get('endpoints', 'unknown')}")
            print(f"   LangGraph integration: {data.get('langgraph_integration', 'unknown')}")
        else:
            print(f"   [FAIL] Gateway info error: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Gateway info: {str(e)[:50]}")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_rl_routes()