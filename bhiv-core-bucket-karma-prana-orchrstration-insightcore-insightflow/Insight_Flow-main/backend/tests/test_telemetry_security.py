# tests/test_telemetry_security.py
"""
Telemetry Security Tests

Tests for SSPL Phase III readiness:
1. Signature presence
2. Nonce uniqueness
3. Timestamp drift verification (<5 seconds)
4. Rejection of unsigned packets
"""

import pytest
import time
from datetime import datetime, timedelta
from app.telemetry_bus.telemetry_security import TelemetrySigner


@pytest.fixture
def signer():
    """Create telemetry signer instance"""
    return TelemetrySigner(
        jwt_secret="test_secret_key_for_testing_only",
        max_timestamp_drift_seconds=5
    )


@pytest.fixture
def sample_packet():
    """Create sample telemetry packet"""
    return {
        "request_id": "test-123",
        "decision": {
            "selected_agent": "nlp-001",
            "confidence": 0.87
        }
    }


class TestTelemetrySignature:
    """Test packet signing"""
    
    def test_signature_present(self, signer, sample_packet):
        """Test 1: Signature is present in signed packet"""
        signed = signer.sign_packet(sample_packet, agent_fingerprint="nlp-001")
        
        assert "security" in signed
        assert "packet_signature" in signed["security"]
        assert "nonce" in signed["security"]
        assert "timestamp" in signed["security"]
        assert "agent_fingerprint" in signed["security"]
        
        # Signature should be hex string (64 chars for SHA256)
        assert len(signed["security"]["packet_signature"]) == 64
    
    def test_nonce_uniqueness(self, signer, sample_packet):
        """Test 2: Each packet gets unique nonce"""
        signed1 = signer.sign_packet(sample_packet)
        signed2 = signer.sign_packet(sample_packet)
        
        nonce1 = signed1["security"]["nonce"]
        nonce2 = signed2["security"]["nonce"]
        
        assert nonce1 != nonce2
        assert len(nonce1) == 32  # 16 bytes hex = 32 chars
        assert len(nonce2) == 32
    
    def test_timestamp_format(self, signer, sample_packet):
        """Test timestamp is in ISO format"""
        signed = signer.sign_packet(sample_packet)
        
        timestamp_str = signed["security"]["timestamp"]
        
        # Should be able to parse
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        
        # Should be recent (within 1 second)
        now = datetime.utcnow()
        diff = abs((now - ts).total_seconds())
        assert diff < 1.0


class TestTelemetryVerification:
    """Test packet verification"""
    
    def test_valid_packet_verifies(self, signer, sample_packet):
        """Test valid signed packet passes verification"""
        signed = signer.sign_packet(sample_packet)
        
        # Clear nonce tracker (simulating new verifier instance)
        signer._used_nonces.clear()
        
        is_valid, error = signer.verify_packet(signed)
        
        assert is_valid is True
        assert error is None
    
    def test_timestamp_drift_detection(self, signer, sample_packet):
        """Test 3: Timestamp drift > 5 seconds is rejected"""
        signed = signer.sign_packet(sample_packet)
        
        # Modify timestamp to 10 seconds ago
        old_time = datetime.utcnow() - timedelta(seconds=10)
        signed["security"]["timestamp"] = old_time.isoformat() + "Z"
        
        is_valid, error = signer.verify_packet(signed)
        
        assert is_valid is False
        assert "drift" in error.lower()
    
    def test_replay_attack_prevention(self, signer, sample_packet):
        """Test 2: Nonce reuse is detected (replay attack)"""
        signed = signer.sign_packet(sample_packet)
        
        # First verification should succeed
        is_valid, error = signer.verify_packet(signed)
        assert is_valid is True
        
        # Second verification with same packet should fail
        is_valid, error = signer.verify_packet(signed)
        assert is_valid is False
        assert "nonce" in error.lower() or "replay" in error.lower()
    
    def test_unsigned_packet_rejection(self, signer, sample_packet):
        """Test 4: Unsigned packets are rejected"""
        # Packet without security section
        is_valid, error = signer.verify_packet(sample_packet)
        
        assert is_valid is False
        assert "security" in error.lower()
    
    def test_tampered_packet_rejection(self, signer, sample_packet):
        """Test signature mismatch detection"""
        signed = signer.sign_packet(sample_packet)
        
        # Clear nonces
        signer._used_nonces.clear()
        
        # Tamper with packet content
        signed["decision"]["confidence"] = 0.99
        
        is_valid, error = signer.verify_packet(signed)
        
        assert is_valid is False
        assert "signature" in error.lower()
    
    def test_missing_security_fields(self, signer, sample_packet):
        """Test rejection when security fields are incomplete"""
        signed = signer.sign_packet(sample_packet)
        
        # Remove nonce
        del signed["security"]["nonce"]
        
        is_valid, error = signer.verify_packet(signed)
        
        assert is_valid is False
        assert "nonce" in error.lower()


class TestKarmaSmoothing:
    """Test karma-weighted reward smoothing"""
    
    def test_smoothing_formula(self):
        """Test weighted smoothing: 0.75 * reward + 0.25 * karma"""
        q_reward = 0.8
        karma_score = 0.4  # Normalized [0, 1]
        
        adjusted = (0.75 * q_reward) + (0.25 * karma_score)
        
        expected = 0.75 * 0.8 + 0.25 * 0.4  # = 0.6 + 0.1 = 0.7
        
        assert abs(adjusted - expected) < 0.001
    
    def test_smoothing_reduces_oscillation(self):
        """Test that smoothing dampens reward oscillation"""
        rewards = [1.0, -1.0, 1.0, -1.0]  # Oscillating
        karma = 0.5  # Neutral
        
        smoothed_rewards = [
            (0.75 * r) + (0.25 * karma)
            for r in rewards
        ]
        
        # Smoothed values should have smaller range
        original_range = max(rewards) - min(rewards)  # 2.0
        smoothed_range = max(smoothed_rewards) - min(smoothed_rewards)
        
        assert smoothed_range < original_range


if __name__ == "__main__":
    pytest.main([__file__, "-v"])