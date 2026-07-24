"""
Workflow → Bucket Integration Diagnostic
Tests if workflow events are reaching Bucket
"""
import requests
import time
import json

WORKFLOW_URL = "http://localhost:8003"
BUCKET_URL = "http://localhost:8001"

def test_workflow_to_bucket():
    print("=" * 70)
    print("Workflow → Bucket Integration Diagnostic")
    print("=" * 70)
    
    # Step 1: Check services are running
    print("\n[Step 1] Checking services...")
    try:
        workflow_health = requests.get(f"{WORKFLOW_URL}/healthz", timeout=5)
        print(f"✅ Workflow Executor: {workflow_health.status_code}")
    except Exception as e:
        print(f"❌ Workflow Executor: OFFLINE - {e}")
        return
    
    try:
        bucket_health = requests.get(f"{BUCKET_URL}/health", timeout=5)
        print(f"✅ Bucket: {bucket_health.status_code}")
    except Exception as e:
        print(f"❌ Bucket: OFFLINE - {e}")
        return
    
    # Step 2: Get current event count
    print("\n[Step 2] Getting current event count...")
    try:
        response = requests.get(f"{BUCKET_URL}/core/events?limit=100", timeout=5)
        events_before = response.json().get('events', [])
        workflow_events_before = [e for e in events_before if e.get('event_type') == 'workflow_execution']
        print(f"📊 Current workflow events in Bucket: {len(workflow_events_before)}")
    except Exception as e:
        print(f"❌ Failed to get events: {e}")
        return
    
    # Step 3: Execute workflow
    print("\n[Step 3] Executing workflow...")
    trace_id = f"diagnostic_{int(time.time())}"
    
    payload = {
        "trace_id": trace_id,
        "decision": "workflow",
        "data": {
            "workflow_type": "workflow",
            "payload": {
                "trace_id": trace_id,
                "action_type": "task",
                "user_id": "diagnostic_user",
                "title": "Diagnostic Test Task",
                "description": "Testing workflow-bucket integration"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{WORKFLOW_URL}/api/workflow/execute",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Workflow executed successfully")
            print(f"   Trace ID: {result.get('trace_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Result: {json.dumps(result.get('execution_result'), indent=2)}")
        else:
            print(f"❌ Workflow execution failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Workflow execution error: {e}")
        return
    
    # Step 4: Wait and check for event
    print("\n[Step 4] Waiting for event to reach Bucket...")
    for i in range(5):
        time.sleep(1)
        print(f"   Checking... ({i+1}/5)")
        
        try:
            response = requests.get(f"{BUCKET_URL}/core/events?limit=100", timeout=5)
            events_after = response.json().get('events', [])
            workflow_events_after = [e for e in events_after if e.get('event_type') == 'workflow_execution']
            
            if len(workflow_events_after) > len(workflow_events_before):
                print(f"\n✅ SUCCESS! Event reached Bucket!")
                print(f"   New workflow events: {len(workflow_events_after) - len(workflow_events_before)}")
                
                # Find our event
                our_event = next((e for e in workflow_events_after if e.get('trace_id') == trace_id), None)
                if our_event:
                    print(f"\n📦 Event Details:")
                    print(json.dumps(our_event, indent=2))
                return True
        except Exception as e:
            print(f"   Error checking events: {e}")
    
    print(f"\n❌ FAILED: Event did not reach Bucket after 5 seconds")
    print(f"   Events before: {len(workflow_events_before)}")
    print(f"   Events after: {len(workflow_events_after)}")
    
    # Step 5: Check Bucket logs
    print("\n[Step 5] Troubleshooting...")
    print("   Check Bucket logs at: BHIV_Central_Depository-main/logs/application.log")
    print("   Check Workflow logs in Terminal 4 (where workflow is running)")
    print("\n   Possible issues:")
    print("   1. Bucket not accepting workflow_executor as requester")
    print("   2. Network timeout (check if 2s timeout is too short)")
    print("   3. Event format mismatch")
    
    return False

if __name__ == "__main__":
    test_workflow_to_bucket()
