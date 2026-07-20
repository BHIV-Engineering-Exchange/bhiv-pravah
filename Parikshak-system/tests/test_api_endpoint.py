"""
Test the API endpoint directly
"""
import requests
import json

def test_api_endpoint():
    """Test the next task API endpoint"""
    
    # First, submit a task to get a submission ID
    submit_data = {
        'task_title': 'Test API Authentication',
        'task_description': 'Build a REST API with JWT authentication and user management',
        'submitted_by': 'api-test-user',
        'github_repo_link': 'https://github.com/test/api-auth',
        'module_id': 'task-review-agent',
        'schema_version': 'v1.0'
    }
    
    try:
        # Submit task
        print("Testing task submission...")
        submit_response = requests.post('http://localhost:8000/api/v1/lifecycle/submit', data=submit_data)
        
        if submit_response.status_code == 200:
            submit_result = submit_response.json()
            submission_id = submit_result['submission_id']
            print(f"Task submitted successfully: {submission_id}")
            
            # Test next task endpoint
            print(f"Testing next task endpoint for submission: {submission_id}")
            next_task_response = requests.get(f'http://localhost:8000/api/v1/lifecycle/next/{submission_id}')
            
            print(f"Next task response status: {next_task_response.status_code}")
            
            if next_task_response.status_code == 200:
                next_task_result = next_task_response.json()
                print("Next task retrieved successfully:")
                print(json.dumps(next_task_result, indent=2))
            else:
                print(f"Next task endpoint failed: {next_task_response.status_code}")
                print(f"Response: {next_task_response.text}")
                
        else:
            print(f"Task submission failed: {submit_response.status_code}")
            print(f"Response: {submit_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_endpoint()