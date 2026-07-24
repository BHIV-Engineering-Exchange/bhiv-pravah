#!/usr/bin/env python3
"""
Test script for configuration fixes in InsightFlow project.

Tests:
1. Environment Variable Parsing with error handling
2. Production Configuration Validation
"""

import os
import sys
from unittest.mock import patch

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def test_safe_environment_parsing():
    """Test safe environment variable parsing"""
    print("🔧 Testing Safe Environment Variable Parsing...")
    
    # Import the safe parsing functions
    from app.core.config import safe_int, safe_float, safe_bool
    
    # Test 1: Valid integer parsing
    result = safe_int("123", 0)
    if result != 123:
        print(f"❌ FAIL: Expected 123, got {result}")
        return False
    print("✅ PASS: Valid integer parsing works")
    
    # Test 2: Invalid integer parsing (fallback)
    result = safe_int("invalid", 42)
    if result != 42:
        print(f"❌ FAIL: Expected fallback 42, got {result}")
        return False
    print("✅ PASS: Invalid integer falls back to default")
    
    # Test 3: Valid float parsing
    result = safe_float("3.14", 0.0)
    if abs(result - 3.14) > 0.001:
        print(f"❌ FAIL: Expected 3.14, got {result}")
        return False
    print("✅ PASS: Valid float parsing works")
    
    # Test 4: Invalid float parsing (fallback)
    result = safe_float("not_a_float", 1.5)
    if result != 1.5:
        print(f"❌ FAIL: Expected fallback 1.5, got {result}")
        return False
    print("✅ PASS: Invalid float falls back to default")
    
    # Test 5: Boolean parsing (true values)
    for true_val in ['true', 'True', '1', 'yes', 'on']:
        result = safe_bool(true_val, False)
        if not result:
            print(f"❌ FAIL: '{true_val}' should parse as True")
            return False
    print("✅ PASS: Boolean true values parse correctly")
    
    # Test 6: Boolean parsing (false values)
    for false_val in ['false', 'False', '0', 'no', 'off', 'invalid']:
        result = safe_bool(false_val, True)
        if result:
            print(f"❌ FAIL: '{false_val}' should parse as False")
            return False
    print("✅ PASS: Boolean false values parse correctly")
    
    # Test 7: None handling
    result = safe_bool(None, True)
    if not result:
        print("❌ FAIL: None should return default True")
        return False
    print("✅ PASS: None values use default")
    
    return True


def test_configuration_with_invalid_env_vars():
    """Test configuration loading with invalid environment variables"""
    print("⚙️ Testing Configuration with Invalid Environment Variables...")
    
    # Test with invalid environment variables
    invalid_env = {
        'SOVEREIGN_DB_PORT': 'not_a_number',
        'KARMA_CACHE_TTL': 'invalid_int',
        'KARMA_WEIGHT': 'not_a_float',
        'STP_ENABLED': 'maybe',
        'KARMA_ENABLED': 'invalid_bool'
    }
    
    with patch.dict(os.environ, invalid_env):
        try:
            # Import after setting invalid environment
            import importlib
            if 'app.core.config' in sys.modules:
                importlib.reload(sys.modules['app.core.config'])
            
            from app.core.config import Settings
            
            # This should not crash, but use defaults
            settings = Settings(JWT_SECRET_KEY="test-key")
            
            # Verify defaults are used
            if settings.SOVEREIGN_DB_PORT != 5432:
                print(f"❌ FAIL: Expected default port 5432, got {settings.SOVEREIGN_DB_PORT}")
                return False
            
            if settings.KARMA_CACHE_TTL != 60:
                print(f"❌ FAIL: Expected default TTL 60, got {settings.KARMA_CACHE_TTL}")
                return False
            
            if abs(settings.KARMA_WEIGHT - 0.15) > 0.001:
                print(f"❌ FAIL: Expected default weight 0.15, got {settings.KARMA_WEIGHT}")
                return False
            
            print("✅ PASS: Invalid environment variables use safe defaults")
            return True
            
        except Exception as e:
            print(f"❌ FAIL: Configuration should not crash with invalid env vars: {e}")
            return False


