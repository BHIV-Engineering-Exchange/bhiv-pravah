import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "myverysecureapikey123"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def test_rate_limiting():
    """Test API rate limiting"""
    print("Testing rate limiting...")
    
    # Test health endpoint (30/minute limit)
    for i in range(35):
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS)
        if response.status_code == 429:
            print(f"Rate limit triggered after {i+1} requests")
            return True
    
    print("Rate limiting not working")
    return False

def test_security_headers():
    """Test security headers"""
    print("Testing security headers...")
    
    response = requests.get(f"{BASE_URL}/health", headers=HEADERS)
    headers = response.headers
    
    required_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options", 
        "X-XSS-Protection",
        "Strict-Transport-Security"
    ]
    
    missing = [h for h in required_headers if h not in headers]
    if not missing:
        print("All security headers present")
        return True
    else:
        print(f"Missing headers: {missing}")
        return False

def test_input_validation():
    """Test input validation"""
    print("Testing input validation...")
    
    # Test invalid email
    invalid_job = {
        "title": "Test Job",
        "description": "Test Description", 
        "requirements": "Test Requirements",
        "contact_email": "invalid-email"
    }
    
    response = requests.post(f"{BASE_URL}/v1/jobs", json=invalid_job, headers=HEADERS)
    if response.status_code == 400:
        print("Input validation working")
        return True
    else:
        print("Input validation not working")
        return False

if __name__ == "__main__":
    print("Phase 1 Security Testing")
    print("=" * 40)
    
    tests = [
        test_security_headers,
        test_input_validation,
        test_rate_limiting
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    if passed == len(tests):
        print("Phase 1 Security: COMPLETE")
    else:
        print("Some security features need attention")
