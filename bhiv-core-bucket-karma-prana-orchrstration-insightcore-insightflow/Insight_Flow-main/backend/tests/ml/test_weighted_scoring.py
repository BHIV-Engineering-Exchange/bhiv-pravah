# tests/ml/test_weighted_scoring.py

import pytest
import tempfile
import os
from app.ml.weighted_scoring import (
    WeightedScoringEngine,
    ConfidenceScore,
    ScoreComponent,
    get_scoring_engine
)


@pytest.fixture
def scoring_engine(tmp_path):
    """Create scoring engine with temp config"""
    config_file = tmp_path / "scoring_config.yaml"
    config_file.write_text("""
scoring_weights:
  rule_based: 0.4
  feedback_based: 0.4
  availability: 0.2

score_sources:
  rule_based:
    enabled: true
    fallback_weight: 0.5
  feedback_based:
    enabled: true
    cache_ttl: 30
    fallback_weight: 0.5
  availability:
    enabled: true
    timeout_threshold: 5.0

normalization:
  strategy: "min_max"
  min_confidence: 0.1
  max_confidence: 1.0

logging:
  level: "DEBUG"
  score_breakdown: true
""")
    return WeightedScoringEngine(str(config_file))


class TestWeightedScoringEngine:
    """Test Weighted Scoring Engine"""
    
    def test_perfect_scores(self, scoring_engine):
        """Test calculation with all perfect scores"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=1.0,
            feedback_score=1.0,
            availability_score=1.0
        )
        
        assert result.final_score == 1.0
        assert len(result.components) == 3
    
    def test_zero_scores(self, scoring_engine):
        """Test calculation with all zero scores"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=0.0,
            feedback_score=0.0,
            availability_score=0.0
        )
        
        # Should apply minimum confidence floor
        assert result.final_score >= 0.1  # min_confidence from config
    
    def test_mixed_scores(self, scoring_engine):
        """Test calculation with mixed scores"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=0.8,
            feedback_score=0.9,
            availability_score=0.85
        )
        
        # Expected: (0.8*0.4) + (0.9*0.4) + (0.85*0.2) = 0.32 + 0.36 + 0.17 = 0.85
        expected = 0.85
        assert abs(result.final_score - expected) < 0.01
    
    def test_weight_validation(self, scoring_engine):
        """Test that weights sum to 1.0"""
        total_weight = sum(scoring_engine.weights.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_score_breakdown(self, scoring_engine):
        """Test score breakdown output"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=0.8,
            feedback_score=0.9,
            availability_score=0.7
        )
        
        breakdown = result.get_breakdown()
        assert "final_score" in breakdown
        assert "components" in breakdown
        assert "rule_based" in breakdown["components"]
        assert "feedback_based" in breakdown["components"]
        assert "availability" in breakdown["components"]
        
        # Check component structure
        rule_component = breakdown["components"]["rule_based"]
        assert "score" in rule_component
        assert "weight" in rule_component
        assert "weighted_value" in rule_component
        assert rule_component["score"] == 0.8
        assert rule_component["weight"] == 0.4
        assert rule_component["weighted_value"] == 0.32
    
    def test_out_of_bounds_clamping(self, scoring_engine):
        """Test that out-of-bounds scores are clamped"""
        result = scoring_engine.calculate_confidence(
            agent_id="nlp-001",
            rule_based_score=1.5,  # Out of bounds
            feedback_score=-0.2,   # Out of bounds
            availability_score=0.8
        )
        
        # Should be valid score
        assert 0.0 <= result.final_score <= 1.0
        
        # Check clamped values
        assert result.components["rule_based"].score == 1.0
        assert result.components["feedback_based"].score == 0.0
        assert result.components["availability"].score == 0.8
    
    def test_score_component_weighted_value(self):
        """Test ScoreComponent weighted value calculation"""
        component = ScoreComponent(
            name="test_component",
            score=0.75,
            weight=0.6
        )
        
        expected_weighted = 0.75 * 0.6
        assert component.weighted_value() == expected_weighted
    
    def test_confidence_score_breakdown_structure(self):
        """Test ConfidenceScore breakdown structure"""
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
        assert len(breakdown["components"]) == 3
        
        # Verify each component
        for name, expected_comp in components.items():
            comp_data = breakdown["components"][name]
            assert comp_data["score"] == expected_comp.score
            assert comp_data["weight"] == expected_comp.weight
            assert comp_data["weighted_value"] == expected_comp.weighted_value()
    
    def test_weight_normalization(self, scoring_engine):
        """Test weight normalization functionality"""
        # Test with weights that don't sum to 1.0
        weights = {"a": 0.6, "b": 0.8, "c": 0.4}  # Sum = 1.8
        normalized = scoring_engine._normalize_weights(weights)
        
        # Should sum to 1.0
        assert abs(sum(normalized.values()) - 1.0) < 0.001
        
        # Should maintain relative proportions
        assert normalized["b"] > normalized["a"] > normalized["c"]
    
    def test_clamp_function(self, scoring_engine):
        """Test value clamping utility"""
        # Test default range [0, 1]
        assert scoring_engine._clamp(-0.5) == 0.0
        assert scoring_engine._clamp(1.5) == 1.0
        assert scoring_engine._clamp(0.7) == 0.7
        
        # Test custom range
        assert scoring_engine._clamp(0.3, 0.5, 0.8) == 0.5  # Below min
        assert scoring_engine._clamp(0.9, 0.5, 0.8) == 0.8  # Above max
        assert scoring_engine._clamp(0.6, 0.5, 0.8) == 0.6  # Within range
    
    def test_score_normalization_with_floor(self, scoring_engine):
        """Test score normalization with minimum confidence floor"""
        # Test with score below minimum
        result = scoring_engine._normalize_score(0.05, min_conf=0.1)
        assert result == 0.1
        
        # Test with normal score
        result = scoring_engine._normalize_score(0.8, min_conf=0.1)
        assert result == 0.8
        
        # Test with out-of-bounds score
        result = scoring_engine._normalize_score(1.2, min_conf=0.1)
        assert result == 1.0
    
    def test_default_config_structure(self):
        """Test default configuration structure"""
        config = WeightedScoringEngine._default_config()
        
        assert "scoring_weights" in config
        assert "normalization" in config
        
        weights = config["scoring_weights"]
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert "rule_based" in weights
        assert "feedback_based" in weights
        assert "availability" in weights
        
        normalization = config["normalization"]
        assert "strategy" in normalization
        assert "min_confidence" in normalization
    
    def test_config_loading_fallback(self):
        """Test configuration loading with missing file"""
        # Try to load non-existent config file
        engine = WeightedScoringEngine("non_existent_config.yaml")
        
        # Should use default config
        assert engine.weights is not None
        assert len(engine.weights) == 3
        assert abs(sum(engine.weights.values()) - 1.0) < 0.01
    
    def test_singleton_pattern(self):
        """Test get_scoring_engine singleton behavior"""
        engine1 = get_scoring_engine()
        engine2 = get_scoring_engine()
        
        # Should return same instance
        assert engine1 is engine2
        assert isinstance(engine1, WeightedScoringEngine)
    
    def test_integration_with_decision_engine(self):
        """Test integration with decision engine"""
        from app.services.decision_engine import decision_engine
        
        # Verify scoring engine is integrated
        assert hasattr(decision_engine, 'scoring_engine')
        assert decision_engine.scoring_engine is not None
        assert isinstance(decision_engine.scoring_engine, WeightedScoringEngine)
    
    def test_realistic_scoring_scenario(self, scoring_engine):
        """Test realistic agent scoring scenario"""
        # Simulate different agent profiles
        agents = [
            {
                "id": "high-performance",
                "rule_score": 0.9,      # Excellent match
                "feedback_score": 0.95,  # Great user feedback
                "availability": 1.0      # Fully available
            },
            {
                "id": "balanced",
                "rule_score": 0.7,      # Good match
                "feedback_score": 0.8,   # Good feedback
                "availability": 0.9      # Mostly available
            },
            {
                "id": "backup",
                "rule_score": 0.5,      # Moderate match
                "feedback_score": 0.6,   # Average feedback
                "availability": 1.0      # Fully available
            }
        ]
        
        results = []
        for agent in agents:
            confidence = scoring_engine.calculate_confidence(
                agent_id=agent["id"],
                rule_based_score=agent["rule_score"],
                feedback_score=agent["feedback_score"],
                availability_score=agent["availability"]
            )
            results.append((agent["id"], confidence.final_score))
        
        # Sort by confidence score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # High-performance agent should rank first
        assert results[0][0] == "high-performance"
        assert results[0][1] > results[1][1] > results[2][1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])