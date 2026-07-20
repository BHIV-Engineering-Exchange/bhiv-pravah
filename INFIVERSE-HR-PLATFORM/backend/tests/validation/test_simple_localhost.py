#!/usr/bin/env python3
"""
Simple Localhost Test - Basic functionality check
"""
import requests
import json
from datetime import datetime

# Configuration
GATEWAY_URL = "http://localhost:8000"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_basic():
    """Basic functionality test"""
    print("BHIV HR Platform - Simple Localhost Test")
    print("=" * 50)
    
    results = []
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Test 1: Gateway Health
    print("\n1. Gateway Health Check...")
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   [PASS] Gateway is running")
            results.append(("Gateway Health", True))
        else:
            print(f"   [FAIL] Gateway error: {response.status_code}")
            results.append(("Gateway Health", False))
    except Exception as e:
        print(f"   [ERROR] Gateway not accessible: {e}")
        results.append(("Gateway Health", False))
        return False
    
    # Test 2: API Key Auth
    print("\n2. API Key Authentication...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/candidates/stats", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] API Key works - {data.get('total_candidates', 0)} candidates")
            results.append(("API Key Auth", True))
        else:
            print(f"   [FAIL] API Key failed: {response.status_code}")
            results.append(("API Key Auth", False))
    except Exception as e:
        print(f"   [ERROR] API Key test: {e}")
        results.append(("API Key Auth", False))
    
    # Test 3: RL Analytics
    print("\n3. RL Analytics...")
    try:
        response = requests.get(f"{GATEWAY_URL}/api/v1/rl/analytics", headers=headers, timeout=10)
        if response.status_code == 200:
            print("   [PASS] RL Analytics working")
            results.append(("RL Analytics", True))
        else:
            print(f"   [FAIL] RL Analytics: {response.status_code}")
            results.append(("RL Analytics", False))
    except Exception as e:
        print(f"   [ERROR] RL Analytics: {e}")
        results.append(("RL Analytics", False))
    
    # Test 4: Database Schema
    print("\n4. Database Schema...")
    try:
        response = requests.get(f"{GATEWAY_URL}/v1/analytics/schema", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tables = data.get("total_tables", 0)
            print(f"   [PASS] Database accessible - {tables} tables")
            results.append(("Database Schema", True))
        else:
            print(f"   [FAIL] Database: {response.status_code}")
            results.append(("Database Schema", False))
    except Exception as e:
        print(f"   [ERROR] Database: {e}")
        results.append(("Database Schema", False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print(f"{'='*50}")
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:20s}: [{status}]")
    
    if passed >= 3:
        print("\nSystem is ready for development!")
        return True
    else:
        print("\nSystem needs attention.")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = test_basic()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")