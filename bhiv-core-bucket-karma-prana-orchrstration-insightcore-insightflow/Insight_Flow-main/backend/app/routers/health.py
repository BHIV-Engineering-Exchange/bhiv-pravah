"""
Health check and basic system endpoints
"""

from fastapi import APIRouter, status
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        System health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "healthy",
            "database": "healthy" if not settings.USE_SOVEREIGN_CORE else "mock",
            "stp": "enabled" if settings.STP_ENABLED else "disabled",
            "karma": "enabled" if settings.KARMA_ENABLED else "disabled"
        }
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint
    
    Returns:
        API information
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """
    Simple ping endpoint
    
    Returns:
        Pong response
    """
    return {"message": "pong"}