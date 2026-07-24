#!/usr/bin/env python3
"""
Test runner for Packet Validator tests.

This script can be used to run the packet validator tests independently.
"""

import subprocess
import sys
import os

def run_packet_validator_tests():
    """Run the packet validator tests"""
    try:
        # Change to the backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(backend_dir)
        
        # Run the tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/validators/test_packet_validator.py", 
            "-v"
        ], capture_output=True, text=True)
        
        print("Packet Validator Test Results:")
        print("=" * 50)
        print(result.stdout)
        
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_packet_validator_tests()
    sys.exit(0 if success else 1)