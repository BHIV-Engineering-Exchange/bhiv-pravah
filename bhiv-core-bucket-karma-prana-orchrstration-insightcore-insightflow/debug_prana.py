import requests
import json

# Test the failing endpoint
try:
    response = requests.get("http://localhost:8001/bucket/prana/packets?limit=10", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 500:
        try:
            error_data = response.json()
            print(f"Error JSON: {json.dumps(error_data, indent=2)}")
        except:
            print("Could not parse error as JSON")
except Exception as e:
    print(f"Request failed: {e}")
