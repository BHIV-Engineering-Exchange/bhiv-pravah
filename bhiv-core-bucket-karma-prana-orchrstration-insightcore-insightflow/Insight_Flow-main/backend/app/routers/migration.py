"""
Migration API endpoints for v1 to v2 transition management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict
from app.core.security import get_current_user
from app.services.migration_service import migration_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migration", tags=["migration"])


@router.get("/status")
async def get_migration_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get migration status for current user
    
    Returns:
        Migration progress and recommendations
    """
    try:
        user_id = current_user.get("user_id")
        status_data = await migration_service.get_migration_status(user_id)
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error getting migration status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving migration status"
        )


@router.get("/analytics")
async def get_migration_analytics(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get overall migration analytics (admin only)
    
    Returns:
        System-wide migration statistics
    """
    try:
        # Check if user is admin
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        analytics_data = await migration_service.get_migration_analytics()
        
        return analytics_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting migration analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving migration analytics"
        )


@router.get("/guide")
async def get_migration_guide():
    """
    Get migration guide information
    
    Returns:
        Migration guide summary and links
    """
    return {
        "title": "API Migration Guide: v1 → v2",
        "summary": "InsightFlow now supports both API v1 (legacy) and v2 (Core-integrated) with backward compatibility.",
        "timeline": {
            "current": "Both versions working (backward compatible)",
            "30_days": "Deprecation warnings for v1",
            "60_days": "v1 endpoints removed"
        },
        "key_changes": [
            "Enhanced response format with alternatives and metadata",
            "Improved error handling with structured error codes",
            "New batch processing capabilities",
            "KSML format support",
            "Enhanced context and preferences support"
        ],
        "migration_steps": [
            "Update API version in client headers",
            "Update request format to include new fields",
            "Handle enhanced response structure",
            "Update error handling for new format",
            "Test all endpoints in staging environment"
        ],
        "resources": {
            "full_guide": "/docs/MIGRATION_GUIDE.md",
            "api_docs": "/docs",
            "support_email": "support@insightflow.ai"
        }
    }


@router.post("/convert/request")
async def convert_request_format(
    v1_request: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Convert v1 request format to v2 format
    
    Args:
        v1_request: v1 format request
        
    Returns:
        Converted v2 format request
    """
    try:
        v2_request = await migration_service.convert_v1_to_v2_request(v1_request)
        
        return {
            "original_format": "v1",
            "converted_format": "v2",
            "v1_request": v1_request,
            "v2_request": v2_request,
            "conversion_notes": [
                "Added empty preferences object (new in v2)",
                "Added migration metadata to context",
                "Preserved all original fields"
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error converting request format: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error converting request format"
        )


@router.post("/convert/response")
async def convert_response_format(
    v2_response: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Convert v2 response format to v1 format
    
    Args:
        v2_response: v2 format response
        
    Returns:
        Converted v1 format response
    """
    try:
        v1_response = await migration_service.convert_v2_to_v1_response(v2_response)
        
        return {
            "original_format": "v2",
            "converted_format": "v1",
            "v2_response": v2_response,
            "v1_response": v1_response,
            "conversion_notes": [
                "Extracted core fields from enhanced v2 response",
                "Removed alternatives and enhanced metadata",
                "Maintained backward compatibility"
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error converting response format: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error converting response format"
        )


@router.get("/compatibility/check")
async def check_compatibility(
    endpoint: str,
    version: str = "v1"
):
    """
    Check if endpoint is compatible with API version
    
    Args:
        endpoint: Endpoint path to check
        version: API version (v1 or v2)
        
    Returns:
        Compatibility information
    """
    from app.api.middleware.version_detector import APIVersionDetector
    
    is_compatible = APIVersionDetector.validate_version_compatibility(version, endpoint)
    warnings = APIVersionDetector.get_deprecation_warning(version)
    
    return {
        "endpoint": endpoint,
        "version": version,
        "compatible": is_compatible,
        "warnings": [warnings] if warnings else [],
        "recommendations": [
            "Migrate to v2 for enhanced features" if version == "v1" else "Using latest API version"
        ]
    }