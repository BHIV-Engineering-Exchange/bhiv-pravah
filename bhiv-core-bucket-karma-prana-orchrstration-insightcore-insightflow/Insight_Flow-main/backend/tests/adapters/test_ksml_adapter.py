# tests/adapters/test_ksml_adapter.py

import pytest
import json
from app.adapters.ksml_adapter import (
    KSMLAdapter, 
    KSMLPacketType, 
    KSMLFormatError
)


class TestKSMLAdapter:
    """Test KSML Adapter functionality"""
    
    def test_wrap_routing_request(self):
        """Test wrapping routing request"""
        data = {
            "agent_type": "nlp",
            "confidence_threshold": 0.75,
            "context": "test"
        }
        
        ksml_packet = KSMLAdapter.wrap(
            data, 
            KSMLPacketType.ROUTING_REQUEST.value
        )
        
        # Verify structure
        assert "meta" in ksml_packet
        assert "payload" in ksml_packet
        
        # Verify meta fields
        meta = ksml_packet["meta"]
        assert meta["version"] == "1.0"
        assert meta["packet_type"] == "routing_request"
        assert meta["source"] == "insightflow"
        assert meta["destination"] == "core"
        assert "message_id" in meta
        assert "timestamp" in meta
        assert "checksum" in meta
        
        # Verify payload
        assert ksml_packet["payload"]["data"] == data
    
    def test_unwrap_packet(self):
        """Test unwrapping KSML packet"""
        original_data = {
            "agent_id": "nlp-001",
            "score": 0.85
        }
        
        # Wrap data
        ksml_packet = KSMLAdapter.wrap(
            original_data,
            KSMLPacketType.ROUTING_RESPONSE.value
        )
        
        # Unwrap and verify
        unwrapped_data = KSMLAdapter.unwrap(ksml_packet)
        assert unwrapped_data == original_data
    
    def test_invalid_packet_type(self):
        """Test error on invalid packet type"""
        with pytest.raises(KSMLFormatError):
            KSMLAdapter.wrap({"test": "data"}, "invalid_type")
    
    def test_invalid_packet_structure(self):
        """Test error on invalid packet structure"""
        invalid_packet = {"invalid": "structure"}
        
        with pytest.raises(KSMLFormatError):
            KSMLAdapter.unwrap(invalid_packet)
    
    def test_validate_ksml_structure(self):
        """Test KSML structure validation"""
        valid_packet = KSMLAdapter.wrap(
            {"test": "data"},
            KSMLPacketType.HEALTH_CHECK.value
        )
        
        assert KSMLAdapter.validate_ksml_structure(valid_packet) is True
        
        # Invalid packet
        invalid_packet = {"no": "structure"}
        assert KSMLAdapter.validate_ksml_structure(invalid_packet) is False
    
    def test_roundtrip_conversion(self):
        """Test wrap then unwrap produces original data"""
        original = {
            "agent_id": "nlp-001",
            "confidence": 0.92,
            "timestamp": "2025-10-29T15:10:00Z"
        }
        
        # Wrap to KSML
        ksml_packet = KSMLAdapter.wrap(
            original,
            KSMLPacketType.METRICS_UPDATE.value
        )
        
        # Unwrap back
        recovered = KSMLAdapter.unwrap(ksml_packet)
        
        assert recovered == original
    
    def test_bytes_conversion(self):
        """Test bytes conversion for transmission"""
        data = {"test": "data"}
        
        # Convert to bytes
        ksml_bytes = KSMLAdapter.convert_to_ksml_bytes(
            data,
            KSMLPacketType.FEEDBACK_LOG.value
        )
        
        assert isinstance(ksml_bytes, bytes)
        
        # Convert back from bytes
        recovered = KSMLAdapter.convert_from_ksml_bytes(ksml_bytes)
        assert recovered == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])