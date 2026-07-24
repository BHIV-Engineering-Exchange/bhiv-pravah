# tests/test_stp_middleware.py
"""
Tests for STP Middleware functionality
"""

import pytest
import json
from app.middleware.stp_middleware import STPMiddleware, STPPacketType, STPPriority, STPLayerError


class TestSTPMiddleware:
    """Test STP middleware functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.stp_middleware = STPMiddleware(enable_stp=True)
        self.test_payload = {
            "agent_id": "test-agent-123",
            "confidence_score": 0.85,
            "routing_reason": "High performance match"
        }
    
    def test_token_generation(self):
        """Test STP token generation"""
        token1 = STPMiddleware.generate_stp_token()
        token2 = STPMiddleware.generate_stp_token()
        
        assert token1.startswith("stp-")
        assert token2.startswith("stp-")
        assert token1 != token2  # Should be unique
        assert len(token1) == 16  # stp- + 12 char hash
    
    def test_checksum_calculation(self):
        """Test checksum calculation"""
        checksum1 = STPMiddleware.calculate_checksum(self.test_payload)
        checksum2 = STPMiddleware.calculate_checksum(self.test_payload)
        
        assert checksum1 == checksum2  # Same payload = same checksum
        assert len(checksum1) == 16  # 16 character hex string
        
        # Different payload should have different checksum
        different_payload = {**self.test_payload, "agent_id": "different-agent"}
        checksum3 = STPMiddleware.calculate_checksum(different_payload)
        assert checksum1 != checksum3
    
    def test_wrap_routing_decision(self):
        """Test wrapping routing decision in STP format"""
        wrapped = self.stp_middleware.wrap(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value,
            priority=STPPriority.HIGH.value
        )
        
        # Verify STP structure
        assert "stp_version" in wrapped
        assert "stp_token" in wrapped
        assert "stp_timestamp" in wrapped
        assert "stp_type" in wrapped
        assert "stp_metadata" in wrapped
        assert "payload" in wrapped
        assert "stp_checksum" in wrapped
        
        # Verify values
        assert wrapped["stp_version"] == "1.0"
        assert wrapped["stp_type"] == STPPacketType.ROUTING_DECISION.value
        assert wrapped["stp_metadata"]["priority"] == STPPriority.HIGH.value
        assert wrapped["payload"] == self.test_payload
    
    def test_unwrap_stp_packet(self):
        """Test unwrapping STP packet"""
        # First wrap
        wrapped = self.stp_middleware.wrap(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        # Then unwrap
        payload, metadata = self.stp_middleware.unwrap(wrapped)
        
        # Verify payload is restored
        assert payload == self.test_payload
        
        # Verify metadata extraction
        assert "stp_token" in metadata
        assert "stp_timestamp" in metadata
        assert metadata["stp_type"] == STPPacketType.ROUTING_DECISION.value
        assert metadata["source"] == "insightflow"
    
    def test_checksum_verification(self):
        """Test checksum verification during unwrap"""
        wrapped = self.stp_middleware.wrap(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        # Corrupt checksum
        wrapped["stp_checksum"] = "invalid_checksum"
        
        # Should still unwrap but log warning
        payload, metadata = self.stp_middleware.unwrap(wrapped)
        assert payload == self.test_payload
        
        # Check metrics for checksum failure
        metrics = self.stp_middleware.get_metrics()
        assert metrics["checksum_failures"] > 0
    
    def test_invalid_packet_type(self):
        """Test handling of invalid packet type"""
        with pytest.raises(STPLayerError):
            self.stp_middleware.wrap(
                payload=self.test_payload,
                packet_type="invalid_type"
            )
    
    def test_disabled_stp(self):
        """Test STP middleware in disabled mode"""
        disabled_middleware = STPMiddleware(enable_stp=False)
        
        # Should return original payload unchanged
        result = disabled_middleware.wrap(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        assert result == self.test_payload
        
        # Unwrap should also pass through
        payload, metadata = disabled_middleware.unwrap(self.test_payload)
        assert payload == self.test_payload
        assert metadata == {}
    
    def test_packet_validation(self):
        """Test STP packet validation"""
        # Valid packet
        wrapped = self.stp_middleware.wrap(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        assert self.stp_middleware.validate_stp_packet(wrapped) is True
        
        # Invalid packet (missing fields)
        invalid_packet = {"some": "data"}
        assert self.stp_middleware.validate_stp_packet(invalid_packet) is False
        
        # Invalid packet type
        wrapped["stp_type"] = "invalid_type"
        assert self.stp_middleware.validate_stp_packet(wrapped) is False
    
    @pytest.mark.asyncio
    async def test_async_operations(self):
        """Test async wrap/unwrap operations"""
        # Async wrap
        wrapped = await self.stp_middleware.wrap_async(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        assert "stp_token" in wrapped
        assert wrapped["payload"] == self.test_payload
        
        # Async unwrap
        payload, metadata = await self.stp_middleware.unwrap_async(wrapped)
        assert payload == self.test_payload
        assert "stp_token" in metadata
    
    def test_metrics_tracking(self):
        """Test metrics collection"""
        initial_metrics = self.stp_middleware.get_metrics()
        
        # Perform operations
        wrapped = self.stp_middleware.wrap(
            payload=self.test_payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        payload, metadata = self.stp_middleware.unwrap(wrapped)
        
        # Check metrics updated
        final_metrics = self.stp_middleware.get_metrics()
        assert final_metrics["packets_wrapped"] == initial_metrics["packets_wrapped"] + 1
        assert final_metrics["packets_unwrapped"] == initial_metrics["packets_unwrapped"] + 1
        
        # Test metrics reset
        self.stp_middleware.reset_metrics()
        reset_metrics = self.stp_middleware.get_metrics()
        assert reset_metrics["packets_wrapped"] == 0
        assert reset_metrics["packets_unwrapped"] == 0
    
    def test_feedback_packet_wrapping(self):
        """Test wrapping feedback packets"""
        feedback_payload = {
            "routing_log_id": "log-123",
            "success": True,
            "latency_ms": 145.5,
            "accuracy_score": 0.88
        }
        
        wrapped = self.stp_middleware.wrap(
            payload=feedback_payload,
            packet_type=STPPacketType.FEEDBACK_PACKET.value,
            priority=STPPriority.NORMAL.value,
            requires_ack=True
        )
        
        assert wrapped["stp_type"] == STPPacketType.FEEDBACK_PACKET.value
        assert wrapped["stp_metadata"]["requires_ack"] is True
        assert wrapped["payload"] == feedback_payload
    
    def test_health_check_wrapping(self):
        """Test wrapping health check packets"""
        health_payload = {
            "status": "healthy",
            "app": "InsightFlow",
            "version": "1.0.0"
        }
        
        wrapped = self.stp_middleware.wrap(
            payload=health_payload,
            packet_type=STPPacketType.HEALTH_CHECK.value,
            priority=STPPriority.NORMAL.value
        )
        
        assert wrapped["stp_type"] == STPPacketType.HEALTH_CHECK.value
        assert wrapped["payload"] == health_payload