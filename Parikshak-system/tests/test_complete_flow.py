import requests
import json

def test_complete_flow():
    base_url = "http://localhost:8000/api/v1/lifecycle"
    
    print("🧪 Testing Complete Task Review Agent Flow")
    print("=" * 50)
    
    # Step 1: Submit a task
    print("\n1️⃣ Submitting a test task...")
    submit_data = {
        'task_title': 'Build REST API with Authentication',
        'task_description': '''
        Create a comprehensive REST API with the following features:
        - User authentication using JWT tokens
        - CRUD operations for user management
        - Role-based access control
        - Input validation and error handling
        - API documentation with Swagger
        - Unit tests with 80%+ coverage
        - Docker containerization
        - Database integration with PostgreSQL
        ''',
        'submitted_by': 'Test Developer',
        'github_repo_link': 'https://github.com/test/api-project'
    }
    
    try:
        response = requests.post(f"{base_url}/submit", data=submit_data)
        if response.status_code == 200:
            submit_result = response.json()
            submission_id = submit_result['submission_id']
            print(f"✅ Task submitted successfully!")
            print(f"   Submission ID: {submission_id}")
            print(f"   Score: {submit_result['review_summary']['score']}")
            print(f"   Status: {submit_result['review_summary']['status']}")
            print(f"   Next Task: {submit_result['next_task_summary']['title']}")
        else:
            print(f"❌ Submit failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Submit error: {e}")
        return False
    
    # Step 2: Get review details
    print(f"\n2️⃣ Fetching review details for {submission_id}...")
    try:
        response = requests.get(f"{base_url}/review/{submission_id}")
        if response.status_code == 200:
            review_data = response.json()
            print(f"✅ Review data retrieved!")
            print(f"   Overall Score: {review_data['score']}/100")
            print(f"   Title Score: {review_data['title_score']}/20")
            print(f"   Description Score: {review_data['description_score']}/40")
            print(f"   Repository Score: {review_data['repository_score']}/40")
            print(f"   Status: {review_data['status']}")
            print(f"   Feature Coverage: {review_data['feature_coverage']:.1%}")
        else:
            print(f"❌ Review fetch failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Review fetch error: {e}")
        return False
    
    # Step 3: Get next task details
    print(f"\n3️⃣ Fetching next task for {submission_id}...")
    try:
        response = requests.get(f"{base_url}/next/{submission_id}")
        if response.status_code == 200:
            next_task = response.json()
            print(f"✅ Next task retrieved!")
            print(f"   Task ID: {next_task['next_task_id']}")
            print(f"   Title: {next_task['title']}")
            print(f"   Type: {next_task['task_type']}")
            print(f"   Difficulty: {next_task['difficulty']}")
            print(f"   Focus Area: {next_task['focus_area']}")
        else:
            print(f"❌ Next task fetch failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Next task fetch error: {e}")
        return False
    
    # Step 4: Get task history
    print(f"\n4️⃣ Fetching task history...")
    try:
        response = requests.get(f"{base_url}/history")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ History retrieved!")
            print(f"   Total tasks: {len(history)}")
            if history:
                latest = history[-1]
                print(f"   Latest task: {latest['task_title']}")
                print(f"   Latest score: {latest['score']}")
                print(f"   Latest status: {latest['status']}")
        else:
            print(f"❌ History fetch failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ History fetch error: {e}")
        return False
    
    print(f"\n🎉 Complete flow test PASSED!")
    print("=" * 50)
    print("✅ All API endpoints working correctly")
    print("✅ Task submission → Review → Next Task → History flow complete")
    print("✅ Frontend should now display all data properly")
    return True

if __name__ == "__main__":
    test_complete_flow()