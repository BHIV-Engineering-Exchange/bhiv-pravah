#!/usr/bin/env python3
"""
Test script for security fixes in InsightFlow project.

Tests:
1. STP token cryptographic security
2. Configuration secret validation
"""

import os
import sys
import re
from unittest.mock import patch

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def test_stp_token_security():
    """Test STP token cryptographic security"""
    print("🔐 Testing STP Token Security...")
    
    from app.middleware.stp_middleware import STPMiddleware
    
    # Test 1: Token uniqueness and randomness
    tokens = set()
    for _ in range(1000):
        token = STPMiddleware.generate_stp_token()
        
        # Check format
        if not token.startswith('stp-'):
            print("❌ FAIL: Token should start with 'stp-'")
            return False
        
        # Check length (stp- + 32 hex chars = 36 total)
        if len(token) != 36:
            print(f"❌ FAIL: Token should be 36 characters, got {len(token)}")
            return False
        
        # Check hex format after prefix
        hex_part = token[4:]  # Remove 'stp-' prefix
        if not re.match(r'^[0-9a-f]{32}$', hex_part):
            print("❌ FAIL: Token should contain 32 hex characters after prefix")
            return False
        
        tokens.add(token)
    
    # Check uniqueness (should be 1000 unique tokens)
    if len(tokens) != 1000:
        print(f"❌ FAIL: Expected 1000 unique tokens, got {len(tokens)}")
        return False
    
    print("✅ PASS: STP tokens are unique and properly formatted")
    
    # Test 2: Entropy analysis (basic check)
    token_hex_parts = [token[4:] for token in list(tokens)[:100]]
    
    # Check character distribution
    char_counts = {}
    for token_hex in token_hex_parts:
        for char in token_hex:
            char_counts[char] = char_counts.get(char, 0) + 1
    
    # Should have reasonable distribution across hex characters
    expected_chars = set('0123456789abcdef')
    actual_chars = set(char_counts.keys())
    
    if not expected_chars.issubset(actual_chars):
        print("❌ FAIL: Token entropy appears low (missing hex characters)")
        return False
    
    print("✅ PASS: STP tokens have good entropy distribution")
    
    # Test 3: No predictable patterns
    tokens_list = list(tokens)[:10]
    
    # Check that consecutive tokens are not similar
    for i in range(len(tokens_list) - 1):
        token1 = tokens_list[i][4:]  # Remove prefix
        token2 = tokens_list[i + 1][4:]
        
        # Count different characters
        diff_count = sum(c1 != c2 for c1, c2 in zip(token1, token2))
        
        # Should have significant differences (at least 50% different)
        if diff_count < 16:  # Less than 50% of 32 characters
            print(f"❌ FAIL: Consecutive tokens too similar: {diff_count}/32 differences")
            return False
    
    print("✅ PASS: STP tokens show no predictable patterns")
    
    return True


def test_configuration_secret_validation():
    """Test configuration secret validation"""
    print("🔒 Testing Configuration Secret Validation...")
    
    from app.core.config import Settings
    from pydantic import ValidationError
    
    # Test 1: Placeholder values should be rejected
    try:
        Settings(
            JWT_SECRET_KEY="test-key",
            SOVEREIGN_SERVICE_KEY="sovereign-service-key-placeholder",
            ENVIRONMENT="production"
        )
        print("❌ FAIL: Placeholder service key should be rejected")
        return False
    except ValidationError as e:
        if "placeholder" in str(e):
            print("✅ PASS: Placeholder service key correctly rejected")
        else:
            print(f"❌ FAIL: Wrong validation error: {e}")
            return False
    
    # Test 2: Default JWT secret should be rejected
    try:
        Settings(
            JWT_SECRET_KEY="your-super-secret-key-change-in-production",
            SOVEREIGN_SERVICE_KEY="valid-service-key-12345",
            SOVEREIGN_JWT_SECRET="valid-jwt-secret-with-sufficient-length-12345"
        )
        print("❌ FAIL: Default JWT secret should be rejected")
        return False
    except ValidationError as e:
        if "placeholder" in str(e) or "default" in str(e):
            print("✅ PASS: Default JWT secret correctly rejected")
        else:
            print(f"❌ FAIL: Wrong validation error: {e}")
            return False
    
    # Test 3: Short secrets should be rejected
    try:
        Settings(
            JWT_SECRET_KEY="short",  # Too short
            SOVEREIGN_SERVICE_KEY="valid-service-key-12345",
            SOVEREIGN_JWT_SECRET="valid-jwt-secret-with-sufficient-length-12345"
        )
        print("❌ FAIL: Short JWT secret should be rejected")
        return False
    except ValidationError as e:
        if "32 characters" in str(e):
            print("✅ PASS: Short JWT secret correctly rejected")
        else:
            print(f"❌ FAIL: Wrong validation error: {e}")
            return False
    
    # Test 4: Valid secrets should be accepted
    try:
        settings = Settings(
            JWT_SECRET_KEY="this-is-a-very-secure-jwt-secret-key-with-sufficient-length",
            SOVEREIGN_SERVICE_KEY="secure-service-key-12345",
            SOVEREIGN_JWT_SECRET="this-is-a-very-secure-sovereign-jwt-secret-with-sufficient-length",
            ENVIRONMENT="development"  # Use development to avoid production validation
        )
        print("✅ PASS: Valid secrets accepted")
    except ValidationError as e:
        print(f"❌ FAIL: Valid secrets should be accepted: {e}")
        return False
    
    # Test 5: Production validation should catch security issues
    try:
        settings = Settings(
            JWT_SECRET_KEY="secure-jwt-secret-key-with-sufficient-length-for-production",
            SOVEREIGN_SERVICE_KEY="secure-service-key-12345",
            SOVEREIGN_JWT_SECRET="secure-sovereign-jwt-secret-with-sufficient-length-for-production",
            SOVEREIGN_DB_PASSWORD="sovereign_password",  # Default weak password
            ENVIRONMENT="production"
        )
        
        # This should trigger production validation
        if not settings.validate_config():
            print("✅ PASS: Production validation caught weak password")
        else:
            print("❌ FAIL: Production validation should catch weak password")
            return False
            
    except Exception as e:
        if "weak password" in str(e) or "default" in str(e):
            print("✅ PASS: Production validation caught security issue")
        else:
            print(f"❌ FAIL: Unexpected error: {e}")
            return False
    
    return True


