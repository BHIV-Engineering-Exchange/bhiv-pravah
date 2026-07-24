"""
Test script for Document 07: Integration Gate Checklist endpoints
Run this after starting the server to verify all integration gate endpoints work correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", params=None, json_data=None):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, params=params, json=json_data)
        
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
    print("DOCUMENT 07: INTEGRATION GATE CHECKLIST - ENDPOINT TESTS")
    print("="*60)
    
    results = []
    
    # Test GET endpoints
    get_tests = [
        ("Get Integration Requirements", f"{BASE_URL}/governance/integration-gate/requirements"),
        ("Get Approval Checklist", f"{BASE_URL}/governance/integration-gate/checklist"),
        ("Get Blocking Criteria", f"{BASE_URL}/governance/integration-gate/blocking-criteria"),
        ("Get Approval Timeline", f"{BASE_URL}/governance/integration-gate/timeline"),
        ("Get Approval Likelihood", f"{BASE_URL}/governance/integration-gate/approval-likelihood"),
        ("Get Conditional Examples", f"{BASE_URL}/governance/integration-gate/conditional-examples"),
    ]
    
    for name, url in get_tests:
        results.append(test_endpoint(name, url))
    
    # Test validate integration request
    print(f"\n{'='*60}")
    print("Testing: Validate Integration Request")
    
    # Test with complete request
    complete_request = {
        "integration_overview": {
            "system_name": "TestSystem",
            "purpose": "Test integration",
            "owner_contact": "test@example.com",
            "timeline": "2 weeks"
        },
        "data_requirements": {
            "bucket_data_needed": "execution logs",
            "usage_description": "analytics",
            "access_frequency": "5x/day"
        },
        "architecture_diagram": {
            "connection_method": "REST API",
            "data_flow": "one-way",
            "reverse_dependencies": "none"
        },
        "api_usage_plan": {
            "endpoints": ["/run-basket"],
            "call_frequency": "5x/day",
            "error_handling": "retry with backoff",
            "timeout_handling": "5 second timeout"
        },
        "error_handling_document": {
            "bucket_down_strategy": "cache and retry",
            "error_response_strategy": "log and alert",
            "slow_response_strategy": "timeout after 5s",
            "graceful_degradation": "use cached data"
        }
    }
    
    results.append(test_endpoint(
        "Validate Complete Request",
        f"{BASE_URL}/governance/integration-gate/validate-request",
        method="POST",
        json_data=complete_request
    ))
    
    # Test with incomplete request
    incomplete_request = {
        "integration_overview": {
            "system_name": "TestSystem"
        }
    }
    
    results.append(test_endpoint(
        "Validate Incomplete Request",
        f"{BASE_URL}/governance/integration-gate/validate-request",
        method="POST",
        json_data=incomplete_request
    ))
    
    # Test validate checklist section
    print(f"\n{'='*60}")
    print("Testing: Validate Checklist Section")
    
    checklist_data = {
        "integration_overview_provided": True,
        "data_requirements_specified": True,
        "architecture_diagram_provided": True,
        "api_usage_plan_documented": True,
        "error_handling_plan_provided": False
    }
    
    results.append(test_endpoint(
        "Validate Section A",
        f"{BASE_URL}/governance/integration-gate/validate-section?section_name=section_a_requirements",
        method="POST",
        json_data=checklist_data
    ))
    
    # Test check blocking criteria
    print(f"\n{'='*60}")
    print("Testing: Check Blocking Criteria")
    
    # Test with no violations
    clean_integration = {
        "bidirectional_dependency": False,
        "uses_rejected_artifacts": False,
        "has_pii_without_anonymization": False,
        "reverse_dependency": False,
        "has_error_handling": True,
        "violates_one_way_flow": False,
        "requires_unavailable_guarantees": False,
        "has_embedded_bucket_logic": False
    }
    
    results.append(test_endpoint(
        "Check Blocking (Clean)",
        f"{BASE_URL}/governance/integration-gate/check-blocking",
        method="POST",
        json_data=clean_integration
    ))
    
    # Test with violations
    blocked_integration = {
        "bidirectional_dependency": True,
        "uses_rejected_artifacts": False,
        "has_pii_without_anonymization": True,
        "reverse_dependency": False,
        "has_error_handling": False,
        "violates_one_way_flow": False,
        "requires_unavailable_guarantees": False,
        "has_embedded_bucket_logic": False
    }
    
    results.append(test_endpoint(
        "Check Blocking (Violations)",
        f"{BASE_URL}/governance/integration-gate/check-blocking",
        method="POST",
        json_data=blocked_integration
    ))
    
    # Test generate approval decision
    print(f"\n{'='*60}")
    print("Testing: Generate Approval Decision")
    
    results.append(test_endpoint(
        "Generate Approval",
        f"{BASE_URL}/governance/integration-gate/generate-approval",
        method="POST",
        params={
            "system_name": "TestSystem",
            "status": "approved",
            "rationale": "Meets all criteria",
            "owner_contact": "test@example.com"
        }
    ))
    
    # Test generate rejection feedback
    print(f"\n{'='*60}")
    print("Testing: Generate Rejection Feedback")
    
    rejection_data = {
        "system_name": "TestSystem",
        "issues": [
            {"section": "section_b", "issue": "Bidirectional dependency detected"},
            {"section": "section_f", "issue": "No HTTPS enforcement"}
        ],
        "path_forward": [
            "Remove bidirectional dependency",
            "Implement HTTPS-only calls"
        ]
    }
    
    results.append(test_endpoint(
        "Generate Rejection",
        f"{BASE_URL}/governance/integration-gate/generate-rejection",
        method="POST",
        json_data=rejection_data
    ))
    
    # Test calculate deadline
    print(f"\n{'='*60}")
    print("Testing: Calculate Approval Deadline")
    
    results.append(test_endpoint(
        "Calculate Deadline (Now)",
        f"{BASE_URL}/governance/integration-gate/calculate-deadline",
        method="POST"
    ))
    
    results.append(test_endpoint(
        "Calculate Deadline (Specific Date)",
        f"{BASE_URL}/governance/integration-gate/calculate-deadline",
        method="POST",
        params={"submission_date": "2026-01-13T00:00:00"}
    ))
    
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
