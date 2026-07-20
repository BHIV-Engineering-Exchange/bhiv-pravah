import requests

def test_module_selection():
    base_url = "http://localhost:8000/api/v1/lifecycle"
    
    print("Testing Module Selection and Schema Version")
    print("=" * 50)
    
    # Test with Core Development module
    print("\n1. Testing Core Development module...")
    submit_data = {
        'task_title': 'Implement User Authentication System',
        'task_description': '''
        Build a comprehensive user authentication system with:
        - JWT token-based authentication
        - Password hashing with bcrypt
        - Role-based access control (RBAC)
        - Session management
        - Password reset functionality
        - Multi-factor authentication (MFA)
        - OAuth integration (Google, GitHub)
        - Rate limiting for login attempts
        - Audit logging for security events
        ''',
        'submitted_by': 'Core Developer',
        'github_repo_link': 'https://github.com/example/auth-system',
        'module_id': 'core-development',
        'schema_version': 'v1.0'
    }
    
    try:
        response = requests.post(f"{base_url}/submit", data=submit_data)
        if response.status_code == 200:
            result = response.json()
            submission_id = result['submission_id']
            print(f"SUCCESS: Core Development task submitted!")
            print(f"   Submission ID: {submission_id}")
            print(f"   Score: {result['review_summary']['score']}")
            print(f"   Status: {result['review_summary']['status']}")
            
            # Check review details for registry validation
            review_response = requests.get(f"{base_url}/review/{submission_id}")
            if review_response.status_code == 200:
                review_data = review_response.json()
                if review_data.get('registry_validation'):
                    reg_val = review_data['registry_validation']
                    print(f"   Registry Validation:")
                    print(f"     Module ID: {reg_val['module_id']}")
                    print(f"     Schema Version: {reg_val['schema_version']}")
                    print(f"     Validation Passed: {reg_val['validation_passed']}")
            
        else:
            print(f"FAILED: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test with Security Implementation module
    print("\n2. Testing Security Implementation module...")
    submit_data_security = {
        'task_title': 'Security Hardening and Vulnerability Assessment',
        'task_description': '''
        Implement comprehensive security measures:
        - SQL injection prevention
        - XSS protection
        - CSRF tokens
        - Input validation and sanitization
        - Secure headers implementation
        - Encryption at rest and in transit
        - Security scanning and monitoring
        - Penetration testing framework
        ''',
        'submitted_by': 'Security Engineer',
        'github_repo_link': 'https://github.com/example/security-hardening',
        'module_id': 'security-implementation',
        'schema_version': 'v1.0'
    }
    
    try:
        response = requests.post(f"{base_url}/submit", data=submit_data_security)
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Security Implementation task submitted!")
            print(f"   Submission ID: {result['submission_id']}")
            print(f"   Score: {result['review_summary']['score']}")
            print(f"   Status: {result['review_summary']['status']}")
        else:
            print(f"FAILED: {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    print(f"\nModule selection testing complete!")
    print("The frontend form now includes:")
    print("- Module Selection dropdown (8 available modules)")
    print("- Schema Version selection (v1.0, v1.1, v3.0)")
    print("- Registry validation display in review results")

if __name__ == "__main__":
    test_module_selection()