#!/usr/bin/env python3
"""
JWT Debug Test - Investigate Gateway JWT validation issues
"""

import asyncio
import httpx
import os
import jwt
from datetime import datetime, timezone

# Configuration
GATEWAY_SERVICE_URL = "http://localhost:8000"
API_KEY = "<YOUR_API_KEY>"
JWT_SECRET_KEY = "<YOUR_JWT_SECRET>"
CANDIDATE_JWT_SECRET_KEY = "<YOUR_CANDIDATE_JWT_SECRET>"

async def test_jwt_validation():
    """Test JWT validation with different configurations"""
    print("JWT Debug Test - Gateway Authentication Investigation")
    print("=" * 60)
    
    # Test data
    test_client = {
        "client_id": f"debug_client_{int(datetime.now().timestamp())}",
        "company_name": "Debug Test Company",
        "contact_email": f"debug.{int(datetime.now().timestamp())}@test.com",
        "password": "DebugPass123!"
    }
    
    test_candidate = {
        "name": "Debug Test Candidate",
        "email": f"debug.candidate.{int(datetime.now().timestamp())}@test.com",
        "phone": "+919876543210",
        "location": "Mumbai",
        "experience_years": 5,
        "technical_skills": "Python, FastAPI, PostgreSQL",
        "education_level": "Masters",
        "seniority_level": "Senior Developer",
        "password": "DebugPass123!"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        print("\n1. Testing API Key Authentication")
        print("-" * 40)
        
        # Test API key
        headers = {'Authorization': f'Bearer {API_KEY}'}
        response = await client.get(f"{GATEWAY_SERVICE_URL}/health", headers=headers)
        print(f"Health check with API key: {response.status_code}")
        
        # Test protected endpoint with API key
        response = await client.get(f"{GATEWAY_SERVICE_URL}/v1/test-candidates", headers=headers)
        print(f"Protected endpoint with API key: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        
        print("\n2. Client Registration & Login")
        print("-" * 40)
        
        # Register client
        response = await client.post(f"{GATEWAY_SERVICE_URL}/v1/client/register", json=test_client)
        print(f"Client registration: {response.status_code}")
        if response.status_code not in [200, 201]:
            print(f"Registration error: {response.text}")
            return
        
        # Login client
        login_data = {"client_id": test_client["client_id"], "password": test_client["password"]}
        response = await client.post(f"{GATEWAY_SERVICE_URL}/v1/client/login", json=login_data)
        print(f"Client login: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            if login_result.get('success') and 'access_token' in login_result:
                client_token = login_result['access_token']
                print(f"Client token obtained: {client_token[:50]}...")
                
                # Test JWT token validation
                print("\n3. JWT Token Validation")
                print("-" * 40)
                
                # Decode token to check payload
                try:
                    decoded = jwt.decode(client_token, JWT_SECRET_KEY, algorithms=["HS256"])
                    print(f"Token decoded successfully: {decoded}")
                except Exception as e:
                    print(f"Token decode failed: {e}")
                
                # Test protected endpoint with JWT
                jwt_headers = {'Authorization': f'Bearer {client_token}'}
                response = await client.get(f"{GATEWAY_SERVICE_URL}/v1/jobs", headers=jwt_headers)
                print(f"Jobs endpoint with JWT: {response.status_code}")
                if response.status_code != 200:
                    print(f"JWT Error: {response.text}")
                
                # Test different JWT secrets
                print("\n4. Testing Different JWT Secrets")
                print("-" * 40)
                
                # Try with JWT_SECRET_KEY (alternative)
                try:
                    decoded_alt = jwt.decode(client_token, "<YOUR_JWT_SECRET>", algorithms=["HS256"])
                    print(f"Token works with JWT_SECRET_KEY: {decoded_alt}")
                except Exception as e:
                    print(f"JWT_SECRET_KEY failed: {e}")
                
            else:
                print(f"Login failed: {login_result}")
        else:
            print(f"Login request failed: {response.text}")
        
        print("\n5. Candidate Registration & Login")
        print("-" * 40)
        
        # Register candidate
        response = await client.post(f"{GATEWAY_SERVICE_URL}/v1/candidate/register", json=test_candidate)
        print(f"Candidate registration: {response.status_code}")
        if response.status_code not in [200, 201]:
            print(f"Registration error: {response.text}")
            return
        
        # Login candidate
        candidate_login = {"email": test_candidate["email"], "password": test_candidate["password"]}
        response = await client.post(f"{GATEWAY_SERVICE_URL}/v1/candidate/login", json=candidate_login)
        print(f"Candidate login: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            if login_result.get('success') and 'token' in login_result:
                candidate_token = login_result['token']
                print(f"Candidate token obtained: {candidate_token[:50]}...")
                
                # Test candidate JWT validation
                try:
                    decoded = jwt.decode(candidate_token, CANDIDATE_JWT_SECRET_KEY, algorithms=["HS256"])
                    print(f"Candidate token decoded: {decoded}")
                except Exception as e:
                    print(f"Candidate token decode failed: {e}")
                
                # Test protected endpoint with candidate JWT
                candidate_headers = {'Authorization': f'Bearer {candidate_token}'}
                response = await client.get(f"{GATEWAY_SERVICE_URL}/v1/jobs", headers=candidate_headers)
                print(f"Jobs endpoint with candidate JWT: {response.status_code}")
                if response.status_code != 200:
                    print(f"Candidate JWT Error: {response.text}")
            else:
                print(f"Candidate login failed: {login_result}")
        else:
            print(f"Candidate login request failed: {response.text}")
        
        print("\n6. Environment Variable Check")
        print("-" * 40)
        print(f"API_KEY_SECRET matches: {'<YOUR_API_KEY>' == API_KEY}")
        print(f"JWT_SECRET_KEY matches: {'<YOUR_JWT_SECRET>' == JWT_SECRET_KEY}")
        print(f"CANDIDATE_JWT_SECRET_KEY matches: {'<YOUR_CANDIDATE_JWT_SECRET>' == CANDIDATE_JWT_SECRET_KEY}")

if __name__ == "__main__":
    asyncio.run(test_jwt_validation())