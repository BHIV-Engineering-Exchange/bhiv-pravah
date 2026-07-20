#!/usr/bin/env python3
"""
Final validation test after deployment - verify all security changes are working
"""

import requests
import json

def test_deployed_security_changes():
    """Test the deployed security changes on production"""
    print("Testing Deployed Security Changes")
    print("=" * 40)
    
    api_key = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
    gateway_url = "https://bhiv-hr-gateway-ltg0.onrender.com"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Test 1: Length validation for skills (should fail)
    print("\n1. Testing skills length validation (>200 chars)...")
    try:
        long_skills = "A" * 250
        response = requests.get(
            f"{gateway_url}/v1/candidates/search",
            params={"skills": long_skills, "location": "Mumbai"},
            headers=headers,
            timeout=120
        )
        if response.status_code == 400:
            print("   PASS - Length validation working")
            print(f"   Error: {response.json().get('detail', 'Unknown')}")
        else:
            print(f"   FAIL - Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 2: Location length validation (should fail)
    print("\n2. Testing location length validation (>100 chars)...")
    try:
        long_location = "B" * 150
        response = requests.get(
            f"{gateway_url}/v1/candidates/search",
            params={"skills": "Python", "location": long_location},
            headers=headers,
            timeout=120
        )
        if response.status_code == 400:
            print("   PASS - Location length validation working")
            print(f"   Error: {response.json().get('detail', 'Unknown')}")
        else:
            print(f"   FAIL - Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Phone validation (should fail)
    print("\n3. Testing phone validation (invalid format)...")
    try:
        response = requests.put(
            f"{gateway_url}/v1/candidate/profile/1",
            json={"phone": "1234567890"},  # Invalid - starts with 1
            headers=headers,
            timeout=120
        )
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text[:200]}")
        if response.status_code == 400:
            print("   PASS - Phone validation working")
            print(f"   Error: {response.json().get('detail', 'Unknown')}")
        else:
            print(f"   FAIL - Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Experience validation (should fail)
    print("\n4. Testing experience validation (negative value)...")
    try:
        response = requests.put(
            f"{gateway_url}/v1/candidate/profile/1",
            json={"experience_years": -5},
            headers=headers,
            timeout=120
        )
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text[:200]}")
        if response.status_code == 400:
            print("   PASS - Experience validation working")
            print(f"   Error: {response.json().get('detail', 'Unknown')}")
        else:
            print(f"   FAIL - Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 5: Valid inputs (should pass)
    print("\n5. Testing valid inputs (should work)...")
    try:
        response = requests.get(
            f"{gateway_url}/v1/candidates/search",
            params={"skills": "Python Java", "location": "Mumbai"},
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            print("   PASS - Valid inputs working")
            data = response.json()
            print(f"   Found: {len(data.get('candidates', []))} candidates")
        else:
            print(f"   FAIL - Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 6: AI Matching with 120s timeout
    print("\n6. Testing AI matching with 120s timeout...")
    try:
        response = requests.get(
            f"{gateway_url}/v1/match/1/top",
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            print("   PASS - AI matching working")
            data = response.json()
            print(f"   Matches: {len(data.get('matches', []))}")
        else:
            print(f"   FAIL - Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")

    # Test 7: Valid phone format (should pass)
    print("\n7. Testing valid phone format...")
    try:
        response = requests.put(
            f"{gateway_url}/v1/candidate/profile/1",
            json={"phone": "9876543210"},  # Valid Indian number
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            print("   PASS - Valid phone accepted")
        else:
            print(f"   FAIL - Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 8: Valid experience (should pass)
    print("\n8. Testing valid experience...")
    try:
        response = requests.put(
            f"{gateway_url}/v1/candidate/profile/1",
            json={"experience_years": 5},  # Valid positive number
            headers=headers,
            timeout=120
        )
        if response.status_code == 200:
            print("   PASS - Valid experience accepted")
        else:
            print(f"   FAIL - Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    test_deployed_security_changes()
    print("\n" + "=" * 40)
    print("Final validation testing completed!")