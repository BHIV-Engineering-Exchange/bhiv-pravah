#!/usr/bin/env python3
"""
Test script for migration and integration fixes in InsightFlow project.

Tests:
1. Supabase/Sovereign Core migration validation
2. STP acknowledgment handling
"""

import os
import sys
import asyncio
from unittest.mock import patch
from datetime import datetime, timedelta

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def test_migration_validation():
    """Test Supabase to Sovereign Core migration validation"""
    print("🔄 Testing Migration Validation...")
    
    from app.core.config import Settings
    
    # Test 1: Supabase mode configuration
    supabase_settings = Settings(
        JWT_SECRET_KEY="test-key",
        USE_SOVEREIGN_CORE=False,
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_ANON_KEY="test-anon-key",
        SUPABASE_SERVICE_KEY="test-service-key"
    )
    
    status, issues = supabase_settings.validate_migration_config()
    
    if status != 'supabase':
        print(f"❌ FAIL: Expected 'supabase' mode, got '{status}'")
        return False
    
    if len(issues) > 0:
        print(f"❌ FAIL: Supabase mode should have no issues, got: {issues}")
        return False
    
    print("✅ PASS: Supabase mode validation works")
    
    # Test 2: Sovereign Core mode configuration
    sovereign_settings = Settings(
        JWT_SECRET_KEY="test-key",
        USE_SOVEREIGN_CORE=True,
        SOVEREIGN_DB_HOST="prod-db.company.com",
        SOVEREIGN_DB_NAME="insightflow_prod",
        SOVEREIGN_DB_USER="prod_user",
        SOVEREIGN_DB_PASSWORD="secure_password",
        SOVEREIGN_SERVICE_KEY="secure-service-key"
    )
    
    status, issues = sovereign_settings.validate_migration_config()
    
    if status != 'sovereign_core':
        print(f"❌ FAIL: Expected 'sovereign_core' mode, got '{status}'")
        return False
    
    if len(issues) > 0:
        print(f"❌ FAIL: Sovereign Core mode should have no issues, got: {issues}")
        return False
    
    print("✅ PASS: Sovereign Core mode validation works")
    
    # Test 3: Incomplete migration (both configs present)
    mixed_settings = Settings(
        JWT_SECRET_KEY="test-key",
        USE_SOVEREIGN_CORE=True,
        SOVEREIGN_DB_HOST="prod-db.company.com",
        SOVEREIGN_DB_NAME="insightflow_prod",
        SOVEREIGN_DB_USER="prod_user",
        SOVEREIGN_DB_PASSWORD="secure_password",
        SOVEREIGN_SERVICE_KEY="secure-service-key",
        # Supabase config still present (incomplete migration)
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_ANON_KEY="test-anon-key"
    )
    
    status, issues = mixed_settings.validate_migration_config()
    
    if status != 'sovereign_core':
        print(f"❌ FAIL: Expected 'sovereign_core' mode, got '{status}'")
        return False
    
    if len(issues) == 0:
        print("❌ FAIL: Mixed config should have migration issues")
        return False
    
    # Should detect incomplete migration
    migration_issue_found = any('incomplete' in issue.lower() for issue in issues)
    if not migration_issue_found:
        print(f"❌ FAIL: Should detect incomplete migration, got: {issues}")
        return False
    
    print("✅ PASS: Incomplete migration detection works")
    
    # Test 4: Migration guide
    guide = sovereign_settings.get_migration_guide()
    
    required_keys = ['current_mode', 'migration_steps', 'required_env_vars']
    for key in required_keys:
        if key not in guide:
            print(f"❌ FAIL: Migration guide missing key: {key}")
            return False
    
    if len(guide['migration_steps']) < 5:
        print("❌ FAIL: Migration guide should have multiple steps")
        return False
    
    print("✅ PASS: Migration guide generation works")
    
    return True


