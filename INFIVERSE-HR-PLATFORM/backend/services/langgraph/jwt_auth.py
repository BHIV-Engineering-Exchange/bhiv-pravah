"""
JWT Authentication Module for BHIV HR Platform Backend
Validates JWT tokens from frontend
"""

import os
import jwt
import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# JWT configuration - Standardized variable names (see ENVIRONMENT_VARIABLES.md)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
CANDIDATE_JWT_SECRET_KEY = os.getenv("CANDIDATE_JWT_SECRET_KEY", "")

# API Key for service-to-service communication
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "")


def validate_api_key(api_key: str) -> bool:
    """Validate API key for service-to-service communication"""
    if not API_KEY_SECRET:
        return False
    return api_key == API_KEY_SECRET


def verify_jwt_token(token: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return the payload.
    Uses HS256 with the JWT secret from environment settings.
    Supports tokens with or without audience claim.
    """
    # Use explicit secret if provided, otherwise use JWT_SECRET_KEY
    jwt_secret = secret or JWT_SECRET_KEY
    
    if not jwt_secret:
        logger.error("JWT_SECRET_KEY not configured")
        return None
    
    try:
        # First try with audience validation
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            return payload
        except jwt.InvalidAudienceError:
            # If audience validation fails, try without audience (for custom tokens)
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def get_user_from_token(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user information from JWT token payload"""
    # Support both standard JWT tokens (sub) and custom tokens (candidate_id, client_id, user_id)
    user_id = payload.get("sub") or payload.get("candidate_id") or payload.get("client_id") or payload.get("user_id")
    
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "role": payload.get("user_metadata", {}).get("role") or payload.get("role", "candidate"),
        "name": payload.get("user_metadata", {}).get("name") or payload.get("name", ""),
        "aud": payload.get("aud"),
        "exp": payload.get("exp"),
    }


def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Dependency for API key only authentication"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not validate_api_key(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return credentials.credentials


def get_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Unified authentication: API key OR JWT token
    - API keys: For service-to-service communication
    - JWT: For authenticated users from frontend
    Supports both client JWT tokens (JWT_SECRET_KEY) and candidate JWT tokens (CANDIDATE_JWT_SECRET_KEY)
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = credentials.credentials
    
    # Try API key first (for service-to-service)
    if validate_api_key(token):
        return {
            "type": "api_key",
            "credentials": token,
            "user_id": "service",
            "role": "admin"
        }
    
    # Try candidate JWT token first (CANDIDATE_JWT_SECRET_KEY)
    if CANDIDATE_JWT_SECRET_KEY:
        payload = verify_jwt_token(token, secret=CANDIDATE_JWT_SECRET_KEY)
        if payload:
            user_info = get_user_from_token(payload)
            return {
                "type": "jwt_token",
                "user_id": user_info["user_id"],
                "email": user_info["email"],
                "role": "candidate",  # Candidate tokens always have candidate role
                "name": user_info["name"],
            }
    
    # Try client JWT token (JWT_SECRET_KEY)
    jwt_secret = JWT_SECRET_KEY
    if jwt_secret:
        payload = verify_jwt_token(token, secret=jwt_secret)
        if payload:
            user_info = get_user_from_token(payload)
            return {
                "type": "jwt_token",
                "user_id": user_info["user_id"],
                "email": user_info["email"],
                "role": user_info["role"],
                "name": user_info["name"],
            }
    
    raise HTTPException(status_code=401, detail="Invalid authentication token")


def auth_dependency(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Standard auth dependency for all services"""
    return get_auth(credentials)


def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles.
    Usage: Depends(require_role("admin", "recruiter"))
    """
    def role_checker(auth: dict = Security(get_auth)):
        user_role = auth.get("role", "")
        if user_role not in allowed_roles and auth.get("type") != "api_key":
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return auth
    return role_checker


# Role-specific dependencies
def get_candidate_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Authentication for candidate-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth  # API keys have full access
    if auth.get("role") != "candidate":
        raise HTTPException(status_code=403, detail="Candidate access required")
    return auth


def get_recruiter_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Authentication for recruiter-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth
    if auth.get("role") not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return auth


def get_client_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Authentication for client-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth
    if auth.get("role") not in ["client", "admin"]:
        raise HTTPException(status_code=403, detail="Client access required")
    return auth


def get_admin_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Authentication for admin-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth
    if auth.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth


# Optional auth (for public endpoints that can optionally use auth)
def get_optional_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None
    
    try:
        return get_auth(credentials)
    except HTTPException:
        return None