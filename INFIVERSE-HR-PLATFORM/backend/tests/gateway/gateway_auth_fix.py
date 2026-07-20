#!/usr/bin/env python3
"""
Gateway Authentication Fix - Update comprehensive test to use correct authentication
"""

import asyncio
import httpx

GATEWAY_SERVICE_URL = "http://localhost:8000"
API_KEY = "<YOUR_API_KEY>"

async def analyze_gateway_endpoints():
    """Analyze which endpoints need API key vs JWT authentication"""
    print("Gateway Authentication Analysis")
    print("=" * 50)
    
    # Test data
    test_client = {
        "client_id": f"auth_fix_{int(asyncio.get_event_loop().time())}",
        "company_name": "Auth Fix Company", 
        "contact_email": f"auth.fix.{int(asyncio.get_event_loop().time())}@test.com",
        "password": "AuthFix123!"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Get JWT token
        print("1. Setting up JWT token...")
        response = await client.post(f"{GATEWAY_SERVICE_URL}/v1/client/register", json=test_client)
        if response.status_code == 200:
            login_data = {"client_id": test_client["client_id"], "password": test_client["password"]}
            response = await client.post(f"{GATEWAY_SERVICE_URL}/v1/client/login", json=login_data)
            if response.status_code == 200:
                client_token = response.json()['access_token']
                print(f"JWT token obtained: {client_token[:30]}...")
            else:
                print("Failed to get JWT token")
                return
        else:
            print("Failed to register client")
            return
        
        print("\n2. Testing endpoint authentication requirements...")
        
        # Endpoints that are failing in comprehensive test
        failing_endpoints = [
            "/v1/test-candidates",
            "/v1/candidates/stats", 
            "/v1/database/schema",
            "/v1/security/rate-limit-status",
            "/v1/security/blocked-ips",
            "/v1/security/test-input-validation",
            "/v1/security/validate-email",
            "/v1/security/validate-phone",
            "/v1/security/test-headers",
            "/v1/security/csp-policies",
            "/v1/security/test-auth",
            "/v1/auth/2fa/setup",
            "/v1/auth/2fa/status/test_user",
            "/v1/auth/2fa/qr/test_user",
            "/v1/auth/password/validate",
            "/v1/auth/password/generate",
            "/v1/auth/password/policy",
            "/v1/auth/password/security-tips",
            "/v1/candidates",
            "/v1/candidates/search",
            "/v1/interviews",
            "/v1/feedback",
            "/v1/match/1/top",
            "/v1/match/batch"
        ]
        
        # Test each endpoint with different auth methods
        results = {}
        
        for endpoint in failing_endpoints:
            print(f"\nTesting {endpoint}:")
            
            # Test with API key
            api_headers = {'Authorization': f'Bearer {API_KEY}'}
            try:
                if endpoint in ["/v1/security/test-input-validation", "/v1/security/validate-email", 
                               "/v1/security/validate-phone", "/v1/auth/password/validate", 
                               "/v1/auth/2fa/setup", "/v1/match/batch"]:
                    # POST endpoints
                    test_data = {"input_data": "test"} if "input-validation" in endpoint else \
                               {"email": "test@test.com"} if "validate-email" in endpoint else \
                               {"phone": "+919876543210"} if "validate-phone" in endpoint else \
                               {"password": "Test123!"} if "password/validate" in endpoint else \
                               {"user_id": "test_user"} if "2fa/setup" in endpoint else \
                               [1, 2] if "match/batch" in endpoint else {}
                    response = await client.post(f"{GATEWAY_SERVICE_URL}{endpoint}", json=test_data, headers=api_headers)
                else:
                    # GET endpoints
                    response = await client.get(f"{GATEWAY_SERVICE_URL}{endpoint}", headers=api_headers)
                api_status = response.status_code
            except Exception as e:
                api_status = f"ERROR: {e}"
            
            # Test with JWT token
            jwt_headers = {'Authorization': f'Bearer {client_token}'}
            try:
                if endpoint in ["/v1/security/test-input-validation", "/v1/security/validate-email",
                               "/v1/security/validate-phone", "/v1/auth/password/validate",
                               "/v1/auth/2fa/setup", "/v1/match/batch"]:
                    # POST endpoints
                    test_data = {"input_data": "test"} if "input-validation" in endpoint else \
                               {"email": "test@test.com"} if "validate-email" in endpoint else \
                               {"phone": "+919876543210"} if "validate-phone" in endpoint else \
                               {"password": "Test123!"} if "password/validate" in endpoint else \
                               {"user_id": "test_user"} if "2fa/setup" in endpoint else \
                               [1, 2] if "match/batch" in endpoint else {}
                    response = await client.post(f"{GATEWAY_SERVICE_URL}{endpoint}", json=test_data, headers=jwt_headers)
                else:
                    # GET endpoints
                    response = await client.get(f"{GATEWAY_SERVICE_URL}{endpoint}", headers=jwt_headers)
                jwt_status = response.status_code
            except Exception as e:
                jwt_status = f"ERROR: {e}"
            
            results[endpoint] = {
                "api_key": api_status,
                "jwt_token": jwt_status
            }
            
            # Determine which auth method works
            if api_status == 200:
                auth_method = "API_KEY"
            elif jwt_status == 200:
                auth_method = "JWT_TOKEN"
            elif api_status == jwt_status:
                auth_method = "BOTH_FAIL"
            else:
                auth_method = "UNKNOWN"
            
            print(f"  API Key: {api_status}, JWT: {jwt_status} -> {auth_method}")
        
        print("\n3. Authentication Summary:")
        print("-" * 30)
        
        api_key_endpoints = []
        jwt_endpoints = []
        both_fail_endpoints = []
        
        for endpoint, result in results.items():
            if result["api_key"] == 200:
                api_key_endpoints.append(endpoint)
            elif result["jwt_token"] == 200:
                jwt_endpoints.append(endpoint)
            else:
                both_fail_endpoints.append(endpoint)
        
        print(f"API Key Required ({len(api_key_endpoints)}):")
        for ep in api_key_endpoints:
            print(f"  - {ep}")
        
        print(f"\nJWT Token Works ({len(jwt_endpoints)}):")
        for ep in jwt_endpoints:
            print(f"  - {ep}")
        
        print(f"\nBoth Fail ({len(both_fail_endpoints)}):")
        for ep in both_fail_endpoints:
            print(f"  - {ep}")
        
        print(f"\n4. Recommendation:")
        print("-" * 20)
        print("The comprehensive test should:")
        print("1. Use API key authentication for most protected endpoints")
        print("2. Only use JWT tokens for endpoints that specifically require them")
        print("3. Update the _test_endpoint_with_auth method to prioritize API key over JWT")

if __name__ == "__main__":
    asyncio.run(analyze_gateway_endpoints())