# tests/test_stp_service.py
"""
Tests for STP Service functionality
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.stp_service import STPService, get_stp_service
from app.middleware.stp_middleware import STPPacketType, STPPriority


class TestSTPService:
    """Test STP service functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        with patch('app.services.stp_service.settings') as mock_settings:
            mock_settings.STP_ENABLED = True
            mock_settings.STP_DEFAULT_DESTINATION = "test_destination"
            mock_settings.STP_DEFAULT_PRIORITY = "normal"
            self.stp_service = STPService()
    
    @pytest.mark.asyncio
    async def test_wrap_routing_decision_high_confidence(self):
        """Test wrapping routing decision with high confidence"""
        routing_decision = {
            "request_id": "req-123",
            "agent_id": "agent-456",
            "confidence_score": 0.95,
            "routing_reason": "Perfect match"
        }
        
        wrapped = await self.stp_service.wrap_routing_decision(routing_decision)
        
        # Should be wrapped in STP format
        assert "stp_token" in wrapped
        assert "payload" in wrapped
        assert wrapped["payload"] == routing_decision
        assert wrapped["stp_type"] == STPPacketType.ROUTING_DECISION.value
        # High confidence should result in HIGH priority
        assert wrapped["stp_metadata"]["priority"] == STPPriority.HIGH.value
    
    @pytest.mark.asyncio
    async def test_wrap_routing_decision_low_confidence(self):
        """Test wrapping routing decision with low confidence"""
        routing_decision = {
            "request_id": "req-123",
            "agent_id": "agent-456",
            "confidence_score": 0.25,
            "routing_reason": "Uncertain match"
        }
        
        wrapped = await self.stp_service.wrap_routing_decision(routing_decision)
        
        # Low confidence should result in CRITICAL priority
        assert wrapped["stp_metadata"]["priority"] == STPPriority.CRITICAL.value
    
    @pytest.mark.asyncio
    async def test_wrap_feedback_packet_success(self):
        """Test wrapping successful feedback packet"""
        feedback_data = {
            "routing_log_id": "log-123",
            "success": True,
            "latency_ms": 150.0,
            "accuracy_score": 0.88
        }
        
        wrapped = await self.stp_service.wrap_feedback_packet(feedback_data)
        
        assert "stp_token" in wrapped
        assert wrapped["stp_type"] == STPPacketType.FEEDBACK_PACKET.value
        assert wrapped["stp_metadata"]["requires_ack"] is True
        assert wrapped["stp_metadata"]["priority"] == "normal"  # Good performance
    
    @pytest.mark.asyncio
    async def test_wrap_feedback_packet_failure(self):
        """Test wrapping failed feedback packet"""
        feedback_data = {
            "routing_log_id": "log-123",
            "success": False,
            "latency_ms": 5500.0,  # Very slow
            "accuracy_score": 0.2
        }
        
        wrapped = await self.stp_service.wrap_feedback_packet(feedback_data)
        
        # Failed + slow should result in CRITICAL priority
        assert wrapped["stp_metadata"]["priority"] == STPPriority.CRITICAL.value
    
    @pytest.mark.asyncio
    async def test_wrap_health_check_healthy(self):
        """Test wrapping healthy status"""
        health_data = {
            "status": "healthy",
            "app": "InsightFlow",
            "services": {"database": "healthy"}
        }
        
        wrapped = await self.stp_service.wrap_health_check(health_data)
        
        assert wrapped["stp_type"] == STPPacketType.HEALTH_CHECK.value
        assert wrapped["stp_metadata"]["priority"] == STPPriority.NORMAL.value
        assert wrapped["stp_metadata"]["requires_ack"] is False
    
    @pytest.mark.asyncio
    async def test_wrap_health_check_unhealthy(self):
        """Test wrapping unhealthy status"""
        health_data = {
            "status": "unhealthy",
            "app": "InsightFlow",
            "services": {"database": "unhealthy"}
        }
        
        wrapped = await self.stp_service.wrap_health_check(health_data)
        
        # Unhealthy should result in CRITICAL priority
        assert wrapped["stp_metadata"]["priority"] == STPPriority.CRITICAL.value
    
    @pytest.mark.asyncio
    async def test_unwrap_packet(self):
        """Test unwrapping STP packet"""
        # First create a wrapped packet
        original_data = {
            "test": "data",
            "value": 123
        }
        
        wrapped = await self.stp_service.stp_middleware.wrap_async(
            payload=original_data,
            packet_type=STPPacketType.ROUTING_DECISION.value
        )
        
        # Then unwrap it
        payload, metadata = await self.stp_service.unwrap_packet(wrapped)
        
        assert payload == original_data
        assert "stp_token" in metadata
        assert metadata["stp_type"] == STPPacketType.ROUTING_DECISION.value
    
    def test_is_stp_packet(self):
        """Test STP packet detection"""
        # Valid STP packet
        stp_packet = {
            "stp_version": "1.0",
            "stp_token": "stp-abc123",
            "stp_timestamp": "2024-01-01T00:00:00Z",
            "stp_type": "routing_decision",
            "stp_metadata": {},
            "payload": {}
        }
        
        assert self.stp_service.is_stp_packet(stp_packet) is True
        
        # Regular JSON
        regular_json = {"some": "data"}
        assert self.stp_service.is_stp_packet(regular_json) is False
    
    def test_get_stp_metrics(self):
        """Test getting STP metrics"""
        metrics = self.stp_service.get_stp_metrics()
        
        assert "enabled" in metrics
        assert "packets_wrapped" in metrics
        assert "packets_unwrapped" in metrics
        assert "errors" in metrics
    
    def test_singleton_pattern(self):
        """Test that get_stp_service returns singleton"""
        service1 = get_stp_service()
        service2 = get_stp_service()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_error_handling_fallback(self):
        """Test that errors fall back to original data"""
        with patch.object(self.stp_service.stp_middleware, 'wrap_async', side_effect=Exception("Test error")):
            routing_decision = {"test": "data"}
            
            # Should return original data on error
            result = await self.stp_service.wrap_routing_decision(routing_decision)
            assert result == routing_decision
    
    @pytest.mark.asyncio
    async def test_custom_destination_and_priority(self):
        """Test custom destination and priority settings"""
        routing_decision = {"test": "data"}
        
        wrapped = await self.stp_service.wrap_routing_decision(
            routing_decision=routing_decision,
            destination="custom_system",
            priority=STPPriority.HIGH.value
        )
        
        assert wrapped["stp_metadata"]["destination"] == "custom_system"
        assert wrapped["stp_metadata"]["priority"] == STPPriority.HIGH.value