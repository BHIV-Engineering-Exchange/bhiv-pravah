"""
Utility functions for the School Management System.
"""

from app.models import UserRole
from fastapi import HTTPException, status


def validate_role_creation(role: UserRole) -> None:
    """
    Validate that the role being created is not SUPER_ADMIN.
    SUPER_ADMIN can only be created via the one-time setup script/endpoint.
    
    Raises HTTPException if attempting to create SUPER_ADMIN role.
    """
    if role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create SUPER_ADMIN role via API. SUPER_ADMIN can only be created through the one-time setup process."
        )
