#!/usr/bin/env python3
"""
Add feedback samples for RL retraining test
"""

import requests
import json

LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def add_feedback_samples():
    """Add 10 feedback samples for retraining test"""
    print("Adding feedback samples for RL retraining test...")
    
    outcomes = ["hired", "rejected", "interviewed", "shortlisted"]
    scores = [4.5, 2.0, 3.5, 4.0]
    
    for i in range(10):
        payload = {
            "candidate_id": i + 1,
            "job_id": 1,
            "actual_outcome": outcomes[i % len(outcomes)],
            "feedback_score": scores[i % len(scores)],
            "feedback_source": "hr",
            "feedback_notes": f"Test feedback sample {i+1}"
        }
        
        try:
            response = requests.post(
                f"{LANGGRAPH_URL}/rl/feedback",
                headers=HEADERS,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"  Added feedback {i+1}: ID {data.get('data', {}).get('feedback_id')}")
                else:
                    print(f"  Failed feedback {i+1}: {data}")
            else:
                print(f"  Failed feedback {i+1}: Status {response.status_code}")
                
        except Exception as e:
            print(f"  Error feedback {i+1}: {str(e)}")
    
    print("Feedback samples added!")

if __name__ == "__main__":
    add_feedback_samples()