def test_production_configuration_validation():
    """Test production configuration validation"""
    print("🏭 Testing Production Configuration Validation...")
    
    from app.core.config import Settings
    
    # Test 1: Development configuration (should have warnings)
    dev_settings = Settings(
        JWT_SECRET_KEY="your-super-secret-key-change-in-production",  # Default value
        SOVEREIGN_DB_HOST="localhost",  # Localhost
        SOVEREIGN_AUTH_URL="http://localhost:8003/auth",  # Localhost
        KARMA_ENDPOINT="http://localhost:8002/api/karma",  # Localhost
        SOVEREIGN_SERVICE_KEY="sovereign-service-key-placeholder",  # Placeholder
        ENVIRONMENT="development",
        DEBUG=True
    )
    
    is_ready, warnings = dev_settings.validate_production_config()
    
    if is_ready:
        print("❌ FAIL: Development config should not be production ready")
        return False
    
    if len(warnings) == 0:
        print("❌ FAIL: Development config should have warnings")
        return False
    
    print(f"✅ PASS: Development config has {len(warnings)} warnings (expected)")
    
    # Test 2: Production configuration (should be ready)
    prod_settings = Settings(
        JWT_SECRET_KEY="secure-production-jwt-secret-key-256-bits",
        SOVEREIGN_DB_HOST="prod-db.company.com",
        SOVEREIGN_AUTH_URL="https://auth.company.com/auth",
        KARMA_ENDPOINT="https://karma.company.com/api/karma",
        SOVEREIGN_SERVICE_KEY="secure-production-service-key",
        SOVEREIGN_JWT_SECRET="secure-production-jwt-secret",
        ENVIRONMENT="production",
        DEBUG=False,
        CORS_ORIGINS=["https://app.company.com"]
    )
    
    is_ready, warnings = prod_settings.validate_production_config()
    
    if not is_ready:
        print(f"❌ FAIL: Production config should be ready. Warnings: {warnings}")
        return False
    
    if len(warnings) > 0:
        print(f"❌ FAIL: Production config should have no warnings. Got: {warnings}")
        return False
    
    print("✅ PASS: Production config is ready with no warnings")
    
    # Test 3: Mixed configuration (some issues)
    mixed_settings = Settings(
        JWT_SECRET_KEY="secure-key",
        SOVEREIGN_DB_HOST="prod-db.company.com",  # Good
        SOVEREIGN_AUTH_URL="http://localhost:8003/auth",  # Bad - localhost
        KARMA_ENDPOINT="https://karma.company.com/api/karma",  # Good
        SOVEREIGN_SERVICE_KEY="sovereign-service-key-placeholder",  # Bad - placeholder
        ENVIRONMENT="production",
        DEBUG=True,  # Bad - debug in production
        CORS_ORIGINS=["https://app.company.com", "http://localhost:3000"]  # Mixed
    )
    
    is_ready, warnings = mixed_settings.validate_production_config()
    
    if is_ready:
        print("❌ FAIL: Mixed config should not be production ready")
        return False
    
    expected_warnings = 4  # localhost auth, placeholder key, debug=true, localhost cors
    if len(warnings) != expected_warnings:
        print(f"❌ FAIL: Expected {expected_warnings} warnings, got {len(warnings)}: {warnings}")
        return False
    
    print(f"✅ PASS: Mixed config has expected {len(warnings)} warnings")
    
    return True


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running InsightFlow Configuration Fixes Tests\\n")
    
    tests = [
        ("Safe Environment Parsing", test_safe_environment_parsing),
        ("Configuration with Invalid Env Vars", test_configuration_with_invalid_env_vars),
        ("Production Configuration Validation", test_production_configuration_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All configuration fixes are working correctly!")
        return True
    else:
        print("⚠️ Some fixes need attention.")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)