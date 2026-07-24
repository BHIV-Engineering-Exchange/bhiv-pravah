# examples/test_integration.py
"""
Test script to verify route-agent logging integration.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_route_agent_logging():
    """Test route-agent endpoint with logging"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing Route-Agent Logging Integration ===\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Test route-agent endpoint
            print("1. Testing route-agent endpoint...")
            
            route_request = {
                "agent_type": "nlp",
                "context": {
                    "priority": "normal",
                    "domain": "text_processing"
                },
                "confidence_threshold": 0.5,
                "request_id": f"test-{datetime.utcnow().strftime('%H%M%S')}"
            }
            
            async with session.post(
                f"{base_url}/api/v1/routing/route-agent",
                json=route_request
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Route-agent successful:")
                    print(f"  Agent: {data.get('agent_id')}")
                    print(f"  Confidence: {data.get('confidence_score', 0):.2f}")
                    print(f"  Request ID: {data.get('request_id')}")
                    print()
                else:
                    print(f"✗ Route-agent failed: {response.status}")
                    error_text = await response.text()
                    print(f"  Error: {error_text}")
                    return
            
            # 2. Check if decision was logged
            print("2. Checking routing logs...")
            
            # Wait a moment for logging to complete
            await asyncio.sleep(0.5)
            
            async with session.get(
                f"{base_url}/api/routing/decisions?limit=5"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    decisions = data.get('decisions', [])
                    
                    if decisions:
                        latest = decisions[0]
                        print(f"✓ Latest decision logged:")
                        print(f"  Agent: {latest.get('agent_selected')}")
                        print(f"  Confidence: {latest.get('confidence_score', 0):.2f}")
                        print(f"  Request ID: {latest.get('request_id')}")
                        print(f"  Response Time: {latest.get('response_time_ms', 0):.1f}ms")
                        print()
                    else:
                        print("✗ No decisions found in logs")
                        print()
                else:
                    print(f"✗ Failed to get routing logs: {response.status}")
                    print()
            
            # 3. Check routing statistics
            print("3. Checking routing statistics...")
            
            async with session.get(
                f"{base_url}/api/routing/statistics"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get('statistics', {})
                    
                    print(f"✓ Routing statistics:")
                    print(f"  Total decisions: {stats.get('total_decisions', 0)}")
                    print(f"  Average confidence: {stats.get('avg_confidence', 0):.2f}")
                    print(f"  Unique agents: {stats.get('unique_agents', 0)}")
                    if 'avg_response_time_ms' in stats:
                        print(f"  Avg response time: {stats['avg_response_time_ms']:.1f}ms")
                    print()
                else:
                    print(f"✗ Failed to get statistics: {response.status}")
                    print()
            
            print("=== Integration test completed ===")
    
    except Exception as e:
        print(f"Error during testing: {str(e)}")


async def test_admin_endpoints():
    """Test admin endpoints (requires authentication)"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing Admin Endpoints (without auth) ===\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test admin endpoints (should return 401/403 without auth)
            endpoints = [
                "/admin/routing-logs",
                "/admin/routing-statistics",
                "/admin/system-health"
            ]
            
            for endpoint in endpoints:
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status in [401, 403]:
                        print(f"✓ {endpoint}: Properly protected (status {response.status})")
                    else:
                        print(f"✗ {endpoint}: Unexpected status {response.status}")
            
            print("\nNote: Admin endpoints require authentication.")
            print("Use a valid JWT token to access these endpoints.")
    
    except Exception as e:
        print(f"Error testing admin endpoints: {str(e)}")


if __name__ == "__main__":
    print("Starting integration tests...")
    print("Make sure the server is running on http://localhost:8000\n")
    
    # Run tests
    asyncio.run(test_route_agent_logging())
    print()
    asyncio.run(test_admin_endpoints())