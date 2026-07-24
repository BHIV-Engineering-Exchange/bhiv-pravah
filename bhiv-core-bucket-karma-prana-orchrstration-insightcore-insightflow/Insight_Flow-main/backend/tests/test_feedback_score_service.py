# tests/services/test_feedback_score_service.py

"""
Tests for Feedback Score Service
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from app.services.feedback_score_service import FeedbackScoreService, ScoreBreakdown
from app.core.dependencies import get_feedback_service


@pytest.fixture
def feedback_service():
    """Create feedback service instance for testing"""
    return FeedbackScoreService(
        core_feedback_url="http://localhost:8001",  # Test server
        cache_ttl=10,
        timeout=2,
        max_retries=2
    )


class TestFeedbackScoreService:
    """Test cases for FeedbackScoreService"""
    
    def setup_method(self):
        """Setup test instance"""
        self.service = FeedbackScoreService(
            core_feedback_url="http://test-core:9000/api/feedback",
            cache_ttl=30,
            timeout=5,
            max_retries=2
        )
    
    @pytest.mark.asyncio
    async def test_get_agent_score_success(self):
        """Test successful score retrieval"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"score": 0.85})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            score = await self.service.get_agent_score("agent-123")
            
            assert score == 0.85
            assert self.service.metrics["requests"] == 1
            assert self.service.metrics["cache_misses"] == 1
    
    @pytest.mark.asyncio
    async def test_get_agent_score_cached(self):
        """Test cached score retrieval"""
        # First call to populate cache
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"score": 0.75})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            score1 = await self.service.get_agent_score("agent-456")
            score2 = await self.service.get_agent_score("agent-456")  # Should be cached
            
            assert score1 == score2 == 0.75
            assert self.service.metrics["cache_hits"] == 1
            assert self.service.metrics["cache_misses"] == 1
    
    @pytest.mark.asyncio
    async def test_get_agent_scores_multiple(self):
        """Test retrieving scores for multiple agents"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(side_effect=[
                {"score": 0.8}, {"score": 0.9}, {"score": 0.7}
            ])
            mock_get.return_value.__aenter__.return_value = mock_response
            
            agent_ids = ["agent-1", "agent-2", "agent-3"]
            scores = await self.service.get_agent_scores(agent_ids)
            
            assert len(scores) == 3
            assert scores["agent-1"] == 0.8
            assert scores["agent-2"] == 0.9
            assert scores["agent-3"] == 0.7
    
    @pytest.mark.asyncio
    async def test_get_agent_score_retry_logic(self):
        """Test retry logic on failure"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # First call fails, second succeeds
            mock_response_fail = AsyncMock()
            mock_response_fail.status = 500
            
            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value={"score": 0.6})
            
            mock_get.return_value.__aenter__.side_effect = [
                mock_response_fail,
                mock_response_success
            ]
            
            score = await self.service.get_agent_score("agent-retry")
            
            assert score == 0.6
            assert self.service.metrics["retries"] == 1
    
    @pytest.mark.asyncio
    async def test_get_agent_score_default_on_failure(self):
        """Test default score returned on complete failure"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response
            
            score = await self.service.get_agent_score("agent-fail")
            
            assert score == 0.5  # Default score
            assert self.service.metrics["errors"] == 1
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            is_healthy = await self.service.health_check()
            
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            is_healthy = await self.service.health_check()
            
            assert is_healthy is False
    
    def test_cache_management(self):
        """Test cache clearing functionality"""
        # Manually add cache entries
        from datetime import datetime
        self.service._score_cache = {
            "agent-1": (0.8, datetime.utcnow()),
            "agent-2": (0.9, datetime.utcnow())
        }
        
        # Clear specific agent
        self.service.clear_cache("agent-1")
        assert "agent-1" not in self.service._score_cache
        assert "agent-2" in self.service._score_cache
        
        # Clear all
        self.service.clear_cache()
        assert len(self.service._score_cache) == 0
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        self.service.metrics["requests"] = 10
        self.service.metrics["cache_hits"] = 5
        
        metrics = self.service.get_metrics()
        
        assert metrics["requests"] == 10
        assert metrics["cache_hits"] == 5
        assert "cache_size" in metrics
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, feedback_service):
        """Test cache hit increases hit count"""
        # First request (cache miss)
        feedback_service._score_cache["nlp-001"] = (0.85, time.time())
        
        # Second request (cache hit)
        score = await feedback_service.get_agent_score("nlp-001")
        
        assert feedback_service.metrics["cache_hits"] > 0
        assert score == 0.85
    
    @pytest.mark.asyncio
    async def test_multiple_agents(self, feedback_service):
        """Test retrieving scores for multiple agents"""
        # Mock scores in cache
        current_time = time.time()
        feedback_service._score_cache["nlp-001"] = (0.85, current_time)
        feedback_service._score_cache["audio-001"] = (0.92, current_time)
        
        scores = await feedback_service.get_agent_scores(
            ["nlp-001", "audio-001"]
        )
        
        assert "nlp-001" in scores
        assert "audio-001" in scores
        assert scores["nlp-001"] == 0.85
        assert scores["audio-001"] == 0.92
    
    def test_metrics_tracking(self, feedback_service):
        """Test metrics are tracked"""
        feedback_service.metrics["requests"] = 5
        feedback_service.metrics["errors"] = 1
        
        metrics = feedback_service.get_metrics()
        
        assert metrics["requests"] == 5
        assert metrics["errors"] == 1
        assert "cache_size" in metrics
    
    def test_dependency_injection(self):
        """Test dependency injection works correctly"""
        service1 = get_feedback_service()
        service2 = get_feedback_service()
        
        # Should return same instance (singleton)
        assert service1 is service2
        assert isinstance(service1, FeedbackScoreService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])