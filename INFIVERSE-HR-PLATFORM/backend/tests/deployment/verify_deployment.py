import requests
import json

# API Configuration
BASE_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY = "<YOUR_API_KEY>"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def test_endpoint(endpoint, method="GET", data=None):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        
        return {
            "status": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
        }
    except Exception as e:
        return {"status": "ERROR", "success": False, "data": str(e)}

def main():
    print("BHIV HR Platform - Deployment Verification")
    print("=" * 50)
    
    # Critical endpoints to test
    endpoints = [
        ("/health", "GET"),
        ("/v1/database/schema", "GET"),
        ("/v1/match/1/top", "GET"),  # AI matching test
        ("/v1/client/login", "POST", {"username": "<DEMO_USERNAME>", "password": "<DEMO_PASSWORD>"}),
        ("/v1/candidates", "GET"),
        ("/v1/jobs", "GET")
    ]
    
    results = []
    for endpoint_info in endpoints:
        endpoint = endpoint_info[0]
        method = endpoint_info[1]
        data = endpoint_info[2] if len(endpoint_info) > 2 else None
        
        print(f"Testing {method} {endpoint}...")
        result = test_endpoint(endpoint, method, data)
        results.append((endpoint, result))
        
        if result["success"]:
            print(f"  ✅ SUCCESS ({result['status']})")
        else:
            print(f"  ❌ FAILED ({result['status']}) - {result['data']}")
    
    # Summary
    successful = sum(1 for _, r in results if r["success"])
    total = len(results)
    
    print(f"\nSUMMARY: {successful}/{total} endpoints working ({successful/total*100:.1f}%)")
    
    # Check specific issues
    print("\nCRITICAL CHECKS:")
    
    # Database schema check
    schema_result = next((r for e, r in results if "/database/schema" in e), None)
    if schema_result and schema_result["success"]:
        print("  ✅ Database schema accessible")
    else:
        print("  ❌ Database schema issues")
    
    # AI matching check
    match_result = next((r for e, r in results if "/match/" in e), None)
    if match_result and match_result["success"]:
        print("  ✅ AI matching working")
    else:
        print("  ❌ AI matching needs Gateway redeploy")
    
    # Client login check
    login_result = next((r for e, r in results if "/client/login" in e), None)
    if login_result and login_result["success"]:
        print("  ✅ Client login working")
    else:
        print("  ❌ Client login issues")

if __name__ == "__main__":
    main()
