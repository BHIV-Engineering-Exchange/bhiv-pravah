import requests
import json

def test_agent_endpoints():
    base_url = "https://bhiv-hr-agent-nhgg.onrender.com"
    
    endpoints = [
        {"method": "GET", "path": "/", "name": "Root"},
        {"method": "GET", "path": "/health", "name": "Health Check"},
        {"method": "GET", "path": "/test-db", "name": "Database Test"},
        {"method": "POST", "path": "/match", "name": "Single Match", "data": {"job_id": 1, "candidate_id": 7}},
        {"method": "POST", "path": "/batch-match", "name": "Batch Match", "data": {"job_id": 1}},
        {"method": "GET", "path": "/analyze/7", "name": "Analyze Candidate"}
    ]
    
    print("BHIV AI Agent Service - Endpoint Testing")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint['path']}"
            
            if endpoint["method"] == "GET":
                response = requests.get(url, timeout=15)
            else:
                response = requests.post(url, json=endpoint.get("data", {}), timeout=15)
            
            status = "OK" if response.status_code == 200 else f"FAIL ({response.status_code})"
            time = f"{response.elapsed.total_seconds():.2f}s"
            
            print(f"{endpoint['name']:15} | {status:8} | {time:6} | {endpoint['method']} {endpoint['path']}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "matches" in data:
                        print(f"                   Matches: {len(data['matches'])}")
                    elif "score" in data:
                        print(f"                   Score: {data['score']}")
                    elif "status" in data:
                        print(f"                   Status: {data['status']}")
                except:
                    print(f"                   Response: {response.text[:50]}...")
            else:
                print(f"                   Error: {response.text[:50]}...")
                
        except Exception as e:
            print(f"{endpoint['name']:15} | ERROR | ERROR | {endpoint['method']} {endpoint['path']}")
            print(f"                   {str(e)[:50]}...")

if __name__ == "__main__":
    test_agent_endpoints()
