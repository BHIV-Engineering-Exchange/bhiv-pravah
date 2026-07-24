"""
Dependency injection for InsightFlow services
"""

from typing import Optional
from app.core.config import settings
from app.services.feedback_score_service import FeedbackScoreService

# Initialize feedback service as singleton
_feedback_service: Optional[FeedbackScoreService] = None


def get_feedback_service() -> FeedbackScoreService:
    """Get feedback score service instance (dependency injection)"""
    global _feedback_service
    
    if _feedback_service is None:
        _feedback_service = FeedbackScoreService(
            core_feedback_url=settings.CORE_FEEDBACK_SERVICE_URL,
            cache_ttl=settings.CORE_FEEDBACK_CACHE_TTL,
            timeout=settings.CORE_FEEDBACK_TIMEOUT,
            max_retries=settings.CORE_FEEDBACK_MAX_RETRIES,
        )
    
    return _feedback_service


# FastAPI dependency for endpoints
async def get_feedback_service_dependency() -> FeedbackScoreService:
    """FastAPI dependency for feedback service"""
    return get_feedback_service()