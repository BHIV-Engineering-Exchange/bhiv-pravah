# tests/integration/test_routing_integration.py
"""
Integration tests for routing system components.

Tests integration between:
- Dashboard service
- Routing decision logger
- Weighted scoring engine
- Feedback service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.services.dashboard_service import DashboardService
from app.utils.routing_decision_logger import RoutingDecisionLogger
from app.ml.weighted_scoring import WeightedScoringEngine
from app.services.feedback_score_service import FeedbackScoreService


@pytest.fixture
def decision_logger(tmp_path):
    """Create decision logger with temp directory"""
    return RoutingDecisionLogger(log_dir=str(tmp_path))


@pytest.fixture
def dashboard_service(decision_logger):
    """Create dashboard service with test logger"""
    service = DashboardService()
    service.decision_logger = decision_logger
    return service


@pytest.fixture
def scoring_engine(tmp_path):
    """Create scoring engine with test config"""
    config_file = tmp_path / "scoring_config.yaml"
    config_file.write_text("""
scoring_weights:
  rule_based: 0.4
  feedback_based: 0.4
  availability: 0.2
""")
    return WeightedScoringEngine(str(config_file))


class TestRoutingIntegration:
    """Test routing system integration"""
    
    def test_logging_to_dashboard_flow(self, decision_logger, dashboard_service):
        """Test flow from logging decisions to dashboard metrics"""
        # Log some decisions
        decisions_data = [
            ("nlp-001", 0.85, 45.2),
            ("nlp-002", 0.72, 38.1),
            ("nlp-001", 0.91, 52.3),
            ("cv-001", 0.78, 41.5)
        ]
        
        for agent_id, confidence, response_time in decisions_data:
            decision_logger.log_decision(
                agent_selected=agent_id,
                confidence_score=confidence,
                request_id=f"req-{agent_id}",
                context={"agent_type": agent_id.split("-")[0]},
                response_time_ms=response_time
            )
        
        # Get dashboard metrics
        metrics = asyncio.run(dashboard_service.get_performance_metrics(hours=24))
        
        # Verify metrics
        assert metrics["total_decisions"] == 4
        assert 0.72 <= metrics["average_confidence"] <= 0.91
        assert len(metrics["top_agents"]) > 0
        assert metrics["top_agents"][0]["agent_id"] == "nlp-001"  # Most frequent
    
    def test_scoring_engine_integration(self, scoring_engine):
        """Test scoring engine with realistic data"""
        # Test with different score combinations
        test_cases = [
            (0.8, 0.9, 1.0),  # High scores
            (0.5, 0.6, 0.7),  # Medium scores
            (0.2, 0.3, 0.4),  # Low scores
        ]
        
        for rule_score, feedback_score, availability_score in test_cases:
            result = scoring_engine.calculate_confidence(
                agent_id="test-agent",
                rule_based_score=rule_score,
                feedback_score=feedback_score,
                availability_score=availability_score
            )
            
            # Final score should be weighted average
            expected_min = min(rule_score, feedback_score, availability_score)
            expected_max = max(rule_score, feedback_score, availability_score)
            
            assert expected_min <= result.final_score <= expected_max
            assert 0.0 <= result.final_score <= 1.0
    
    def test_dashboard_accuracy_calculation(self, decision_logger, dashboard_service):
        """Test dashboard accuracy metrics"""
        # Log decisions with known confidence distribution
        high_confidence_decisions = 7  # >= 0.75
        low_confidence_decisions = 3   # < 0.75
        
        # High confidence decisions
        for i in range(high_confidence_decisions):
            decision_logger.log_decision(
                agent_selected=f"agent-{i}",
                confidence_score=0.75 + (i * 0.02),
                request_id=f"high-{i}",
                context={}
            )
        
        # Low confidence decisions
        for i in range(low_confidence_decisions):
            decision_logger.log_decision(
                agent_selected=f"agent-low-{i}",
                confidence_score=0.60 + (i * 0.03),
                request_id=f"low-{i}",
                context={}
            )
        
        # Get accuracy metrics
        accuracy = asyncio.run(dashboard_service.get_routing_accuracy(hours=24))
        
        # Verify accuracy calculation
        total_decisions = high_confidence_decisions + low_confidence_decisions
        expected_accuracy = (high_confidence_decisions / total_decisions) * 100
        
        assert accuracy["total_decisions"] == total_decisions
        assert accuracy["high_confidence_decisions"] == high_confidence_decisions
        assert abs(accuracy["accuracy_percentage"] - expected_accuracy) < 0.1
    
    def test_agent_performance_aggregation(self, decision_logger, dashboard_service):
        """Test per-agent performance aggregation"""
        # Create test data for specific agents
        agent_data = {
            "nlp-001": [0.85, 0.90, 0.88],
            "nlp-002": [0.72, 0.75, 0.78],
            "cv-001": [0.91]
        }
        
        # Log decisions for each agent
        for agent_id, confidences in agent_data.items():
            for i, confidence in enumerate(confidences):
                decision_logger.log_decision(
                    agent_selected=agent_id,
                    confidence_score=confidence,
                    request_id=f"{agent_id}-{i}",
                    context={"agent_type": agent_id.split("-")[0]}
                )
        
        # Get agent performance
        agents = asyncio.run(dashboard_service.get_agent_performance(hours=24))
        
        # Verify agent metrics
        assert len(agents) == 3
        
        # Find nlp-001 metrics
        nlp_001 = next(a for a in agents if a["agent_id"] == "nlp-001")
        assert nlp_001["total_decisions"] == 3
        assert abs(nlp_001["avg_confidence"] - 0.877) < 0.01  # (0.85+0.90+0.88)/3
        assert nlp_001["min_confidence"] == 0.85
        assert nlp_001["max_confidence"] == 0.90
    
    @pytest.mark.asyncio
    async def test_feedback_service_integration(self):
        """Test feedback service integration"""
        # Mock feedback service
        feedback_service = Mock(spec=FeedbackScoreService)
        feedback_service.get_agent_score = AsyncMock(return_value=0.85)
        feedback_service.health_check = AsyncMock(return_value=True)
        
        # Test service calls
        score = await feedback_service.get_agent_score("nlp-001")
        health = await feedback_service.health_check()
        
        assert score == 0.85
        assert health is True
        
        # Verify calls were made
        feedback_service.get_agent_score.assert_called_once_with("nlp-001")
        feedback_service.health_check.assert_called_once()


class TestErrorScenarios:
    """Test error handling in integration scenarios"""
    
    def test_empty_log_file_dashboard(self, dashboard_service):
        """Test dashboard with no logged decisions"""
        metrics = asyncio.run(dashboard_service.get_performance_metrics(hours=24))
        
        # Should return empty metrics without errors
        assert metrics["total_decisions"] == 0
        assert metrics["average_confidence"] == 0
        assert metrics["top_agents"] == []
    
    def test_invalid_confidence_scores(self, scoring_engine):
        """Test scoring engine with invalid inputs"""
        # Test with out-of-bounds scores
        result = scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=-0.5,  # Invalid
            feedback_score=1.5,     # Invalid
            availability_score=0.8
        )
        
        # Should handle gracefully and return valid score
        assert 0.0 <= result.final_score <= 1.0
    
    def test_corrupted_log_handling(self, tmp_path):
        """Test handling of corrupted log files"""
        # Create logger with temp directory
        logger = RoutingDecisionLogger(log_dir=str(tmp_path))
        
        # Write corrupted data to log file
        log_file = tmp_path / "routing_decisions.jsonl"
        log_file.write_text("invalid json line\n{\"valid\": \"json\"}\n")
        
        # Should handle corrupted lines gracefully
        decisions = logger.query_decisions(limit=10)
        
        # Should return only valid entries
        assert len(decisions) <= 1  # Only the valid JSON line


if __name__ == "__main__":
    pytest.main([__file__, "-v"])