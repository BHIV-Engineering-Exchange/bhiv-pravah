import requests
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5000"

def test_decide():
    print("Testing /ai/decide...")
    payload = {
        "candidate": {"id": "test_1", "name": "Test"},
        "job": {"id": "job_1"},
        "history": {}
    }
    try:
        response = requests.post(f"{BASE_URL}/ai/decide", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

def test_feedback():
    print("\nTesting /ai/feedback...")
    payload = {
        "candidate_id": "test_1",
        "job_id": "job_1",
        "decision_taken": "shortlist",
        "outcome": "good"
    }
    try:
        response = requests.post(f"{BASE_URL}/ai/feedback", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_decide()
    test_feedback()
