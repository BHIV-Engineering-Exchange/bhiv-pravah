"""
API Version Detection Middleware
Detects API version from headers and routes to appropriate handlers
"""

from fastapi import Request, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class APIVersionDetector:
    """Detects and validates API version from request headers"""
    
    SUPPORTED_VERSIONS = ["v1", "v2"]
    DEFAULT_VERSION = "v1"
    
    @classmethod
    def get_version_from_request(cls, request: Request) -> str:
        """
        Extract API version from request headers
        
        Priority:
        1. Accept-Version header
        2. URL path version
        3. Default version
        """
        # Check Accept-Version header
        version = request.headers.get("Accept-Version")
        if version and cls._is_valid_version(version):
            return version
        
        # Check URL path for version
        path_parts = request.url.path.split("/")
        for part in path_parts:
            if part.startswith("v") and cls._is_valid_version(part):
                return part
        
        # Return default version
        return cls.DEFAULT_VERSION
    
    @classmethod
    def _is_valid_version(cls, version: str) -> bool:
        """Check if version is supported"""
        return version in cls.SUPPORTED_VERSIONS
    
    @classmethod
    def validate_version_compatibility(cls, version: str, endpoint: str) -> bool:
        """
        Validate if version is compatible with endpoint
        
        Args:
            version: API version (v1, v2)
            endpoint: Endpoint path
            
        Returns:
            True if compatible, False otherwise
        """
        # v2 endpoints that don't exist in v1
        v2_only_endpoints = [
            "/api/v2/routing/ksml/route",
            "/api/v2/routing/batch",
            "/api/v2/agents/bulk"
        ]
        
        if version == "v1" and any(v2_endpoint in endpoint for v2_endpoint in v2_only_endpoints):
            return False
        
        return True
    
    @classmethod
    def get_deprecation_warning(cls, version: str) -> Optional[str]:
        """Get deprecation warning for version"""
        if version == "v1":
            return "API v1 is deprecated. Please migrate to v2. See /docs/migration for details."
        return None


def detect_api_version(request: Request) -> str:
    """
    Middleware function to detect API version
    
    Args:
        request: FastAPI request object
        
    Returns:
        API version string
        
    Raises:
        HTTPException: If version is invalid or incompatible
    """
    version = APIVersionDetector.get_version_from_request(request)
    
    # Validate version compatibility
    if not APIVersionDetector.validate_version_compatibility(version, request.url.path):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not compatible with endpoint {request.url.path}"
        )
    
    # Log version usage for analytics
    logger.info(f"API {version} request: {request.method} {request.url.path}")
    
    return version


def add_version_headers(response, version: str):
    """Add version-related headers to response"""
    response.headers["X-API-Version"] = version
    
    # Add deprecation warning for v1
    warning = APIVersionDetector.get_deprecation_warning(version)
    if warning:
        response.headers["X-Deprecation-Warning"] = warning
    
    return response