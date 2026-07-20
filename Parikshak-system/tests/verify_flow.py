
import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1/task"

def test_flow(payload, label):
    print(f"\n--- Testing: {label} ---")
    try:
        # Submit
        res_submit = requests.post(f"{BASE_URL}/submit", json=payload)
        print(f"Submit Status: {res_submit.status_code}")
        if res_submit.status_code != 200:
            print(f"Submit Error: {res_submit.text}")
            return
        
        task_id = res_submit.json().get("task_id")
        print(f"Task ID: {task_id}")

        # Review
        res_review = requests.post(f"{BASE_URL}/review", json={"task_id": task_id})
        print(f"Review Status: {res_review.status_code}")
        if res_review.status_code != 200:
            print(f"Review Error: {res_review.text}")
            return
        
        review_data = res_review.json()
        print(f"Review JSON: {json.dumps(review_data, indent=2)}")

        # Next Task
        res_next = requests.post(f"{BASE_URL}/generate-next", json=review_data)
        print(f"Next Task Status: {res_next.status_code}")
        if res_next.status_code == 200:
            print(f"Next Task JSON: {json.dumps(res_next.json(), indent=2)}")
        else:
            print(f"Next Task Error: {res_next.text}")

        # Contract Verification
        required_keys = ["score", "readiness_percent", "status", "failure_reasons", "improvement_hints", "analysis", "meta"]
        missing = [k for k in required_keys if k not in review_data]
        if missing:
            print(f"FAILED CONTRACT: Missing keys: {missing}")
        else:
            print("PASSED CONTRACT: All mandatory keys present.")
        
        analysis_keys = ["technical_quality", "clarity", "discipline_signals"]
        missing_analysis = [k for k in analysis_keys if k not in review_data.get("analysis", {})]
        if missing_analysis:
            print(f"FAILED CONTRACT: Missing analysis keys: {missing_analysis}")
        
    except Exception as e:
        print(f"Exception during test: {e}")

# Scenarios
valid_full = {
    "task_title": "Build a Secure Async API Gateway for User Authentication and Management",
    "task_description": "The objective is to implement a robust API gateway. Requirements include schema validation using Pydantic, security constraints for JWT, and async database connections. This task ensures production readiness by adding caching and frontend integration layers. Final success criteria: 100% test coverage and full documentation.",
    "submitted_by": "Test User"
}

short_weak = {
    "task_title": "Fix bug",
    "task_description": "fix the bugs in the code quickly",
    "submitted_by": "Test User"
}

empty_input = {
    "task_title": "",
    "task_description": "",
    "submitted_by": ""
}

garbage_input = {
    "task_title": "!!!!! @@@@@ #####",
    "task_description": "asdf asdf asdf asdf asdf asdf asdf asdf asdf asdf",
    "submitted_by": "???"
}

test_flow(valid_full, "Valid Full Task")
test_flow(short_weak, "Short Weak Task")
test_flow(empty_input, "Empty Input")
test_flow(garbage_input, "Garbage Input")
