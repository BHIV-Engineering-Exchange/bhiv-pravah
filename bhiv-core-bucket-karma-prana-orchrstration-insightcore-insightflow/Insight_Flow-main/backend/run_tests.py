# run_tests.py
"""
Complete test suite runner for InsightFlow.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run command and report results"""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")
        return result.returncode
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return 1


def main():
    """Run complete test suite"""
    
    print("=== InsightFlow Complete Test Suite ===\n")
    
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    failed_tests = []
    
    # 1. Run all tests with coverage
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--cov=app", "--cov-report=html"]
    if run_command(cmd, "Complete Test Suite with Coverage") != 0:
        failed_tests.append("Complete Test Suite")
    
    # 2. Run specific test categories
    test_categories = [
        ("tests/adapters/", "Phase 1 - Adapter Tests"),
        ("tests/validators/", "Phase 1 - Validator Tests"), 
        ("tests/services/", "Phase 2 - Service Tests"),
        ("tests/ml/", "Phase 2 - ML Tests"),
        ("tests/integration/", "Phase 3 - Integration Tests"),
        ("tests/performance/", "Phase 3 - Performance Tests")
    ]
    
    for test_path, description in test_categories:
        if Path(test_path).exists():
            cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
            if run_command(cmd, description) != 0:
                failed_tests.append(description)
    
    # 3. Run with detailed output
    cmd = [sys.executable, "-m", "pytest", "tests/", "-vv", "-s"]
    if run_command(cmd, "Detailed Test Output") != 0:
        failed_tests.append("Detailed Tests")
    
    # 4. Show slowest tests
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--durations=10"]
    if run_command(cmd, "Performance Analysis") != 0:
        failed_tests.append("Performance Analysis")
    
    # Summary
    print(f"\n=== Test Suite Summary ===")
    if failed_tests:
        print(f"❌ {len(failed_tests)} test categories failed:")
        for test in failed_tests:
            print(f"  - {test}")
        return 1
    else:
        print("✅ All test categories passed!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)