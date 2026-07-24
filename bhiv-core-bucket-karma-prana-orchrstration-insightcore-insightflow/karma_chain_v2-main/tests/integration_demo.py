"""
Quick Integration Test for Karma Chain - Unreal Engine Integration
Tests the unified event endpoint with correct schema
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/v1"
USER_ID = "arjuna_warrior_001"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_life_event():
    """Test logging a life event (player action)"""
    print_section("TEST 1: Life Event - Player Helps NPC")
    
    payload = {
        "type": "life_event",
        "data": {
            "user_id": USER_ID,
            "action": "helping_peers",  # Using valid action from ACTIONS list
            "role": "learner",
            "note": "Helped village elder carry supplies"
        },
        "source": "unreal_engine"
    }
    
    print(f"[SEND] Sending request to: {BASE_URL}/event/")
    print(f"[DATA] Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/event/", json=payload)
        print(f"\n[STAT] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS]")
            print(f"[RESP] Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"[FAILED]")
            print(f"[ERR] Error: {response.json()}")
            return False
    except Exception as e:
        print(f"[EXCEPTION] Exception: {str(e)}")
        return False

def test_stats_request():
    """Test getting user stats"""
    print_section("TEST 2: Stats Request - Get User Karma")
    
    payload = {
        "type": "stats_request",
        "data": {
            "user_id": USER_ID
        },
        "source": "unreal_engine"
    }
    
    print(f"[SEND] Sending request to: {BASE_URL}/event/")
    print(f"[DATA] Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/event/", json=payload)
        print(f"\n[STAT] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS]")
            print(f"[RESP] User Stats: {json.dumps(result['data'], indent=2)}")
            return True
        else:
            print(f"[FAILED]")
            print(f"[ERR] Error: {response.json()}")
            return False
    except Exception as e:
        print(f"[EXCEPTION] Exception: {str(e)}")
        return False

def test_appeal():
    """Test submitting an appeal"""
    print_section("TEST 3: Appeal - Player Contests Action")
    
    payload = {
        "type": "appeal",
        "data": {
            "user_id": USER_ID,
            "action": "cheat",  # Appealing a cheat action
            "context": "Was testing the system, not actual cheating"
        },
        "source": "unreal_engine"
    }
    
    print(f"[SEND] Sending request to: {BASE_URL}/event/")
    print(f"[DATA] Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/event/", json=payload)
        print(f"\n[STAT] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS]")
            print(f"[RESP] Appeal Result: {json.dumps(result['data'], indent=2)}")
            return True
        else:
            print(f"[FAILED]")
            print(f"[ERR] Error: {response.json()}")
            return False
    except Exception as e:
        print(f"[EXCEPTION] Exception: {str(e)}")
        return False

def test_death_event():
    """Test recording a death event"""
    print_section("TEST 4: Death Event - Player Rebirth Cycle")
    
    payload = {
        "type": "death_event",
        "data": {
            "user_id": USER_ID
        },
        "source": "unreal_engine"
    }
    
    print(f"[SEND] Sending request to: {BASE_URL}/event/")
    print(f"[DATA] Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/event/", json=payload)
        print(f"\n[STAT] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS]")
            print(f"[RESP] Death Event: {json.dumps(result['data'], indent=2)}")
            return True
        else:
            print(f"[FAILED]")
            print(f"[ERR] Error: {response.json()}")
            return False
    except Exception as e:
        print(f"[EXCEPTION] Exception: {str(e)}")
        return False

def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("  [KARMA CHAIN - UNREAL ENGINE INTEGRATION TEST]")
    print("="*70)
    print(f"  Testing against: {BASE_URL}")
    print(f"  Test user: {USER_ID}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    
    # Test 1: Life Event
    results.append(("Life Event", test_life_event()))
    
    # Test 2: Stats Request
    results.append(("Stats Request", test_stats_request()))
    
    # Test 3: Appeal
    results.append(("Appeal", test_appeal()))
    
    # Test 4: Death Event
    results.append(("Death Event", test_death_event()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name:20} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  [SUCCESS] All tests passed! System is ready for Unreal integration!")
    else:
        print(f"\n  [WARNING] {total - passed} test(s) failed. Please check the errors above.")
    
    print("\n" + "="*70 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
