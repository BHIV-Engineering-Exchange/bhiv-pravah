"""
Comprehensive Test Runner for Sovereign Application Runtime (SAR)
Executes all test suites and provides consolidated results
"""
import subprocess
import sys
import os
from datetime import datetime

def run_test_suite(test_file, suite_name):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"RUNNING {suite_name} TEST SUITE")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                               capture_output=True, text=True, timeout=120)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"❌ {suite_name} test suite timed out")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ Error running {suite_name} test suite: {str(e)}")
        return False, "", str(e)

def main():
    """Main function to run all test suites"""
    print("🚀 Starting Comprehensive BHIV Application Framework Test Suite")
    print(f"📅 Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define all test suites
    test_suites = [
        ("test_auth_service.py", "Authentication Service"),
        ("test_tenant_service.py", "Tenant Service"),
        ("test_role_service.py", "Role Service"),
        ("test_audit_service.py", "Audit Service"),
        ("test_workflow_service.py", "Workflow Service"),
        ("test_adapters.py", "Integration Adapters")
    ]
    
    results = {}
    total_tests = len(test_suites)
    passed_tests = 0
    
    # Run each test suite
    for test_file, suite_name in test_suites:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            success, stdout, stderr = run_test_suite(test_path, suite_name)
            results[suite_name] = {
                "success": success,
                "stdout": stdout,
                "stderr": stderr
            }
            
            if success:
                passed_tests += 1
                print(f"✅ {suite_name} test suite PASSED")
            else:
                print(f"❌ {suite_name} test suite FAILED")
        else:
            print(f"⚠️  {suite_name} test suite file not found: {test_path}")
            results[suite_name] = {
                "success": False,
                "stdout": "",
                "stderr": "File not found"
            }
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST RUN SUMMARY")
    print(f"{'='*60}")
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for suite_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {status} - {suite_name}")
    
    # Overall result
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! BHIV Application Framework is functioning correctly.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)