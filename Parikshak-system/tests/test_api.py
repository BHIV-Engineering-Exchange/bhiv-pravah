import requests

def test_api():
    url = "http://localhost:8000/api/v1/lifecycle/submit"
    
    # Test data
    data = {
        'task_title': 'Test Task',
        'task_description': 'This is a test task description for testing the API',
        'submitted_by': 'Test User',
        'github_repo_link': ''
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API is working!")
            return True
        else:
            print("❌ API returned an error")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_api()