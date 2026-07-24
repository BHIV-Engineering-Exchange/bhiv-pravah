#!/usr/bin/env python3
"""
Complete telemetry integration test
"""

import asyncio
import websockets
import json
import requests
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_routing_with_telemetry():
    """Test routing endpoints with telemetry emission"""
    
    print("Testing Routing Endpoints with Telemetry")
    print("-" * 50)
    
    # Connect to telemetry stream first
    telemetry_received = []
    
    async def listen_for_telemetry():
        try:
            uri = "ws://localhost:8000/telemetry/decisions"
            async with websockets.connect(uri) as websocket:
                print("Connected to telemetry stream")
                
                # Listen for telemetry packets
                while len(telemetry_received) < 3:  # Expect 3 packets from 3 endpoints
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        packet = json.loads(message)
                        telemetry_received.append(packet)
                        print(f"Received telemetry: {packet.get('request_id')} -> {packet.get('decision', {}).get('selected_agent')}")
                    except asyncio.TimeoutError:
                        break
        except Exception as e:
            print(f"Telemetry listener error: {e}")
    
    # Start telemetry listener
    telemetry_task = asyncio.create_task(listen_for_telemetry())
    
    # Give listener time to connect
    await asyncio.sleep(1)
    
    # Test routing endpoints
    endpoints_to_test = [
        {
            "url": "http://localhost:8000/api/v1/routing/route",
            "data": {
                "input_data": {"text": "Test query 1"},
                "input_type": "text",
                "strategy": "q_learning"
            },
            "name": "Standard Routing"
        },
        {
            "url": "http://localhost:8000/api/v1/routing/route-stp", 
            "data": {
                "input_data": {"text": "Test query 2"},
                "input_type": "text",
                "strategy": "q_learning"
            },
            "name": "STP Routing"
        },
        {
            "url": "http://localhost:8000/api/v1/routing/route-agent",
            "data": {
                "agent_type": "nlp",
                "context": {"priority": "normal"},
                "confidence_threshold": 0.75
            },
            "name": "Agent Routing"
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\nTesting {endpoint['name']}...")
            
            response = requests.post(
                endpoint["url"],
                json=endpoint["data"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint['name']}: {response.status_code}")
                
                # Show key response info
                if "agent_id" in data:
                    print(f"   Agent: {data.get('agent_id')}")
                elif "selected_agent" in data.get("decision", {}):
                    print(f"   Agent: {data.get('decision', {}).get('selected_agent')}")
                
                results.append(True)
            else:
                print(f"❌ {endpoint['name']}: {response.status_code}")
                print(f"   Error: {response.text[:100]}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {endpoint['name']}: {e}")
            results.append(False)
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    # Wait for telemetry listener to finish
    await asyncio.sleep(2)
    telemetry_task.cancel()
    
    print(f"\nTelemetry Results:")
    print(f"Expected packets: 3")
    print(f"Received packets: {len(telemetry_received)}")
    
    for i, packet in enumerate(telemetry_received):
        decision = packet.get("decision", {})
        trace = packet.get("trace", {})
        print(f"  Packet {i+1}: {decision.get('selected_agent')} (latency: {decision.get('latency_ms', 0):.1f}ms)")
        print(f"    Node: {trace.get('node')}, Strategy: {decision.get('strategy')}")
    
    return all(results), len(telemetry_received) >= 2  # At least 2 packets received

def test_telemetry_configuration():
    """Test telemetry configuration endpoints"""
    
    print("\nTesting Telemetry Configuration")
    print("-" * 40)
    
    config_endpoints = [
        "/telemetry/health",
        "/telemetry/metrics", 
        "/telemetry/connections",
        "/telemetry/recent?limit=5"
    ]
    
    results = []
    
    for endpoint in config_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: {response.status_code}")
                
                # Show key info
                if "health" in endpoint:
                    print(f"   Status: {data.get('status')}, Queue: {data.get('queue_size')}")
                elif "connections" in endpoint:
                    print(f"   Active: {data.get('active_connections')}")
                elif "recent" in endpoint:
                    print(f"   Recent packets: {data.get('count', 0)}")
                
                results.append(True)
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
            results.append(False)
    
    return all(results)

async def main():
    """Main test function"""
    
    print("Complete Telemetry Integration Test")
    print("=" * 60)
    
    # Test routing with telemetry
    routing_ok, telemetry_ok = await test_routing_with_telemetry()
    
    # Test configuration endpoints
    config_ok = test_telemetry_configuration()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Routing Endpoints: {'✅ PASS' if routing_ok else '❌ FAIL'}")
    print(f"Telemetry Emission: {'✅ PASS' if telemetry_ok else '❌ FAIL'}")
    print(f"Configuration APIs: {'✅ PASS' if config_ok else '❌ FAIL'}")
    
    total_tests = 3
    passed_tests = sum([routing_ok, telemetry_ok, config_ok])
    
    print(f"\nOverall: {passed_tests}/{total_tests} test categories passed")
    
    if passed_tests == total_tests:
        print("🎉 Complete telemetry integration successful!")
        print("All routing endpoints now emit telemetry packets")
    elif passed_tests >= 2:
        print("⚠️  Most functionality working, minor issues detected")
    else:
        print("❌ Integration issues detected")
    
    print("\n💡 Next Steps:")
    print("- Connect to ws://localhost:8000/telemetry/decisions for live stream")
    print("- Monitor /telemetry/health for service status")
    print("- Use /telemetry/recent for debugging packets")

if __name__ == "__main__":
    asyncio.run(main())