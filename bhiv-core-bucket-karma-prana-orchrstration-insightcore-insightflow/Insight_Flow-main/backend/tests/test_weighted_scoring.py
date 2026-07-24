"""
Tests for Weighted Scoring Engine
"""

import pytest
from app.ml.weighted_scoring import WeightedScoringEngine, ScoreComponent, ConfidenceScore


class TestWeightedScoringEngine:
    """Test cases for WeightedScoringEngine"""
    
    def setup_method(self):
        """Setup test instance"""
        self.engine = WeightedScoringEngine()
    
    def test_score_component_weighted_value(self):
        """Test ScoreComponent weighted value calculation"""
        component = ScoreComponent(
            name="test",
            score=0.8,
            weight=0.4
        )
        
        assert component.weighted_value() == 0.32  # 0.8 * 0.4
    
    def test_confidence_score_breakdown(self):
        """Test ConfidenceScore breakdown generation"""
        components = {
            "rule_based": ScoreComponent("rule_based", 0.8, 0.4),
            "feedback_based": ScoreComponent("feedback_based", 0.9, 0.4),
            "availability": ScoreComponent("availability", 1.0, 0.2)
        }
        
        confidence = ConfidenceScore(
            final_score=0.86,
            components=components,
            normalization_method="min_max"
        )
        
        breakdown = confidence.get_breakdown()
        
        assert breakdown["final_score"] == 0.86
        assert "rule_based" in breakdown["components"]
        assert breakdown["components"]["rule_based"]["score"] == 0.8
        assert breakdown["components"]["rule_based"]["weight"] == 0.4
        assert breakdown["components"]["rule_based"]["weighted_value"] == 0.32
    
    def test_calculate_confidence_normal_scores(self):
        """Test confidence calculation with normal scores"""
        result = self.engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.8,
            feedback_score=0.9,
            availability_score=1.0
        )
        
        assert isinstance(result, ConfidenceScore)
        assert 0.0 <= result.final_score <= 1.0
        assert len(result.components) == 3
        assert "rule_based" in result.components
        assert "feedback_based" in result.components
        assert "availability" in result.components
    
    def test_calculate_confidence_out_of_bounds(self):
        """Test confidence calculation with out-of-bounds scores"""
        result = self.engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=1.5,  # Out of bounds
            feedback_score=-0.2,   # Out of bounds
            availability_score=0.8
        )
        
        # Should clamp values to valid range
        assert result.components["rule_based"].score == 1.0
        assert result.components["feedback_based"].score == 0.0
        assert result.components["availability"].score == 0.8
    
    def test_weight_normalization(self):
        """Test weight normalization"""
        weights = {"a": 0.6, "b": 0.8, "c": 0.4}  # Sum = 1.8
        normalized = self.engine._normalize_weights(weights)
        
        # Should sum to 1.0
        assert abs(sum(normalized.values()) - 1.0) < 0.001
        
        # Should maintain proportions
        assert normalized["b"] > normalized["a"] > normalized["c"]
    
    def test_clamp_function(self):
        """Test value clamping"""
        assert self.engine._clamp(-0.5) == 0.0
        assert self.engine._clamp(1.5) == 1.0
        assert self.engine._clamp(0.7) == 0.7
        assert self.engine._clamp(0.3, 0.5, 0.8) == 0.5  # Below min
        assert self.engine._clamp(0.9, 0.5, 0.8) == 0.8  # Above max
    
    def test_score_normalization(self):
        """Test score normalization with minimum confidence"""
        # Test with minimum confidence floor
        result = self.engine._normalize_score(0.05, min_conf=0.1)
        assert result == 0.1
        
        # Test normal score
        result = self.engine._normalize_score(0.8, min_conf=0.1)
        assert result == 0.8
        
        # Test out of bounds
        result = self.engine._normalize_score(1.2, min_conf=0.1)
        assert result == 1.0
    
    def test_default_config(self):
        """Test default configuration"""
        config = WeightedScoringEngine._default_config()
        
        assert "scoring_weights" in config
        assert "normalization" in config
        
        weights = config["scoring_weights"]
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert "rule_based" in weights
        assert "feedback_based" in weights
        assert "availability" in weights
    
    def test_integration_with_decision_engine(self):
        """Test integration with decision engine"""
        from app.services.decision_engine import decision_engine
        
        # Verify scoring engine is initialized
        assert hasattr(decision_engine, 'scoring_engine')
        assert decision_engine.scoring_engine is not None
    
    def test_weighted_calculation_accuracy(self):
        """Test weighted calculation accuracy"""
        # Known weights: rule=0.4, feedback=0.4, availability=0.2
        result = self.engine.calculate_confidence(
            agent_id="test",
            rule_based_score=0.5,    # 0.5 * 0.4 = 0.2
            feedback_score=0.8,      # 0.8 * 0.4 = 0.32
            availability_score=1.0   # 1.0 * 0.2 = 0.2
        )
        
        # Expected: 0.2 + 0.32 + 0.2 = 0.72
        expected_score = 0.72
        assert abs(result.final_score - expected_score) < 0.01