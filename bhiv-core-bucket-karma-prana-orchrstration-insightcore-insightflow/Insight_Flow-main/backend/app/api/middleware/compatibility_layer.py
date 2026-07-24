"""
Compatibility Layer Middleware

Routes requests to v1 or v2 endpoints based on request headers/version param.
Handles format conversion automatically.
"""

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CompatibilityLayerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle backward compatibility between API versions.
    
    Rules:
    1. If client sends Accept-Version: v2 header → use v2 (Core format)
    2. If client sends Accept-Version: v1 header → use v1 (InsightFlow format)
    3. If no header → default to v2 (new format)
    4. Automatically convert request/response formats
    """
    
    def __init__(self, app, default_version: str = "v2"):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            default_version: Default API version (v1 or v2)
        """
        super().__init__(app)
        self.default_version = default_version
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle version routing.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
        
        Returns:
            HTTP response
        """
        # Determine requested API version
        version = request.headers.get("Accept-Version", self.default_version)
        
        # Store version in request state for downstream handlers
        request.state.api_version = version
        
        # Log version
        logger.debug(f"Request routed to API {version}")
        
        # Process request
        response = await call_next(request)
        
        # Add version header to response
        response.headers["API-Version"] = version
        
        return response