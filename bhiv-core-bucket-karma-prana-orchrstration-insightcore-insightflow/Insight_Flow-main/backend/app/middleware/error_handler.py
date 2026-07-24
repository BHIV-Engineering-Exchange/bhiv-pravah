"""
Global error handling middleware for InsightFlow API
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GlobalErrorHandler(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
        except ConnectionError as e:
            logger.error(f"Database connection error: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Database temporarily unavailable",
                    "error_type": "connection_error",
                    "fallback_mode": True
                }
            )
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": str(e),
                    "error_type": "validation_error"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_type": "internal_error",
                    "debug_info": str(e) if logger.isEnabledFor(logging.DEBUG) else None
                }
            )


def create_error_response(
    status_code: int,
    message: str,
    error_type: str = "generic_error",
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Create standardized error response"""
    
    content = {
        "detail": message,
        "error_type": error_type,
        "timestamp": "2024-01-01T00:00:00Z"  # In production, use actual timestamp
    }
    
    if details:
        content.update(details)
    
    return JSONResponse(status_code=status_code, content=content)


def handle_database_error(e: Exception) -> JSONResponse:
    """Handle database-related errors"""
    
    error_msg = str(e).lower()
    
    if "connection" in error_msg or "timeout" in error_msg:
        return create_error_response(
            503,
            "Database temporarily unavailable",
            "database_connection_error",
            {"fallback_mode": True}
        )
    elif "not found" in error_msg:
        return create_error_response(
            404,
            "Resource not found",
            "resource_not_found"
        )
    elif "constraint" in error_msg or "foreign key" in error_msg:
        return create_error_response(
            400,
            "Invalid data reference",
            "constraint_violation"
        )
    else:
        return create_error_response(
            500,
            "Database operation failed",
            "database_error"
        )


def handle_validation_error(e: Exception) -> JSONResponse:
    """Handle validation errors"""
    
    return create_error_response(
        400,
        str(e),
        "validation_error"
    )


def handle_authentication_error(e: Exception) -> JSONResponse:
    """Handle authentication errors"""
    
    return create_error_response(
        401,
        "Authentication required",
        "authentication_error"
    )


def handle_authorization_error(e: Exception) -> JSONResponse:
    """Handle authorization errors"""
    
    return create_error_response(
        403,
        "Insufficient permissions",
        "authorization_error"
    )