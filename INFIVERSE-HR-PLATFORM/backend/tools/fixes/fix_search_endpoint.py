# Quick fix for candidate search endpoint path parameter issue
# The issue is in line 500+ of main.py - the search endpoint is incorrectly defined

print("BHIV HR Platform - Search Endpoint Fix")
print("=" * 50)

print("ISSUE IDENTIFIED:")
print("The candidate search endpoint has a path parameter parsing error.")
print("URL: /v1/candidates/search?skills=Python&limit=5")
print("Error: Input should be a valid integer, unable to parse string as an integer")
print()

print("ROOT CAUSE:")
print("The endpoint is trying to parse 'search' as an integer candidate_id")
print("This suggests the route order is incorrect in FastAPI")
print()

print("SOLUTION:")
print("The /v1/candidates/search route must be defined BEFORE /v1/candidates/{candidate_id}")
print("Currently the order is:")
print("1. /v1/candidates/{candidate_id} - catches 'search' as candidate_id")
print("2. /v1/candidates/search - never reached")
print()

print("REQUIRED FIX:")
print("Move the search endpoint definition above the {candidate_id} endpoint in main.py")
print("Lines to reorder: ~500-550 (search) should come before ~600-650 (get by id)")
print()

print("IMMEDIATE WORKAROUND:")
print("Use different URL: /v1/candidates?skills=Python (without /search)")
print("This uses the main candidates endpoint with query parameters")

# Test the workaround
import requests

try:
    url = "https://bhiv-hr-gateway-ltg0.onrender.com/v1/candidates"
    params = {"skills": "Python", "limit": 5}
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    
    print("\nTesting workaround...")
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Workaround status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"SUCCESS: Found {data.get('count', 0)} candidates")
    else:
        print(f"Workaround failed: {response.text[:100]}")
        
except Exception as e:
    print(f"Test error: {e}")
