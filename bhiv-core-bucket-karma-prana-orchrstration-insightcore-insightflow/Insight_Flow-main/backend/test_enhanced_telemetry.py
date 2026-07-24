#!/usr/bin/env python3
"""
Test enhanced telemetry WebSocket endpoints
"""

import asyncio
import websockets
import json
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_decisions_websocket():
    """Test decisions WebSocket endpoint"""
    
    print("Testing /telemetry/decisions WebSocket...")
    
    try:
        uri = "ws://localhost:8000/telemetry/decisions"
        
        async with websockets.connect(uri) as websocket:
            print("Connected to decisions stream")
            
            # Test ping/pong
            await websocket.send("ping")
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Ping response: {response}")
            
            # Test status command
            await websocket.send("status")
            status_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            status_data = json.loads(status_response)
            print(f"Status: {status_data.get('status')}, Connections: {status_data.get('active_connections')}")
            
            # Trigger a test broadcast
            test_response = requests.post("http://localhost:8000/telemetry/test", timeout=5)
            if test_response.status_code == 200:
                print("Test broadcast triggered")
                
                # Wait for telemetry message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    telemetry_data = json.loads(message)
                    print("Received telemetry packet:")
                    print(f"  Request ID: {telemetry_data.get('request_id')}")
                    print(f"  Agent: {telemetry_data.get('decision', {}).get('selected_agent')}")
                    print(f"  Confidence: {telemetry_data.get('decision', {}).get('confidence')}")
                    return True
                except asyncio.TimeoutError:
                    print("No telemetry received within timeout")
                    return False
            else:
                print(f"Test broadcast failed: {test_response.status_code}")
                return False
                
    except Exception as e:
        print(f"Decisions WebSocket test failed: {e}")
        return False

async def test_metrics_websocket():
    """Test metrics WebSocket endpoint"""
    
    print("\nTesting /telemetry/metrics WebSocket...")
    
    try:
        uri = "ws://localhost:8000/telemetry/metrics"
        
        async with websockets.connect(uri) as websocket:
            print("Connected to metrics stream")
            
            # Test health command
            await websocket.send("health")
            health_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            health_data = json.loads(health_response)
            print(f"Health status: {health_data.get('status')}")
            print(f"Queue size: {health_data.get('queue_size')}")
            print(f"Messages sent: {health_data.get('messages_sent')}")
            
            # Test metrics command
            await websocket.send("metrics")
            metrics_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            metrics_data = json.loads(metrics_response)
            print(f"Metrics: {metrics_data.get('metrics')}")
            
            return True
                
    except Exception as e:
        print(f"Metrics WebSocket test failed: {e}")
        return False

def test_rest_endpoints():
    """Test REST endpoints"""
    
    print("\nTesting REST endpoints...")
    
    endpoints = [
        ("/telemetry/health", "Health endpoint"),
        ("/telemetry/metrics", "Metrics endpoint"),
        ("/telemetry/connections", "Connections endpoint"),
        ("/telemetry/recent?limit=5", "Recent packets endpoint")
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: {response.status_code}")
                
                # Show key info
                if "health" in endpoint:
                    print(f"   Status: {data.get('status')}, Connections: {data.get('active_connections')}")
                elif "connections" in endpoint:
                    print(f"   Active: {data.get('active_connections')}, Max: {data.get('max_connections')}")
                elif "recent" in endpoint:
                    print(f"   Recent packets: {data.get('count')}")
                
                results.append(True)
            else:
                print(f"❌ {description}: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {description}: {e}")
            results.append(False)
    
    return all(results)

async def test_legacy_compatibility():
    """Test legacy WebSocket endpoint"""
    
    print("\nTesting legacy /telemetry/stream WebSocket...")
    
    try:
        uri = "ws://localhost:8000/telemetry/stream"
        
        async with websockets.connect(uri) as websocket:
            print("Connected to legacy stream")
            
            # Trigger test broadcast
            test_response = requests.post("http://localhost:8000/telemetry/test", timeout=5)
            if test_response.status_code == 200:
                # Wait for telemetry message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    print("Legacy endpoint received telemetry packet")
                    return True
                except asyncio.TimeoutError:
                    print("Legacy endpoint: No telemetry received")
                    return False
            else:
                return False
                
    except Exception as e:
        print(f"Legacy WebSocket test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    print("Enhanced Telemetry WebSocket Endpoints Test")
    print("=" * 50)
    
    # Test REST endpoints first
    rest_ok = test_rest_endpoints()
    
    # Test WebSocket endpoints
    decisions_ok = await test_decisions_websocket()
    metrics_ok = await test_metrics_websocket()
    legacy_ok = await test_legacy_compatibility()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"REST Endpoints: {'✅ PASS' if rest_ok else '❌ FAIL'}")
    print(f"Decisions WebSocket: {'✅ PASS' if decisions_ok else '❌ FAIL'}")
    print(f"Metrics WebSocket: {'✅ PASS' if metrics_ok else '❌ FAIL'}")
    print(f"Legacy WebSocket: {'✅ PASS' if legacy_ok else '❌ FAIL'}")
    
    total_tests = 4
    passed_tests = sum([rest_ok, decisions_ok, metrics_ok, legacy_ok])
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All enhanced telemetry endpoints working!")
    elif passed_tests >= 3:
        print("⚠️  Most endpoints working, minor issues detected")
    else:
        print("❌ Multiple endpoint issues detected")

if __name__ == "__main__":
    asyncio.run(main())