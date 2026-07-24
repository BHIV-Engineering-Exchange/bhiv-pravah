"""
Insight Core Integration Test
Tests JWT validation and replay protection
"""
import requests
import time
import jwt
import uuid

INSIGHT_URL = "http://localhost:8005"
SECRET_KEY = "demo-secret"
ALGORITHM = "HS256"

def generate_token(ttl=300):
    """Generate valid JWT token"""
    payload = {
        "sub": "bhiv_core",
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_nonce():
    """Generate unique nonce"""
    return f"{uuid.uuid4()}-{int(time.time())}"

def test_health():
    """Test 1: Health Check"""
    print("\n[1/6] Testing Insight Core Health...")
    try:
        response = requests.get(f"{INSIGHT_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_valid_request():
    """Test 2: Valid Request (should ALLOW)"""
    print("\n[2/6] Testing Valid Request...")
    try:
        token = generate_token()
        nonce = generate_nonce()
        
        payload = {
            "token": token,
            "nonce": nonce,
            "payload": {"test": "data"}
        }
        
        response = requests.post(f"{INSIGHT_URL}/ingest", json=payload, timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data["decision"] == "ALLOW":
            print(f"✅ Valid request allowed: {data}")
            return True
        else:
            print(f"❌ Valid request rejected: {data}")
            return False
    except Exception as e:
        print(f"❌ Valid request error: {e}")
        return False

def test_expired_token():
    """Test 3: Expired Token (should DENY)"""
    print("\n[3/6] Testing Expired Token...")
    try:
        # Generate token that expired 10 seconds ago
        payload = {
            "sub": "bhiv_core",
            "iat": int(time.time()) - 20,
            "exp": int(time.time()) - 10
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        nonce = generate_nonce()
        
        request_payload = {
            "token": expired_token,
            "nonce": nonce,
            "payload": {"test": "data"}
        }
        
        response = requests.post(f"{INSIGHT_URL}/ingest", json=request_payload, timeout=5)
        data = response.json()
        
        if response.status_code == 403 and data["decision"] == "DENY" and "JWT" in data["reason"]:
            print(f"✅ Expired token rejected: {data}")
            return True
        else:
            print(f"❌ Expired token not rejected properly: {data}")
            return False
    except Exception as e:
        print(f"❌ Expired token test error: {e}")
        return False

def test_replay_attack():
    """Test 4: Replay Attack (should DENY)"""
    print("\n[4/6] Testing Replay Attack Protection...")
    try:
        token = generate_token()
        nonce = generate_nonce()
        
        payload = {
            "token": token,
            "nonce": nonce,
            "payload": {"test": "data"}
        }
        
        # First request should succeed
        response1 = requests.post(f"{INSIGHT_URL}/ingest", json=payload, timeout=5)
        data1 = response1.json()
        
        if response1.status_code != 200 or data1["decision"] != "ALLOW":
            print(f"❌ First request failed: {data1}")
            return False
        
        # Second request with same nonce should be rejected
        response2 = requests.post(f"{INSIGHT_URL}/ingest", json=payload, timeout=5)
        data2 = response2.json()
        
        if response2.status_code == 403 and data2["decision"] == "DENY" and "REPLAY" in data2["reason"]:
            print(f"✅ Replay attack detected and blocked: {data2}")
            return True
        else:
            print(f"❌ Replay attack not detected: {data2}")
            return False
    except Exception as e:
        print(f"❌ Replay attack test error: {e}")
        return False

def test_invalid_token():
    """Test 5: Invalid Token (should DENY)"""
    print("\n[5/6] Testing Invalid Token...")
    try:
        nonce = generate_nonce()
        
        payload = {
            "token": "invalid.token.here",
            "nonce": nonce,
            "payload": {"test": "data"}
        }
        
        response = requests.post(f"{INSIGHT_URL}/ingest", json=payload, timeout=5)
        data = response.json()
        
        if response.status_code == 403 and data["decision"] == "DENY":
            print(f"✅ Invalid token rejected: {data}")
            return True
        else:
            print(f"❌ Invalid token not rejected: {data}")
            return False
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")
        return False

def test_metrics():
    """Test 6: Metrics Endpoint"""
    print("\n[6/6] Testing Metrics Endpoint...")
    try:
        response = requests.get(f"{INSIGHT_URL}/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics retrieved: {data}")
            return True
        else:
            print(f"❌ Metrics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Metrics error: {e}")
        return False

def main():
    print("=" * 80)
    print("INSIGHT CORE INTEGRATION TEST")
    print("=" * 80)
    
    tests = [
        test_health,
        test_valid_request,
        test_expired_token,
        test_replay_attack,
        test_invalid_token,
        test_metrics
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Insight Core is production ready!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
