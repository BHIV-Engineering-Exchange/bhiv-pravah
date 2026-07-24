# tests/middleware/test_stp_middleware.py
"""
Tests for STP-Layer middleware
"""

import pytest
from app.middleware.stp_middleware import (
    STPMiddleware,
    STPPacketType,
    STPPriority,
    STPLayerError
)


@pytest.fixture
def stp_middleware():
    """Create STP middleware instance"""
    return STPMiddleware(enable_stp=True)


@pytest.fixture
def stp_middleware_disabled():
    """Create disabled STP middleware"""
    return STPMiddleware(enable_stp=False)


class TestSTPMiddleware:
    """Test STP middleware functionality"""
    
    def test_wrap_routing_decision(self, stp_middleware):
        """Test wrapping routing decision"""
        payload = {
            "agent_id": "nlp-001",
            "confidence": 0.87,
            "timestamp": "2025-11-08T09:00:00Z"
        }
        
        stp_packet = stp_middleware.wrap(
            payload=payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        # Verify STP structure
        assert "stp_version" in stp_packet
        assert "stp_token" in stp_packet
        assert "stp_timestamp" in stp_packet
        assert "stp_type" in stp_packet
        assert "stp_metadata" in stp_packet
        assert "payload" in stp_packet
        assert "stp_checksum" in stp_packet
        
        # Verify payload preserved
        assert stp_packet["payload"] == payload
        
        # Verify packet type
        assert stp_packet["stp_type"] == "routing_decision"
    
    def test_unwrap_packet(self, stp_middleware):
        """Test unwrapping STP packet"""
        original_payload = {
            "agent_id": "nlp-001",
            "score": 0.92
        }
        
        # Wrap
        stp_packet = stp_middleware.wrap(
            payload=original_payload,
            packet_type=STPPacketType.FEEDBACK_PACKET.value
        )
        
        # Unwrap
        payload, metadata = stp_middleware.unwrap(stp_packet)
        
        # Verify payload recovered
        assert payload == original_payload
        
        # Verify metadata extracted
        assert "stp_token" in metadata
        assert "stp_timestamp" in metadata
        assert metadata["stp_type"] == "feedback_packet"
    
    def test_roundtrip_conversion(self, stp_middleware):
        """Test wrap then unwrap produces original"""
        original = {
            "agent_id": "nlp-001",
            "confidence": 0.85,
            "context": {"test": "data"}
        }
        
        # Wrap
        stp_packet = stp_middleware.wrap(
            payload=original,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        # Unwrap
        recovered, _ = stp_middleware.unwrap(stp_packet)
        
        assert recovered == original
    
    def test_disabled_passthrough(self, stp_middleware_disabled):
        """Test that disabled middleware passes through"""
        payload = {"test": "data"}
        
        # Wrap should return original
        result = stp_middleware_disabled.wrap(
            payload=payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        assert result == payload
    
    def test_validate_stp_packet(self, stp_middleware):
        """Test STP packet validation"""
        payload = {"test": "data"}
        
        stp_packet = stp_middleware.wrap(
            payload=payload,
            packet_type=STPPacketType.HEALTH_CHECK.value
        )
        
        assert stp_middleware.validate_stp_packet(stp_packet) is True
        
        # Invalid packet
        invalid_packet = {"invalid": "structure"}
        assert stp_middleware.validate_stp_packet(invalid_packet) is False
    
    def test_priority_levels(self, stp_middleware):
        """Test different priority levels"""
        payload = {"test": "data"}
        
        for priority in [STPPriority.NORMAL, STPPriority.HIGH, STPPriority.CRITICAL]:
            stp_packet = stp_middleware.wrap(
                payload=payload,
                packet_type=STPPacketType.ROUTING_DECISION.value,
                priority=priority.value
            )
            
            assert stp_packet["stp_metadata"]["priority"] == priority.value
    
    def test_checksum_verification(self, stp_middleware):
        """Test checksum calculation and verification"""
        payload = {"test": "data"}
        
        stp_packet = stp_middleware.wrap(
            payload=payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        # Unwrap should succeed
        recovered, _ = stp_middleware.unwrap(stp_packet)
        assert recovered == payload
        
        # Tamper with checksum
        stp_packet["stp_checksum"] = "invalid"
        
        # Should still unwrap but log warning
        recovered, _ = stp_middleware.unwrap(stp_packet)
        assert recovered == payload
    
    def test_metrics_tracking(self, stp_middleware):
        """Test that metrics are tracked"""
        payload = {"test": "data"}
        
        initial_wrapped = stp_middleware.metrics["packets_wrapped"]
        
        stp_packet = stp_middleware.wrap(
            payload=payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        assert stp_middleware.metrics["packets_wrapped"] == initial_wrapped + 1
        
        initial_unwrapped = stp_middleware.metrics["packets_unwrapped"]
        
        stp_middleware.unwrap(stp_packet)
        
        assert stp_middleware.metrics["packets_unwrapped"] == initial_unwrapped + 1
    
    @pytest.mark.asyncio
    async def test_async_wrap(self, stp_middleware):
        """Test async wrapping"""
        payload = {"test": "data"}
        
        stp_packet = await stp_middleware.wrap_async(
            payload=payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        assert "stp_token" in stp_packet
    
    @pytest.mark.asyncio
    async def test_async_unwrap(self, stp_middleware):
        """Test async unwrapping"""
        payload = {"test": "data"}
        
        stp_packet = stp_middleware.wrap(
            payload=payload,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        recovered, metadata = await stp_middleware.unwrap_async(stp_packet)
        
        assert recovered == payload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])