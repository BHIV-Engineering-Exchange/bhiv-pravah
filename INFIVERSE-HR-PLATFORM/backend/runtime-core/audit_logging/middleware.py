"""
Audit Logging Middleware for Sovereign Application Runtime (SAR)

This module provides middleware for automatic audit logging of requests
with provenance tracking for all operations.
"""
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp
import time
import uuid
from audit_logging.audit_service import sar_audit, AuditEventType
from auth.auth_service import get_auth, AuthResult
import logging

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log audit events for all requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate a correlation ID for this request
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Capture start time
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host if hasattr(request, 'client') else None
        user_agent = request.headers.get('user-agent')
        request_path = request.url.path
        request_method = request.method
        request_query = str(request.url.query) if request.url.query else ""
        
        # Extract user and tenant info from request state (set by other middleware)
        user_id = None
        tenant_id = None
        
        # Try to get user info from request state (set by auth middleware)
        auth_info = getattr(request.state, 'auth_info', None)
        if auth_info:
            user_id = (auth_info.get("user_id") or 
                      auth_info.get("client_id") or 
                      auth_info.get("candidate_id"))
        
        # Try to get tenant info from request state (set by tenant middleware)
        tenant_info = getattr(request.state, 'tenant_info', None)
        if tenant_info and hasattr(tenant_info, 'tenant_id'):
            tenant_id = tenant_info.tenant_id
        elif auth_info and 'tenant_id' in auth_info:
            tenant_id = auth_info['tenant_id']
        
        # Try to get auth result directly
        auth_result = getattr(request.state, 'auth_result', None)
        if auth_result and isinstance(auth_result, AuthResult):
            user_id = (auth_result.user_id or auth_result.client_id or auth_result.candidate_id)
            if hasattr(auth_result, 'tenant_id'):
                tenant_id = auth_result.tenant_id
        
        # Log the request (before processing)
        request_event_id = str(uuid.uuid4())
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error and re-raise
            duration = time.time() - start_time
            sar_audit.log_event(
                event_type=AuditEventType.API_ACCESS,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=client_ip,
                user_agent=user_agent,
                resource=request_path,
                action=request_method,
                correlation_id=correlation_id,
                success=False,
                error_message=str(e),
                metadata={
                    "duration_ms": round(duration * 1000, 2),
                    "request_method": request_method,
                    "request_path": request_path,
                    "request_query": request_query,
                    "response_status": 500
                }
            )
            raise e
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log the response
        sar_audit.log_event(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource=request_path,
            action=request_method,
            correlation_id=correlation_id,
            success=response.status_code < 400,
            metadata={
                "duration_ms": round(duration * 1000, 2),
                "request_method": request_method,
                "request_path": request_path,
                "request_query": request_query,
                "response_status": response.status_code
            }
        )
        
        # Add correlation ID to response headers for tracking
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class DetailedAuditMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for detailed audit logging with data modification tracking"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host if hasattr(request, 'client') else None
        user_agent = request.headers.get('user-agent')
        request_path = request.url.path
        request_method = request.method
        
        # Extract user and tenant info
        user_id = None
        tenant_id = None
        
        auth_info = getattr(request.state, 'auth_info', None)
        if auth_info:
            user_id = (auth_info.get("user_id") or 
                      auth_info.get("client_id") or 
                      auth_info.get("candidate_id"))
        
        tenant_info = getattr(request.state, 'tenant_info', None)
        if tenant_info and hasattr(tenant_info, 'tenant_id'):
            tenant_id = tenant_info.tenant_id
        elif auth_info and 'tenant_id' in auth_info:
            tenant_id = auth_info['tenant_id']
        
        # Capture request body for POST/PUT/PATCH requests (for data modification tracking)
        request_body = None
        old_values = None
        new_values = None
        
        if request_method in ["POST", "PUT", "PATCH"] and request_path.startswith(('/v1/', '/api/v1/')):
            # Read the request body for modification tracking
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = body_bytes.decode('utf-8')
                    # In a real implementation, you would parse this and extract old/new values
                    # For now, we'll just store the raw body
                    new_values = {"raw_body": request_body[:1000]}  # Limit size
            except:
                pass  # If we can't read the body, continue without it
        
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            sar_audit.log_event(
                event_type=AuditEventType.API_ACCESS,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=client_ip,
                user_agent=user_agent,
                resource=request_path,
                action=request_method,
                correlation_id=correlation_id,
                success=False,
                error_message=str(e),
                metadata={
                    "duration_ms": round(duration * 1000, 2),
                    "request_method": request_method,
                    "request_path": request_path,
                    "response_status": 500
                }
            )
            raise e
        
        duration = time.time() - start_time
        
        # Determine if this is a data modification event
        event_type = AuditEventType.API_ACCESS
        action = request_method.lower()
        
        # Check if this request modifies data
        if request_method in ["POST", "PUT", "PATCH", "DELETE"]:
            event_type = AuditEventType.DATA_MODIFICATION
            if request_method == "POST":
                action = "create"
            elif request_method == "PUT":
                action = "update"
            elif request_method == "PATCH":
                action = "update"
            elif request_method == "DELETE":
                action = "delete"
        elif request_method == "GET":
            event_type = AuditEventType.DATA_ACCESS
            action = "read"
        
        # Extract resource and resource_id from path
        resource = self._extract_resource_from_path(request_path)
        resource_id = self._extract_resource_id_from_path(request_path)
        
        # Log the detailed audit event
        sar_audit.log_event(
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource=resource,
            action=action,
            resource_id=resource_id,
            correlation_id=correlation_id,
            success=response.status_code < 400,
            old_values=old_values,
            new_values=new_values,
            metadata={
                "duration_ms": round(duration * 1000, 2),
                "request_method": request_method,
                "request_path": request_path,
                "response_status": response.status_code
            }
        )
        
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    
    def _extract_resource_from_path(self, path: str) -> str:
        """Extract resource name from API path"""
        # Example: /v1/jobs -> jobs, /api/v1/candidates -> candidates
        path_parts = path.strip('/').split('/')
        for part in path_parts:
            if part not in ['v1', 'api', 'v2', 'v3']:  # Skip version numbers
                return part
        return path
    
    def _extract_resource_id_from_path(self, path: str) -> Optional[str]:
        """Extract resource ID from API path"""
        path_parts = path.strip('/').split('/')
        # Look for patterns like /v1/jobs/{id}
        for i, part in enumerate(path_parts):
            if part not in ['v1', 'api', 'v2', 'v3'] and i + 1 < len(path_parts):
                next_part = path_parts[i + 1]
                # If the next part is not a known endpoint, assume it's an ID
                if not next_part.isdigit() and next_part not in ['create', 'update', 'delete', 'get', 'list']:
                    continue
                if next_part.isdigit() or len(next_part) > 5:  # Likely an ID
                    return next_part
        return None


