#!/usr/bin/env python3
"""
Test Telemetry Service Update

Verifies that the updated telemetry service with packet signing works correctly
while maintaining backward compatibility.
"""

import asyncio
import json
from datetime import datetime

from app.telemetry_bus.service import TelemetryBusService
from app.telemetry_bus.models import TelemetryPacket, DecisionPayload, TracePayload
from app.core.config import settings


async def test_emit_packet_without_signing():
    """Test emit_packet without signing enabled"""
    print("🔓 Testing emit_packet without signing...")
    
    # Ensure signing is disabled
    original_signing = getattr(settings, 'TELEMETRY_PACKET_SIGNING', False)
    settings.TELEMETRY_PACKET_SIGNING = False
    settings.ENABLE_TELEMETRY_SIGNING = False
    
    try:
        service = TelemetryBusService(max_queue_size=5)
        
        # Create test packet
        decision_payload = DecisionPayload(
            selected_agent="nlp-001",
            alternatives=["tts-001"],
            confidence=0.85,
            latency_ms=150.0,
            strategy="q_learning"
        )
        
        trace_payload = TracePayload(
            version="1.0.0",
            node="test-node",
            ts=datetime.utcnow().isoformat() + "Z"
        )
        
        packet = TelemetryPacket(
            request_id="test-unsigned-123",
            decision=decision_payload,
            trace=trace_payload
        )
        
        # Emit packet
        await service.emit_packet(packet)
        
        # Check queue
        assert len(service._packet_queue) == 1
        queued_packet = service._packet_queue[0]
        
        # Should be a dict without security section
        assert isinstance(queued_packet, dict)
        assert "security" not in queued_packet
        assert queued_packet["request_id"] == "test-unsigned-123"
        
        print("✅ Unsigned packet emission successful")
        return True
        
    except Exception as e:
        print(f"❌ Unsigned packet test failed: {e}")
        return False
    
    finally:
        # Restore original setting
        settings.TELEMETRY_PACKET_SIGNING = original_signing
        settings.ENABLE_TELEMETRY_SIGNING = original_signing


async def test_emit_packet_with_signing():
    """Test emit_packet with signing enabled"""
    print("\n🔐 Testing emit_packet with signing...")
    
    # Enable signing
    original_signing = getattr(settings, 'TELEMETRY_PACKET_SIGNING', False)
    settings.TELEMETRY_PACKET_SIGNING = True
    settings.ENABLE_TELEMETRY_SIGNING = True
    
    try:
        service = TelemetryBusService(max_queue_size=5)
        
        # Create test packet
        decision_payload = DecisionPayload(
            selected_agent="nlp-001",
            alternatives=["tts-001"],
            confidence=0.85,
            latency_ms=150.0,
            strategy="q_learning"
        )
        
        trace_payload = TracePayload(
            version="1.0.0",
            node="test-node",
            ts=datetime.utcnow().isoformat() + "Z"
        )
        
        packet = TelemetryPacket(
            request_id="test-signed-456",
            decision=decision_payload,
            trace=trace_payload
        )
        
        # Emit packet with agent fingerprint
        await service.emit_packet(packet, agent_fingerprint="nlp-001")
        
        # Check queue
        assert len(service._packet_queue) == 1
        queued_packet = service._packet_queue[0]
        
        # Should be a dict with security section
        assert isinstance(queued_packet, dict)
        assert "security" in queued_packet
        assert queued_packet["request_id"] == "test-signed-456"
        
        # Verify security fields
        security = queued_packet["security"]
        assert "nonce" in security
        assert "timestamp" in security
        assert "packet_signature" in security
        assert security["agent_fingerprint"] == "nlp-001"
        
        print("✅ Signed packet emission successful")
        print(f"   Nonce: {security['nonce'][:8]}...")
        print(f"   Signature: {security['packet_signature'][:8]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Signed packet test failed: {e}")
        return False
    
    finally:
        # Restore original setting
        settings.TELEMETRY_PACKET_SIGNING = original_signing
        settings.ENABLE_TELEMETRY_SIGNING = original_signing


async def test_broadcast_decision_compatibility():
    """Test broadcast_decision backward compatibility"""
    print("\n🔄 Testing broadcast_decision compatibility...")
    
    try:
        service = TelemetryBusService(max_queue_size=5)
        
        # Test old-style call
        decision_data = {
            "agent_id": "nlp-001",
            "confidence_score": 0.87,
            "routing_strategy": "q_learning",
            "request_id": "compat-test-789"
        }
        
        await service.broadcast_decision(decision_data)
        
        # Should work without errors
        print("✅ Old-style broadcast_decision works")
        
        # Test new-style call with agent fingerprint
        await service.broadcast_decision(decision_data, agent_fingerprint="nlp-001")
        
        print("✅ New-style broadcast_decision works")
        
        return True
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        return False


async def test_get_recent_packets():
    """Test get_recent_packets with mixed packet types"""
    print("\n📋 Testing get_recent_packets...")
    
    try:
        service = TelemetryBusService(max_queue_size=10)
        
        # Add some packets manually to test mixed types
        service._packet_queue.append({"request_id": "dict-packet-1", "type": "dict"})
        
        # Add via emit_packet (will be dict format)
        decision_payload = DecisionPayload(
            selected_agent="nlp-001",
            alternatives=[],
            confidence=0.85,
            latency_ms=150.0,
            strategy="q_learning"
        )
        
        trace_payload = TracePayload(
            version="1.0.0",
            node="test-node",
            ts=datetime.utcnow().isoformat() + "Z"
        )
        
        packet = TelemetryPacket(
            request_id="object-packet-2",
            decision=decision_payload,
            trace=trace_payload
        )
        
        await service.emit_packet(packet)
        
        # Get recent packets
        recent = await service.get_recent_packets(limit=5)
        
        # Should return list of dicts
        assert isinstance(recent, list)
        assert len(recent) == 2
        assert all(isinstance(p, dict) for p in recent)
        
        print("✅ get_recent_packets handles mixed types correctly")
        print(f"   Retrieved {len(recent)} packets")
        
        return True
        
    except Exception as e:
        print(f"❌ get_recent_packets test failed: {e}")
        return False


async def main():
    """Run all telemetry service update tests"""
    print("🚀 Testing Telemetry Service Updates")
    print("=" * 50)
    
    tests = [
        ("Emit Packet Without Signing", test_emit_packet_without_signing),
        ("Emit Packet With Signing", test_emit_packet_with_signing),
        ("Broadcast Decision Compatibility", test_broadcast_decision_compatibility),
        ("Get Recent Packets", test_get_recent_packets),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
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
        print("🎉 All telemetry service updates working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)