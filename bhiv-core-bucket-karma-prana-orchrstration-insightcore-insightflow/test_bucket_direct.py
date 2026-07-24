"""
Direct Bucket Endpoint Test
Tests if Bucket accepts workflow_executor events
"""
import requests
import json

BUCKET_URL = "http://localhost:8001"

def test_bucket_endpoint():
    print("=" * 70)
    print("Direct Bucket Endpoint Test")
    print("=" * 70)
    
    # Test payload
    payload = {
        "requester_id": "workflow_executor",
        "event_data": {
            "event_type": "workflow_execution",
            "trace_id": "direct_test_123",
            "action_type": "task",
            "status": "success",
            "execution_result": {"success": True},
            "metadata": {"test": "direct"},
            "timestamp": "2026-02-02T10:00:00Z"
        }
    }
    
    print("\n[Step 1] Sending event to Bucket...")
    print(f"URL: {BUCKET_URL}/core/write-event")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BUCKET_URL}/core/write-event",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"\n[Step 2] Response received")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Bucket accepted the event")
            
            # Verify event is stored
            print("\n[Step 3] Verifying event in Bucket...")
            events_response = requests.get(f"{BUCKET_URL}/core/events?limit=10", timeout=5)
            events = events_response.json().get('events', [])
            
            our_event = next((e for e in events if e.get('trace_id') == 'direct_test_123'), None)
            if our_event:
                print("✅ Event found in Bucket!")
                print(f"Event: {json.dumps(our_event, indent=2)}")
            else:
                print("⚠️ Event not found in Bucket (might be in MongoDB only)")
        else:
            print(f"\n❌ FAILED! Bucket rejected the event")
            print(f"This means Bucket is NOT accepting workflow_executor events")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    test_bucket_endpoint()
