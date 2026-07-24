#!/usr/bin/env python3
"""
V3 Complete Integration Test

Tests all V3 components: Telemetry, STP, Q-Learning, and Dashboard.
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:3000"

def test_telemetry_bus():
    """Test telemetry bus service"""
    print("🔄 Testing Telemetry Bus...")
    
    try:
        from app.telemetry_bus.service import TelemetryBusService
        from app.telemetry_bus.models import TelemetryPacket, DecisionPayload, FeedbackPayload, TracePayload
        
        # Create telemetry service
        service = TelemetryBusService(max_queue_size=10)
        
        # Create test packet
        packet = TelemetryPacket(
            request_id="test-v3-001",
            decision=DecisionPayload(
                selected_agent="nlp-001",
                alternatives=["audio-001", "vision-001"],
                confidence=0.85,
                latency_ms=120,
                strategy="q_learning"
            ),
            feedback=FeedbackPayload(
                reward_signal=0.8,
                last_outcome="success"
            ),
            trace=TracePayload(
                version="v3",
                node="test-node",
                ts=datetime.utcnow().isoformat() + "Z"
            )
        )
        
        # Test packet emission
        asyncio.run(service.emit_packet(packet))
        
        # Check health
        health = service.get_health()
        assert health.status == "ok"
        assert health.queue_size >= 0
        
        print("✅ Telemetry Bus: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Telemetry Bus: FAILED - {e}")
        return False

def test_stp_bridge():
    """Test STP bridge integration"""
    print("🔄 Testing STP Bridge...")
    
    try:
        from app.stp_bridge.stp_bridge_integration import STPBridgeIntegration
        
        # Create STP bridge
        bridge = STPBridgeIntegration(enable_feedback=True)
        
        # Test decision wrapping
        decision = {"agent": "nlp-001", "confidence": 0.85}
        wrapped = bridge.wrap_decision_for_stp(decision)
        
        assert "stp_token" in wrapped
        assert "stp_timestamp" in wrapped
        assert wrapped["payload"] == decision
        
        # Test feedback parsing
        feedback = {
            "karmic_weight": 0.34,
            "reward_value": 0.7,
            "context_tags": ["success", "fast"],
            "stp_version": "stp-1"
        }
        
        parsed = bridge.parse_stp_feedback(feedback)
        assert parsed.reward == 0.7
        assert parsed.weights["karmic_weight"] == 0.34
        
        print("✅ STP Bridge: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ STP Bridge: FAILED - {e}")
        return False

def test_q_learning():
    """Test Q-learning updater"""
    print("🔄 Testing Q-Learning...")
    
    try:
        from app.ml.q_learning_updater import QLearningUpdater
        
        # Create Q-learning updater
        updater = QLearningUpdater(
            learning_rate=0.1,
            discount_factor=0.95,
            enable_updates=True
        )
        
        # Test Q-update
        old_conf, new_conf = updater.q_update(
            state="nlp_task",
            action="nlp-001",
            reward=0.8,
            request_id="test-q-001"
        )
        
        assert 0.0 <= new_conf <= 1.0
        assert old_conf != new_conf
        
        # Test bounds with extreme values
        for reward in [-1.0, 1.0]:
            _, conf = updater.q_update("test", "agent", reward)
            assert 0.0 <= conf <= 1.0
        
        # Test learning trace
        trace = updater.get_learning_trace(limit=10)
        assert len(trace) > 0
        
        print("✅ Q-Learning: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Q-Learning: FAILED - {e}")
        return False

def test_feedback_endpoint():
    """Test feedback endpoint with Q-learning"""
    print("🔄 Testing Feedback Endpoint...")
    
    try:
        # Test feedback submission
        feedback_data = {
            "karmic_weight": 0.45,
            "reward_value": 0.8,
            "context_tags": ["success", "efficient"],
            "state": "nlp_task",
            "action": "nlp-001",
            "request_id": "test-feedback-001",
            "stp_version": "stp-1"
        }
        
        response = requests.post(
            f"{BASE_URL}/feedback",
            json=feedback_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "accepted"
            assert data["parsed_reward"] == 0.8
            print("✅ Feedback Endpoint: PASSED")
            return True
        else:
            print(f"❌ Feedback Endpoint: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Feedback Endpoint: FAILED - {e}")
        return False

def test_admin_endpoints():
    """Test Q-learning admin endpoints"""
    print("🔄 Testing Admin Endpoints...")
    
    try:
        # Test Q-learning trace
        response = requests.get(f"{BASE_URL}/admin/q-learning/trace?limit=10")
        if response.status_code == 200:
            data = response.json()
            assert "trace" in data
            print("✅ Admin Q-Learning Trace: PASSED")
        else:
            print(f"❌ Admin Q-Learning Trace: FAILED - HTTP {response.status_code}")
            return False
        
        # Test Q-table save
        response = requests.post(f"{BASE_URL}/admin/q-learning/save")
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True
            print("✅ Admin Q-Table Save: PASSED")
        else:
            print(f"❌ Admin Q-Table Save: FAILED - HTTP {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Admin Endpoints: FAILED - {e}")
        return False

def test_telemetry_websocket():
    """Test telemetry WebSocket endpoint"""
    print("🔄 Testing Telemetry WebSocket...")
    
    try:
        # Test WebSocket health endpoint
        response = requests.get(f"{BASE_URL}/telemetry/health")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            print("✅ Telemetry WebSocket Health: PASSED")
            return True
        else:
            print(f"❌ Telemetry WebSocket: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telemetry WebSocket: FAILED - {e}")
        return False

def main():
    """Run complete V3 integration test suite"""
    print("🚀 Starting V3 Complete Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Telemetry Bus", test_telemetry_bus),
        ("STP Bridge", test_stp_bridge),
        ("Q-Learning", test_q_learning),
        ("Feedback Endpoint", test_feedback_endpoint),
        ("Admin Endpoints", test_admin_endpoints),
        ("Telemetry WebSocket", test_telemetry_websocket),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            results.append((test_name, False))
        
        print()  # Add spacing between tests
    
    # Summary
    print("=" * 60)
    print("📊 V3 Integration Test Results:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All V3 integration tests PASSED!")
        print("✅ V3 system is ready for production!")
    else:
        print("⚠️  Some tests failed. Please check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)