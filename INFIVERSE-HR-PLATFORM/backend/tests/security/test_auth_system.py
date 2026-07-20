#!/usr/bin/env python3
"""
BHIV HR Platform - Authentication System Test
Tests 2FA, JWT tokens, and database authentication
"""
import requests
import json
import os
from datetime import datetime

# Configuration
GATEWAY_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_auth_system():
    """Test complete authentication system"""
    print("BHIV HR Platform - Authentication System Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: API Key Authentication
    print("\n1. Testing API Key Authentication...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/candidates/stats",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        if response.status_code == 200:
            print("[PASS] API Key authentication")
            results.append(("API Key Auth", True))
        else:
            print(f"[FAIL] API Key authentication ({response.status_code})")
            results.append(("API Key Auth", False))
    except Exception as e:
        print(f"[ERROR] API Key authentication ({e})")
        results.append(("API Key Auth", False))
    
    # Test 2: Client JWT Authentication
    print("\n2. Testing Client JWT Authentication...")
    try:
        login_response = requests.post(
            f"{GATEWAY_URL}/v1/client/login",
            json={"client_id": "TECH001", "password": "demo123"},
            timeout=30
        )
        if login_response.status_code == 200:
            login_data = login_response.json()
            if login_data.get("success") and "access_token" in login_data:
                print("[PASS] Client JWT login")
                
                # Test using JWT token
                jwt_token = login_data["access_token"]
                jwt_response = requests.get(
                    f"{GATEWAY_URL}/v1/jobs",
                    headers={"Authorization": f"Bearer {jwt_token}"},
                    timeout=30
                )
                if jwt_response.status_code == 200:
                    print("[PASS] Client JWT usage")
                    results.append(("Client JWT Auth", True))
                else:
                    print(f"[FAIL] Client JWT usage ({jwt_response.status_code})")
                    results.append(("Client JWT Auth", False))
            else:
                print("[FAIL] Client JWT login (No token)")
                results.append(("Client JWT Auth", False))
        else:
            print(f"[FAIL] Client JWT login ({login_response.status_code})")
            results.append(("Client JWT Auth", False))
    except Exception as e:
        print(f"[ERROR] Client JWT authentication ({e})")
        results.append(("Client JWT Auth", False))
    
    # Test 3: 2FA Setup
    print("\n3. Testing 2FA Setup...")
    try:
        setup_response = requests.post(
            f"{GATEWAY_URL}/v1/auth/2fa/setup",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"user_id": "test_user"},
            timeout=30
        )
        if setup_response.status_code == 200:
            setup_data = setup_response.json()
            if "secret" in setup_data and "qr_code" in setup_data:
                print("[PASS] 2FA setup")
                results.append(("2FA Setup", True))
            else:
                print("[FAIL] 2FA setup (Missing data)")
                results.append(("2FA Setup", False))
        else:
            print(f"[FAIL] 2FA setup ({setup_response.status_code})")
            results.append(("2FA Setup", False))
    except Exception as e:
        print(f"[ERROR] 2FA setup ({e})")
        results.append(("2FA Setup", False))
    
    # Test 4: Database Schema Check
    print("\n4. Testing Database Schema...")
    try:
        schema_response = requests.get(
            f"{GATEWAY_URL}/v1/database/schema",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        if schema_response.status_code == 200:
            schema_data = schema_response.json()
            if "schema_version" in schema_data and "total_tables" in schema_data:
                version = schema_data.get("schema_version", "unknown")
                tables = schema_data.get("total_tables", 0)
                print(f"[PASS] Database schema (v{version}, {tables} tables)")
                results.append(("Database Schema", True))
            else:
                print("[FAIL] Database schema (Missing data)")
                results.append(("Database Schema", False))
        else:
            print(f"[FAIL] Database schema ({schema_response.status_code})")
            results.append(("Database Schema", False))
    except Exception as e:
        print(f"[ERROR] Database schema ({e})")
        results.append(("Database Schema", False))
    
    # Test 5: RL Tables Check
    print("\n5. Testing RL Integration...")
    try:
        # Test RL prediction endpoint
        rl_response = requests.post(
            f"{GATEWAY_URL}/api/v1/rl/predict",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"candidate_id": 1, "job_id": 1},
            timeout=30
        )
        # Note: This might return 404 if RL routes not available, which is expected
        if rl_response.status_code in [200, 404]:
            if rl_response.status_code == 200:
                print("[PASS] RL integration (Active)")
                results.append(("RL Integration", True))
            else:
                print("[PARTIAL] RL integration (Routes not active)")
                results.append(("RL Integration", "Partial"))
        else:
            print(f"[FAIL] RL integration ({rl_response.status_code})")
            results.append(("RL Integration", False))
    except Exception as e:
        print(f"[ERROR] RL integration ({e})")
        results.append(("RL Integration", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("AUTHENTICATION SYSTEM TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    partial = sum(1 for _, result in results if result == "Partial")
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result is True else "[PARTIAL]" if result == "Partial" else "[FAIL]"
        print(f"{test_name:20s}: {status}")
    
    print(f"\nOverall: {passed}/{total} passed, {partial} partial")
    success_rate = (passed + partial * 0.5) / total * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\nAuthentication system is READY for automation sprint!")
        return True
    else:
        print("\nAuthentication system needs attention before automation sprint.")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = test_auth_system()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exit(0 if success else 1)