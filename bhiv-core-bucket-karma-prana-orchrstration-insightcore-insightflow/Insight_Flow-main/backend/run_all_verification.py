# run_all_verification.py
"""
Master verification script that runs all tests and checks.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_script(script_name, description):
    """Run a verification script"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], check=False)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run complete verification suite"""
    
    print("=== InsightFlow Complete Verification Suite ===")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    
    verification_steps = [
        ("run_tests.py", "Complete Test Suite"),
        ("check_code_quality.py", "Code Quality Checks"),
        ("verify_endpoints.py", "Endpoint Verification")
    ]
    
    passed_steps = []
    failed_steps = []
    
    for script, description in verification_steps:
        script_path = backend_dir / script
        if script_path.exists():
            if run_script(str(script_path), description):
                passed_steps.append(description)
            else:
                failed_steps.append(description)
        else:
            print(f"⚠️  {description} - Script not found: {script}")
            failed_steps.append(description)
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {len(passed_steps)}")
    for step in passed_steps:
        print(f"   - {step}")
    
    if failed_steps:
        print(f"\n❌ Failed: {len(failed_steps)}")
        for step in failed_steps:
            print(f"   - {step}")
    
    print(f"\nCompleted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_steps:
        print("\n❌ VERIFICATION FAILED - Some checks did not pass")
        return 1
    else:
        print("\n✅ VERIFICATION PASSED - All checks successful!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)