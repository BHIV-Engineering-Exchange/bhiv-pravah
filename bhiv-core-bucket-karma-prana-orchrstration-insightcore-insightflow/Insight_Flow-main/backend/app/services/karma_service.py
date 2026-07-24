# app/services/karma_service.py
"""
Karma Service Client

Pulls Karma scores from Siddhesh's Karma Tracker endpoint.
Adds behavioral weighting to routing decisions.
Includes caching, retry logic, and toggle flag for experiments.
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KarmaScore(BaseModel):
    """Karma score data model"""
    agent_id: str
    karma_score: float  # Range: -1.0 to 1.0 (negative=bad, positive=good)
    karma_trend: str  # "improving" | "stable" | "declining"
    last_updated: str
    feedback_count: int


class KarmaServiceClient:
    """
    Client for Karma Tracker service.
    
    Features:
    - Async Karma score retrieval
    - Score caching with TTL
    - Retry logic
    - Toggle ON/OFF for experiments
    - Graceful degradation
    """
    
    def __init__(
        self,
        karma_endpoint: str,
        cache_ttl: int = 60,
        timeout: int = 5,
        max_retries: int = 3,
        enabled: bool = True
    ):
        """
        Initialize Karma service client.
        
        Args:
            karma_endpoint: Karma Tracker API endpoint
            cache_ttl: Cache time-to-live in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enabled: Enable/disable Karma weighting (toggle flag)
        """
        self.karma_endpoint = karma_endpoint
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = enabled
        
        # Karma score cache: {agent_id: (score, timestamp, performance_baseline)}
        self._karma_cache: Dict[str, tuple] = {}
        
        # Performance tracking for cache invalidation
        self._performance_history: Dict[str, List[float]] = {}
        self._invalidation_threshold = 0.2  # 20% performance change triggers invalidation
        
        # Metrics
        self.metrics = {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "retries": 0,
            "non_retryable_errors": 0,
        }
        
        logger.info(
            f"KarmaServiceClient initialized (enabled={enabled}, "
            f"endpoint={karma_endpoint})"
        )
    
    async def get_karma_score(self, agent_id: str) -> float:
        """
        Get Karma score for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Karma score (-1.0 to 1.0), or 0.0 if disabled/error
        """
        if not self.enabled:
            logger.debug("Karma weighting disabled, returning neutral score")
            return 0.0
        
        # Check cache first
        if self._is_cached(agent_id):
            self.metrics["cache_hits"] += 1
            cached_score, _ = self._karma_cache[agent_id]
            logger.debug(f"Cache hit for {agent_id}: karma={cached_score}")
            return cached_score
        
        self.metrics["cache_misses"] += 1
        
        # Fetch from Karma Tracker
        score = await self._fetch_karma_from_endpoint(agent_id)
        
        # Cache result with performance baseline
        current_performance = await self._get_agent_performance(agent_id)
        self._karma_cache[agent_id] = (score, datetime.utcnow(), current_performance)
        
        return score
    
    async def get_karma_scores_batch(
        self,
        agent_ids: List[str]
    ) -> Dict[str, float]:
        """
        Get Karma scores for multiple agents.
        
        Args:
            agent_ids: List of agent IDs
        
        Returns:
            Dict mapping agent_id → karma_score
        """
        if not self.enabled:
            return {agent_id: 0.0 for agent_id in agent_ids}
        
        scores = {}
        
        # Fetch in parallel
        tasks = [self.get_karma_score(agent_id) for agent_id in agent_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                logger.warning(f"Error fetching Karma for {agent_id}: {result}")
                scores[agent_id] = 0.0  # Neutral score on error
            else:
                scores[agent_id] = result
        
        return scores
    
    async def get_karma_details(
        self,
        agent_id: str
    ) -> Optional[KarmaScore]:
        """
        Get detailed Karma information for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            KarmaScore object or None if unavailable
        """
        if not self.enabled:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.karma_endpoint}/agents/{agent_id}/details"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return KarmaScore(**data)
                    else:
                        logger.warning(
                            f"Failed to get Karma details: {response.status}"
                        )
                        return None
        
        except Exception as e:
            logger.error(f"Error fetching Karma details: {e}")
            return None
    
    def _should_retry(self, error: Exception, status_code: int = None) -> bool:
        """Determine if error should be retried based on failure type"""
        # Don't retry client errors (4xx)
        if status_code and 400 <= status_code < 500:
            return False
        
        # Retry on network/timeout errors
        if isinstance(error, (asyncio.TimeoutError, aiohttp.ClientError)):
            return True
        
        # Retry on server errors (5xx)
        if status_code and status_code >= 500:
            return True
        
        return False
    
    async def _fetch_karma_from_endpoint(self, agent_id: str) -> float:
        """
        Fetch Karma score from Karma Tracker endpoint with smart retry logic.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Karma score (-1.0 to 1.0), or 0.0 on error
        """
        self.metrics["requests"] += 1
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.karma_endpoint}/agents/{agent_id}/score"
                    
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            score = float(data.get("karma_score", 0.0))
                            score = max(-1.0, min(1.0, score))
                            logger.info(f"Retrieved Karma for {agent_id}: {score}")
                            return score
                        
                        # Check if we should retry based on status code
                        if not self._should_retry(None, response.status):
                            logger.warning(f"Non-retryable error {response.status} for {agent_id}")
                            break
                        
                        logger.warning(f"Retryable error {response.status} for {agent_id}")
            
            except Exception as e:
                # Check if we should retry this error type
                if not self._should_retry(e):
                    logger.error(f"Non-retryable error for {agent_id}: {e}")
                    self.metrics["non_retryable_errors"] += 1
                    break
                
                logger.warning(f"Retryable error on attempt {attempt + 1}: {e}")
                self.metrics["retries"] += 1
                
                # Only sleep if we're going to retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        self.metrics["errors"] += 1
        return 0.0
    
    def _is_cached(self, agent_id: str) -> bool:
        """Check if Karma score is cached, not expired, and performance hasn't changed significantly"""
        if agent_id not in self._karma_cache:
            return False
        
        score, timestamp, baseline_performance = self._karma_cache[agent_id]
        age = (datetime.utcnow() - timestamp).total_seconds()
        
        # Check time-based expiration
        if age >= self.cache_ttl:
            return False
        
        # Check performance-based invalidation
        if self._should_invalidate_cache(agent_id, baseline_performance):
            logger.debug(f"Invalidating cache for {agent_id} due to performance change")
            del self._karma_cache[agent_id]
            return False
        
        return True
    
    def clear_cache(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear Karma cache for specific agent or all agents.
        
        Args:
            agent_id: Agent to clear cache for, or None to clear all
        
        Returns:
            True if cache was cleared successfully, False if agent not found
        """
        if agent_id is None:
            cache_size = len(self._karma_cache)
            self._karma_cache.clear()
            logger.info(f"Cleared all Karma caches ({cache_size} entries)")
            return True
        else:
            if agent_id in self._karma_cache:
                del self._karma_cache[agent_id]
                logger.debug(f"Cleared Karma cache for {agent_id}")
                return True
            else:
                logger.debug(f"No cache entry found for {agent_id}")
                return False
    
    def toggle_karma_weighting(self, enabled: bool):
        """
        Toggle Karma weighting ON/OFF.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        logger.info(f"Karma weighting {'enabled' if enabled else 'disabled'}")
    
    async def _get_agent_performance(self, agent_id: str) -> float:
        """Get current agent performance for cache invalidation"""
        try:
            # Simplified performance calculation - in real implementation,
            # this would fetch from agent performance metrics
            details = await self.get_karma_details(agent_id)
            if details:
                return details.karma_score
            return 0.0
        except Exception:
            return 0.0
    
    def _should_invalidate_cache(self, agent_id: str, baseline_performance: float) -> bool:
        """Check if cache should be invalidated due to performance drift"""
        try:
            # Get recent performance history
            if agent_id not in self._performance_history:
                return False
            
            recent_performance = self._performance_history[agent_id][-5:]  # Last 5 measurements
            if len(recent_performance) < 3:
                return False
            
            avg_recent = sum(recent_performance) / len(recent_performance)
            performance_drift = abs(avg_recent - baseline_performance)
            
            return performance_drift > self._invalidation_threshold
        except Exception:
            return False
    
    async def update_agent_performance(self, agent_id: str, performance_score: float):
        """Update agent performance history for cache invalidation"""
        if agent_id not in self._performance_history:
            self._performance_history[agent_id] = []
        
        self._performance_history[agent_id].append(performance_score)
        
        # Keep only last 10 measurements
        if len(self._performance_history[agent_id]) > 10:
            self._performance_history[agent_id] = self._performance_history[agent_id][-10:]
        
        # Check if cache should be invalidated
        if agent_id in self._karma_cache:
            _, _, baseline = self._karma_cache[agent_id]
            if self._should_invalidate_cache(agent_id, baseline):
                self.clear_cache(agent_id)
                logger.info(f"Invalidated cache for {agent_id} due to performance change")
    
    def invalidate_cache_by_performance_change(self, agent_id: str, old_performance: float, new_performance: float):
        """Invalidate cache if performance change exceeds threshold"""
        performance_change = abs(new_performance - old_performance)
        
        if performance_change > self._invalidation_threshold:
            if self.clear_cache(agent_id):
                logger.info(
                    f"Invalidated cache for {agent_id} due to significant performance change: "
                    f"{old_performance:.3f} -> {new_performance:.3f} (change: {performance_change:.3f})"
                )
    
    def get_metrics(self) -> Dict:
        """Get service metrics with cache invalidation stats"""
        cache_ages = []
        for agent_id, (_, timestamp, _) in self._karma_cache.items():
            age = (datetime.utcnow() - timestamp).total_seconds()
            cache_ages.append(age)
        
        return {
            **self.metrics,
            "cache_size": len(self._karma_cache),
            "enabled": self.enabled,
            "avg_cache_age_seconds": sum(cache_ages) / len(cache_ages) if cache_ages else 0,
            "performance_tracking_agents": len(self._performance_history),
            "invalidation_threshold": self._invalidation_threshold
        }


# Global Karma service instance
_karma_service: Optional[KarmaServiceClient] = None


def get_karma_service() -> KarmaServiceClient:
    """
    Get or create Karma service singleton.
    
    Returns:
        KarmaServiceClient instance
    """
    global _karma_service
    
    if _karma_service is None:
        from app.core.config import settings
        
        _karma_service = KarmaServiceClient(
            karma_endpoint=settings.KARMA_ENDPOINT,
            cache_ttl=settings.KARMA_CACHE_TTL,
            timeout=settings.KARMA_TIMEOUT,
            max_retries=3,  # Default value since KARMA_MAX_RETRIES not in config
            enabled=settings.KARMA_ENABLED
        )
    
    return _karma_service