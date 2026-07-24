from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.APP_NAME
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Verify JWT token from Authorization header
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token_data: Dict[str, Any] = Security(verify_token)) -> Dict[str, Any]:
    """
    Get current authenticated user from token
    
    Args:
        token_data: Decoded JWT token data
        
    Returns:
        User information dictionary
    """
    user_id = token_data.get("sub")
    if not user_id:
        logger.warning("Token missing user ID (sub claim)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return {
        "user_id": user_id,
        "email": token_data.get("email"),
        "role": token_data.get("role", "user")
    }


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False))) -> Dict[str, Any]:
    """
    Get current user with optional authentication (for testing)
    
    Args:
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        User information dictionary or default test user
    """
    if not credentials:
        # Return default test user when no auth provided
        return {
            "user_id": "test_user",
            "email": "test@example.com",
            "role": "user"
        }
    
    try:
        token_data = verify_token(credentials)
        user_id = token_data.get("sub")
        if not user_id:
            raise ValueError("Missing user ID")
        
        return {
            "user_id": user_id,
            "email": token_data.get("email"),
            "role": token_data.get("role", "user")
        }
    except Exception as e:
        logger.warning(f"Optional auth failed, using test user: {e}")
        return {
            "user_id": "test_user",
            "email": "test@example.com",
            "role": "user"
        }