def log_user_security_event(user_id: str, event_type: str, description: str = "", 
                          tenant_id: Optional[str] = None, client_ip: Optional[str] = None,
                          severity: str = "medium") -> bool:
    """Helper function to log security-related events for a user"""
    return sar_audit.log_security_event(
        event_subtype=event_type,
        user_id=user_id,
        tenant_id=tenant_id,
        client_ip=client_ip,
        description=description,
        severity=severity
    )


def log_data_access_event(user_id: str, resource: str, resource_id: str,
                        tenant_id: Optional[str] = None, success: bool = True) -> bool:
    """Helper function to log data access events"""
    return sar_audit.log_data_access(
        user_id=user_id,
        tenant_id=tenant_id,
        resource=resource,
        resource_id=resource_id,
        success=success
    )


def log_data_modification_event(user_id: str, resource: str, resource_id: str,
                              action: str, old_values: Optional[Dict[str, Any]] = None,
                              new_values: Optional[Dict[str, Any]] = None,
                              tenant_id: Optional[str] = None,
                              success: bool = True, error_message: Optional[str] = None) -> bool:
    """Helper function to log data modification events with provenance tracking"""
    return sar_audit.log_data_modification(
        user_id=user_id,
        tenant_id=tenant_id,
        resource=resource,
        resource_id=resource_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        success=success,
        error_message=error_message
    )