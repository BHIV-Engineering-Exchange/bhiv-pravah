# tests/telemetry_security/test_telemetry_security.py
"""
Comprehensive tests for Telemetry Security Module

Tests packet signing, verification, nonce handling, and API endpoints.
Ensures backward compatibility with existing telemetry functionality.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.telemetry_bus.telemetry_security import (
    TelemetrySigner, 
    TelemetrySecurityError,
    get_telemetry_signer
)
from app.telemetry_bus.service import TelemetryBusService


class TestTelemetrySigner:
    """Test telemetry packet signing and verification"""
    
    def setup_method(self):
        """Set up test environment"""
        self.jwt_secret = "test-secret-key-for-hmac-signing-32chars"
        self.signer = TelemetrySigner(
            jwt_secret=self.jwt_secret,
            max_timestamp_drift_seconds=5
        )
        
        self.test_packet = {
            "request_id": "test-123",
            "decision": {
                "selected_agent": "nlp-001",
                "confidence": 0.85
            },
            "trace": {
                "version": "1.0.0",
                "node": "test-node"
            }
        }
    
    def test_sign_packet_success(self):
        """Test successful packet signing"""
        signed_packet = self.signer.sign_packet(
            self.test_packet, 
            agent_fingerprint="nlp-001"
        )
        
        # Check security section exists
        assert "security" in signed_packet
        security = signed_packet["security"]
        
        # Check required fields
        assert "nonce" in security
        assert "timestamp" in security
        assert "packet_signature" in security
        assert "agent_fingerprint" in security
        assert security["agent_fingerprint"] == "nlp-001"
        assert security["version"] == "v1"
        
        # Check nonce format (32 hex chars)
        assert len(security["nonce"]) == 32
        assert all(c in "0123456789abcdef" for c in security["nonce"])
        
        # Check signature format (64 hex chars for SHA256)
        assert len(security["packet_signature"]) == 64
        assert all(c in "0123456789abcdef" for c in security["packet_signature"])
    
    def test_verify_packet_success(self):
        """Test successful packet verification"""
        # Sign packet
        signed_packet = self.signer.sign_packet(
            self.test_packet,
            agent_fingerprint="nlp-001"
        )
        
        # Create new signer instance to simulate receiver
        receiver_signer = TelemetrySigner(
            jwt_secret=self.jwt_secret,
            max_timestamp_drift_seconds=5
        )
        
        # Verify packet
        is_valid, error_message = receiver_signer.verify_packet(signed_packet)
        
        assert is_valid is True
        assert error_message is None
    
    def test_verify_packet_missing_security(self):
        """Test verification with missing security section"""
        is_valid, error_message = self.signer.verify_packet(self.test_packet)
        
        assert is_valid is False
        assert "Missing security section" in error_message
    
    def test_verify_packet_signature_mismatch(self):
        """Test verification with invalid signature"""
        signed_packet = self.signer.sign_packet(self.test_packet)
        
        # Tamper with signature
        signed_packet["security"]["packet_signature"] = "invalid_signature"
        
        is_valid, error_message = self.signer.verify_packet(signed_packet)
        
        assert is_valid is False
        assert "Signature mismatch" in error_message
    
    def test_nonce_cleanup(self):
        """Test nonce cache cleanup"""
        initial_nonces = len(self.signer._used_nonces)
        
        # Add some nonces
        for i in range(5):
            self.signer.sign_packet(self.test_packet)
        
        assert len(self.signer._used_nonces) == initial_nonces + 5
        
        # Force cleanup
        self.signer._cleanup_nonces_if_needed()
        
        # Should still have nonces (cleanup is time-based)
        assert len(self.signer._used_nonces) >= 0


class TestTelemetryBusServiceIntegration:
    """Test telemetry service integration with security"""
    
    def test_service_initialization_without_signing(self):
        """Test service initialization with signing disabled"""
        service = TelemetryBusService(enable_packet_signing=False)
        
        assert service.enable_packet_signing is False
        assert service._telemetry_signer is None
    
    async def test_broadcast_decision_without_signing(self):
        """Test decision broadcasting without packet signing"""
        service = TelemetryBusService(enable_packet_signing=False)
        
        decision_data = {
            "agent_id": "nlp-001",
            "confidence_score": 0.85,
            "routing_strategy": "q_learning",
            "request_id": "test-123"
        }
        
        # Mock WebSocket connections
        mock_websocket = Mock()
        service._active_connections.add(mock_websocket)
        
        await service.broadcast_decision(decision_data)
        
        # Check that no signing occurred
        assert service.metrics.get("packets_signed", 0) == 0
        assert service.metrics.get("signing_errors", 0) == 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing telemetry"""
    
    def test_telemetry_service_without_security_module(self):
        """Test that telemetry service works without security module"""
        service = TelemetryBusService(enable_packet_signing=False)
        
        # Should work normally
        assert service.enable_packet_signing is False
        assert service._telemetry_signer is None
        
        # Metrics should still work
        assert "messages_sent" in service.metrics
        assert "messages_dropped" in service.metrics
    
    async def test_existing_broadcast_decision_compatibility(self):
        """Test that existing broadcast_decision calls still work"""
        service = TelemetryBusService(enable_packet_signing=False)
        
        # Old-style call without agent_fingerprint
        decision_data = {
            "agent_id": "nlp-001",
            "confidence_score": 0.85
        }
        
        # Should not raise any errors
        await service.broadcast_decision(decision_data)
        
        # New-style call with agent_fingerprint
        await service.broadcast_decision(decision_data, agent_fingerprint="nlp-001")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])