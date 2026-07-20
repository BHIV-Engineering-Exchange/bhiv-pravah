#!/usr/bin/env python3
"""
Simple test runner for comprehensive endpoint testing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

try:
    from comprehensive_endpoint_tests import ComprehensiveEndpointTester
    
    print("Initializing comprehensive endpoint tester...")
    tester = ComprehensiveEndpointTester()
    print(f"Loaded {len(tester.endpoints)} endpoints for testing")
    
    print("Running synchronous tests...")
    tester.run_sync_tests()
    
except Exception as e:
    print(f"Error running tests: {e}")
    import traceback
    traceback.print_exc()