def test_security_utilities():
    """Test security utilities module"""
    print("🛡️ Testing Security Utilities...")
    
    from app.utils.security import (
        generate_jwt_secret, generate_service_key, generate_database_password,
        validate_secret_strength, generate_production_secrets
    )
    
    # Test 1: JWT secret generation
    jwt_secret = generate_jwt_secret()
    
    if len(jwt_secret) < 32:
        print("❌ FAIL: Generated JWT secret too short")
        return False
    
    # Should be different each time
    jwt_secret2 = generate_jwt_secret()
    if jwt_secret == jwt_secret2:
        print("❌ FAIL: JWT secrets should be unique")
        return False
    
    print("✅ PASS: JWT secret generation works")
    
    # Test 2: Service key generation
    service_key = generate_service_key()
    
    if not service_key.startswith('svc_'):
        print("❌ FAIL: Service key should start with 'svc_'")
        return False
    
    if len(service_key) < 20:  # svc_ + 16 chars minimum
        print("❌ FAIL: Service key too short")
        return False
    
    print("✅ PASS: Service key generation works")
    
    # Test 3: Password generation
    password = generate_database_password()
    
    if len(password) < 16:
        print("❌ FAIL: Generated password too short")
        return False
    
    # Check character diversity
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        print("❌ FAIL: Password should have mixed character types")
        return False
    
    print("✅ PASS: Database password generation works")
    
    # Test 4: Secret strength validation
    is_valid, issues = validate_secret_strength("weak")
    if is_valid:
        print("❌ FAIL: Weak secret should be invalid")
        return False
    
    is_valid, issues = validate_secret_strength("This-Is-A-Very-Strong-Secret-Key-123")
    if not is_valid:
        print(f"❌ FAIL: Strong secret should be valid: {issues}")
        return False
    
    print("✅ PASS: Secret strength validation works")
    
    # Test 5: Production secrets generation
    prod_secrets = generate_production_secrets()
    
    required_keys = ['JWT_SECRET_KEY', 'SOVEREIGN_SERVICE_KEY', 'SOVEREIGN_JWT_SECRET', 
                    'SOVEREIGN_DB_PASSWORD', 'API_KEY']
    
    for key in required_keys:
        if key not in prod_secrets:
            print(f"❌ FAIL: Missing production secret: {key}")
            return False
        
        if len(prod_secrets[key]) < 16:
            print(f"❌ FAIL: Production secret {key} too short")
            return False
    
    print("✅ PASS: Production secrets generation works")
    
    return True


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running InsightFlow Security Fixes Tests\\n")
    
    tests = [
        ("STP Token Security", test_stp_token_security),
        ("Configuration Secret Validation", test_configuration_secret_validation),
        ("Security Utilities", test_security_utilities),
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
        print("🎉 All security fixes are working correctly!")
        return True
    else:
        print("⚠️ Some fixes need attention.")
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)