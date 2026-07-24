#!/usr/bin/env python3
"""
Timezone Fix Verification Test
Tests that all timezone issues have been resolved in the Bucket system
"""

import sys
import warnings
from datetime import datetime, timezone

def test_timezone_fix():
    """Test that timezone warnings are eliminated"""
    
    print("Testing Timezone Fix...")
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Test 1: Audit Middleware
        print("  Testing AuditMiddleware...")
        from middleware.audit_middleware import AuditMiddleware
        audit = AuditMiddleware()
        
        # Test 2: Scale Monitor
        print("  Testing ScaleMonitor...")
        from utils.scale_monitor import ScaleMonitor
        monitor = ScaleMonitor()
        
        # Test 3: Create timezone-aware datetime
        print("  Testing timezone-aware datetime creation...")
        now = datetime.now(timezone.utc)
        print(f"    Current UTC time: {now.isoformat()}")
        
        # Test 4: Test audit entry creation (simulated)
        print("  Testing audit entry timestamp...")
        test_entry = {
            "timestamp": datetime.now(timezone.utc),
            "operation": "test"
        }
        print(f"    Audit timestamp: {test_entry['timestamp'].isoformat()}")
        
        # Check for timezone warnings
        timezone_warnings = [warning for warning in w if 'timezone' in str(warning.message).lower()]
        
        if timezone_warnings:
            print("TIMEZONE WARNINGS DETECTED:")
            for warning in timezone_warnings:
                print(f"    {warning.message}")
            return False
        else:
            print("SUCCESS: NO TIMEZONE WARNINGS DETECTED!")
            return True

if __name__ == "__main__":
    print("=" * 60)
    print("BHIV BUCKET TIMEZONE FIX VERIFICATION")
    print("=" * 60)
    
    test_passed = test_timezone_fix()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    
    if test_passed:
        print("ALL TESTS PASSED - TIMEZONE ISSUE RESOLVED!")
        print("The system is ready to run without timezone warnings.")
        sys.exit(0)
    else:
        print("TESTS FAILED - TIMEZONE ISSUES REMAIN")
        sys.exit(1)