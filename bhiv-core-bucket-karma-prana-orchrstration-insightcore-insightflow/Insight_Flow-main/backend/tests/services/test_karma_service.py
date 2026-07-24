# tests/services/test_karma_service.py
"""
Tests for Karma Service Client
"""

import pytest
import asyncio
from app.services.karma_service import KarmaServiceClient


@pytest.fixture
def karma_service():
    """Create Karma service instance"""
    return KarmaServiceClient(
        karma_endpoint="http://localhost:8002/api/karma",
        cache_ttl=10,
        timeout=2,
        enabled=True
    )


@pytest.fixture
def karma_service_disabled():
    """Create disabled Karma service"""
    return KarmaServiceClient(
        karma_endpoint="http://localhost:8002/api/karma",
        enabled=False
    )


class TestKarmaServiceClient:
    """Test Karma service client"""
    
    @pytest.mark.asyncio
    async def test_disabled_returns_neutral(self, karma_service_disabled):
        """Test that disabled service returns neutral score"""
        score = await karma_service_disabled.get_karma_score("nlp-001")
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_batch_scores(self, karma_service_disabled):
        """Test batch score retrieval"""
        agent_ids = ["nlp-001", "nlp-002", "audio-001"]
        scores = await karma_service_disabled.get_karma_scores_batch(agent_ids)
        
        assert len(scores) == 3
        assert all(score == 0.0 for score in scores.values())
    
    def test_cache_management(self, karma_service):
        """Test cache operations"""
        # Add to cache
        karma_service._karma_cache["nlp-001"] = (0.8, asyncio.get_event_loop().time())
        
        assert karma_service._is_cached("nlp-001")
        
        # Clear specific
        karma_service.clear_cache("nlp-001")
        assert not karma_service._is_cached("nlp-001")
    
    def test_toggle_enabled(self, karma_service):
        """Test toggling Karma weighting"""
        assert karma_service.enabled is True
        
        karma_service.toggle_karma_weighting(False)
        assert karma_service.enabled is False
        
        karma_service.toggle_karma_weighting(True)
        assert karma_service.enabled is True
    
    def test_metrics_tracking(self, karma_service):
        """Test metrics are tracked"""
        metrics = karma_service.get_metrics()
        
        assert "requests" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "errors" in metrics
        assert "enabled" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])