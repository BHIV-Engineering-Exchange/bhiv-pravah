#!/usr/bin/env python3
"""
Service Health Check Script
Tests all services for connectivity and basic functionality
"""

import httpx
import asyncio
import os
from datetime import datetime

# Service configurations
SERVICES = {
    "Gateway": "http://localhost:8000",
    "Agent": "http://localhost:9000", 
    "LangGraph": "http://localhost:9001",
    "HR Portal": "http://localhost:8501",
    "Client Portal": "http://localhost:8502",
    "Candidate Portal": "http://localhost:8503"
}

API_KEY = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def check_service(name: str, url: str) -> dict:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            # Try health endpoint first
            response = await client.get(f"{url}/health", headers=HEADERS, timeout=10.0)
            if response.status_code == 200:
                return {"service": name, "status": "✅ Healthy", "url": url, "response_time": "< 10s"}
            else:
                return {"service": name, "status": f"⚠️ Unhealthy ({response.status_code})", "url": url, "response_time": "< 10s"}
    
    except httpx.TimeoutException:
        return {"service": name, "status": "⏰ Timeout", "url": url, "response_time": "> 10s"}
    except httpx.ConnectError:
        return {"service": name, "status": "❌ Connection Failed", "url": url, "response_time": "N/A"}
    except Exception as e:
        return {"service": name, "status": f"❌ Error: {str(e)[:50]}", "url": url, "response_time": "N/A"}

async def test_langgraph_communication():
    """Test LangGraph communication functionality"""
    try:
        async with httpx.AsyncClient() as client:
            test_data = {
                "candidate_name": "Test User",
                "candidate_email": "test@example.com",
                "candidate_phone": "+1234567890",
                "job_title": "Test Position",
                "message": "Test notification",
                "channels": ["email"],
                "application_status": "test"
            }
            
            response = await client.post(
                "http://localhost:9001/tools/send-notification",
                json=test_data,
                headers=HEADERS,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return "✅ Communication Test Passed"
            else:
                return f"⚠️ Communication Test Failed ({response.status_code})"
    
    except Exception as e:
        return f"❌ Communication Test Error: {str(e)[:50]}"

async def main():
    """Main test function"""
    print("🔍 BHIV HR Platform - Service Health Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all services
    tasks = [check_service(name, url) for name, url in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    
    # Display results
    print("📊 Service Status:")
    print("-" * 50)
    for result in results:
        print(f"{result['service']:<15} | {result['status']:<25} | {result['response_time']}")
    
    print()
    
    # Test LangGraph communication
    print("📧 Communication Test:")
    print("-" * 50)
    comm_result = await test_langgraph_communication()
    print(f"LangGraph Comm   | {comm_result}")
    
    print()
    
    # Summary
    healthy_count = sum(1 for r in results if "✅" in r['status'])
    total_count = len(results)
    
    print("📈 Summary:")
    print("-" * 50)
    print(f"Healthy Services: {healthy_count}/{total_count}")
    print(f"System Status: {'✅ All Systems Operational' if healthy_count == total_count else '⚠️ Some Issues Detected'}")
    
    if healthy_count < total_count:
        print("\n💡 Troubleshooting Tips:")
        print("- Ensure Docker containers are running: docker-compose ps")
        print("- Check logs: docker-compose logs [service_name]")
        print("- Restart services: docker-compose restart")

if __name__ == "__main__":
    asyncio.run(main())