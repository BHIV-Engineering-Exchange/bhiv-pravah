"""
Role Enforcement Middleware for Sovereign Application Runtime (SAR)

This module provides middleware for role-based access control enforcement
at the request level, ensuring proper authorization before processing requests.
"""
from typing import Callable, Optional, Dict, Any
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from auth.auth_service import get_auth, sar_auth
from tenancy.tenant_service import sar_tenant_resolver, get_tenant_info
from role_enforcement.rbac_service import sar_rbac
import jwt
import os
import logging

logger = logging.getLogger(__name__)


class RoleEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce role-based access control for requests"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract authentication info using the new get_auth function
        auth_info = None
        
        try:
            # Use the unified authentication function from auth_service
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # Create a mock credentials object for the get_auth function
                from fastapi.security import HTTPAuthorizationCredentials
                credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                auth_info = get_auth(credentials)
        except Exception as e:
            logger.warning(f"Failed to authenticate request: {e}")
            # Continue without auth info
            pass
        
        # Store auth info in request state for later use
        request.state.auth_info = auth_info
        
        # Try to resolve tenant information
        tenant_info = None
        try:
            tenant_info = await get_tenant_info(request)
            request.state.tenant_info = tenant_info
        except Exception as e:
            # If tenant resolution fails, continue without tenant info
            logger.warning(f"Failed to resolve tenant: {e}")
            request.state.tenant_info = None
        
        # Store auth info in request state for later use
        request.state.auth_info = auth_info
        
        # Try to resolve tenant information
        tenant_info = None
        try:
            tenant_info = sar_tenant_resolver.resolve_tenant(request)
            request.state.tenant_info = tenant_info
        except Exception:
            # If tenant resolution fails, continue without tenant info
            request.state.tenant_info = None
        
        # Perform role enforcement based on the endpoint
        await self._enforce_role_access(request, auth_info, tenant_info)
        
        # Continue with the request
        response = await call_next(request)
        return response
    
    async def _enforce_role_access(self, request: Request, auth_info: Optional[Dict], 
                                 tenant_info: Optional[Any]):
        """Enforce role-based access control for the request"""
        # Get the endpoint path
        path = request.url.path
        method = request.method
        
        # Skip role enforcement for public endpoints
        public_endpoints = [
            "/",
            "/health",
            "/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/health",
            "/auth/password",
            "/candidate/register",
            "/candidate/login",
            "/tenants/health",
            "/role/health",
            "/audit/health",
            "/workflow/health"
        ]
        
        if any(path.startswith(endpoint) for endpoint in public_endpoints):
            return
        
        # If no authentication info, deny access to protected endpoints
        if not auth_info:
            # For SAR management endpoints, let the endpoint handle auth
            if path.startswith("/role/") or path.startswith("/audit/") or path.startswith("/workflow/") or path.startswith("/tenants/"):
                return
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Determine resource and action based on the endpoint
        resource, action = self._map_endpoint_to_resource(path, method)
        
        # If we couldn't map the endpoint, allow it to proceed to individual endpoint validation
        if not resource or not action:
            return
        
        # Check if the user has permission to access this resource with this action
        user_id = (auth_info.get("user_id") or 
                  auth_info.get("client_id") or 
                  auth_info.get("candidate_id"))
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Get the user's tenant ID
        user_tenant_id = auth_info.get("tenant_id")
        
        # For tenant-scoped resources, ensure tenant isolation
        if tenant_info and user_tenant_id:
            # Check if this is a tenant-scoped operation
            if self._is_tenant_scoped_resource(resource):
                # Ensure the user's tenant matches the requested tenant context
                if user_tenant_id != tenant_info.tenant_id:
                    raise HTTPException(
                        status_code=403, 
                        detail="Access denied: Cross-tenant operation not allowed"
                    )
        
        # Check permissions using the RBAC service
        has_permission = sar_rbac.has_permission(
            user_id=user_id,
            resource=resource,
            action=action,
            tenant_id=tenant_info.tenant_id if tenant_info else None,
            user_tenant_id=user_tenant_id
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=403, 
                detail=f"Insufficient permissions to {action} {resource}"
            )
    
    def _map_endpoint_to_resource(self, path: str, method: str) -> tuple[Optional[str], Optional[str]]:
        """Map an endpoint path and method to a resource and action"""
        # Define endpoint to resource mappings
        endpoint_mappings = {
            # Job Management
            "/v1/jobs": {"resource": "jobs", "action": method.lower()},
            "/v1/jobs/": {"resource": "jobs", "action": method.lower()},
            
            # Candidate Management
            "/v1/candidates": {"resource": "candidates", "action": method.lower()},
            "/v1/candidates/": {"resource": "candidates", "action": method.lower()},
            
            # Feedback Management
            "/v1/feedback": {"resource": "feedback", "action": method.lower()},
            "/v1/feedback/": {"resource": "feedback", "action": method.lower()},
            
            # Interview Management
            "/v1/interviews": {"resource": "interviews", "action": method.lower()},
            "/v1/interviews/": {"resource": "interviews", "action": method.lower()},
            
            # Offer Management
            "/v1/offers": {"resource": "offers", "action": method.lower()},
            "/v1/offers/": {"resource": "offers", "action": method.lower()},
            
            # Analytics
            "/v1/analytics": {"resource": "analytics", "action": method.lower()},
            "/v1/analytics/": {"resource": "analytics", "action": method.lower()},
            
            # Client Portal
            "/v1/client": {"resource": "clients", "action": method.lower()},
            "/v1/client/": {"resource": "clients", "action": method.lower()},
            
            # Candidate Portal
            "/v1/candidate": {"resource": "candidates", "action": method.lower()},
            "/v1/candidate/": {"resource": "candidates", "action": method.lower()},
            
            # Security
            "/v1/security": {"resource": "security", "action": method.lower()},
            "/v1/security/": {"resource": "security", "action": method.lower()},
        }
        
        # Check for exact matches first
        if path in endpoint_mappings:
            mapping = endpoint_mappings[path]
            return mapping["resource"], mapping["action"]
        
        # Check for prefix matches
        for endpoint, mapping in endpoint_mappings.items():
            if path.startswith(endpoint):
                # Determine action based on HTTP method
                action = self._get_action_from_method(method, path)
                return mapping["resource"], action
        
        # If no mapping found, return None to allow endpoint-level validation
        return None, None
    
    def _get_action_from_method(self, method: str, path: str) -> str:
        """Determine the action based on HTTP method and path"""
        method_lower = method.lower()
        
        # Map standard HTTP methods to actions
        method_to_action = {
            "get": "read",
            "post": "create",
            "put": "update",
            "patch": "update",
            "delete": "delete"
        }
        
        return method_to_action.get(method_lower, "access")
    
    def _is_tenant_scoped_resource(self, resource: str) -> bool:
        """Check if a resource is tenant-scoped"""
        tenant_scoped_resources = {
            "jobs", "candidates", "feedback", "interviews", "offers", 
            "applications", "profiles", "documents"
        }
        return resource in tenant_scoped_resources


def get_user_auth_info(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency function to get user authentication info from request state"""
    if hasattr(request.state, 'auth_info'):
        return request.state.auth_info
    return None


def get_user_tenant_info(request: Request) -> Optional[Any]:
    """Dependency function to get user tenant info from request state"""
    if hasattr(request.state, 'tenant_info'):
        return request.state.tenant_info
    return None