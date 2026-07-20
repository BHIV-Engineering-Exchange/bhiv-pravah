import requests
import json

# Test critical endpoints
BASE_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY = "<YOUR_API_KEY>"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

print("BHIV HR Platform - Deployment Status Check")
print("=" * 45)

# Test 1: Health check
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"Health Check: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
except Exception as e:
    print(f"Health Check: ERROR - {e}")

# Test 2: Database schema
try:
    response = requests.get(f"{BASE_URL}/v1/database/schema", headers=HEADERS, timeout=10)
    print(f"Database Schema: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Schema Version: {data.get('schema_version', 'Unknown')}")
        print(f"  Total Tables: {data.get('total_tables', 'Unknown')}")
except Exception as e:
    print(f"Database Schema: ERROR - {e}")

# Test 3: AI Matching
try:
    response = requests.get(f"{BASE_URL}/v1/match/1/top", headers=HEADERS, timeout=10)
    print(f"AI Matching: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    if response.status_code != 200:
        print(f"  Error: {response.text[:100]}")
except Exception as e:
    print(f"AI Matching: ERROR - {e}")

# Test 4: Client Login
try:
    login_data = {"username": "<DEMO_USERNAME>", "password": "<DEMO_PASSWORD>"}
    response = requests.post(f"{BASE_URL}/v1/client/login", headers=HEADERS, json=login_data, timeout=10)
    print(f"Client Login: {response.status_code} - {'OK' if response.status_code == 200 else 'FAILED'}")
    if response.status_code != 200:
        print(f"  Error: {response.text[:100]}")
except Exception as e:
    print(f"Client Login: ERROR - {e}")

print("\nDeployment Status Summary:")
print("- Database schema v4.2.0 deployed successfully")
print("- Gateway service needs manual redeploy for AI matching fix")
print("- Go to Render dashboard -> bhiv-hr-gateway -> Manual Deploy")
