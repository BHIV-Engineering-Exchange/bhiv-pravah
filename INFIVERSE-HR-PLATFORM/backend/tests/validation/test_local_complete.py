#!/usr/bin/env python3
"""
Complete Local Testing Suite for BHIV HR Platform
Tests all services locally before Render deployment
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Local service URLs
SERVICES = {
    "gateway": "http://localhost:8000",
    "agent": "http://localhost:9000", 
    "langgraph": "http://localhost:9001",
    "hr_portal": "http://localhost:8501",
    "client_portal": "http://localhost:8502",
    "candidate_portal": "http://localhost:8503"
}

API_KEY = "test-api-key-12345"

async def test_all_services():
    """Test all services are running"""
    print("🔍 Testing All Local Services...")
    
    async with aiohttp.ClientSession() as session:
        for service, url in SERVICES.items():
            try:
                if service.endswith('_portal'):
                    # Streamlit services - just check if accessible
                    async with session.get(url, timeout=5) as resp:
                        status = "✅ RUNNING" if resp.status == 200 else f"❌ ERROR {resp.status}"
                else:
                    # API services - check health endpoint
                    async with session.get(f"{url}/health", timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            status = f"✅ HEALTHY - {data.get('status', 'OK')}"
                        else:
                            status = f"❌ ERROR {resp.status}"
                            
                print(f"  {service.upper()}: {status}")
                
            except Exception as e:
                print(f"  {service.upper()}: ❌ OFFLINE - {str(e)}")

async def test_langgraph_integration():
    """Test LangGraph service specifically"""
    print("\n🤖 Testing LangGraph Service...")
    
    async with aiohttp.ClientSession() as session:
        # Test workflow start
        test_data = {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_name": "Test User",
            "candidate_email": "test@example.com",
            "job_title": "Software Engineer"
        }
        
        try:
            async with session.post(f"{SERVICES['langgraph']}/workflows/application/start", json=test_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"  ✅ Workflow Started: {result.get('workflow_id')}")
                    return True
                else:
                    print(f"  ❌ Workflow Failed: HTTP {resp.status}")
                    return False
        except Exception as e:
            print(f"  ❌ LangGraph Error: {e}")
            return False

if __name__ == "__main__":
    print("🚀 BHIV HR Platform - Local Testing Suite")
    print("=" * 50)
    
    asyncio.run(test_all_services())
    asyncio.run(test_langgraph_integration())
    
    print("\n📋 Next Steps:")
    print("1. If all services are running ✅, proceed to Render deployment")
    print("2. If any service fails ❌, check Docker containers: docker-compose ps")
    print("3. View logs: docker-compose logs [service-name]")