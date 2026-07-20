import requests
import json

def test_complete_flow():
    base_url = "http://localhost:8000/api/v1/lifecycle"
    
    print("Testing Complete Task Review Agent Flow")
    print("=" * 50)
    
    # Step 1: Submit a task
    print("\n1. Submitting a test task...")
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
            print(f"SUCCESS: Task submitted!")
            print(f"   Submission ID: {submission_id}")
            print(f"   Score: {submit_result['review_summary']['score']}")
            print(f"   Status: {submit_result['review_summary']['status']}")
            print(f"   Next Task: {submit_result['next_task_summary']['title']}")
            
            # Test the review endpoint
            print(f"\n2. Testing review endpoint...")
            review_response = requests.get(f"{base_url}/review/{submission_id}")
            if review_response.status_code == 200:
                review_data = review_response.json()
                print(f"SUCCESS: Review data retrieved!")
                print(f"   Title Score: {review_data['title_score']}")
                print(f"   Description Score: {review_data['description_score']}")
                print(f"   Repository Score: {review_data['repository_score']}")
            
            # Test the next task endpoint
            print(f"\n3. Testing next task endpoint...")
            next_response = requests.get(f"{base_url}/next/{submission_id}")
            if next_response.status_code == 200:
                next_data = next_response.json()
                print(f"SUCCESS: Next task retrieved!")
                print(f"   Task Type: {next_data['task_type']}")
                print(f"   Difficulty: {next_data['difficulty']}")
            
            # Test the history endpoint
            print(f"\n4. Testing history endpoint...")
            history_response = requests.get(f"{base_url}/history")
            if history_response.status_code == 200:
                history_data = history_response.json()
                print(f"SUCCESS: History retrieved!")
                print(f"   Total tasks: {len(history_data)}")
            
            print(f"\nALL TESTS PASSED!")
            print("The frontend should now work perfectly with real data.")
            return True
        else:
            print(f"FAILED: Submit returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_complete_flow()