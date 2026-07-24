"""
Migration Middleware for API version tracking and deprecation warnings
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.middleware.version_detector import detect_api_version, add_version_headers
from app.services.migration_service import migration_service
import logging
import time

logger = logging.getLogger(__name__)


class MigrationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API migration tracking and warnings"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Detect API version
        try:
            api_version = detect_api_version(request)
            request.state.api_version = api_version
        except Exception as e:
            logger.warning(f"Failed to detect API version: {e}")
            api_version = "v1"  # Default fallback
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        add_version_headers(response, api_version)
        
        # Track API usage for migration analytics
        try:
            # Extract user ID from request if available
            user_id = getattr(request.state, 'user_id', None)
            if user_id and request.url.path.startswith('/api/'):
                await migration_service.track_api_usage(
                    user_id=user_id,
                    api_version=api_version,
                    endpoint=request.url.path
                )
        except Exception as e:
            logger.warning(f"Failed to track API usage: {e}")
        
        # Add deprecation warnings for v1
        if api_version == "v1":
            warnings = migration_service.get_deprecation_warnings(api_version)
            if warnings:
                response.headers["X-Deprecation-Warning"] = "; ".join(warnings)
        
        # Add processing time
        processing_time = (time.time() - start_time) * 1000
        response.headers["X-Processing-Time-Ms"] = str(round(processing_time, 2))
        
        return response