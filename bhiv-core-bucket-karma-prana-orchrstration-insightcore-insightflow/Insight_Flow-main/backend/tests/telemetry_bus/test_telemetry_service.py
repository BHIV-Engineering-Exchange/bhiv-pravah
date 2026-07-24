# tests/telemetry_bus/test_telemetry_service.py
"""
Tests for Telemetry Bus Service
"""

import pytest
import asyncio
from app.telemetry_bus.service import TelemetryBusService
from app.telemetry_bus.models import (
    TelemetryPacket,
    DecisionPayload,
    FeedbackPayload,
    TracePayload
)


@pytest.fixture
def telemetry_service():
    """Create telemetry service instance"""
    return TelemetryBusService(max_queue_size=10, max_connections=5)


@pytest.fixture
def sample_packet():
    """Create sample telemetry packet"""
    return TelemetryPacket(
        request_id="test-123",
        decision=DecisionPayload(
            selected_agent="nlp-001",
            alternatives=["audio-001", "vision-001"],
            confidence=0.87,
            latency_ms=142,
            strategy="q_learning"
        ),
        feedback=FeedbackPayload(
            reward_signal=0.12,
            last_outcome="success"
        ),
        trace=TracePayload(
            version="v3",
            node="test-node",
            ts="2025-11-15T11:15:00Z"
        )
    )


class TestTelemetryBusService:
    """Test telemetry bus service"""
    
    @pytest.mark.asyncio
    async def test_emit_packet(self, telemetry_service, sample_packet):
        """Test packet emission"""
        await telemetry_service.emit_packet(sample_packet)
        
        health = telemetry_service.get_health()
        assert health.queue_size == 1
    
    @pytest.mark.asyncio
    async def test_queue_overflow(self, telemetry_service, sample_packet):
        """Test backpressure when queue is full"""
        # Fill queue beyond capacity
        for i in range(15):
            packet = sample_packet.model_copy()
            packet.request_id = f"test-{i}"
            await telemetry_service.emit_packet(packet)
        
        health = telemetry_service.get_health()
        assert health.queue_size == telemetry_service.max_queue_size
        assert health.messages_dropped > 0
    
    def test_health_response(self, telemetry_service):
        """Test health endpoint response"""
        health = telemetry_service.get_health()
        
        assert health.status == "ok"
        assert health.queue_size >= 0
        assert health.active_connections >= 0
        assert health.uptime_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_recent_packets(self, telemetry_service, sample_packet):
        """Test retrieving recent packets"""
        # Emit some packets
        for i in range(5):
            packet = sample_packet.model_copy()
            packet.request_id = f"test-{i}"
            await telemetry_service.emit_packet(packet)
        
        recent = await telemetry_service.get_recent_packets(limit=3)
        assert len(recent) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])