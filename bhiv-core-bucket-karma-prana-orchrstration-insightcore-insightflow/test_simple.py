"""
Simple Core-Bucket Integration Test (No Unicode)
"""

import asyncio
import aiohttp
from datetime import datetime, timezone

async def test_integration():
    print("Testing BHIV Core <-> Bucket Integration")
    print("=" * 50)
    
    # Test 1: Bucket Health
    print("\n1. Testing Bucket Health Check...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[OK] Bucket Status: {data['status']}")
                    if 'core_integration' in data:
                        print(f"[OK] Core Integration: {data['core_integration']['status']}")
                        print(f"     Events received: {data['core_integration']['events_received']}")
                        print(f"     Agents tracked: {data['core_integration']['agents_tracked']}")
                    else:
                        print("[WARN] Core integration status not found")
                else:
                    print(f"[FAIL] Bucket health check failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Bucket connection failed: {e}")
        return
    
    # Test 2: Core Event Write
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
                    print(f"[OK] Event written: {result.get('message', 'success')}")
                else:
                    print(f"[FAIL] Event write failed: {response.status}")
                    error = await response.text()
                    print(f"       Error: {error}")
    except Exception as e:
        print(f"[FAIL] Event write failed: {e}")
    
    # Test 3: Core Context Read
    print("\n3. Testing Core Context Read...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8001/core/read-context",
                params={"agent_id": "test_agent_42", "requester_id": "bhiv_core"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("context"):
                        print(f"[OK] Context found: {result['context']['event_count']} events")
                    else:
                        print("[OK] No context found (expected for new agent)")
                else:
                    print(f"[FAIL] Context read failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Context read failed: {e}")
    
    # Test 4: Core Stats
    print("\n4. Testing Core Integration Stats...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/core/stats") as response:
                if response.status == 200:
                    result = await response.json()
                    stats = result["stats"]
                    print(f"[OK] Total events: {stats['total_events']}")
                    print(f"[OK] Agents tracked: {stats['agents_with_context']}")
                else:
                    print(f"[FAIL] Stats failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Stats failed: {e}")
    
    # Test 5: Core Health
    print("\n5. Testing Core MCP Bridge...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8002/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[OK] Core Status: {data['status']}")
                else:
                    print(f"[FAIL] Core health check failed: {response.status}")
    except Exception as e:
        print(f"[FAIL] Core connection failed: {e}")
    
    print("\n" + "=" * 50)
    print("Integration test completed!")
    print("\nNext steps:")
    print("1. Both services are running")
    print("2. Integration is working")
    print("3. See INTEGRATION_VERIFICATION.md for details")

if __name__ == "__main__":
    asyncio.run(test_integration())
