"""
Sovereign Application Runtime (SAR) - Authentication Service

This module provides a generic, multi-tenant authentication service that can be reused across
different BHIV products (HR, CRM, ERP, Nyaya, Setu, Design Tools).

Features:
- Dual authentication (API key and JWT tokens)
- Multi-tenant support with tenant isolation
- 2FA/TOTP support
- Password management and validation
- Candidate and client authentication
"""

from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import jwt
import httpx
from datetime import datetime, timezone, timedelta
import pyotp
import qrcode
import io
import base64
import secrets
import string
import random
import re
import bcrypt
from typing import Optional, Dict, Any, Union
from enum import Enum
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Enumeration of authentication types supported by the SAR"""
    API_KEY = "api_key"
    CLIENT_JWT = "client_jwt"
    CANDIDATE_JWT = "candidate_jwt"
    USER_JWT = "user_jwt"


class SARAuthConfig:
    """Configuration class for SAR authentication service"""
    
    def __init__(self):
        # Use the same environment variables as the services
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.api_key_secret = os.getenv("API_KEY_SECRET", "")
        self.candidate_jwt_secret = os.getenv("CANDIDATE_JWT_SECRET_KEY", "")
        self.token_expiry_hours = int(os.getenv("SAR_TOKEN_EXPIRY_HOURS", "24"))
        self.require_2fa = os.getenv("SAR_REQUIRE_2FA", "false").lower() == "true"
        self.password_min_length = int(os.getenv("SAR_PASSWORD_MIN_LENGTH", "8"))
        self.enable_rate_limiting = os.getenv("SAR_ENABLE_RATE_LIMITING", "true").lower() == "true"


class SARAuthentication:
    """Main authentication service class for the Sovereign Application Runtime"""
    
    def __init__(self):
        self.config = SARAuthConfig()
        self.security = HTTPBearer()
        self.totp_secrets = {}  # In production, use a persistent store
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key for service-to-service communication"""
        if not self.config.api_key_secret:
            return False
        return api_key == self.config.api_key_secret
    
    def get_api_key(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        """Dependency for API key authentication"""
        if not credentials or not self.validate_api_key(credentials.credentials):
            raise HTTPException(status_code=401, detail="Invalid API key")
        return credentials.credentials
    
    def get_auth(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        """
        Unified authentication: API key OR JWT token
        - API keys: For service-to-service communication
        - JWT: For authenticated users from frontend
        Supports both client JWT tokens (JWT_SECRET_KEY) and candidate JWT tokens (CANDIDATE_JWT_SECRET_KEY)
        """
        if not credentials:
            logger.warning("No credentials provided in Authorization header")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        token = credentials.credentials
        
        if not token:
            logger.warning("Empty token in credentials")
            raise HTTPException(status_code=401, detail="Authentication token is empty")
        
        logger.info(f"[AUTH] Attempting authentication with token (first 30 chars): {token[:30]}...")
        
        # Try API key first (for service-to-service)
        if self.validate_api_key(token):
            logger.debug("Authentication successful: API key")
            return {
                "type": "api_key",
                "credentials": token,
                "user_id": "service",
                "role": "admin"
            }
        
        # Try candidate JWT token first (CANDIDATE_JWT_SECRET_KEY)
        # This includes both candidates and recruiters (recruiters use candidate login endpoint)
        if self.config.candidate_jwt_secret:
            logger.info(f"Attempting candidate JWT validation with secret (exists: {bool(self.config.candidate_jwt_secret)}, length: {len(self.config.candidate_jwt_secret) if self.config.candidate_jwt_secret else 0})")
            payload = self.verify_jwt_token(token, secret=self.config.candidate_jwt_secret)
            if payload:
                user_info = self.get_user_from_token(payload)
                # Get role from token payload (supports both "candidate" and "recruiter")
                token_role = payload.get("role", "candidate")
                if token_role not in ["candidate", "recruiter"]:
                    token_role = "candidate"  # Default to candidate if invalid role
                logger.info(f"[OK] Authentication successful: Candidate JWT token for user {user_info.get('user_id')} with role {token_role}")
                return {
                    "type": "jwt_token",
                    "user_id": user_info["user_id"],
                    "email": user_info["email"],
                    "role": token_role,  # Use role from token payload (supports recruiter)
                    "name": user_info["name"],
                }
            else:
                logger.error(f"[ERROR] Candidate JWT token validation failed. Token (first 50 chars): {token[:50] if token else 'None'}...")
                logger.error(f"Secret configured: {bool(self.config.candidate_jwt_secret)}, Secret length: {len(self.config.candidate_jwt_secret) if self.config.candidate_jwt_secret else 0}")
        else:
            logger.error("[ERROR] CANDIDATE_JWT_SECRET_KEY not configured")
        
        # Try client JWT token (JWT_SECRET_KEY)
        jwt_secret = self.config.jwt_secret_key
        if jwt_secret:
            logger.debug(f"Attempting client JWT validation with secret (exists: {bool(jwt_secret)})")
            payload = self.verify_jwt_token(token, secret=jwt_secret)
            if payload:
                user_info = self.get_user_from_token(payload)
                logger.debug(f"Authentication successful: Client JWT token for user {user_info.get('user_id')}")
                return {
                    "type": "jwt_token",
                    "user_id": user_info["user_id"],
                    "email": user_info["email"],
                    "role": user_info["role"],
                    "name": user_info["name"],
                }
            else:
                logger.warning("Client JWT token validation failed")
        else:
            logger.warning("JWT_SECRET_KEY not configured")
        
        logger.error(f"All authentication methods failed for token (first 20 chars): {token[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    def generate_jwt_token(self, payload_data: Dict[str, Any], token_type: AuthType = AuthType.USER_JWT) -> str:
        """Generate a JWT token with the provided payload"""
        # Add standard claims
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=self.config.token_expiry_hours),
            "iat": datetime.utcnow(),
            "type": token_type.value
        }
        
        # Add custom claims
        payload.update(payload_data)
        
        # Select appropriate secret based on token type
        secret_key = self.config.jwt_secret_key
        if token_type == AuthType.CANDIDATE_JWT:
            secret_key = self.config.candidate_jwt_secret
        
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def verify_jwt_token(self, token: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token and return the payload.
        Uses HS256 with the JWT secret from environment settings.
        Supports tokens with or without audience claim.
        """
        # Use explicit secret if provided, otherwise use JWT_SECRET_KEY
        jwt_secret = secret or self.config.jwt_secret_key
        
        if not jwt_secret:
            logger.error("JWT_SECRET_KEY not configured")
            return None
        
        if not token:
            logger.error("Empty token provided to verify_jwt_token")
            return None
        
        try:
            # First try without audience validation (for custom tokens without aud claim)
            # This is more efficient and handles tokens created by our login endpoints
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            logger.debug("JWT token verified successfully without audience validation")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidSignatureError as e:
            logger.error(f"[ERROR] JWT token signature invalid: {e}. Secret mismatch or wrong secret used.")
            logger.error(f"Secret provided: {bool(jwt_secret)}, Secret length: {len(jwt_secret) if jwt_secret else 0}")
            logger.error(f"Token (first 50 chars): {token[:50] if token else 'None'}...")
            # Try with audience validation as fallback
            try:
                logger.debug("Attempting verification with audience validation as fallback")
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated"
                )
                logger.debug("JWT token verified successfully with audience validation")
                return payload
            except Exception as e2:
                logger.debug(f"Fallback verification with audience also failed: {e2}")
                return None
        except jwt.InvalidAudienceError:
            # Token has aud claim but it doesn't match - try without audience validation
            logger.debug("JWT token audience mismatch, trying without audience validation")
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                logger.debug("JWT token verified successfully without audience validation")
                return payload
            except Exception as e2:
                logger.debug(f"Verification without audience also failed: {e2}")
                return None
        except jwt.DecodeError as e:
            logger.warning(f"JWT token decode error: {e}")
            return None
        except jwt.InvalidTokenError as e:
            # Token might be missing aud claim - try without audience validation
            logger.debug(f"JWT token validation error (possibly missing aud claim): {e}, trying without audience")
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                logger.debug("JWT token verified successfully without audience validation")
                return payload
            except Exception as e2:
                logger.warning(f"Invalid JWT token even without audience validation: {e2}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error verifying JWT token: {e}")
            return None
    
    def get_user_from_token(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def setup_2fa(self, user_id: str) -> Dict[str, str]:
        """Setup 2FA TOTP for a user"""
        secret = pyotp.random_base32()
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_id,
            issuer_name="BHIV Sovereign Application Runtime"
        )
        
        # Store the secret temporarily (in production, use a secure persistent store)
        self.totp_secrets[user_id] = secret
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return {
            "user_id": user_id,
            "secret": secret,
            "qr_code": f"data:image/png;base64,{img_str}",
            "manual_entry_key": secret,
            "instructions": "Scan QR code with Google Authenticator, Microsoft Authenticator, or Authy"
        }
    
    def verify_2fa(self, user_id: str, totp_code: str) -> bool:
        """Verify 2FA TOTP code"""
        secret = self.totp_secrets.get(user_id)
        if not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(totp_code, valid_window=1)
    
    def validate_password(self, password: str) -> Dict[str, Union[int, str, list]]:
        """Validate password strength and return feedback"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= self.config.password_min_length:
            score += 20
        else:
            feedback.append(f"Password should be at least {self.config.password_min_length} characters long")
        
        # Uppercase check
        if any(c.isupper() for c in password):
            score += 20
        else:
            feedback.append("Password should contain uppercase letters")
        
        # Lowercase check
        if any(c.islower() for c in password):
            score += 20
        else:
            feedback.append("Password should contain lowercase letters")
        
        # Digit check
        if any(c.isdigit() for c in password):
            score += 20
        else:
            feedback.append("Password should contain numbers")
        
        # Special character check
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 20
        else:
            feedback.append("Password should contain special characters")
        
        # Determine strength
        strength = "Very Weak"
        if score >= 80:
            strength = "Very Strong"
        elif score >= 60:
            strength = "Strong"
        elif score >= 40:
            strength = "Medium"
        elif score >= 20:
            strength = "Weak"
        
        return {
            "password_strength": strength,
            "score": score,
            "max_score": 100,
            "is_valid": score >= 60,
            "feedback": feedback
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_password(self, length: int = 12, include_symbols: bool = True) -> str:
        """Generate a secure random password"""
        if length < 8 or length > 128:
            raise ValueError("Password length must be between 8 and 128 characters")
        
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += "!@#$%^&*()_+-="
        
        return ''.join(random.choice(chars) for _ in range(length))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format (Indian format by default)"""
        phone_pattern = r'^(\+91|91)?[6-9]\d{9}$'
        return re.match(phone_pattern, phone) is not None


# Global instance of the authentication service
sar_auth = SARAuthentication()


# Convenience functions for use as FastAPI dependencies
def auth_dependency(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Standard auth dependency for all services"""
    return sar_auth.get_auth(credentials)


def api_key_dependency(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """API key auth dependency for services requiring API key only"""
    if not credentials or not sar_auth.validate_api_key(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


def get_api_key(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Dependency for API key only authentication"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not sar_auth.validate_api_key(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return credentials.credentials


def get_auth(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Unified authentication: API key OR JWT token"""
    return sar_auth.get_auth(credentials)


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
def get_candidate_auth(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Authentication for candidate-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth  # API keys have full access
    if auth.get("role") != "candidate":
        raise HTTPException(status_code=403, detail="Candidate access required")
    return auth


def get_recruiter_auth(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Authentication for recruiter-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth
    if auth.get("role") not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return auth


def get_client_auth(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Authentication for client-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth
    if auth.get("role") not in ["client", "admin"]:
        raise HTTPException(status_code=403, detail="Client access required")
    return auth


def get_admin_auth(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Authentication for admin-only endpoints"""
    auth = get_auth(credentials)
    if auth.get("type") == "api_key":
        return auth
    if auth.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth


# Optional auth (for public endpoints that can optionally use auth)
def get_optional_auth(credentials: HTTPAuthorizationCredentials = Security(sar_auth.security)):
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None
    
    try:
        return get_auth(credentials)
    except HTTPException:
        return None