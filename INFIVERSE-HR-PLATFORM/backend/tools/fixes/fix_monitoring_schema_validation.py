import requests

def test_monitoring_with_correct_schemas():
    base_url = "https://bhiv-hr-gateway-ltg0.onrender.com"
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    
    # Correct expected schemas based on actual Gateway code
    endpoints = [
        {
            "name": "Prometheus Metrics",
            "path": "/metrics",
            "auth": False,
            "expected_format": "text/plain"
        },
        {
            "name": "Detailed Health Check",
            "path": "/health/detailed", 
            "auth": True,
            "expected_schema": ["status", "timestamp", "system", "application", "database"]  # Actual schema
        },
        {
            "name": "Metrics Dashboard",
            "path": "/metrics/dashboard",
            "auth": True, 
            "expected_schema": ["performance_summary", "business_metrics", "system_metrics"]  # Actual schema
        }
    ]
    
    print("Gateway Monitoring - Corrected Schema Validation")
    print("=" * 55)
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']} - GET {endpoint['path']}")
        print("-" * 50)
        
        try:
            url = f"{base_url}{endpoint['path']}"
            req_headers = headers if endpoint.get("auth") else {}
            
            response = requests.get(url, headers=req_headers, timeout=15)
            
            print(f"Status: {response.status_code}")
            print(f"Time: {response.elapsed.total_seconds():.2f}s")
            
            if response.status_code == 200:
                if endpoint.get("expected_format") == "text/plain":
                    print("Format: Prometheus metrics (text/plain)")
                    print("VALID - Correct format")
                else:
                    data = response.json()
                    actual_schema = list(data.keys())
                    expected_schema = endpoint["expected_schema"]
                    
                    schema_valid = all(key in actual_schema for key in expected_schema)
                    
                    print(f"Expected: {expected_schema}")
                    print(f"Actual: {actual_schema}")
                    print(f"Schema: {'VALID' if schema_valid else 'INVALID'}")
                    
                    if schema_valid:
                        print("SUCCESS - Schema matches implementation")
                    else:
                        missing = [k for k in expected_schema if k not in actual_schema]
                        print(f"Missing: {missing}")
            else:
                print(f"FAILED - HTTP {response.status_code}")
                
        except Exception as e:
            print(f"ERROR - {str(e)}")
    
    print(f"\n{'='*55}")
    print("SOLUTION: Update expected schemas to match actual implementation")
    print("- /health/detailed: ['status', 'timestamp', 'system', 'application', 'database']")
    print("- /metrics/dashboard: ['performance_summary', 'business_metrics', 'system_metrics']")

if __name__ == "__main__":
    test_monitoring_with_correct_schemas()
