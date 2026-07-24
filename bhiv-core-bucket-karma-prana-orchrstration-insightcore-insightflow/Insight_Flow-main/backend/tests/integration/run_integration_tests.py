# tests/integration/run_integration_tests.py
"""
Script to run integration tests.
"""

import sys
import subprocess
from pathlib import Path


def run_integration_tests():
    """Run all integration tests"""
    
    # Get the integration tests directory
    test_dir = Path(__file__).parent
    
    print("=== Running InsightFlow Integration Tests ===\n")
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All integration tests passed!")
        else:
            print(f"\n❌ Some tests failed (exit code: {result.returncode})")
        
        return result.returncode
    
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_specific_test(test_name):
    """Run a specific test file"""
    
    test_dir = Path(__file__).parent
    test_file = test_dir / f"{test_name}.py"
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return 1
    
    print(f"=== Running {test_name} ===\n")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode
    
    except Exception as e:
        print(f"Error running test: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all integration tests
        exit_code = run_integration_tests()
    
    sys.exit(exit_code)