#!/usr/bin/env python3
"""Test HTTP client fixes in HR Portal"""

import asyncio
import httpx
import os

# Test endpoints
ENDPOINTS = {
    "Gateway Health": "http://localhost:8000/health",
    "Jobs List": "http://localhost:8000/v1/jobs", 
    "Candidates Search": "http://localhost:8000/v1/candidates/search?job_id=1",
    "Interviews List": "http://localhost:8000/v1/interviews",
    "LangGraph Health": "http://localhost:9001/health",
    "LangGraph Notification": "http://localhost:9001/tools/send-notification"
}

API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def test_endpoint(name, url, method="GET", json_data=None):
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=HEADERS, timeout=5.0)
            else:
                response = await client.post(url, headers=HEADERS, json=json_data, timeout=5.0)
            
            if response.status_code == 200:
                return f"PASS {name}: ({response.status_code})"
            else:
                return f"FAIL {name}: ({response.status_code})"
    except httpx.ConnectError:
        return f"CONN {name}: CONNECTION FAILED"
    except httpx.TimeoutException:
        return f"TIME {name}: TIMEOUT"
    except Exception as e:
        return f"ERR {name}: ERROR - {str(e)[:30]}"

async def test_notification():
    test_data = {
        "candidate_name": "Test User",
        "candidate_email": "test@example.com", 
        "candidate_phone": "+1234567890",
        "job_title": "Test Job",
        "message": "Test notification",
        "channels": ["email"],
        "application_status": "test"
    }
    
    return await test_endpoint(
        "LangGraph Notification", 
        ENDPOINTS["LangGraph Notification"],
        "POST", 
        test_data
    )

async def main():
    print("Testing HTTP Client Fixes")
    print("=" * 40)
    
    # Test GET endpoints
    get_tests = [
        test_endpoint(name, url) 
        for name, url in ENDPOINTS.items() 
        if name != "LangGraph Notification"
    ]
    
    # Test POST endpoint
    post_test = test_notification()
    
    # Run all tests
    results = await asyncio.gather(*get_tests, post_test)
    
    for result in results:
        print(result)
    
    # Summary
    passed = sum(1 for r in results if "PASS" in r)
    total = len(results)
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("All HTTP client fixes working!")
    else:
        print("Some endpoints need attention")

if __name__ == "__main__":
    asyncio.run(main())