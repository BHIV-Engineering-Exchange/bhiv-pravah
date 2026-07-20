#!/usr/bin/env python3
"""Simple service test without Unicode issues"""

import httpx
import asyncio

SERVICES = {
    "Gateway": "http://localhost:8000",
    "Agent": "http://localhost:9000", 
    "LangGraph": "http://localhost:9001",
    "HR Portal": "http://localhost:8501",
    "Client Portal": "http://localhost:8502",
    "Candidate Portal": "http://localhost:8503"
}

API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def check_service(name, url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/health", headers=HEADERS, timeout=5.0)
            if response.status_code == 200:
                return f"{name}: HEALTHY"
            else:
                return f"{name}: UNHEALTHY ({response.status_code})"
    except httpx.TimeoutException:
        return f"{name}: TIMEOUT"
    except httpx.ConnectError:
        return f"{name}: CONNECTION FAILED"
    except Exception as e:
        return f"{name}: ERROR - {str(e)[:30]}"

async def test_communication():
    try:
        async with httpx.AsyncClient() as client:
            test_data = {
                "candidate_name": "Test User",
                "candidate_email": "shashankmishra0411@gmail.com",
                "candidate_phone": "+919284967526",
                "job_title": "Test Position",
                "message": "Test notification",
                "channels": ["email"],
                "application_status": "test"
            }
            
            response = await client.post(
                "http://localhost:9001/tools/send-notification",
                json=test_data,
                headers=HEADERS,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return "Communication Test: PASSED"
            else:
                return f"Communication Test: FAILED ({response.status_code})"
    except Exception as e:
        return f"Communication Test: ERROR - {str(e)[:30]}"

async def main():
    print("BHIV HR Platform - Service Health Check")
    print("=" * 50)
    
    # Test all services
    tasks = [check_service(name, url) for name, url in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(result)
    
    print()
    
    # Test communication
    comm_result = await test_communication()
    print(comm_result)
    
    print()
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())