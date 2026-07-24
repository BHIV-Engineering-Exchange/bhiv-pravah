#!/usr/bin/env python3
"""
Test telemetry bus integration
"""

import asyncio
import websockets
import json
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_telemetry_websocket():
    """Test WebSocket telemetry streaming"""
    
    print("Testing Telemetry WebSocket...")
    
    try:
        # Connect to telemetry WebSocket
        uri = "ws://localhost:8000/telemetry/stream"
        
        async with websockets.connect(uri) as websocket:
            print("Connected to telemetry stream")
            
            # Trigger a routing decision to generate telemetry
            routing_request = {
                "agent_type": "nlp",
                "context": {"priority": "normal"},
                "confidence_threshold": 0.75
            }
            
            # Make routing request in background
            response = requests.post(
                "http://localhost:8000/api/v1/routing/route-agent",
                json=routing_request,
                timeout=5
            )
            
            if response.status_code == 200:
                print("Routing request successful, waiting for telemetry...")
                
                # Wait for telemetry message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    telemetry_data = json.loads(message)
                    
                    print("Received telemetry packet:")
                    print(f"  Event Type: {telemetry_data.get('event_type')}")
                    print(f"  Agent ID: {telemetry_data.get('payload', {}).get('agent_id')}")
                    print(f"  Confidence: {telemetry_data.get('payload', {}).get('confidence_score')}")
                    print(f"  Strategy: {telemetry_data.get('payload', {}).get('routing_strategy')}")
                    
                    return True
                    
                except asyncio.TimeoutError:
                    print("No telemetry received within timeout")
                    return False
            else:
                print(f"Routing request failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"WebSocket test failed: {e}")
        return False

def test_telemetry_metrics():
    """Test telemetry metrics endpoint"""
    
    print("\nTesting Telemetry Metrics...")
    
    try:
        response = requests.get("http://localhost:8000/telemetry/metrics", timeout=5)
        
        if response.status_code == 200:
            metrics = response.json()
            print("Telemetry metrics:")
            print(f"  Status: {metrics.get('status')}")
            print(f"  Active Connections: {metrics.get('telemetry_metrics', {}).get('active_connections')}")
            print(f"  Total Connections: {metrics.get('telemetry_metrics', {}).get('total_connections')}")
            print(f"  Packets Sent: {metrics.get('telemetry_metrics', {}).get('packets_sent')}")
            return True
        else:
            print(f"Metrics request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Metrics test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    print("Telemetry Bus Integration Test")
    print("=" * 40)
    
    # Test metrics endpoint first
    metrics_ok = test_telemetry_metrics()
    
    # Test WebSocket streaming
    websocket_ok = await test_telemetry_websocket()
    
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    print(f"Metrics Endpoint: {'PASS' if metrics_ok else 'FAIL'}")
    print(f"WebSocket Stream: {'PASS' if websocket_ok else 'FAIL'}")
    
    if metrics_ok and websocket_ok:
        print("\nTelemetry Bus: FULLY INTEGRATED!")
    elif metrics_ok:
        print("\nTelemetry endpoints work, WebSocket needs server restart")
    else:
        print("\nTelemetry integration issues detected")

if __name__ == "__main__":
    asyncio.run(main())