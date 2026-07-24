"""
Insight Core Security Test
Tests JWT validation and replay attack detection
"""
import jwt
import time
import uuid
import requests

SECRET_KEY = "demo-secret"
INSIGHT_URL = "http://localhost:8005"

def test_valid_request():
    """Test 1: Valid JWT + Nonce should be allowed"""
    print("\n[Test 1] Valid Request...")
    
    # Generate token
    token = jwt.encode({
        "sub": "test_user",
        "iat": int(time.time()),
        "exp": int(time.time()) + 300
    }, SECRET_KEY, algorithm="HS256")
    
    # Generate nonce
    nonce = f"{uuid.uuid4()}-{int(time.time())}"
    
    # Send request
    response = requests.post(
        f"{INSIGHT_URL}/ingest",
        json={
            "token": token,
            "nonce": nonce,
            "payload": {"test": "data"}
        }
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    if response.status_code == 200 and response.json()["decision"] == "ALLOW":
        print("  ✅ PASS - Valid request allowed")
        return True, nonce, token
    else:
        print("  ❌ FAIL - Valid request rejected")
        return False, None, None

def test_replay_attack(nonce, token):
    """Test 2: Replay attack should be blocked"""
    print("\n[Test 2] Replay Attack Detection...")
    
    # Send same request again (same nonce)
    response = requests.post(
        f"{INSIGHT_URL}/ingest",
        json={
            "token": token,
            "nonce": nonce,  # Same nonce!
            "payload": {"test": "data"}
        }
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    if response.status_code == 403 and response.json()["reason"] == "REPLAY_DETECTED":
        print("  ✅ PASS - Replay attack blocked")
        return True
    else:
        print("  ❌ FAIL - Replay attack not detected")
        return False

def test_expired_token():
    """Test 3: Expired token should be rejected"""
    print("\n[Test 3] Expired Token...")
    
    # Generate expired token
    token = jwt.encode({
        "sub": "test_user",
        "iat": int(time.time()) - 400,
        "exp": int(time.time()) - 100  # Expired 100 seconds ago
    }, SECRET_KEY, algorithm="HS256")
    
    nonce = f"{uuid.uuid4()}-{int(time.time())}"
    
    response = requests.post(
        f"{INSIGHT_URL}/ingest",
        json={
            "token": token,
            "nonce": nonce,
            "payload": {"test": "data"}
        }
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    if response.status_code == 403 and "INVALID" in response.json()["reason"]:
        print("  ✅ PASS - Expired token rejected")
        return True
    else:
        print("  ❌ FAIL - Expired token not rejected")
        return False

def test_invalid_signature():
    """Test 4: Invalid signature should be rejected"""
    print("\n[Test 4] Invalid Signature...")
    
    # Generate token with wrong secret
    token = jwt.encode({
        "sub": "test_user",
        "iat": int(time.time()),
        "exp": int(time.time()) + 300
    }, "wrong-secret", algorithm="HS256")
    
    nonce = f"{uuid.uuid4()}-{int(time.time())}"
    
    response = requests.post(
        f"{INSIGHT_URL}/ingest",
        json={
            "token": token,
            "nonce": nonce,
            "payload": {"test": "data"}
        }
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    if response.status_code == 403:
        print("  ✅ PASS - Invalid signature rejected")
        return True
    else:
        print("  ❌ FAIL - Invalid signature not rejected")
        return False

def main():
    print("=" * 60)
    print("Insight Core Security Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Valid request
    success, nonce, token = test_valid_request()
    results.append(success)
    
    if success:
        # Test 2: Replay attack (only if test 1 passed)
        results.append(test_replay_attack(nonce, token))
    else:
        print("\n[Test 2] SKIPPED - Test 1 failed")
        results.append(False)
    
    # Test 3: Expired token
    results.append(test_expired_token())
    
    # Test 4: Invalid signature
    results.append(test_invalid_signature())
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("Status: ✅ ALL TESTS PASSED - Security layer working correctly!")
    else:
        print("Status: ❌ SOME TESTS FAILED - Check Insight Core service")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to Insight Core (port 8005)")
        print("Make sure Insight Core is running:")
        print("  cd insightcore-bridgev4x-main")
        print("  python insight_service.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
