import requests
import json

def test_ai_matching_endpoints():
    base_url = "https://bhiv-hr-gateway-ltg0.onrender.com"
    headers = {"Authorization": "Bearer <YOUR_API_KEY>"}
    
    # Expected schemas based on Gateway code analysis
    endpoints = [
        {
            "name": "Get Top Matches",
            "method": "GET",
            "path": "/v1/match/1/top",
            "auth": True,
            "timeout": 60,  # AI processing can take time
            "expected_schema": ["matches", "top_candidates", "job_id", "limit", "total_candidates", "algorithm_version", "processing_time", "ai_analysis", "agent_status"]
        },
        {
            "name": "Batch Match Jobs",
            "method": "POST",
            "path": "/v1/match/batch",
            "auth": True,
            "timeout": 90,  # Batch processing takes longer
            "data": [1, 2],  # List of job IDs
            "expected_schema": ["batch_results", "total_jobs_processed", "total_candidates_analyzed", "algorithm_version", "status"]
        }
    ]
    
    print("AI Matching Engine Endpoints - Schema Validation & Testing")
    print("=" * 65)
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']} - {endpoint['method']} {endpoint['path']}")
        print("-" * 55)
        
        try:
            url = f"{base_url}{endpoint['path']}"
            req_headers = headers if endpoint.get("auth") else {}
            timeout = endpoint.get("timeout", 15)
            
            print(f"Timeout: {timeout}s (AI processing)")
            
            # Make request
            if endpoint["method"] == "GET":
                response = requests.get(url, headers=req_headers, timeout=timeout)
            elif endpoint["method"] == "POST":
                response = requests.post(url, json=endpoint.get("data", {}), headers=req_headers, timeout=timeout)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
            print(f"Auth Required: {'YES' if endpoint.get('auth') else 'NO'}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    actual_schema = list(data.keys()) if isinstance(data, dict) else []
                    expected_schema = endpoint["expected_schema"]
                    
                    # Schema validation
                    schema_valid = all(key in actual_schema for key in expected_schema)
                    missing = [k for k in expected_schema if k not in actual_schema]
                    extra = [k for k in actual_schema if k not in expected_schema]
                    
                    print(f"Expected Schema: {expected_schema}")
                    print(f"Actual Schema: {actual_schema}")
                    print(f"Schema Valid: {'YES' if schema_valid else 'NO'}")
                    
                    if missing:
                        print(f"Missing Keys: {missing}")
                    if extra:
                        print(f"Extra Keys: {extra}")
                    
                    # Show sample response data
                    print("Sample Response:")
                    sample = json.dumps(data, indent=2)[:400]
                    print(f"{sample}{'...' if len(str(data)) > 400 else ''}")
                    
                    # Validate specific AI matching data
                    if endpoint["path"].startswith("/v1/match/") and endpoint["method"] == "GET":
                        matches = data.get("matches", [])
                        top_candidates = data.get("top_candidates", [])
                        algorithm_version = data.get("algorithm_version", "N/A")
                        processing_time = data.get("processing_time", "N/A")
                        agent_status = data.get("agent_status", "N/A")
                        
                        print(f"Matches Found: {len(matches)}")
                        print(f"Top Candidates: {len(top_candidates)}")
                        print(f"Algorithm Version: {algorithm_version}")
                        print(f"Processing Time: {processing_time}")
                        print(f"Agent Status: {agent_status}")
                        
                        if matches and len(matches) > 0:
                            first_match = matches[0]
                            print(f"Top Match: {first_match.get('name', 'N/A')} (Score: {first_match.get('score', 'N/A')})")
                    
                    elif endpoint["method"] == "POST" and "batch" in endpoint["path"]:
                        batch_results = data.get("batch_results", [])
                        total_jobs = data.get("total_jobs_processed", 0)
                        total_candidates = data.get("total_candidates_analyzed", 0)
                        algorithm_version = data.get("algorithm_version", "N/A")
                        status = data.get("status", "N/A")
                        
                        print(f"Batch Results: {len(batch_results)} jobs processed")
                        print(f"Total Jobs: {total_jobs}")
                        print(f"Total Candidates: {total_candidates}")
                        print(f"Algorithm Version: {algorithm_version}")
                        print(f"Status: {status}")
                    
                except json.JSONDecodeError:
                    print("ERROR: Invalid JSON response")
                    print(f"Raw Response: {response.text[:100]}...")
                    
            else:
                print(f"FAILED - HTTP {response.status_code}")
                print(f"Error: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            print(f"TIMEOUT - Request exceeded {timeout}s (AI processing can be slow)")
        except Exception as e:
            print(f"ERROR - {str(e)}")
    
    print(f"\n{'='*65}")
    print("AI Matching Engine Endpoints validation complete!")
    print("Note: AI processing may take 30-60s for complex matching operations")

if __name__ == "__main__":
    test_ai_matching_endpoints()
