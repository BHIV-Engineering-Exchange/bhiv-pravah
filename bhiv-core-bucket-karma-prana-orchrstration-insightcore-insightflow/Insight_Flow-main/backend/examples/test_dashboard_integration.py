# examples/test_dashboard_integration.py
"""
Test script to verify dashboard integration.
"""

import asyncio
import aiohttp
from datetime import datetime


async def test_dashboard_integration():
    """Test dashboard endpoints integration"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing Dashboard Integration ===\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. First, make some routing requests to generate data
            print("1. Generating sample routing data...")
            
            for i in range(3):
                route_request = {
                    "agent_type": "nlp",
                    "context": {"priority": "normal"},
                    "request_id": f"dashboard-test-{i}"
                }
                
                async with session.post(
                    f"{base_url}/api/v1/routing/route-agent",
                    json=route_request
                ) as response:
                    if response.status == 200:
                        print(f"  ✓ Generated routing decision {i+1}")
                    else:
                        print(f"  ✗ Failed to generate routing decision {i+1}")
            
            # Wait for logging to complete
            await asyncio.sleep(1)
            print()
            
            # 2. Test dashboard endpoints (without auth - should fail)
            print("2. Testing dashboard endpoint protection...")
            
            endpoints = [
                "/dashboard/metrics/performance",
                "/dashboard/metrics/accuracy", 
                "/dashboard/metrics/agents"
            ]
            
            for endpoint in endpoints:
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status == 200:
                        print(f"  ✓ {endpoint}: Available (status {response.status})")
                    else:
                        print(f"  ✗ {endpoint}: Unexpected status {response.status}")
            print()
            
            # 3. Test public routing endpoints (should work)
            print("3. Testing public routing endpoints...")
            
            async with session.get(f"{base_url}/api/routing/statistics") as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get('statistics', {})
                    print(f"  ✓ Statistics: {stats.get('total_decisions', 0)} total decisions")
                else:
                    print(f"  ✗ Statistics endpoint failed: {response.status}")
            
            async with session.get(f"{base_url}/api/routing/decisions?limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    decisions = data.get('decisions', [])
                    print(f"  ✓ Recent decisions: {len(decisions)} found")
                    
                    if decisions:
                        latest = decisions[0]
                        print(f"    Latest: {latest.get('agent_selected')} "
                              f"(confidence: {latest.get('confidence_score', 0):.2f})")
                else:
                    print(f"  ✗ Decisions endpoint failed: {response.status}")
            print()
            
            # 4. Test API version info includes dashboard
            print("4. Testing API version info...")
            
            async with session.get(f"{base_url}/api/version") as response:
                if response.status == 200:
                    data = await response.json()
                    endpoints = data.get('endpoints', {})
                    
                    if 'dashboard' in endpoints:
                        dashboard_endpoints = endpoints['dashboard']
                        print(f"  ✓ Dashboard endpoints registered:")
                        for name, path in dashboard_endpoints.items():
                            if name != 'status':
                                print(f"    {name}: {path}")
                    else:
                        print("  ✗ Dashboard endpoints not found in API version")
                else:
                    print(f"  ✗ API version endpoint failed: {response.status}")
            print()
            
            print("=== Dashboard integration test completed ===")
            print("\nNote: Dashboard endpoints are now public (no authentication required).")
            print("Endpoints return direct data without wrapper objects.")
    
    except Exception as e:
        print(f"Error during testing: {str(e)}")


async def test_dashboard_service_directly():
    """Test dashboard service directly (without HTTP)"""
    
    print("=== Testing Dashboard Service Directly ===\n")
    
    try:
        from app.services.dashboard_service import get_dashboard_service
        
        dashboard_service = get_dashboard_service()
        
        # Test performance metrics
        print("1. Testing performance metrics...")
        metrics = await dashboard_service.get_performance_metrics(hours=24)
        print(f"  Total decisions: {metrics.get('total_decisions', 0)}")
        print(f"  Average confidence: {metrics.get('average_confidence', 0):.2f}")
        print()
        
        # Test accuracy metrics
        print("2. Testing accuracy metrics...")
        accuracy = await dashboard_service.get_routing_accuracy(hours=24)
        print(f"  Accuracy percentage: {accuracy.get('accuracy_percentage', 0):.1f}%")
        print()
        
        # Test agent performance
        print("3. Testing agent performance...")
        agents = await dashboard_service.get_agent_performance(hours=24)
        print(f"  Found {len(agents)} agents")
        
        for agent in agents[:3]:  # Show top 3
            print(f"    {agent['agent_id']}: {agent['total_decisions']} decisions")
        print()
        
        print("=== Direct service test completed ===")
    
    except Exception as e:
        print(f"Error testing service directly: {str(e)}")
        print("Make sure you're running this from the backend directory")


if __name__ == "__main__":
    print("Starting dashboard integration tests...")
    print("Make sure the server is running on http://localhost:8000\n")
    
    # Run HTTP integration tests
    asyncio.run(test_dashboard_integration())
    print()
    
    # Run direct service tests
    asyncio.run(test_dashboard_service_directly())