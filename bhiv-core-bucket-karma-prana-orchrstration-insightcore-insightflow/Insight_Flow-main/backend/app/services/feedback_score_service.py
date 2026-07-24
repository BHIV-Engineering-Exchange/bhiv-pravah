"""
Feedback Score Service: Integrates with Core feedback service.

Retrieves real-time agent performance scores from Core to feed into
routing decisions. Implements caching, retry logic, and graceful degradation.
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    success_rate: float  # 0-1: % of successful routing decisions
    latency_score: float  # 0-1: based on response time
    satisfaction_score: float  # 0-1: user satisfaction
    availability_score: float  # 0-1: agent uptime
    feedback_count: int  # number of feedback entries


class AgentScore(BaseModel):
    """Agent performance score"""
    agent_id: str
    overall_score: float
    breakdown: ScoreBreakdown
    timestamp: str
    is_cached: bool = False


class FeedbackScoreService:
    """
    Service for retrieving agent performance scores from Core feedback service.
    
    Features:
    - Real-time score retrieval
    - Score caching with TTL
    - Retry logic with exponential backoff
    - Graceful degradation on service unavailability
    - Metrics tracking
    """
    
    def __init__(
        self,
        core_feedback_url: str,
        cache_ttl: int = 30,
        timeout: int = 5,
        max_retries: int = 3
    ):
        """
        Initialize Feedback Score Service.
        
        Args:
            core_feedback_url: Core feedback service base URL
            cache_ttl: Cache time-to-live in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.core_feedback_url = core_feedback_url
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Score cache: {agent_id: (score, timestamp)}
        self._score_cache: Dict[str, tuple] = {}
        
        # Metrics
        self.metrics = {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "retries": 0,
        }
    
    async def get_agent_scores(
        self,
        agent_ids: List[str]
    ) -> Dict[str, float]:
        """
        Retrieve performance scores for multiple agents.
        
        Args:
            agent_ids: List of agent IDs
        
        Returns:
            Dict mapping agent_id → score (0-1)
        """
        scores = {}
        
        for agent_id in agent_ids:
            try:
                score = await self.get_agent_score(agent_id)
                scores[agent_id] = score
            except Exception as e:
                logger.warning(f"Error retrieving score for {agent_id}: {e}")
                # Use default score on error
                scores[agent_id] = 0.5
        
        return scores
    
    async def get_agent_score(self, agent_id: str) -> float:
        """
        Retrieve performance score for a single agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Performance score (0-1)
        """
        # Check cache first
        if self._is_cached(agent_id):
            self.metrics["cache_hits"] += 1
            cached_score, _ = self._score_cache[agent_id]
            logger.debug(f"Cache hit for {agent_id}: score={cached_score}")
            return cached_score
        
        self.metrics["cache_misses"] += 1
        
        # Fetch from Core service
        score = await self._fetch_score_from_core(agent_id)
        
        # Cache result
        self._score_cache[agent_id] = (score, datetime.utcnow())
        
        return score
    
    async def get_score_breakdown(
        self,
        agent_id: str
    ) -> Optional[ScoreBreakdown]:
        """
        Retrieve detailed score breakdown for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            ScoreBreakdown object or None on error
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.core_feedback_url}/agents/{agent_id}/breakdown"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ScoreBreakdown(**data)
                    else:
                        logger.warning(
                            f"Failed to get score breakdown: {response.status}"
                        )
                        return None
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching score breakdown for {agent_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching score breakdown: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Core feedback service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.core_feedback_url}/health"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    return response.status == 200
        
        except Exception as e:
            logger.warning(f"Feedback service health check failed: {e}")
            return False
    
    async def _fetch_score_from_core(self, agent_id: str) -> float:
        """
        Fetch score from Core service with retry logic.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Performance score (0-1)
        """
        self.metrics["requests"] += 1
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.core_feedback_url}/agents/{agent_id}"
                    
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            score = float(data.get("score", 0.5))
                            logger.info(
                                f"Retrieved score for {agent_id}: {score}"
                            )
                            return score
                        else:
                            logger.warning(
                                f"Core service returned {response.status} "
                                f"for {agent_id}"
                            )
            
            except asyncio.TimeoutError:
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.max_retries} "
                    f"for {agent_id}"
                )
                self.metrics["retries"] += 1
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except Exception as e:
                logger.error(
                    f"Error fetching score on attempt {attempt + 1}: {e}"
                )
                self.metrics["retries"] += 1
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # All retries exhausted, log error and return default
        logger.error(
            f"Failed to retrieve score for {agent_id} after "
            f"{self.max_retries} attempts"
        )
        self.metrics["errors"] += 1
        return 0.5  # Default score
    
    def _is_cached(self, agent_id: str) -> bool:
        """Check if score is cached and not expired"""
        if agent_id not in self._score_cache:
            return False
        
        _, timestamp = self._score_cache[agent_id]
        age = (datetime.utcnow() - timestamp).total_seconds()
        
        return age < self.cache_ttl
    
    def clear_cache(self, agent_id: Optional[str] = None):
        """
        Clear cache for specific agent or all agents.
        
        Args:
            agent_id: Agent to clear cache for, or None to clear all
        """
        if agent_id is None:
            self._score_cache.clear()
            logger.info("Cleared all score caches")
        else:
            if agent_id in self._score_cache:
                del self._score_cache[agent_id]
                logger.debug(f"Cleared cache for {agent_id}")
    
    def get_metrics(self) -> Dict:
        """
        Get service metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            **self.metrics,
            "cache_size": len(self._score_cache),
        }


# Note: Service instance is now managed via dependency injection
# See app.core.dependencies.get_feedback_service()