from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.core.security import create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    email: str = Field("test@example.com", pattern=r'^[^@]+@[^@]+\.[^@]+$')
    role: str = Field("admin", pattern=r'^(admin|user|service)$')


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def generate_token(request: TokenRequest):
    """
    Generate JWT token for testing purposes
    
    Args:
        request: Token request with username, email, and role
        
    Returns:
        JWT access token
    """
    try:
        token_data = {
            "sub": request.username,
            "email": request.email,
            "role": request.role
        }
        
        access_token = create_access_token(token_data)
        
        return TokenResponse(access_token=access_token)
        
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate token"
        )


@router.post("/quick-token")
async def generate_quick_token():
    """
    Generate a quick test token with default values
    
    Returns:
        JWT access token with default test user
    """
    try:
        token_data = {
            "sub": "test_user",
            "email": "test@insightflow.ai",
            "role": "admin"
        }
        
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usage": f"Authorization: Bearer {access_token}"
        }
        
    except Exception as e:
        logger.error(f"Error generating quick token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate token"
        )