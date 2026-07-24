# tests/test_karma_service.py
"""
Tests for Karma Service Client
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.karma_service import KarmaServiceClient, KarmaScore, get_karma_service


class TestKarmaServiceClient:
    """Test Karma service client functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.karma_service = KarmaServiceClient(
            karma_endpoint="http://test-karma:8000/api/v1",
            cache_ttl=60,
            timeout=5,
            max_retries=3,
            enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_get_karma_score_disabled(self):
        """Test Karma score retrieval when disabled"""
        disabled_service = KarmaServiceClient(
            karma_endpoint="http://test-karma:8000/api/v1",
            enabled=False
        )
        
        score = await disabled_service.get_karma_score("test-agent")
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_get_karma_score_cached(self):
        """Test cached Karma score retrieval"""
        # Pre-populate cache
        from datetime import datetime
        self.karma_service._karma_cache["test-agent"] = (0.75, datetime.utcnow())
        
        score = await self.karma_service.get_karma_score("test-agent")
        assert score == 0.75
        assert self.karma_service.metrics["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_get_karma_scores_batch_disabled(self):
        """Test batch Karma score retrieval when disabled"""
        disabled_service = KarmaServiceClient(
            karma_endpoint="http://test-karma:8000/api/v1",
            enabled=False
        )
        
        agent_ids = ["agent1", "agent2", "agent3"]
        scores = await disabled_service.get_karma_scores_batch(agent_ids)
        
        assert len(scores) == 3
        assert all(score == 0.0 for score in scores.values())
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_fetch_karma_from_endpoint_success(self, mock_get):
        """Test successful Karma score fetch from endpoint"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"karma_score": 0.85}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        score = await self.karma_service._fetch_karma_from_endpoint("test-agent")
        assert score == 0.85
        assert self.karma_service.metrics["requests"] == 1
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_fetch_karma_from_endpoint_error(self, mock_get):
        """Test Karma score fetch with endpoint error"""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response
        
        score = await self.karma_service._fetch_karma_from_endpoint("test-agent")
        assert score == 0.0  # Neutral score on error
        assert self.karma_service.metrics["errors"] == 1
    
    def test_cache_expiry(self):
        """Test cache expiry logic"""
        from datetime import datetime, timedelta
        
        # Add expired cache entry
        expired_time = datetime.utcnow() - timedelta(seconds=120)  # 2 minutes ago
        self.karma_service._karma_cache["expired-agent"] = (0.5, expired_time)
        
        # Should not be cached
        assert not self.karma_service._is_cached("expired-agent")
        
        # Add fresh cache entry
        fresh_time = datetime.utcnow()
        self.karma_service._karma_cache["fresh-agent"] = (0.8, fresh_time)
        
        # Should be cached
        assert self.karma_service._is_cached("fresh-agent")
    
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        # Add some cache entries
        from datetime import datetime
        now = datetime.utcnow()
        self.karma_service._karma_cache["agent1"] = (0.5, now)
        self.karma_service._karma_cache["agent2"] = (0.7, now)
        
        # Clear specific agent
        self.karma_service.clear_cache("agent1")
        assert "agent1" not in self.karma_service._karma_cache
        assert "agent2" in self.karma_service._karma_cache
        
        # Clear all
        self.karma_service.clear_cache()
        assert len(self.karma_service._karma_cache) == 0
    
    def test_toggle_karma_weighting(self):
        """Test toggling Karma weighting"""
        assert self.karma_service.enabled is True
        
        self.karma_service.toggle_karma_weighting(False)
        assert self.karma_service.enabled is False
        
        self.karma_service.toggle_karma_weighting(True)
        assert self.karma_service.enabled is True
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        metrics = self.karma_service.get_metrics()
        
        assert "requests" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "errors" in metrics
        assert "retries" in metrics
        assert "cache_size" in metrics
        assert "enabled" in metrics
        
        assert metrics["enabled"] is True
    
    def test_karma_score_model(self):
        """Test KarmaScore data model"""
        karma_data = {
            "agent_id": "test-agent",
            "karma_score": 0.75,
            "karma_trend": "improving",
            "last_updated": "2025-01-08T10:00:00Z",
            "feedback_count": 150
        }
        
        karma_score = KarmaScore(**karma_data)
        
        assert karma_score.agent_id == "test-agent"
        assert karma_score.karma_score == 0.75
        assert karma_score.karma_trend == "improving"
        assert karma_score.feedback_count == 150
    
    def test_singleton_pattern(self):
        """Test that get_karma_service returns singleton"""
        service1 = get_karma_service()
        service2 = get_karma_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])