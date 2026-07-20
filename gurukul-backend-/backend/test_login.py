import requests
import json

url = "http://localhost:3000/api/v1/auth/login"
payload = {
    "email": "bhiv_user_1@test.gurukul",
    "password": "BhivTest@2025"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
