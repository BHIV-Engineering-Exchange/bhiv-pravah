#!/usr/bin/env python3
"""
Test script to verify routing endpoint fixes
"""

import requests
import json
import sys

def test_routing_endpoints():
    """Test both standard and STP routing endpoints"""
    
    base_url = "http://localhost:8000"
    
    # Test data
    test_request = {
        "input_data": {"text": "What is the weather today?"},
        "input_type": "text",
        "strategy": "q_learning",
        "context": {"user_id": "test_user"}
    }
    
    # Test headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"  # You may need a real token
    }
    
    print("Testing InsightFlow Routing Endpoints")
    print("=" * 50)
    
    # Test 1: Standard routing endpoint (should return RouteResponse format)
    print("\n1. Testing /api/v1/routing/route (Standard)")
    try:
        response = requests.post(
            f"{base_url}/api/v1/routing/route",
            json=test_request,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Response structure:")
            
            # Check for required RouteResponse fields
            required_fields = [
                "request_id", "routing_log_id", "agent_id", 
                "agent_name", "agent_type", "confidence_score", 
                "routing_reason", "routing_strategy"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ All required RouteResponse fields present")
            
            # Check if it's NOT STP wrapped
            if "stp_version" in data:
                print("❌ Response is STP wrapped (should be unwrapped)")
            else:
                print("✅ Response is properly unwrapped")
                
            print(f"Response preview: {json.dumps(data, indent=2)[:300]}...")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: STP routing endpoint (should return STP-wrapped format)
    print("\n2. Testing /api/v1/routing/route-stp (STP Wrapped)")
    try:
        response = requests.post(
            f"{base_url}/api/v1/routing/route-stp",
            json=test_request,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Response structure:")
            
            # Check for STP fields
            stp_fields = ["stp_version", "stp_token", "stp_timestamp", "payload"]
            
            missing_stp_fields = [field for field in stp_fields if field not in data]
            
            if missing_stp_fields:
                print(f"❌ Missing STP fields: {missing_stp_fields}")
            else:
                print("✅ All required STP fields present")
                
                # Check payload structure
                payload = data.get("payload", {})
                required_fields = [
                    "request_id", "routing_log_id", "agent_id", 
                    "agent_name", "agent_type", "confidence_score"
                ]
                
                missing_payload_fields = [field for field in required_fields if field not in payload]
                
                if missing_payload_fields:
                    print(f"❌ Missing payload fields: {missing_payload_fields}")
                else:
                    print("✅ STP payload contains all required routing fields")
            
            print(f"Response preview: {json.dumps(data, indent=2)[:300]}...")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Route agent endpoint (should return unwrapped format)
    print("\n3. Testing /api/v1/routing/route-agent (Agent Routing)")
    
    agent_request = {
        "agent_type": "nlp",
        "context": {"priority": "normal"},
        "confidence_threshold": 0.75
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/routing/route-agent",
            json=agent_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Response structure:")
            
            # Check for agent routing fields
            expected_fields = ["agent_id", "confidence_score", "routing_reasoning"]
            
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"⚠️  Missing optional fields: {missing_fields}")
            else:
                print("✅ All expected agent routing fields present")
            
            # Check if it's NOT STP wrapped
            if "stp_version" in data:
                print("❌ Response is STP wrapped (should be unwrapped)")
            else:
                print("✅ Response is properly unwrapped")
                
            print(f"Response preview: {json.dumps(data, indent=2)[:300]}...")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- Standard routing should return RouteResponse format (unwrapped)")
    print("- STP routing should return STP-wrapped format")
    print("- Agent routing should return unwrapped format")
    print("\nIf all tests pass, the routing validation errors should be fixed!")

if __name__ == "__main__":
    test_routing_endpoints()