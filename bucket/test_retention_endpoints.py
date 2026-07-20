"""
Test script for Document 06: Retention Posture endpoints
Run this after starting the server to verify all retention endpoints work correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", params=None):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, params=params)
        
        if response.status_code == 200:
            print(f"✅ Status: {response.status_code}")
            data = response.json()
            print(f"Response preview: {json.dumps(data, indent=2)[:500]}...")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("="*60)
    print("DOCUMENT 06: RETENTION POSTURE - ENDPOINT TESTS")
    print("="*60)
    
    tests = [
        ("Get Retention Config", f"{BASE_URL}/governance/retention/config"),
        ("Get Retention Rules", f"{BASE_URL}/governance/retention/rules"),
        ("Get Data Lifecycle", f"{BASE_URL}/governance/retention/lifecycle"),
        ("Get Deletion Strategy", f"{BASE_URL}/governance/retention/deletion-strategy"),
        ("Get GDPR Process", f"{BASE_URL}/governance/retention/gdpr"),
        ("Get Legal Hold Process", f"{BASE_URL}/governance/retention/legal-hold"),
        ("Get Storage Impact", f"{BASE_URL}/governance/retention/storage-impact"),
        ("Get Cleanup Procedures", f"{BASE_URL}/governance/retention/cleanup-procedures"),
        ("Get Compliance Checklist", f"{BASE_URL}/governance/retention/compliance-checklist"),
        ("Get DSAR Process", f"{BASE_URL}/governance/retention/dsar"),
    ]
    
    results = []
    for name, url in tests:
        results.append(test_endpoint(name, url))
    
    # Test calculate retention endpoint
    print(f"\n{'='*60}")
    print("Testing: Calculate Retention Date")
    print(f"URL: {BASE_URL}/governance/retention/calculate")
    
    test_cases = [
        ("execution_metadata", None),
        ("agent_specifications", None),
        ("logs_success", "2026-01-01T00:00:00"),
        ("agent_state", datetime.now().isoformat()),
    ]
    
    for artifact_type, created_date in test_cases:
        params = {"artifact_type": artifact_type}
        if created_date:
            params["created_date"] = created_date
        
        print(f"\n  Testing artifact: {artifact_type}")
        try:
            response = requests.post(f"{BASE_URL}/governance/retention/calculate", params=params)
            if response.status_code == 200:
                print(f"  ✅ {response.json()}")
                results.append(True)
            else:
                print(f"  ❌ Status: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results.append(False)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} TESTS FAILED")
    
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\nMake sure the server is running on http://localhost:8000")
    print("Start server with: python main.py\n")
    
    try:
        # Quick health check
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running\n")
            main()
        else:
            print("❌ Server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the server first.")
    except Exception as e:
        print(f"❌ Error: {e}")
