#!/usr/bin/env python3
"""Test all portals to verify HTTP client compatibility"""

import asyncio
import httpx

API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

PORTALS = {
    "HR Portal": "http://localhost:8501",
    "Client Portal": "http://localhost:8502", 
    "Candidate Portal": "http://localhost:8503"
}

async def test_portal_health(name, url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/", timeout=5.0)
            if response.status_code == 200:
                return f"PASS {name}: Portal accessible"
            else:
                return f"FAIL {name}: HTTP {response.status_code}"
    except httpx.ConnectError:
        return f"CONN {name}: Not running"
    except Exception as e:
        return f"ERR {name}: {str(e)[:30]}"

async def test_backend_apis():
    """Test backend APIs that portals depend on"""
    apis = {
        "Gateway API": "http://localhost:8000/health",
        "Jobs API": "http://localhost:8000/v1/jobs",
        "Candidates API": "http://localhost:8000/v1/candidates/search?job_id=1"
    }
    
    results = []
    async with httpx.AsyncClient() as client:
        for name, url in apis.items():
            try:
                response = await client.get(url, headers=HEADERS, timeout=5.0)
                if response.status_code == 200:
                    results.append(f"PASS {name}: Working")
                else:
                    results.append(f"FAIL {name}: HTTP {response.status_code}")
            except Exception as e:
                results.append(f"ERR {name}: {str(e)[:30]}")
    
    return results

async def main():
    print("Testing All Portals Compatibility")
    print("=" * 40)
    
    # Test portal accessibility
    portal_tests = [test_portal_health(name, url) for name, url in PORTALS.items()]
    portal_results = await asyncio.gather(*portal_tests)
    
    # Test backend APIs
    api_results = await test_backend_apis()
    
    print("Portal Status:")
    for result in portal_results:
        print(f"  {result}")
    
    print("\nBackend API Status:")
    for result in api_results:
        print(f"  {result}")
    
    # Summary
    portal_passed = sum(1 for r in portal_results if "PASS" in r)
    api_passed = sum(1 for r in api_results if "PASS" in r)
    
    print(f"\nResults:")
    print(f"  Portals: {portal_passed}/{len(PORTALS)} accessible")
    print(f"  APIs: {api_passed}/{len(api_results)} working")
    
    if portal_passed == len(PORTALS) and api_passed == len(api_results):
        print("All systems compatible!")
    else:
        print("Some systems need attention")

if __name__ == "__main__":
    asyncio.run(main())