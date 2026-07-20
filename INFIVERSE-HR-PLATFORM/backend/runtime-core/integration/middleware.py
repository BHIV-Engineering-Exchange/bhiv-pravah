"""
Middleware for Integration Module

Provides middleware for handling integration-specific concerns like
cross-cutting logging, error handling, and request/response transformation.
"""

import logging
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime
import traceback

from .adapter_manager import sar_integration

logger = logging.getLogger(__name__)


class IntegrationEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce integration-specific policies and logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Add integration-specific headers
        request.state.integration_start_time = datetime.utcnow()
        
        # Set default integration context
        request.state.integration_context = {}
        
        try:
            response = await call_next(request)
            
            # Log successful integration request
            if hasattr(request.state, 'auth_info'):
                auth_info = request.state.auth_info
            else:
                auth_info = {}
                
            logger.info(
                f"Integration request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"User: {auth_info.get('user_id', 'unknown')} "
                f"Duration: {(datetime.utcnow() - request.state.integration_start_time).total_seconds():.2f}s"
            )
            
            return response
            
        except Exception as e:
            # Log integration request error
            if hasattr(request.state, 'auth_info'):
                auth_info = request.state.auth_info
            else:
                auth_info = {}
                
            logger.error(
                f"Integration request failed: {request.method} {request.url.path} "
                f"User: {auth_info.get('user_id', 'unknown')} "
                f"Error: {str(e)} "
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Return appropriate error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Integration service error",
                    "message": str(e) if request.app.debug else "Internal server error"
                }
            )


class IntegrationAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to audit integration requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Capture request details for auditing
        request.state.integration_request_id = f"int_req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Log the incoming request
        logger.info(
            f"Integration audit - Request: {request.state.integration_request_id} "
            f"{request.method} {request.url.path} "
            f"From: {request.client.host if request.client else 'unknown'}"
        )
        
        # Continue with request
        response = await call_next(request)
        
        # Log the response
        logger.info(
            f"Integration audit - Response: {request.state.integration_request_id} "
            f"Status: {response.status_code}"
        )
        
        # If we have MongoDB integration available, log to MongoDB
        if sar_integration and sar_integration._adapter_events_collection:
            try:
                audit_log = {
                    "request_id": request.state.integration_request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "client_ip": request.client.host if request.client else None,
                    "timestamp": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                
                # Add user info if available
                if hasattr(request.state, 'auth_info'):
                    audit_log["user_id"] = request.state.auth_info.get('user_id')
                    audit_log["user_type"] = request.state.auth_info.get('type')
                
                sar_integration._adapter_events_collection.insert_one(audit_log)
            except Exception as e:
                logger.error(f"Failed to log integration audit to MongoDB: {e}")
        
        return response