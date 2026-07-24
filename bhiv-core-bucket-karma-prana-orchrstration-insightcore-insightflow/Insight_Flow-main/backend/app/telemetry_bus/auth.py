"""
Telemetry authentication utilities
"""

import logging
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def verify_telemetry_token(
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[dict]:
    """
    Verify JWT token for telemetry access.
    
    Args:
        credentials: Optional HTTP Bearer credentials
    
    Returns:
        Decoded token payload or None if auth not required
    """
    from app.core.config import settings
    
    # If auth not required, allow access
    if not settings.TELEMETRY_AUTH_REQUIRED:
        return {"user_id": "anonymous", "role": "telemetry_viewer"}
    
    # If auth required but no credentials provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for telemetry access"
        )
    
    try:
        from app.core.security import verify_token
        return verify_token(credentials)
    except Exception as e:
        logger.warning(f"Telemetry token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid telemetry access token"
        )


def check_telemetry_permissions(user_data: Optional[dict]) -> bool:
    """
    Check if user has telemetry access permissions.
    
    Args:
        user_data: Decoded token data
    
    Returns:
        True if access allowed
    """
    if not user_data:
        return True  # Anonymous access allowed when auth not required
    
    # Check role-based permissions
    role = user_data.get("role", "user")
    allowed_roles = ["admin", "telemetry_viewer", "user"]
    
    return role in allowed_roles