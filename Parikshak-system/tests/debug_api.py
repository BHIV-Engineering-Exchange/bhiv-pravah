import requests

def debug_api():
    url = "http://localhost:8000/api/v1/lifecycle/submit"
    
    data = {
        'task_title': 'Test Task',
        'task_description': 'This is a test task description for debugging',
        'submitted_by': 'Debug User',
        'github_repo_link': '',
        'module_id': 'core-development',
        'schema_version': 'v1.0'
    }
    
    try:
        print("Sending request...")
        response = requests.post(url, data=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"JSON Response: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api()