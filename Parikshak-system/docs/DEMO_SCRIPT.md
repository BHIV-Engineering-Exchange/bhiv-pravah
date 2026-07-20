# Product Core v1 - Demo Script

**Purpose**: Demonstrate complete lifecycle from submission to retrieval  
**Audience**: Stakeholders, new team members, integration partners  
**Duration**: 5 minutes

---

## Prerequisites

### Start Backend
```bash
cd "Live Task Review Agent - 1"
uvicorn app.main:app --reload
```

**Verify**: http://localhost:8000/health should return `{"status": "healthy"}`

---

## Demo Flow

### Step 1: Submit Task

**Action**: Submit a task for review

```bash
curl -X POST http://localhost:8000/api/v1/lifecycle/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_title": "Build User Authentication System",
    "task_description": "Objective: Implement secure user authentication with JWT tokens. Requirement: Support email/password login. Constraint: Must use bcrypt for password hashing. Technical Stack: FastAPI, PostgreSQL, Redis for session management.",
    "submitted_by": "Demo User"
  }'
```

**Expected Response**:
```json
{
  "submission_id": "sub-a1b2c3d4e5f6",
  "review_summary": {
    "score": 20,
    "status": "fail",
    "readiness_percent": 18
  },
  "next_task_summary": {
    "task_id": "next-x1y2z3a4b5c6",
    "task_type": "correction",
    "title": "Task Definition Fundamentals",
    "difficulty": "beginner"
  }
}
```

**What Happened**:
1. ✅ Task submitted and stored
2. ✅ Automatic review performed (score: 20/100)
3. ✅ Status determined (fail - needs improvement)
4. ✅ Next task generated (CORRECTION type)
5. ✅ Complete lifecycle stored

---

## Python Demo Script

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/lifecycle"

def demo_complete_lifecycle():
    print("=" * 60)
    print("PRODUCT CORE v1 - COMPLETE LIFECYCLE DEMO")
    print("=" * 60)
    
    # Step 1: Submit task
    print("\n[STEP 1] Submitting task...")
    submit_response = requests.post(f"{BASE_URL}/submit", json={
        "task_title": "Build REST API with Authentication",
        "task_description": "Objective: Create secure API. Requirement: JWT auth.",
        "submitted_by": "Demo User"
    })
    
    data = submit_response.json()
    submission_id = data["submission_id"]
    
    print(f"✓ Submitted: {submission_id}")
    print(f"  Score: {data['review_summary']['score']}/100")
    print(f"  Status: {data['review_summary']['status']}")
    print(f"  Next Task: {data['next_task_summary']['title']}")
    
    # Step 2: Get history
    print("\n[STEP 2] Retrieving submission history...")
    history = requests.get(f"{BASE_URL}/history").json()
    print(f"✓ Total Submissions: {len(history)}")
    
    # Step 3: Get review details
    print("\n[STEP 3] Retrieving review details...")
    review = requests.get(f"{BASE_URL}/review/{submission_id}").json()
    print(f"✓ Review ID: {review['review_id']}")
    print(f"  Failure Reasons: {len(review['failure_reasons'])}")
    print(f"  Improvement Hints: {len(review['improvement_hints'])}")
    
    # Step 4: Get next task details
    print("\n[STEP 4] Retrieving next task details...")
    next_task = requests.get(f"{BASE_URL}/next/{submission_id}").json()
    print(f"✓ Next Task ID: {next_task['next_task_id']}")
    print(f"  Type: {next_task['task_type']}")
    print(f"  Difficulty: {next_task['difficulty']}")
    print(f"  Objective: {next_task['objective'][:50]}...")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE - LIFECYCLE VERIFIED")
    print("=" * 60)

if __name__ == "__main__":
    demo_complete_lifecycle()
```

---

**Demo Status**: READY