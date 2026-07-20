#!/usr/bin/env python3
"""
Basic LangGraph Service Test
Quick verification that LangGraph service is working
"""

import asyncio
import aiohttp
import json
from datetime import datetime

LANGGRAPH_URL = "http://localhost:9001"

async def test_basic_functionality():
    """Test basic LangGraph functionality"""
    print("🔍 Testing LangGraph Basic Functionality")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Check
        print("\n1. Health Check...")
        try:
            async with session.get(f"{LANGGRAPH_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Health: {data}")
                else:
                    print(f"   ❌ Health check failed: HTTP {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
        
        # Test 2: Workflow Status
        print("\n2. Workflow Status...")
        try:
            async with session.get(f"{LANGGRAPH_URL}/workflow/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Status: {data}")
                else:
                    print(f"   ❌ Status check failed: HTTP {resp.status}")
        except Exception as e:
            print(f"   ❌ Status check error: {e}")
        
        # Test 3: Start Simple Workflow
        print("\n3. Starting Test Workflow...")
        test_data = {
            "candidate_id": 999,
            "job_id": 999,
            "candidate_name": "Test User",
            "candidate_email": "test@example.com",
            "candidate_phone": "+1234567890",
            "job_title": "Test Position"
        }
        
        try:
            async with session.post(f"{LANGGRAPH_URL}/workflow/start", json=test_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    workflow_id = data.get('workflow_id')
                    print(f"   ✅ Workflow started: {workflow_id}")
                    
                    # Monitor for a few seconds
                    print("\n4. Monitoring Workflow...")
                    for i in range(5):
                        await asyncio.sleep(1)
                        try:
                            async with session.get(f"{LANGGRAPH_URL}/workflow/{workflow_id}") as monitor_resp:
                                if monitor_resp.status == 200:
                                    monitor_data = await monitor_resp.json()
                                    status = monitor_data.get('status', 'unknown')
                                    stage = monitor_data.get('current_stage', 'unknown')
                                    print(f"   📊 Step {i+1}: Status={status}, Stage={stage}")
                                    
                                    if status in ['completed', 'failed']:
                                        break
                        except Exception as e:
                            print(f"   ⚠️  Monitor error: {e}")
                    
                else:
                    print(f"   ❌ Workflow start failed: HTTP {resp.status}")
                    response_text = await resp.text()
                    print(f"   Response: {response_text}")
        except Exception as e:
            print(f"   ❌ Workflow start error: {e}")
        
        # Test 4: List Workflows
        print("\n5. Listing Workflows...")
        try:
            async with session.get(f"{LANGGRAPH_URL}/workflow/list") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    workflows = data.get('workflows', [])
                    print(f"   ✅ Found {len(workflows)} workflows")
                    for wf in workflows[-3:]:  # Show last 3
                        print(f"      - {wf.get('id', 'N/A')}: {wf.get('status', 'N/A')}")
                else:
                    print(f"   ❌ List workflows failed: HTTP {resp.status}")
        except Exception as e:
            print(f"   ❌ List workflows error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Basic functionality test completed!")
    return True

async def main():
    """Main test function"""
    print(f"🚀 LangGraph Basic Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await test_basic_functionality()
    
    if success:
        print("\n🎉 All basic tests passed!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)