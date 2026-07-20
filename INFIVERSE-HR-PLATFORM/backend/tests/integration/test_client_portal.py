import requests
import time

def test_client_portal_matching():
    """Test client portal AI matching functionality"""
    
    print("Testing Client Portal AI Matching...")
    
    # Test AI agent directly
    print("1. Testing AI Agent (Port 9000):")
    try:
        response = requests.post(
            "http://localhost:9000/match",
            json={"job_id": 4},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   OK AI Agent: {len(data.get('top_candidates', []))} candidates")
        else:
            print(f"   ERROR AI Agent: {response.status_code}")
    except Exception as e:
        print(f"   ERROR AI Agent Connection: {e}")
    
    # Test Gateway API
    print("2. Testing Gateway API (Port 8000):")
    try:
        headers = {"Authorization": "Bearer myverysecureapikey123"}
        response = requests.get(
            "http://localhost:8000/v1/match/4/top",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   OK Gateway: {len(data.get('top_candidates', []))} candidates")
        else:
            print(f"   ERROR Gateway: {response.status_code}")
    except Exception as e:
        print(f"   ERROR Gateway Connection: {e}")
    
    # Test Jobs API
    print("3. Testing Jobs API:")
    try:
        headers = {"Authorization": "Bearer myverysecureapikey123"}
        response = requests.get(
            "http://localhost:8000/v1/jobs",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            print(f"   OK Jobs API: {len(jobs)} jobs available")
            for job in jobs[:3]:
                print(f"      - Job {job.get('id')}: {job.get('title')}")
        else:
            print(f"   ERROR Jobs API: {response.status_code}")
    except Exception as e:
        print(f"   ERROR Jobs API Connection: {e}")

if __name__ == "__main__":
    test_client_portal_matching()
