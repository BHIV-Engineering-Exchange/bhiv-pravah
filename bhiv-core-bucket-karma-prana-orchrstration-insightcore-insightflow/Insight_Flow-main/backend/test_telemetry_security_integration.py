#!/usr/bin/env python3
"""
Telemetry Security Integration Test

Tests the complete telemetry security implementation including:
- Packet signing and verification
- API endpoint functionality
- Backward compatibility
- Integration with existing telemetry system
"""

import asyncio
import json
import time
from datetime import datetime

from app.telemetry_bus.telemetry_security import TelemetrySigner, get_telemetry_signer
from app.telemetry_bus.service import TelemetryBusService, get_telemetry_service
from app.core.config import settings


async def test_basic_signing_and_verification():
    """Test basic packet signing and verification"""
    print("🔐 Testing basic packet signing and verification...")
    
    # Create test packet
    test_packet = {
        "request_id": "integration-test-123",
        "decision": {
            "selected_agent": "nlp-001",
            "confidence": 0.87,
            "alternatives": ["tts-001", "cv-001"]
        },
        "trace": {
            "version": settings.APP_VERSION,
            "node": "insightflow-router",
            "ts": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # Get telemetry signer
    signer = get_telemetry_signer()
    
    # Sign packet
    signed_packet = signer.sign_packet(
        test_packet, 
        agent_fingerprint="nlp-001"
    )
    
    print(f"✅ Packet signed successfully")
    print(f"   Nonce: {signed_packet['security']['nonce'][:8]}...")
    print(f"   Signature: {signed_packet['security']['packet_signature'][:8]}...")
    
    # Verify packet
    is_valid, error_message = signer.verify_packet(signed_packet)
    
    if is_valid:
        print("✅ Packet verification successful")
    else:
        print(f"❌ Packet verification failed: {error_message}")
        return False
    
    return True


async def test_telemetry_service_integration():
    """Test telemetry service with security enabled"""
    print("\n📡 Testing telemetry service integration...")
    
    # Test with signing enabled via configuration
    from app.core.config import settings
    original_signing = getattr(settings, 'TELEMETRY_PACKET_SIGNING', False)
    
    # Temporarily enable signing for test
    settings.TELEMETRY_PACKET_SIGNING = True
    settings.ENABLE_TELEMETRY_SIGNING = True
    
    try:
        # Create service
        service = TelemetryBusService(
            max_queue_size=10,
            max_connections=5
        )
        
        print(f"✅ Telemetry service created (signing enabled via config)")
        
        # Test decision broadcasting
        decision_data = {
            "agent_id": "nlp-001",
            "confidence_score": 0.89,
            "routing_strategy": "q_learning",
            "execution_time_ms": 142.5,
            "context": {"priority": "high"},
            "request_id": "integration-test-456"
        }
        
        await service.broadcast_decision(decision_data, agent_fingerprint="nlp-001")
        print("✅ Decision broadcast successful")
        
        # Check metrics
        metrics = service.metrics
        print(f"   Messages sent: {metrics.get('messages_sent', 0)}")
        print(f"   Messages dropped: {metrics.get('messages_dropped', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Decision broadcast failed: {e}")
        return False
    
    finally:
        # Restore original setting
        settings.TELEMETRY_PACKET_SIGNING = original_signing
        settings.ENABLE_TELEMETRY_SIGNING = original_signing


async def test_backward_compatibility():
    """Test backward compatibility with existing code"""
    print("\n🔄 Testing backward compatibility...")
    
    # Test service without signing
    service_no_signing = TelemetryBusService(enable_packet_signing=False)
    
    # Old-style broadcast call
    decision_data = {
        "agent_id": "tts-001",
        "confidence_score": 0.75
    }
    
    try:
        await service_no_signing.broadcast_decision(decision_data)
        print("✅ Backward compatibility maintained")
        
        # Verify no signing occurred
        assert service_no_signing.metrics.get("packets_signed", 0) == 0
        print("✅ No signing when disabled")
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False
    
    return True


def test_configuration_validation():
    """Test configuration validation"""
    print("\n⚙️  Testing configuration validation...")
    
    try:
        # Test telemetry security settings
        signing_enabled = getattr(settings, 'TELEMETRY_PACKET_SIGNING', False)
        signature_timeout = getattr(settings, 'TELEMETRY_SIGNATURE_TIMEOUT', 5)
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Packet signing: {signing_enabled}")
        print(f"   Signature timeout: {signature_timeout}s")
        
        # Validate timeout range
        if 1 <= signature_timeout <= 30:
            print("✅ Signature timeout within valid range")
        else:
            print(f"⚠️  Signature timeout outside recommended range: {signature_timeout}")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    
    return True


def test_security_features():
    """Test security features"""
    print("\n🛡️  Testing security features...")
    
    try:
        signer = get_telemetry_signer()
        
        # Test nonce generation
        nonce1 = signer._generate_nonce()
        nonce2 = signer._generate_nonce()
        
        assert nonce1 != nonce2, "Nonces should be unique"
        assert len(nonce1) == 32, "Nonce should be 32 characters"
        print("✅ Nonce generation working correctly")
        
        # Test signature generation
        test_payload = "test|payload|for|signing"
        sig1 = signer._generate_signature(test_payload)
        sig2 = signer._generate_signature(test_payload)
        
        assert sig1 == sig2, "Signatures should be deterministic"
        assert len(sig1) == 64, "Signature should be 64 characters (SHA256)"
        print("✅ Signature generation working correctly")
        
    except Exception as e:
        print(f"❌ Security features test failed: {e}")
        return False
    
    return True


async def main():
    """Run all integration tests"""
    print("🚀 Starting Telemetry Security Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Configuration Validation", test_configuration_validation),
        ("Security Features", test_security_features),
        ("Basic Signing & Verification", test_basic_signing_and_verification),
        ("Telemetry Service Integration", test_telemetry_service_integration),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Telemetry security implementation is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)