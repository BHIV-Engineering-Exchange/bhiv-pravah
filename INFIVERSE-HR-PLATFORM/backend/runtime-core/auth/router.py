"""
Sovereign Application Runtime (SAR) - Authentication Router

This module provides a reusable FastAPI router with authentication endpoints
that can be plugged into any BHIV service.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from .auth_service import sar_auth, AuthType, get_auth, get_api_key, get_candidate_auth, get_recruiter_auth, get_client_auth, get_admin_auth, get_optional_auth


router = APIRouter(prefix="/auth", tags=["Sovereign Authentication"])


class TwoFASetup(BaseModel):
    user_id: str


class TwoFAVerify(BaseModel):
    user_id: str
    totp_code: str


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None


class PasswordValidation(BaseModel):
    password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.post("/2fa/setup")
async def setup_2fa(setup_data: TwoFASetup, api_key: str = Depends(get_api_key)):
    """Setup 2FA TOTP for user"""
    return sar_auth.setup_2fa(setup_data.user_id)


@router.post("/2fa/verify")
async def verify_2fa(verify_data: TwoFAVerify, api_key: str = Depends(get_api_key)):
    """Verify 2FA TOTP code"""
    is_valid = sar_auth.verify_2fa(verify_data.user_id, verify_data.totp_code)
    if is_valid:
        return {
            "success": True,
            "user_id": verify_data.user_id,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")


@router.post("/login")
async def login_with_2fa(login_data: LoginRequest):
    """Login with optional 2FA"""
    # This would be implemented with actual user verification against a database
    # For now, this is a placeholder showing the expected flow
    from datetime import datetime, timezone
    
    # Basic authentication (in production, verify against database)
    # This is a simplified example - in a real implementation, you'd check credentials against a user store
    if login_data.username and login_data.password:  # Placeholder check
        # If 2FA is enabled for user, verify TOTP
        if login_data.totp_code:
            is_valid = sar_auth.verify_2fa(login_data.username, login_data.totp_code)
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
        # Generate JWT token
        payload = {
            "user_id": login_data.username,
            "tenant_id": "default",  # This would come from user record in real implementation
        }
        
        token = sar_auth.generate_jwt_token(payload, AuthType.USER_JWT)
        
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 hours
            "user_id": login_data.username,
            "2fa_verified": bool(login_data.totp_code)
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/2fa/status/{user_id}")
async def get_2fa_status(user_id: str, auth_result: dict = Depends(get_auth)):
    """Get 2FA status for user"""
    # In a real implementation, check the database for 2FA status
    return {
        "user_id": user_id,
        "2fa_enabled": True,  # In production, check database
        "setup_date": "2025-01-01T12:00:00Z",
        "last_used": "2025-01-02T08:30:00Z",
        "backup_codes_remaining": 8
    }


@router.post("/password/validate")
async def validate_password(password_data: PasswordValidation, api_key: str = Depends(get_api_key)):
    """Validate password strength"""
    return sar_auth.validate_password(password_data.password)


@router.post("/password/change")
async def change_password(password_change: PasswordChange, auth_result: dict = Depends(get_auth)):
    """Change password - requires valid authentication first"""
    # In a real implementation, this would update the user's password in the database
    # For now, this is a placeholder showing the expected flow
    validation_result = sar_auth.validate_password(password_change.new_password)
    
    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=400, 
            detail=f"New password is not strong enough: {', '.join(validation_result['feedback'])}"
        )
    
    return {
        "message": "Password changed successfully",
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "password_strength": validation_result["password_strength"]
    }


@router.get("/password/generate")
async def generate_password(length: int = 12, include_symbols: bool = True, api_key: str = Depends(get_api_key)):
    """Generate a secure random password"""
    password = sar_auth.generate_password(length, include_symbols)
    
    return {
        "generated_password": password,
        "length": length,
        "include_symbols": include_symbols,
        "entropy_bits": length * 6.5,
        "strength": "Very Strong",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/password/policy")
async def get_password_policy(api_key: str = Depends(get_api_key)):
    """Get password policy information"""
    from datetime import datetime, timezone
    
    return {
        "policy": {
            "minimum_length": sar_auth.config.password_min_length,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "max_age_days": 90,
            "history_count": 5
        },
        "complexity_requirements": [
            f"At least {sar_auth.config.password_min_length} characters long",
            "Contains uppercase letters",
            "Contains lowercase letters", 
            "Contains numbers",
            "Contains special characters"
        ],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health")
async def auth_health_check():
    """Health check for the authentication service"""
    return {
        "status": "healthy",
        "service": "Sovereign Application Runtime - Authentication Service",
        "features": [
            "API Key Authentication",
            "JWT Token Authentication",
            "2FA/TOTP Support",
            "Password Management",
            "Multi-tenant Support"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }