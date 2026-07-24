#!/usr/bin/env python3
"""
STP Tests Runner

Run STP middleware tests to verify functionality.
"""

import subprocess
import sys
import os

def run_stp_tests():
    """Run STP middleware tests"""
    print("=" * 60)
    print("Running STP Middleware Tests")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run STP middleware tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/middleware/test_stp_middleware.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ All STP tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_stp_tests()
    sys.exit(0 if success else 1)