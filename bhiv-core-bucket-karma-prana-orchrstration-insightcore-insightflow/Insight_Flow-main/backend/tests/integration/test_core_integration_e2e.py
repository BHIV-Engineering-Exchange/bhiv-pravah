# tests/integration/test_core_integration_e2e.py
"""
End-to-end integration tests for Core integration.

Tests the complete flow:
1. KSML adapter
2. Interface converter
3. Packet validator
4. Weighted scoring
5. Feedback service
6. /route-agent endpoint
7. Logging and dashboard
"""

import pytest
import asyncio
from datetime import datetime

from app.adapters.ksml_adapter import KSMLAdapter, KSMLPacketType
from app.adapters.interface_converter import InterfaceConverter
from app.ml.weighted_scoring import WeightedScoringEngine
from app.validators.packet_validator import PacketValidator
from app.utils.routing_decision_logger import RoutingDecisionLogger


@pytest.fixture
def ksml_adapter():
    return KSMLAdapter()


@pytest.fixture
def scoring_engine(tmp_path):
    config_file = tmp_path / "scoring_config.yaml"
    config_file.write_text("""
scoring_weights:
  rule_based: 0.4
  feedback_based: 0.4
  availability: 0.2
""")
    return WeightedScoringEngine(str(config_file))


@pytest.fixture
def decision_logger(tmp_path):
    return RoutingDecisionLogger(log_dir=str(tmp_path))


class TestEndToEndFlow:
    """Test complete integration flow"""
    
    def test_ksml_wrap_unwrap_roundtrip(self, ksml_adapter):
        """Test KSML wrapping and unwrapping"""
        original_data = {
            "agent_type": "nlp",
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Wrap
        ksml_packet = ksml_adapter.wrap(
            original_data,
            KSMLPacketType.ROUTING_RESPONSE.value
        )
        
        # Validate
        is_valid, errors = PacketValidator.validate_ksml_packet(ksml_packet)
        assert is_valid, f"KSML validation failed: {errors}"
        
        # Unwrap
        recovered_data = ksml_adapter.unwrap(ksml_packet)
        
        # Verify
        assert recovered_data == original_data
    
    def test_interface_conversion_roundtrip(self):
        """Test v1 <-> v2 format conversion"""
        v1_request = {
            "agent_type": "nlp",
            "context": {"text": "hello"},
            "confidence_threshold": 0.75,
            "request_id": "req-123"
        }
        
        # Convert v1 -> v2
        v2_request = InterfaceConverter.insight_flow_to_core(v1_request)
        
        # Validate v2
        is_valid, errors = PacketValidator.validate_core_routing_request(v2_request)
        assert is_valid, f"v2 validation failed: {errors}"
        
        # Should have correct field mappings
        assert v2_request["task_type"] == "nlp"
        assert v2_request["min_confidence"] == 0.75
    
    def test_scoring_with_multiple_sources(self, scoring_engine):
        """Test weighted scoring calculation"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=0.80,
            feedback_score=0.90,
            availability_score=0.85
        )
        
        # Score should be between min and max inputs
        assert 0.80 <= result.final_score <= 0.90
        
        # Score breakdown should have all sources
        breakdown = result.get_breakdown()
        assert "components" in breakdown
        assert len(breakdown["components"]) == 3
    
    def test_logging_and_retrieval(self, decision_logger):
        """Test decision logging and querying"""
        # Log a decision
        success = decision_logger.log_decision(
            agent_selected="nlp-001",
            confidence_score=0.87,
            request_id="req-123",
            context={"agent_type": "nlp"},
            score_breakdown={
                "rule": 0.80,
                "feedback": 0.90,
                "availability": 0.85
            },
            response_time_ms=45,
            reasoning="Best match"
        )
        
        assert success is True
        
        # Query the decision
        decisions = decision_logger.query_decisions(agent_id="nlp-001", limit=1)
        
        assert len(decisions) > 0
        assert decisions[0]["agent_selected"] == "nlp-001"
        assert decisions[0]["confidence_score"] == 0.87
    
    def test_statistics_calculation(self, decision_logger):
        """Test statistics from logged decisions"""
        # Log multiple decisions
        for i in range(5):
            decision_logger.log_decision(
                agent_selected=f"nlp-{i % 2}",
                confidence_score=0.80 + (i * 0.02),
                request_id=f"req-{i}",
                context={"index": i},
                response_time_ms=40 + i
            )
        
        # Get statistics
        stats = decision_logger.get_statistics()
        
        assert stats["total_decisions"] == 5
        assert "avg_confidence" in stats
        assert "avg_response_time_ms" in stats


class TestErrorHandling:
    """Test error scenarios"""
    
    def test_invalid_ksml_packet(self, ksml_adapter):
        """Test handling of invalid KSML packets"""
        invalid_packet = {"no": "structure"}
        
        from app.adapters.ksml_adapter import KSMLFormatError
        with pytest.raises(KSMLFormatError):
            ksml_adapter.unwrap(invalid_packet)
    
    def test_confidence_out_of_bounds(self, scoring_engine):
        """Test clamping of out-of-bounds confidence"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=1.5,  # Invalid
            feedback_score=0.9,
            availability_score=0.8
        )
        
        # Should be clamped to valid range
        assert 0.0 <= result.final_score <= 1.0
    
    def test_missing_required_fields(self):
        """Test validation with missing fields"""
        incomplete_request = {"task_type": "nlp"}  # Missing min_confidence
        
        is_valid, errors = PacketValidator.validate_core_routing_request(
            incomplete_request
        )
        
        assert is_valid is False
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])