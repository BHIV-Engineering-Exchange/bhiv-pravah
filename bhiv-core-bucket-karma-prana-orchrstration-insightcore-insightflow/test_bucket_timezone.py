#!/usr/bin/env python3
"""
Direct test of the timezone issue in Bucket
"""

import requests
import json
from datetime import datetime, timezone

def test_bucket_timezone():
    """Test the specific timezone issue in Bucket"""
    
    print("Testing Bucket timezone issue...")
    
    # Test event data
    test_event = {
        "requester_id": "bhiv_core",
        "event_data": {
            "event_type": "test_timezone",
            "agent_id": "test_agent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_data": "Testing timezone fix"
        }
    }
    
    try:
        # Send directly to Bucket
        response = requests.post(
            "http://localhost:8001/core/write-event",
            json=test_event,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ SUCCESS: Timezone issue resolved!")
                return True
            else:
                print(f"❌ FAILED: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_bucket_timezone()
    exit(0 if success else 1)