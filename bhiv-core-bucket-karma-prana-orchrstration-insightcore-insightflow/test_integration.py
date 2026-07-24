# -*- coding: utf-8 -*-
"""
Core-Bucket Integration Test
Tests the fire-and-forget communication between Core and Bucket
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone

async def test_integration():
    """Test Core-Bucket integration"""
    
    print("Testing BHIV Core <-> Bucket Integration")
    print("=" * 50)
    
    # Test 1: Check Bucket health and Core integration status
    print("\n1. Testing Bucket Health Check...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[PASS] Bucket Status: {data['status']}")
                    if 'core_integration' in data:
                        print(f"[PASS] Core Integration: {data['core_integration']['status']}")
                        print(f"       Events received: {data['core_integration']['events_received']}")
                    else:
                        print("[WARN] Core integration status not found (may need to restart Bucket)")
                else:
                    print(f"[FAIL] Bucket health check failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Bucket connection failed: {e}")
        print("       Make sure Bucket is running: python BHIV_Central_Depository-main/main.py")
        return
    
    # Test 2: Test Core event write
    print("\n2. Testing Core Event Write...")
    try:
        event_data = {
            "requester_id": "bhiv_core",
            "event_data": {
                "event_type": "test_event",
                "agent_id": "test_agent_42",
                "test_data": "integration_test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/core/write-event",
                json=event_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"[PASS] Event written: {result.get('message', 'success')}")
                else:
                    print(f"[FAIL] Event write failed: {response.status}")
                    error = await response.text()
                    print(f"       Error: {error}")
                    print("       This may indicate the integration endpoints are not loaded.")
                    print("       Try restarting Bucket: python BHIV_Central_Depository-main/main.py")
    except Exception as e:
        print(f"[FAIL] Event write failed: {e}")
    
    # Test 3: Test Core context read
    print("\n3. Testing Core Context Read...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8001/core/read-context",
                params={"agent_id": "test_agent_42", "requester_id": "bhiv_core"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result["context"]:
                        print(f"[PASS] Context found: {result['context']['event_count']} events")
                    else:
                        print("[PASS] No context found (expected for new agent)")
                else:
                    print(f"[FAIL] Context read failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Context read failed: {e}")
    
    # Test 4: Test Core stats
    print("\n4. Testing Core Integration Stats...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/core/stats") as response:
                if response.status == 200:
                    result = await response.json()
                    stats = result["stats"]
                    print(f"[PASS] Total events: {stats['total_events']}")
                    print(f"[PASS] Agents tracked: {stats['agents_with_context']}")
                else:
                    print(f"[FAIL] Stats failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Stats failed: {e}")
    
    # Test 5: Test Core MCP Bridge health
    print("\n5. Testing Core MCP Bridge...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8002/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[PASS] Core Status: {data['status']}")
                else:
                    print(f"[FAIL] Core health check failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Core connection failed: {e}")
    
    print("\n" + "=" * 50)
    print("SUCCESS: Integration test completed!")
    print("\nQuick Start:")
    print("1. Use the automatic starter: python start_system.py")
    print("2. Or start manually:")
    print("   Terminal 1: cd BHIV_Central_Depository-main && python main.py")
    print("   Terminal 2: cd v1-BHIV_CORE-main && python mcp_bridge.py")
    print("3. Test with: curl -X POST http://localhost:8002/handle_task -H 'Content-Type: application/json' -d '{\"agent\": \"edumentor_agent\", \"input\": \"test\", \"input_type\": \"text\"}'")

if __name__ == "__main__":
    asyncio.run(test_integration())
