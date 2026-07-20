#!/usr/bin/env python3
"""
Authentication System Test - Localhost Version
Tests authentication components on local development environment
"""
import requests
import json
from datetime import datetime

# Localhost Configuration
GATEWAY_URL = "http://localhost:8000"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"

def test_auth_localhost():
    """Test authentication system on localhost"""
    print("Authentication System Test - Localhost Environment")
    print("=" * 60)
    
    results = []
    
    # Test 1: Gateway Health Check
    print("\n1. Testing Gateway Health...")
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"   [PASS] Gateway is running: {response.status_code}")
            data = response.json()
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            results.append(("Gateway Health", True))
        else:
            print(f"   [FAIL] Gateway health check failed: {response.status_code}")
            results.append(("Gateway Health", False))
    except Exception as e:
        print(f"   [ERROR] Gateway not accessible: {e}")
        print("   Make sure the gateway service is running on localhost:8000")
        results.append(("Gateway Health", False))
        return False
    
    # Test 2: API Key Authentication
    print("\n2. Testing API Key Authentication...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/v1/candidates/stats",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   [PASS] API Key authentication successful")
            print(f"   Total candidates: {data.get('total_candidates', 0)}")
            print(f"   Active jobs: {data.get('active_jobs', 0)}")
            results.append(("API Key Auth", True))
        else:
            print(f"   [FAIL] API Key authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            results.append(("API Key Auth", False))
    except Exception as e:
        print(f"   [ERROR] API Key authentication: {e}")
        results.append(("API Key Auth", False))
    
    # Test 3: Client JWT Authentication
    print("\n3. Testing Client JWT Authentication...")
    try:
        # First, try to login
        login_response = requests.post(
            f"{GATEWAY_URL}/v1/client/login",
            json={"client_id": "TECH001", "password": "demo123"},
            timeout=30
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            if login_data.get("success") and "access_token" in login_data:
                print(f"   [PASS] Client JWT login successful")
                
                # Test using JWT token
                jwt_token = login_data["access_token"]
                jwt_response = requests.get(
                    f"{GATEWAY_URL}/v1/jobs",
                    headers={"Authorization": f"Bearer {jwt_token}"},
                    timeout=30
                )
                
                if jwt_response.status_code == 200:
                    jobs_data = jwt_response.json()
                    print(f"   [PASS] Client JWT usage successful")
                    print(f"   Jobs count: {jobs_data.get('count', 0)}")
                    results.append(("Client JWT Auth", True))
                else:
                    print(f"   [FAIL] Client JWT usage failed: {jwt_response.status_code}")
                    results.append(("Client JWT Auth", False))
            else:
                print(f"   [FAIL] Client JWT login failed - no token")
                results.append(("Client JWT Auth", False))
        else:
            print(f"   [FAIL] Client JWT login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            results.append(("Client JWT Auth", False))
    except Exception as e:
        print(f"   [ERROR] Client JWT authentication: {e}")
        results.append(("Client JWT Auth", False))
    
    # Test 4: 2FA Setup
    print("\n4. Testing 2FA Setup...")
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
                print(f"   [PASS] 2FA setup successful")
                print(f"   Secret length: {len(setup_data.get('secret', ''))}")
                print(f"   QR code generated: {'Yes' if setup_data.get('qr_code') else 'No'}")
                results.append(("2FA Setup", True))
            else:
                print(f"   [FAIL] 2FA setup incomplete - missing data")
                results.append(("2FA Setup", False))
        else:
            print(f"   [FAIL] 2FA setup failed: {setup_response.status_code}")
            print(f"   Response: {setup_response.text}")
            results.append(("2FA Setup", False))
    except Exception as e:
        print(f"   [ERROR] 2FA setup: {e}")
        results.append(("2FA Setup", False))
    
    # Test 5: Database Schema Check
    print("\n5. Testing Database Schema...")
    try:
        schema_response = requests.get(
            f"{GATEWAY_URL}/v1/analytics/schema",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        
        if schema_response.status_code == 200:
            schema_data = schema_response.json()
            if "schema_version" in schema_data and "total_tables" in schema_data:
                version = schema_data.get("schema_version", "unknown")
                tables = schema_data.get("total_tables", 0)
                print(f"   [PASS] Database schema accessible")
                print(f"   Schema version: {version}")
                print(f"   Total tables: {tables}")
                
                # Check for RL tables
                all_tables = schema_data.get("tables", [])
                rl_tables = [table for table in all_tables if "rl_" in table]
                print(f"   RL tables found: {len(rl_tables)}")
                for rl_table in rl_tables:
                    print(f"   - {rl_table}")
                
                results.append(("Database Schema", True))
            else:
                print(f"   [FAIL] Database schema incomplete")
                results.append(("Database Schema", False))
        else:
            print(f"   [FAIL] Database schema failed: {schema_response.status_code}")
            print(f"   Response: {schema_response.text}")
            results.append(("Database Schema", False))
    except Exception as e:
        print(f"   [ERROR] Database schema: {e}")
        results.append(("Database Schema", False))
    
    # Test 6: Password Management
    print("\n6. Testing Password Management...")
    try:
        # Test password validation
        password_response = requests.post(
            f"{GATEWAY_URL}/v1/password/validate",
            json={"password": "TestPassword123!"},
            timeout=30
        )
        
        if password_response.status_code == 200:
            password_data = password_response.json()
            print(f"   [PASS] Password validation working")
            print(f"   Password strength: {password_data.get('password_strength', 'unknown')}")
            print(f"   Score: {password_data.get('score', 0)}/100")
            results.append(("Password Management", True))
        else:
            print(f"   [FAIL] Password validation failed: {password_response.status_code}")
            results.append(("Password Management", False))
    except Exception as e:
        print(f"   [ERROR] Password management: {e}")
        results.append(("Password Management", False))
    
    # Test 7: Security Features
    print("\n7. Testing Security Features...")
    try:
        # Test rate limit status
        rate_limit_response = requests.get(
            f"{GATEWAY_URL}/v1/security/rate-limit-status",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        
        if rate_limit_response.status_code == 200:
            rate_data = rate_limit_response.json()
            print(f"   [PASS] Security features accessible")
            print(f"   Rate limiting: {rate_data.get('rate_limit_enabled', False)}")
            print(f"   Requests per minute: {rate_data.get('requests_per_minute', 0)}")
            results.append(("Security Features", True))
        else:
            print(f"   [FAIL] Security features failed: {rate_limit_response.status_code}")
            results.append(("Security Features", False))
    except Exception as e:
        print(f"   [ERROR] Security features: {e}")
        results.append(("Security Features", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("LOCALHOST AUTHENTICATION TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result is True else "[FAIL]"
        print(f"{test_name:25s}: {status}")
    
    print(f"\nOverall: {passed}/{total} passed")
    success_rate = passed / total * 100 if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Save results
    with open("auth_localhost_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "environment": "localhost",
            "gateway_url": GATEWAY_URL,
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "results": [
                {
                    "test_name": name,
                    "passed": result
                }
                for name, result in results
            ]
        }, f, indent=2)
    
    print(f"\nResults saved to: auth_localhost_results.json")
    
    if success_rate >= 70:
        print("\nAuthentication system is READY for automation sprint on localhost!")
        return True
    else:
        print("\nAuthentication system needs attention on localhost.")
        return False

if __name__ == "__main__":
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Make sure the gateway service is running on localhost:8000")
    print("Make sure the database is accessible and populated")
    print()
    
    success = test_auth_localhost()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    exit(0 if success else 1)