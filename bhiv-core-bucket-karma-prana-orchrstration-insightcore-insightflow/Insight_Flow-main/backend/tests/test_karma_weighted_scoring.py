# tests/test_karma_weighted_scoring.py
"""
Tests for Karma-weighted scoring functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.ml.weighted_scoring import WeightedScoringEngine, ScoreComponent, ConfidenceScore
from app.services.karma_service import KarmaServiceClient


class TestKarmaWeightedScoring:
    """Test Karma-weighted scoring functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Mock Karma service
        self.karma_service = MagicMock(spec=KarmaServiceClient)
        self.karma_service.enabled = True
        
        # Create scoring engine with Karma service
        self.scoring_engine = WeightedScoringEngine(
            karma_service=self.karma_service
        )
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_karma_positive(self):
        """Test Karma-weighted scoring with positive Karma"""
        # Mock positive Karma score
        self.karma_service.get_karma_score = AsyncMock(return_value=0.5)
        
        # Calculate confidence with Karma
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        # Verify Karma component is included
        assert "karma_weighted" in confidence.components
        assert confidence.components["karma_weighted"].score == 0.5
        
        # Verify score is adjusted upward (positive Karma)
        base_confidence = self.scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        assert confidence.final_score > base_confidence.final_score
        assert confidence.normalization_method == "karma_adjusted"
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_karma_negative(self):
        """Test Karma-weighted scoring with negative Karma"""
        # Mock negative Karma score
        self.karma_service.get_karma_score = AsyncMock(return_value=-0.3)
        
        # Calculate confidence with Karma
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        # Verify Karma component is included
        assert "karma_weighted" in confidence.components
        assert confidence.components["karma_weighted"].score == -0.3
        
        # Verify score is adjusted downward (negative Karma)
        base_confidence = self.scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        assert confidence.final_score < base_confidence.final_score
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_karma_disabled(self):
        """Test Karma-weighted scoring when Karma is disabled"""
        # Disable Karma service
        self.karma_service.enabled = False
        
        # Calculate confidence
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        # Should return base confidence without Karma
        base_confidence = self.scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        assert confidence.final_score == base_confidence.final_score
        assert "karma_weighted" not in confidence.components
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_karma_no_service(self):
        """Test Karma-weighted scoring without Karma service"""
        # Create scoring engine without Karma service
        scoring_engine = WeightedScoringEngine(karma_service=None)
        
        # Calculate confidence
        confidence = await scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        # Should return base confidence
        base_confidence = scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        assert confidence.final_score == base_confidence.final_score
        assert "karma_weighted" not in confidence.components
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_karma_error_fallback(self):
        """Test Karma-weighted scoring with Karma service error"""
        # Mock Karma service error
        self.karma_service.get_karma_score = AsyncMock(
            side_effect=Exception("Karma service error")
        )
        
        # Calculate confidence
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        # Should fallback to base confidence
        base_confidence = self.scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        assert confidence.final_score == base_confidence.final_score
        assert "karma_weighted" not in confidence.components
    
    @pytest.mark.asyncio
    async def test_karma_score_clamping(self):
        """Test that final score is clamped to [0, 1] range"""
        # Mock very negative Karma that would push score below 0
        self.karma_service.get_karma_score = AsyncMock(return_value=-1.0)
        
        # Calculate confidence with low base scores
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.1,
            feedback_score=0.1,
            availability_score=0.1
        )
        
        # Score should be clamped to 0.0
        assert confidence.final_score >= 0.0
        
        # Mock very positive Karma that would push score above 1
        self.karma_service.get_karma_score = AsyncMock(return_value=1.0)
        
        # Calculate confidence with high base scores
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.9,
            feedback_score=0.9,
            availability_score=0.9
        )
        
        # Score should be clamped to 1.0
        assert confidence.final_score <= 1.0
    
    def test_karma_weight_configuration(self):
        """Test Karma weight configuration"""
        # Test default Karma weight (legacy)
        config = self.scoring_engine._default_config()
        assert "karma_weight" in config
        assert config["karma_weight"] == 0.15
        
        # Test new karma_weighting section
        assert "karma_weighting" in config
        assert config["karma_weighting"]["enabled"] is True
        assert config["karma_weighting"]["weight"] == 0.15
        assert config["karma_weighting"]["cache_ttl"] == 60
        assert config["karma_weighting"]["timeout"] == 5
        assert config["karma_weighting"]["max_retries"] == 3
        
        # Test custom configuration
        custom_config = {
            "karma_weighting": {
                "enabled": True,
                "weight": 0.25,
                "cache_ttl": 120
            }
        }
        self.scoring_engine.config = custom_config
        
        karma_config = self.scoring_engine.config.get("karma_weighting", {})
        karma_weight = karma_config.get("weight", 0.15)
        assert karma_weight == 0.25
        assert karma_config.get("cache_ttl") == 120
    
    @pytest.mark.asyncio
    async def test_karma_disabled_via_config(self):
        """Test Karma disabled via configuration"""
        # Mock positive Karma score
        self.karma_service.get_karma_score = AsyncMock(return_value=0.5)
        
        # Disable Karma in configuration
        self.scoring_engine.config = {
            "karma_weighting": {
                "enabled": False,
                "weight": 0.15
            }
        }
        
        # Calculate confidence
        confidence = await self.scoring_engine.calculate_confidence_with_karma(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        # Should return base confidence without Karma
        base_confidence = self.scoring_engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=0.7,
            feedback_score=0.8,
            availability_score=0.9
        )
        
        assert confidence.final_score == base_confidence.final_score
        assert "karma_weighted" not in confidence.components


if __name__ == "__main__":
    pytest.main([__file__, "-v"])