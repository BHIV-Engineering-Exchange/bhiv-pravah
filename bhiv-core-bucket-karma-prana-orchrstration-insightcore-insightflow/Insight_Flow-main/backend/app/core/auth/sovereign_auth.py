# app/core/auth/sovereign_auth.py
"""
Sovereign Core Auth Integration

Replaces Supabase authentication with Core Auth system.
Provides abstract interface for seamless transition.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import os

logger = logging.getLogger(__name__)


class SovereignAuthError(Exception):
    """Raised when Sovereign Auth operations fail"""
    pass


class SovereignAuthClient:
    """
    Client for Sovereign Core authentication.
    
    Features:
    - JWT token generation and validation
    - User authentication
    - Service-to-service auth
    - Backward compatible with Supabase tokens
    """
    
    def __init__(
        self,
        core_auth_url: str,
        service_key: str,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        token_expiry_minutes: int = 60
    ):
        """
        Initialize Sovereign Auth client.
        
        Args:
            core_auth_url: Core Auth service URL
            service_key: Service authentication key
            jwt_secret: Secret for JWT signing
            jwt_algorithm: JWT algorithm (default: HS256)
            token_expiry_minutes: Token expiry time
        """
        self.core_auth_url = core_auth_url
        self.service_key = service_key
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.token_expiry_minutes = token_expiry_minutes
        
        logger.info(
            f"SovereignAuthClient initialized (url={core_auth_url})"
        )
    
    def generate_service_token(
        self,
        service_name: str = "insightflow",
        **claims
    ) -> str:
        """
        Generate JWT token for service-to-service authentication.
        
        Args:
            service_name: Name of the service
            **claims: Additional JWT claims
        
        Returns:
            JWT token string
        """
        try:
            payload = {
                "service": service_name,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(
                    minutes=self.token_expiry_minutes
                ),
                **claims
            }
            
            token = jwt.encode(
                payload,
                self.jwt_secret,
                algorithm=self.jwt_algorithm
            )
            
            logger.debug(f"Generated service token for {service_name}")
            return token
        
        except Exception as e:
            logger.error(f"Error generating service token: {str(e)}")
            raise SovereignAuthError(f"Token generation failed: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
        
        Returns:
            Decoded token payload
        
        Raises:
            SovereignAuthError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            logger.debug(f"Token verified for service: {payload.get('service')}")
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise SovereignAuthError("Token expired")
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise SovereignAuthError(f"Invalid token: {str(e)}")
    
    def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials.
        
        Args:
            username: User username
            password: User password
        
        Returns:
            User info dict or None if authentication fails
        """
        # Implementation would call Core Auth API
        # For now, placeholder
        logger.info(f"Authenticating user: {username}")
        
        # TODO: Implement actual Core Auth API call
        # This is a placeholder for the transition period
        
        return {
            "user_id": username,
            "authenticated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict of auth headers
        """
        token = self.generate_service_token()
        
        return {
            "Authorization": f"Bearer {token}",
            "X-Service-Key": self.service_key
        }


# Backward compatibility adapter for Supabase
class SupabaseCompatibilityAdapter:
    """
    Adapter to maintain backward compatibility with Supabase auth.
    
    During transition period, this allows old code to work while
    gradually migrating to Sovereign Core auth.
    """
    
    def __init__(self, sovereign_auth: SovereignAuthClient):
        """
        Initialize compatibility adapter.
        
        Args:
            sovereign_auth: Sovereign Auth client instance
        """
        self.sovereign_auth = sovereign_auth
        logger.info("Supabase compatibility adapter initialized")
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Supabase-compatible sign in method.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Auth response in Supabase format
        """
        # Authenticate using Sovereign Core
        user_info = self.sovereign_auth.authenticate_user(email, password)
        
        if user_info:
            # Generate token
            token = self.sovereign_auth.generate_service_token(
                service_name="user_session",
                user_id=email
            )
            
            # Return in Supabase-compatible format
            return {
                "user": user_info,
                "session": {
                    "access_token": token,
                    "refresh_token": None,  # Not used in Sovereign
                    "expires_in": self.sovereign_auth.token_expiry_minutes * 60
                }
            }
        else:
            raise SovereignAuthError("Authentication failed")
    
    def get_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from token (Supabase-compatible).
        
        Args:
            token: JWT token
        
        Returns:
            User info or None
        """
        try:
            payload = self.sovereign_auth.verify_token(token)
            
            return {
                "id": payload.get("user_id"),
                "email": payload.get("user_id"),
                "user_metadata": payload
            }
        
        except SovereignAuthError:
            return None