# tests/validators/test_packet_validator.py

import pytest
from app.validators.packet_validator import PacketValidator


class TestPacketValidator:
    """Test Packet Validator functionality"""
    
    def test_validate_valid_ksml_packet(self):
        """Test validation of valid KSML packet"""
        valid_packet = {
            "meta": {
                "version": "1.0",
                "packet_type": "routing_request",
                "timestamp": "2025-10-29T15:10:00Z",
                "source": "insightflow",
                "destination": "core",
                "message_id": "msg-123abc",
                "checksum": "abc123def456"
            },
            "payload": {
                "data": {"test": "data"}
            }
        }
        
        is_valid, errors = PacketValidator.validate_ksml_packet(valid_packet)
        assert is_valid is True
        assert errors == []
    
    def test_validate_invalid_ksml_structure(self):
        """Test validation fails for invalid structure"""
        invalid_packet = {"no": "meta"}  # Missing meta and payload
        
        is_valid, errors = PacketValidator.validate_ksml_packet(invalid_packet)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_core_routing_request(self):
        """Test validation of Core routing request"""
        valid_request = {
            "task_type": "nlp",
            "min_confidence": 0.75,
            "task_context": {}
        }
        
        is_valid, errors = PacketValidator.validate_core_routing_request(
            valid_request
        )
        assert is_valid is True
        assert errors == []
    
    def test_validate_core_routing_response(self):
        """Test validation of Core routing response"""
        valid_response = {
            "selected_agent_id": "nlp-001",
            "agent_category": "nlp",
            "confidence_level": 0.92,
            "timestamp": "2025-10-29T15:10:00Z"
        }
        
        is_valid, errors = PacketValidator.validate_core_routing_response(
            valid_response
        )
        assert is_valid is True
        assert errors == []
    
    def test_validate_confidence_range(self):
        """Test confidence value validation"""
        invalid_request = {
            "task_type": "nlp",
            "min_confidence": 1.5  # Invalid: > 1.0
        }
        
        is_valid, errors = PacketValidator.validate_core_routing_request(
            invalid_request
        )
        assert is_valid is False
        assert any("between 0.0 and 1.0" in error for error in errors)
    
    def test_validate_routing_decision(self):
        """Test routing decision validation"""
        valid_decision = {
            "agent_selected": "nlp-001",
            "confidence_score": 0.87
        }
        
        is_valid, errors = PacketValidator.validate_routing_decision(
            valid_decision
        )
        assert is_valid is True
        assert errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])