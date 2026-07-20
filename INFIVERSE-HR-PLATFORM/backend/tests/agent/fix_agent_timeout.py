import requests
import json

# Quick fix for Agent service timeout by testing with a simpler request
AGENT_URL = "https://bhiv-hr-agent-nhgg.onrender.com"
API_KEY = "<YOUR_API_KEY>"

print("BHIV HR Platform - Agent Service Quick Fix")
print("=" * 50)

# Test with minimal timeout and check if service responds
try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Test database connectivity first
    print("1. Testing Agent database connectivity...")
    response = requests.get(f"{AGENT_URL}/test-db", headers=headers, timeout=15)
    print(f"Database test: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Candidates in DB: {data.get('candidates_count', 'unknown')}")
        print("Database connection working")
    else:
        print(f"Database issue: {response.text[:100]}")
    
    # Test match with shorter timeout
    print("\n2. Testing match with 15s timeout...")
    match_data = {"job_id": 1}
    response = requests.post(f"{AGENT_URL}/match", json=match_data, headers=headers, timeout=15)
    print(f"Match test: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS: Found {len(result.get('top_candidates', []))} candidates")
        print(f"Processing time: {result.get('processing_time', 'unknown')}s")
        print(f"Algorithm: {result.get('algorithm_version', 'unknown')}")
    else:
        print(f"Match failed: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("TIMEOUT: Agent service is taking too long (>15s)")
    print("SOLUTION: Agent service needs optimization or restart")
except Exception as e:
    print(f"ERROR: {e}")

print("\nRECOMMENDATION:")
print("If database works but match times out, the Agent service")
print("needs to be restarted on Render dashboard to clear any")
print("hanging processes or memory issues.")
