#!/usr/bin/env python3
"""
Authentication Flow Debug - Compare working vs failing authentication
"""

import asyncio
import httpx
import json

GATEWAY_URL = "http://localhost:8000"
API_KEY = "<YOUR_API_KEY>"

async def debug_auth_flow():
    """Debug the authentication flow differences"""
    print("Authentication Flow Debug")
    print("=" * 50)
    
    # Test data
    test_client = {
        "client_id": f"auth_debug_{int(asyncio.get_event_loop().time())}",
        "company_name": "Auth Debug Company",
        "contact_email": f"auth.debug.{int(asyncio.get_event_loop().time())}@test.com",
        "password": "AuthDebug123!"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        print("\n1. Direct API Key Test (Working)")
        print("-" * 40)
        
        # Test with API key directly
        headers = {'Authorization': f'Bearer {API_KEY}'}
        response = await client.get(f"{GATEWAY_URL}/v1/jobs", headers=headers)
        print(f"Direct API key test: {response.status_code}")
        if response.status_code == 200:
            print("API key works directly")
        else:
            print(f"API key failed: {response.text}")
        
        print("\n2. Client Registration & Login (Working)")
        print("-" * 40)
        
        # Register client (no auth needed)
        response = await client.post(f"{GATEWAY_URL}/v1/client/register", json=test_client)
        print(f"Client registration: {response.status_code}")
        
        if response.status_code == 200:
            reg_result = response.json()
            print(f"Registration result: {reg_result}")
            
            # Login client (no auth needed)
            login_data = {"client_id": test_client["client_id"], "password": test_client["password"]}
            response = await client.post(f"{GATEWAY_URL}/v1/client/login", json=login_data)
            print(f"Client login: {response.status_code}")
            
            if response.status_code == 200:
                login_result = response.json()
                print(f"Login result keys: {list(login_result.keys())}")
                
                if 'access_token' in login_result:
                    client_token = login_result['access_token']
                    print(f"Client token obtained: {client_token[:50]}...")
                    
                    print("\n3. JWT Token Test (Potentially Failing)")
                    print("-" * 40)
                    
                    # Test with JWT token
                    jwt_headers = {'Authorization': f'Bearer {client_token}'}
                    response = await client.get(f"{GATEWAY_URL}/v1/jobs", headers=jwt_headers)
                    print(f"JWT token test: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("JWT token works")
                        jobs_data = response.json()
                        print(f"Jobs returned: {jobs_data.get('count', 0)}")
                    else:
                        print(f"JWT token failed: {response.text}")
                        
                        # Try to understand why
                        print("\n4. Debugging JWT Failure")
                        print("-" * 40)
                        
                        # Check if it's a 401 Unauthorized
                        if response.status_code == 401:
                            print("401 Unauthorized - JWT validation failed")
                            print("Possible causes:")
                            print("- JWT secret mismatch")
                            print("- Token format issue")
                            print("- Token expiration")
                            print("- Authentication dependency issue")
                        
                        # Try with different endpoints
                        test_endpoints = [
                            "/v1/test-candidates",
                            "/v1/candidates/stats",
                            "/v1/database/schema"
                        ]
                        
                        for endpoint in test_endpoints:
                            response = await client.get(f"{GATEWAY_URL}{endpoint}", headers=jwt_headers)
                            print(f"JWT test {endpoint}: {response.status_code}")
                else:
                    print("No access_token in login response")
                    print(f"Available keys: {list(login_result.keys())}")
            else:
                print(f"Login failed: {response.text}")
        else:
            print(f"Registration failed: {response.text}")
        
        print("\n5. Comprehensive Test Simulation")
        print("-" * 40)
        
        # Simulate the comprehensive test's _make_authenticated_request method
        def make_auth_headers(service: str, api_key: str, client_token: str = None):
            headers = {"Content-Type": "application/json"}
            
            if service == "gateway":
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                # Client JWT token would override API key if present
                if client_token:
                    headers["Authorization"] = f"Bearer {client_token}"
            elif service in ["agent", "langgraph"]:
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            
            return headers
        
        # Test the comprehensive test's authentication logic
        if 'client_token' in locals():
            comp_headers = make_auth_headers("gateway", API_KEY, client_token)
            print(f"Comprehensive test headers: {comp_headers}")
            
            response = await client.get(f"{GATEWAY_URL}/v1/jobs", headers=comp_headers)
            print(f"Comprehensive test simulation: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Comprehensive test would fail: {response.text}")
                
                # Try without client token (API key only)
                api_only_headers = make_auth_headers("gateway", API_KEY, None)
                response = await client.get(f"{GATEWAY_URL}/v1/jobs", headers=api_only_headers)
                print(f"API key only test: {response.status_code}")
                
                if response.status_code == 200:
                    print("API key works, JWT token is the problem")
                else:
                    print("Both API key and JWT token fail")

if __name__ == "__main__":
    asyncio.run(debug_auth_flow())