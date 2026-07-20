#!/usr/bin/env python3
"""
Quick Agent Service Status Check
"""

import requests
import time

AGENT_URL = "https://bhiv-hr-agent-nhgg.onrender.com"
API_KEY = "<YOUR_API_KEY>"

def check_agent():
    print("Checking Agent Service Status...")
    print(f"URL: {AGENT_URL}")
    
    # Test 1: Basic health check
    try:
        print("\n1. Health Check...")
        response = requests.get(f"{AGENT_URL}/health", timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
    except requests.exceptions.Timeout:
        print("   TIMEOUT: Service may be sleeping (Render free tier)")
    except requests.exceptions.ConnectionError:
        print("   CONNECTION ERROR: Service may be down")
    except Exception as e:
        print(f"   ERROR: {str(e)}")
    
    # Test 2: Try to wake up service
    print("\n2. Attempting to wake up service...")
    for i in range(3):
        try:
            print(f"   Attempt {i+1}/3...")
            response = requests.get(f"{AGENT_URL}/", timeout=90)
            if response.status_code == 200:
                print("   SUCCESS: Service is now responding!")
                return True
            else:
                print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   Failed: {str(e)}")
        
        if i < 2:  # Don't sleep after last attempt
            time.sleep(10)
    
    return False

def test_ai_endpoint():
    print("\n3. Testing AI Match Endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"job_id": 1, "candidate_ids": []}
        
        response = requests.post(
            f"{AGENT_URL}/match", 
            json=payload, 
            headers=headers, 
            timeout=60
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Algorithm: {data.get('algorithm_version', 'unknown')}")
            print(f"   Candidates: {len(data.get('top_candidates', []))}")
            return True
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Agent Service Diagnostic")
    print("=" * 40)
    
    # Check if service is responding
    service_up = check_agent()
    
    if service_up:
        # Test AI functionality
        ai_working = test_ai_endpoint()
        
        print("\n" + "=" * 40)
        print("DIAGNOSIS RESULTS")
        print("=" * 40)
        
        if ai_working:
            print("PASS - Agent Service is fully operational")
            print("The Gateway should now connect successfully")
        else:
            print("PARTIAL - Service is up but AI endpoints failing")
            print("Check Agent service logs for internal errors")
    else:
        print("\n" + "=" * 40)
        print("DIAGNOSIS RESULTS")
        print("=" * 40)
        print("FAIL - Agent Service is not responding")
        print("\nMost likely cause: Render free tier service sleeping")
        print("\nSolutions:")
        print("1. Wait 2-3 minutes and try again")
        print("2. Make a request to wake up the service")
        print("3. Check Render dashboard for service status")
        print("4. Gateway fallback is currently handling requests")
