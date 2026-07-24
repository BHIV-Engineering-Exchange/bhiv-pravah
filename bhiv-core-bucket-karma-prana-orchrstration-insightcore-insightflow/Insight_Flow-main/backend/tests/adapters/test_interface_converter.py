# tests/adapters/test_interface_converter.py

import pytest
from app.adapters.interface_converter import InterfaceConverter


class TestInterfaceConverter:
    """Test Interface Converter functionality"""
    
    def test_insight_flow_to_core_conversion(self):
        """Test converting InsightFlow format to Core format"""
        insight_request = {
            "agent_type": "nlp",
            "context": {"text": "hello"},
            "confidence_threshold": 0.8,
            "request_id": "req-123"
        }
        
        core_request = InterfaceConverter.insight_flow_to_core(insight_request)
        
        assert core_request["task_type"] == "nlp"
        assert core_request["task_context"] == {"text": "hello"}
        assert core_request["min_confidence"] == 0.8
        assert core_request["correlation_id"] == "req-123"
        assert core_request["metadata"]["source"] == "insightflow_v1"
    
    def test_core_to_insight_flow_conversion(self):
        """Test converting Core format to InsightFlow format"""
        core_response = {
            "selected_agent_id": "nlp-001",
            "agent_category": "nlp",
            "confidence_level": 0.95,
            "correlation_id": "req-123",
            "timestamp": "2025-10-29T15:10:00Z"
        }
        
        insight_response = InterfaceConverter.core_to_insight_flow(
            core_response
        )
        
        assert insight_response["agent_id"] == "nlp-001"
        assert insight_response["agent_type"] == "nlp"
        assert insight_response["confidence_score"] == 0.95
        assert insight_response["request_id"] == "req-123"
    
    def test_validate_insightflow_fields(self):
        """Test validation for InsightFlow format"""
        valid_data = {
            "agent_type": "nlp",
            "confidence_threshold": 0.75
        }
        
        assert InterfaceConverter.validate_field_mapping(
            valid_data, 
            "insightflow"
        ) is True
    
    def test_validate_core_fields(self):
        """Test validation for Core format"""
        valid_data = {
            "selected_agent_id": "nlp-001",
            "agent_category": "nlp",
            "confidence_level": 0.85
        }
        
        assert InterfaceConverter.validate_field_mapping(
            valid_data,
            "core"
        ) is True
    
    def test_missing_required_fields(self):
        """Test error on missing required fields"""
        invalid_data = {"confidence_threshold": 0.75}  # Missing agent_type
        
        with pytest.raises(ValueError) as exc_info:
            InterfaceConverter.validate_field_mapping(
                invalid_data,
                "insightflow"
            )
        
        assert "Missing required fields" in str(exc_info.value)
    
    def test_bidirectional_conversion(self):
        """Test bidirectional conversion"""
        # Start with InsightFlow format
        insight_data = {
            "agent_type": "nlp",
            "context": {"data": "test"},
            "confidence_threshold": 0.8
        }
        
        # Convert to Core
        core_data = InterfaceConverter.bidirectional_convert(
            insight_data,
            "insightflow"
        )
        
        assert "task_type" in core_data
        assert core_data["task_type"] == "nlp"


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    pytest.main([__file__, "-v"])