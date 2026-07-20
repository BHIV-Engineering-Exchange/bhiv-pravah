import requests
import json

def debug_batch_matching():
    agent_url = "https://bhiv-hr-agent-nhgg.onrender.com"
    gateway_service_url = "https://bhiv-hr-gateway-ltg0.onrender.com"
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    
    print("Debugging Batch Matching Issue")
    print("=" * 50)
    
    # 1. Check Agent service health
    print("\n1. Agent Service Health Check:")
    try:
        response = requests.get(f"{agent_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 2. Check Agent service endpoints
    print("\n2. Agent Service Endpoints:")
    try:
        response = requests.get(f"{agent_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get('available_endpoints', [])
            print(f"   Available endpoints: {endpoints}")
            batch_endpoint_exists = any('/batch-match' in str(ep) for ep in endpoints)
            print(f"   Batch endpoint exists: {batch_endpoint_exists}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 3. Test Agent batch-match directly
    print("\n3. Direct Agent Batch-Match Test:")
    try:
        test_data = {"job_ids": [1, 2]}
        response = requests.post(
            f"{agent_url}/batch-match", 
            json=test_data, 
            headers=headers, 
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code != 200:
            print(f"   ISSUE: Agent batch-match returns {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 4. Check Gateway batch endpoint with detailed error
    print("\n4. Gateway Batch Endpoint Analysis:")
    try:
        test_data = [1, 2]  # Gateway expects List[int], not {"job_ids": [...]}
        response = requests.post(
            f"{gateway_service_url}/v1/match/batch", 
            json=test_data, 
            headers=headers, 
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:300]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # 5. Check configuration mismatch
    print("\n5. Configuration Analysis:")
    print("   Gateway Code Analysis:")
    print("   - Gateway sends: {'job_ids': job_ids} to Agent")
    print("   - Gateway expects Agent at: /batch-match")
    print("   - Gateway timeout: 60s")
    print("   - Auth header: Bearer token")
    
    print("\n6. Potential Issues:")
    print("   A. Agent /batch-match endpoint may not exist")
    print("   B. Agent expects different request format")
    print("   C. Agent service timeout/performance issue")
    print("   D. Authentication issue with Agent service")
    
    # 7. Test single match for comparison
    print("\n7. Single Match Test (for comparison):")
    try:
        test_data = {"job_id": 1, "candidate_ids": [7]}
        response = requests.post(
            f"{agent_url}/match", 
            json=test_data, 
            headers=headers, 
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Single match works: {'YES' if response.status_code == 200 else 'NO'}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    debug_batch_matching()
