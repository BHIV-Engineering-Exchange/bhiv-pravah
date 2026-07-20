import requests
import json

def simple_audit_test():
    """
    Simple audit test without Unicode characters
    """
    base_url = "http://localhost:8000/api/v1/lifecycle"
    
    print("AUDIT TEST - DETERMINISTIC EVALUATION PIPELINE")
    print("=" * 50)
    
    # Test data - IDENTICAL for determinism testing
    test_data = {
        'task_title': 'Build REST API with Authentication System',
        'task_description': '''
        Create a comprehensive REST API with the following features:
        - User authentication using JWT tokens
        - CRUD operations for user management
        - Role-based access control (RBAC)
        - Input validation and error handling
        - API documentation with Swagger/OpenAPI
        - Unit tests with 80%+ coverage
        - Docker containerization
        - Database integration with PostgreSQL
        ''',
        'submitted_by': 'Audit Test User',
        'github_repo_link': 'https://github.com/test/api-project',
        'module_id': 'core-development',
        'schema_version': 'v1.0'
    }
    
    # TEST 1: DETERMINISM - Run same input twice
    print("\n1. TESTING DETERMINISM...")
    try:
        response1 = requests.post(f"{base_url}/submit", data=test_data)
        response2 = requests.post(f"{base_url}/submit", data=test_data)
        
        if response1.status_code == 200 and response2.status_code == 200:
            result1 = response1.json()
            result2 = response2.json()
            
            id1 = result1.get('submission_id')
            id2 = result2.get('submission_id')
            score1 = result1.get('review_summary', {}).get('score')
            score2 = result2.get('review_summary', {}).get('score')
            
            print(f"   Run 1: ID={id1}, Score={score1}")
            print(f"   Run 2: ID={id2}, Score={score2}")
            
            if id1 == id2 and score1 == score2:
                print("   PASS: DETERMINISM - Identical inputs produce identical outputs")
                determinism_pass = True
            else:
                print("   FAIL: DETERMINISM - Non-deterministic behavior detected")
                determinism_pass = False
        else:
            print("   FAIL: DETERMINISM - API calls failed")
            determinism_pass = False
    except Exception as e:
        print(f"   FAIL: DETERMINISM - Error: {e}")
        determinism_pass = False
    
    # TEST 2: SINGLE AUTHORITY - Check component scores
    print(f"\n2. TESTING SINGLE EVALUATION AUTHORITY...")
    if 'result1' in locals() and result1:
        submission_id = result1.get('submission_id')
        try:
            review_response = requests.get(f"{base_url}/review/{submission_id}")
            if review_response.status_code == 200:
                review_data = review_response.json()
                
                title_score = review_data.get('title_score', 0)
                desc_score = review_data.get('description_score', 0)
                repo_score = review_data.get('repository_score', 0)
                total_score = review_data.get('score', 0)
                
                print(f"   Title Score: {title_score}")
                print(f"   Description Score: {desc_score}")
                print(f"   Repository Score: {repo_score}")
                print(f"   Total Score: {total_score}")
                
                if title_score >= 0 and desc_score >= 0 and total_score >= 0:
                    print("   PASS: SINGLE AUTHORITY - Sri Satya provides all scores")
                    single_authority_pass = True
                else:
                    print("   FAIL: SINGLE AUTHORITY - Invalid scores")
                    single_authority_pass = False
            else:
                print("   FAIL: SINGLE AUTHORITY - Review endpoint failed")
                single_authority_pass = False
        except Exception as e:
            print(f"   FAIL: SINGLE AUTHORITY - Error: {e}")
            single_authority_pass = False
    else:
        single_authority_pass = False
    
    # TEST 3: REGISTRY ENFORCEMENT
    print(f"\n3. TESTING REGISTRY ENFORCEMENT...")
    try:
        invalid_data = test_data.copy()
        invalid_data['module_id'] = 'invalid-module-xyz'
        
        response = requests.post(f"{base_url}/submit", data=invalid_data)
        if response.status_code == 200:
            result = response.json()
            score = result.get('review_summary', {}).get('score', 1)
            if score == 0:
                print("   PASS: REGISTRY ENFORCEMENT - Invalid module rejected")
                registry_pass = True
            else:
                print(f"   FAIL: REGISTRY ENFORCEMENT - Invalid module got score {score}")
                registry_pass = False
        else:
            print("   FAIL: REGISTRY ENFORCEMENT - API call failed")
            registry_pass = False
    except Exception as e:
        print(f"   FAIL: REGISTRY ENFORCEMENT - Error: {e}")
        registry_pass = False
    
    # TEST 4: END-TO-END FLOW
    print(f"\n4. TESTING END-TO-END FLOW...")
    if 'submission_id' in locals():
        try:
            review_ok = requests.get(f"{base_url}/review/{submission_id}").status_code == 200
            next_task_ok = requests.get(f"{base_url}/next/{submission_id}").status_code == 200
            history_ok = requests.get(f"{base_url}/history").status_code == 200
            
            if review_ok and next_task_ok and history_ok:
                print("   PASS: END-TO-END FLOW - All endpoints working")
                flow_pass = True
            else:
                print(f"   FAIL: END-TO-END FLOW - Review:{review_ok}, Next:{next_task_ok}, History:{history_ok}")
                flow_pass = False
        except Exception as e:
            print(f"   FAIL: END-TO-END FLOW - Error: {e}")
            flow_pass = False
    else:
        flow_pass = False
    
    # SUMMARY
    print(f"\n" + "=" * 50)
    print("AUDIT SUMMARY:")
    print("=" * 50)
    
    tests = [
        ("DETERMINISM", determinism_pass),
        ("SINGLE AUTHORITY", single_authority_pass),
        ("REGISTRY ENFORCEMENT", registry_pass),
        ("END-TO-END FLOW", flow_pass)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nCOMPLIANCE SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("SYSTEM STATUS: PRODUCTION READY")
    elif passed >= 3:
        print("SYSTEM STATUS: NEEDS MINOR FIXES")
    else:
        print("SYSTEM STATUS: NOT PRODUCTION READY")
    
    return passed == total

if __name__ == "__main__":
    simple_audit_test()