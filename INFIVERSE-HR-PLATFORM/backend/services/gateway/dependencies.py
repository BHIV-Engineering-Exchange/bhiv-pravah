"""
Gateway Authentication Dependencies
Uses JWT tokens for user authentication
"""

# Re-export from local JWT auth module
from jwt_auth import (
    security,
    validate_api_key,
    get_api_key,
    get_auth,
    auth_dependency,
    verify_jwt_token,
    get_user_from_token,
    require_role,
    get_candidate_auth,
    get_recruiter_auth,
    get_client_auth,
    get_admin_auth,
    get_optional_auth,
)

# Re-export all for backwards compatibility
__all__ = [
    "security",
    "validate_api_key",
    "get_api_key",
    "get_auth",
    "auth_dependency",
    "verify_jwt_token",
    "get_user_from_token",
    "require_role",
    "get_candidate_auth",
    "get_recruiter_auth",
    "get_client_auth",
    "get_admin_auth",
    "get_optional_auth",
]
