#!/usr/bin/env python3
"""
Test LangGraph Integration with Gateway Service
"""

import asyncio
import aiohttp
import json

# Service URLs
GATEWAY_URL = "http://localhost:8000"
LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "test-api-key-12345"

async def test_integration():
    """Test LangGraph integration endpoints"""
    print("🔍 Testing LangGraph Integration...")
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Test 1: Gateway health
        try:
            async with session.get(f"{GATEWAY_URL}/health") as resp:
                if resp.status == 200:
                    print("✅ Gateway service: HEALTHY")
                else:
                    print(f"❌ Gateway service: ERROR {resp.status}")
        except Exception as e:
            print(f"❌ Gateway service: OFFLINE - {e}")
        
        # Test 2: LangGraph health
        try:
            async with session.get(f"{LANGGRAPH_URL}/health") as resp:
                if resp.status == 200:
                    print("✅ LangGraph service: HEALTHY")
                else:
                    print(f"❌ LangGraph service: ERROR {resp.status}")
        except Exception as e:
            print(f"❌ LangGraph service: OFFLINE - {e}")
        
        # Test 3: Gateway LangGraph health check
        try:
            async with session.get(f"{GATEWAY_URL}/api/v1/workflow/health", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Gateway → LangGraph: {data.get('langgraph_status', 'unknown')}")
                else:
                    print(f"❌ Gateway → LangGraph: ERROR {resp.status}")
        except Exception as e:
            print(f"❌ Gateway → LangGraph: FAILED - {e}")
        
        # Test 4: Workflow trigger
        try:
            workflow_data = {
                "candidate_id": 1,
                "job_id": 1,
                "candidate_name": "Test User",
                "candidate_email": "test@example.com",
                "job_title": "Software Engineer"
            }
            
            async with session.post(f"{GATEWAY_URL}/api/v1/workflow/trigger", 
                                  json=workflow_data, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Workflow trigger: {data.get('status', 'unknown')}")
                else:
                    print(f"❌ Workflow trigger: ERROR {resp.status}")
        except Exception as e:
            print(f"❌ Workflow trigger: FAILED - {e}")

if __name__ == "__main__":
    print("🚀 LangGraph Integration Test")
    print("=" * 40)
    asyncio.run(test_integration())
    print("\n📋 Next Steps:")
    print("1. Ensure both Gateway and LangGraph services are running")
    print("2. Check environment variables (LANGGRAPH_URL)")
    print("3. Verify API authentication is working")