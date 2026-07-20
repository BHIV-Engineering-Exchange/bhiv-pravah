"""
Workflow Middleware for Sovereign Application Runtime (SAR)

This module provides middleware for workflow execution and management
with proper tenant isolation and security measures.
"""
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp
from workflow.workflow_service import sar_workflow, WorkflowStatus
from auth.auth_service import get_auth
from tenancy.tenant_service import get_tenant_info
from role_enforcement.rbac_service import sar_rbac
import logging

logger = logging.getLogger(__name__)


class WorkflowEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce workflow access control and tenant isolation"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract user and tenant info from request state
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
        
        # Add workflow context to request state
        request.state.workflow_context = {
            'user_id': user_id,
            'tenant_id': tenant_id
        }
        
        # Process the request
        response = await call_next(request)
        
        return response


class WorkflowAuditMiddleware(BaseHTTPMiddleware):
    """Middleware to audit workflow operations"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Import here to avoid circular imports
        from audit_logging.audit_service import sar_audit
        self.audit_service = sar_audit
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Capture workflow-related information
        path = request.url.path
        method = request.method
        
        # Check if this is a workflow-related endpoint
        if path.startswith('/workflow') or path.startswith('/wf'):
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
            
            # Log the workflow operation
            self.audit_service.log_event(
                event_type=self.audit_service.AuditEventType.API_ACCESS,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=request.client.host if hasattr(request, 'client') else None,
                user_agent=request.headers.get('user-agent'),
                resource="workflow",
                action=method.lower(),
                resource_id=path.split('/')[-1] if path.split('/')[-1] else None,
                metadata={
                    "request_path": path,
                    "request_method": method,
                    "workflow_operation": True
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        return response


def check_workflow_permissions(request: Request, operation: str, workflow_name: Optional[str] = None) -> bool:
    """Check if user has permission to perform workflow operation"""
    auth_info = getattr(request.state, 'auth_info', None)
    tenant_info = getattr(request.state, 'tenant_info', None)
    
    if not auth_info:
        return False
    
    # API key authentication grants full access to workflow operations
    if auth_info.get("type") == "api_key_secret":
        return True
    
    user_id = (auth_info.get("user_id") or 
              auth_info.get("client_id") or 
              auth_info.get("candidate_id"))
    
    user_tenant_id = None
    if tenant_info and hasattr(tenant_info, 'tenant_id'):
        user_tenant_id = tenant_info.tenant_id
    elif auth_info and 'tenant_id' in auth_info:
        user_tenant_id = auth_info['tenant_id']
    
    # Check permissions using the RBAC service
    return sar_rbac.has_permission(
        user_id=user_id,
        resource="workflow",
        action=operation,
        tenant_id=user_tenant_id,
        user_tenant_id=user_tenant_id
    )


def validate_workflow_tenant_access(instance_id: str, request: Request) -> bool:
    """Validate that user has access to the workflow instance"""
    # For API key authentication, grant full access
    auth_info = getattr(request.state, 'auth_info', None)
    if auth_info and auth_info.get("type") == "api_key_secret":
        return True
    
    # Get the workflow instance from memory (sync access)
    instance = sar_workflow._running_workflows.get(instance_id)
    
    if not instance:
        # Instance not found in running workflows, allow access check at route level
        return True
    
    # Get user tenant info
    tenant_info = getattr(request.state, 'tenant_info', None)
    user_tenant_id = None
    if tenant_info and hasattr(tenant_info, 'tenant_id'):
        user_tenant_id = tenant_info.tenant_id
    elif auth_info and 'tenant_id' in auth_info:
        user_tenant_id = auth_info.get('tenant_id')
    
    # If no tenant info, allow access (tenant isolation may be disabled)
    if not user_tenant_id:
        return True
    
    # Validate tenant isolation
    return instance.tenant_id == user_tenant_id


def enrich_workflow_context(request: Request, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enrich workflow context with user and tenant information"""
    context = additional_context or {}
    
    auth_info = getattr(request.state, 'auth_info', None)
    tenant_info = getattr(request.state, 'tenant_info', None)
    
    if auth_info:
        context['user_id'] = (auth_info.get("user_id") or 
                             auth_info.get("client_id") or 
                             auth_info.get("candidate_id"))
    
    if tenant_info and hasattr(tenant_info, 'tenant_id'):
        context['tenant_id'] = tenant_info.tenant_id
    elif auth_info and 'tenant_id' in auth_info:
        context['tenant_id'] = auth_info['tenant_id']
    
    context['timestamp'] = asyncio.run(asyncio.sleep(0)) or datetime.now(timezone.utc).isoformat()
    
    return context


# Import here to avoid circular imports
from datetime import datetime