async def test_stp_acknowledgment_handling():
    """Test STP acknowledgment handling"""
    print("📡 Testing STP Acknowledgment Handling...")
    
    from app.services.stp_service import STPService
    
    # Create STP service
    stp_service = STPService()
    
    # Test 1: Track packet for acknowledgment
    test_token = "stp-test-token-123"
    test_packet = {
        "stp_token": test_token,
        "payload": {"test": "data"},
        "stp_metadata": {"requires_ack": True}
    }
    
    await stp_service._track_for_acknowledgment(
        test_token, 
        test_packet, 
        "test_packet"
    )
    
    if test_token not in stp_service.pending_acks:
        print("❌ FAIL: Packet not tracked for acknowledgment")
        return False
    
    print("✅ PASS: Packet tracking for acknowledgment works")
    
    # Test 2: Handle acknowledgment
    ack_result = await stp_service.handle_acknowledgment(test_token)
    
    if not ack_result:
        print("❌ FAIL: Acknowledgment handling failed")
        return False
    
    if test_token in stp_service.pending_acks:
        print("❌ FAIL: Packet should be removed after acknowledgment")
        return False
    
    print("✅ PASS: Acknowledgment handling works")
    
    # Test 3: Handle unknown acknowledgment
    unknown_ack = await stp_service.handle_acknowledgment("unknown-token")
    
    if unknown_ack:
        print("❌ FAIL: Unknown acknowledgment should return False")
        return False
    
    print("✅ PASS: Unknown acknowledgment handling works")
    
    # Test 4: Acknowledgment timeout handling
    timeout_token = "stp-timeout-token-456"
    timeout_packet = {
        "stp_token": timeout_token,
        "payload": {"test": "timeout"},
        "stp_metadata": {"requires_ack": True}
    }
    
    await stp_service._track_for_acknowledgment(
        timeout_token,
        timeout_packet,
        "timeout_test"
    )
    
    # Simulate timeout by setting old timestamp
    stp_service.pending_acks[timeout_token]['timestamp'] = (
        datetime.utcnow() - timedelta(seconds=stp_service.ack_timeout + 10)
    )
    
    # Check for timeouts
    await stp_service.check_pending_acknowledgments()
    
    # Should still be tracked (first retry)
    if timeout_token not in stp_service.pending_acks:
        print("❌ FAIL: Packet should still be tracked after first timeout")
        return False
    
    # Check retry count
    if stp_service.pending_acks[timeout_token]['retries'] != 1:
        print("❌ FAIL: Retry count should be 1 after timeout")
        return False
    
    print("✅ PASS: Acknowledgment timeout handling works")
    
    # Test 5: Acknowledgment status
    status = stp_service.get_acknowledgment_status()
    
    required_keys = ['pending_acknowledgments', 'overdue_acknowledgments', 
                    'ack_timeout_seconds', 'max_retries', 'pending_tokens']
    for key in required_keys:
        if key not in status:
            print(f"❌ FAIL: Acknowledgment status missing key: {key}")
            return False
    
    if status['pending_acknowledgments'] != 1:  # timeout_token still pending
        print(f"❌ FAIL: Expected 1 pending acknowledgment, got {status['pending_acknowledgments']}")
        return False
    
    print("✅ PASS: Acknowledgment status reporting works")
    
    # Test 6: Clear pending acknowledgments
    cleared_count = stp_service.clear_pending_acknowledgments()
    
    if cleared_count != 1:
        print(f"❌ FAIL: Expected to clear 1 acknowledgment, cleared {cleared_count}")
        return False
    
    if len(stp_service.pending_acks) != 0:
        print("❌ FAIL: Pending acknowledgments should be empty after clear")
        return False
    
    print("✅ PASS: Clear pending acknowledgments works")
    
    return True


async def test_stp_packet_wrapping_with_ack():
    """Test STP packet wrapping with acknowledgment tracking"""
    print("📦 Testing STP Packet Wrapping with Acknowledgment...")
    
    from app.services.stp_service import STPService
    
    # Create STP service
    stp_service = STPService()
    
    # Test 1: Wrap routing decision with acknowledgment
    routing_decision = {
        "request_id": "test-request-123",
        "agent_selected": "test-agent",
        "confidence_score": 0.85
    }
    
    wrapped_packet = await stp_service.wrap_routing_decision(
        routing_decision,
        priority="high",
        requires_ack=True
    )
    
    if "stp_token" not in wrapped_packet:
        print("❌ FAIL: Wrapped packet should have stp_token")
        return False
    
    stp_token = wrapped_packet["stp_token"]
    
    # Should be tracked for acknowledgment
    if stp_token not in stp_service.pending_acks:
        print("❌ FAIL: High priority packet should be tracked for acknowledgment")
        return False
    
    print("✅ PASS: Routing decision wrapping with acknowledgment works")
    
    # Test 2: Wrap feedback packet with acknowledgment
    feedback_data = {
        "routing_log_id": "log-456",
        "success": False,
        "latency_ms": 6000  # High latency should trigger critical priority
    }
    
    wrapped_feedback = await stp_service.wrap_feedback_packet(
        feedback_data,
        requires_ack=True
    )
    
    if "stp_token" not in wrapped_feedback:
        print("❌ FAIL: Wrapped feedback should have stp_token")
        return False
    
    feedback_token = wrapped_feedback["stp_token"]
    
    # Should be tracked for acknowledgment
    if feedback_token not in stp_service.pending_acks:
        print("❌ FAIL: Feedback packet should be tracked for acknowledgment")
        return False
    
    print("✅ PASS: Feedback packet wrapping with acknowledgment works")
    
    # Test 3: Check acknowledgment status
    status = stp_service.get_acknowledgment_status()
    
    if status['pending_acknowledgments'] != 2:  # routing + feedback
        print(f"❌ FAIL: Expected 2 pending acknowledgments, got {status['pending_acknowledgments']}")
        return False
    
    print("✅ PASS: Multiple packet acknowledgment tracking works")
    
    # Cleanup
    stp_service.clear_pending_acknowledgments()
    
    return True


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running InsightFlow Migration & Integration Fixes Tests\\n")
    
    tests = [
        ("Migration Validation", test_migration_validation),
        ("STP Acknowledgment Handling", test_stp_acknowledgment_handling),
        ("STP Packet Wrapping with ACK", test_stp_packet_wrapping_with_ack),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
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
        print("🎉 All migration and integration fixes are working correctly!")
        return True
    else:
        print("⚠️ Some fixes need attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)