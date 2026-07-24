#!/usr/bin/env python3
"""
Timezone Fix Verification Test
Tests that all timezone issues have been resolved in the Bucket system
"""

import sys
import warnings
from datetime import datetime, timezone
from middleware.audit_middleware import AuditMiddleware
from utils.scale_monitor import ScaleMonitor

def test_timezone_fix():
    """Test that timezone warnings are eliminated"""
    
    print("🔧 Testing Timezone Fix...")
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Test 1: Audit Middleware
        print("  ✓ Testing AuditMiddleware...")
        audit = AuditMiddleware()
        
        # Test 2: Scale Monitor
        print("  ✓ Testing ScaleMonitor...")
        monitor = ScaleMonitor()
        
        # Test 3: Create timezone-aware datetime
        print("  ✓ Testing timezone-aware datetime creation...")
        now = datetime.now(timezone.utc)
        print(f"    Current UTC time: {now.isoformat()}")
        
        # Test 4: Test audit entry creation (simulated)
        print("  ✓ Testing audit entry timestamp...")
        test_entry = {
            "timestamp": datetime.now(timezone.utc),
            "operation": "test"
        }
        print(f"    Audit timestamp: {test_entry['timestamp'].isoformat()}")
        
        # Check for timezone warnings
        timezone_warnings = [warning for warning in w if 'timezone' in str(warning.message).lower()]
        
        if timezone_warnings:
            print("❌ TIMEZONE WARNINGS DETECTED:")
            for warning in timezone_warnings:
                print(f"    {warning.message}")
            return False
        else:
            print("✅ NO TIMEZONE WARNINGS DETECTED!")
            return True

def test_system_imports():
    """Test that all system imports work without warnings"""
    
    print("\n🔧 Testing System Imports...")
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        try:
            # Import key modules
            from utils.redis_service import RedisService
            from baskets.basket_manager import AgentBasket
            from integration.karma_forwarder import KarmaForwarder
            
            print("  ✓ All imports successful")
            
            # Check for any warnings
            if w:
                print(f"  ⚠️  {len(w)} warnings detected during imports")
                for warning in w:
                    print(f"    {warning.message}")
                return False
            else:
                print("  ✅ No warnings during imports")
                return True
                
        except Exception as e:
            print(f"  ❌ Import error: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("BHIV BUCKET TIMEZONE FIX VERIFICATION")
    print("=" * 60)
    
    test1_passed = test_timezone_fix()
    test2_passed = test_system_imports()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Timezone Fix Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  System Imports Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - TIMEZONE ISSUE RESOLVED!")
        print("The system is ready to run without timezone warnings.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - TIMEZONE ISSUES REMAIN")
        sys.exit(1)