"""
Integration Module for Sovereign Application Runtime (SAR) Role Enforcement

This module provides integration between role enforcement, authentication, and tenant services.
"""
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Depends
from ..auth.auth_service import sar_auth, get_current_user
from ..tenancy.tenant_service import sar_tenant_resolver, get_tenant_info
from .rbac_service import sar_rbac, RoleType


def integrate_role_auth_tenant():
    """
    Initialize integration between role enforcement, authentication, and tenant services.
    
    This function sets up the necessary connections and configurations to ensure
    proper coordination between the three core SAR services.
    """
    # Verify that all services are properly initialized
    services = {
        "authentication": sar_auth,
        "tenant_resolver": sar_tenant_resolver,
        "role_enforcement": sar_rbac
    }
    
    for name, service in services.items():
        if service is None:
            raise ValueError(f"Service {name} not properly initialized")
    
    print("SAR Integration: All services initialized successfully")
    print(f"Authentication service: {type(sar_auth).__name__}")
    print(f"Tenant resolver service: {type(sar_tenant_resolver).__name__}")
    print(f"Role enforcement service: {type(sar_rbac).__name__}")


def get_enriched_auth_context(request: Request) -> Dict[str, Any]:
    """
    Get an enriched authentication context that includes role and tenant information.
    
    This function combines information from authentication, tenant resolution, and role enforcement
    to provide a comprehensive security context for the request.
    """
    # Get basic authentication info
    auth_info = getattr(request.state, 'auth_info', None)
    if not auth_info:
        # Try to extract from headers if not in state
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            auth_info = sar_auth.get_auth_from_token(token)
    
    if not auth_info:
        return {"authenticated": False}
    
    # Get tenant info
    tenant_info = getattr(request.state, 'tenant_info', None)
    if not tenant_info:
        tenant_info = sar_tenant_resolver.resolve_tenant(request)
    
    # Get user roles
    user_id = (auth_info.get("user_id") or 
              auth_info.get("client_id") or 
              auth_info.get("candidate_id"))
    
    if user_id:
        user_roles = sar_rbac.get_user_roles(
            user_id, 
            tenant_info.tenant_id if tenant_info else None
        )
    else:
        user_roles = []
    
    # Build enriched context
    context = {
        "authenticated": True,
        "auth_info": auth_info,
        "tenant_info": tenant_info.to_dict() if tenant_info else None,
        "user_roles": [ra.role.name for ra in user_roles],
        "user_permissions": [],
        "tenant_isolation_enabled": sar_tenant_resolver.config.tenant_isolation_enabled if sar_tenant_resolver.config else False
    }
    
    # Get user permissions if we have user_id and tenant_info
    if user_id:
        permissions = sar_rbac.get_user_permissions(
            user_id, 
            tenant_info.tenant_id if tenant_info else None
        )
        context["user_permissions"] = [
            {"resource": p.resource, "action": p.action, "scope": p.scope} 
            for p in permissions
        ]
    
    return context


def validate_cross_service_access(request: Request, required_resource: str, required_action: str) -> bool:
    """
    Validate access across authentication, tenant, and role services.
    
    This function performs comprehensive access validation by checking:
    1. Authentication status
    2. Tenant isolation compliance
    3. Role-based permissions
    """
    # Get the enriched authentication context
    auth_context = get_enriched_auth_context(request)
    
    if not auth_context.get("authenticated"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Extract necessary information
    auth_info = auth_context.get("auth_info", {})
    tenant_info = auth_context.get("tenant_info")
    
    user_id = (auth_info.get("user_id") or 
              auth_info.get("client_id") or 
              auth_info.get("candidate_id"))
    
    # Check if this is an API key authentication (which has full access)
    if auth_info.get("type") == "api_key_secret":
        return True
    
    # If tenant isolation is enabled, verify tenant compliance
    if (auth_context.get("tenant_isolation_enabled") and 
        tenant_info and 
        required_resource in ["jobs", "candidates", "feedback", "interviews", "offers"]):
        
        # Extract tenant ID from request path or parameters if needed
        # This would typically come from the route parameters or request body
        request_tenant_id = _extract_tenant_id_from_request(request, required_resource)
        
        if request_tenant_id and tenant_info.get("tenant_id") != request_tenant_id:
            raise HTTPException(
                status_code=403, 
                detail="Tenant isolation violation: Cannot access cross-tenant resources"
            )
    
    # Check role-based permissions
    user_tenant_id = tenant_info.get("tenant_id") if tenant_info else auth_info.get("tenant_id")
    
    has_permission = sar_rbac.has_permission(
        user_id=user_id,
        resource=required_resource,
        action=required_action,
        tenant_id=tenant_info.get("tenant_id") if tenant_info else None,
        user_tenant_id=user_tenant_id
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=403, 
            detail=f"Insufficient permissions to {required_action} {required_resource}"
        )
    
    return True


def _extract_tenant_id_from_request(request: Request, resource_type: str) -> Optional[str]:
    """
    Extract tenant ID from request based on resource type.
    
    This helper function looks for tenant identifiers in different parts of the request
    depending on the resource type.
    """
    # Look for tenant ID in path parameters (common for REST APIs)
    if hasattr(request, 'path_params'):
        # Common patterns for tenant identification in paths
        for param_name in ['tenant_id', 'client_id', 'company_id']:
            if param_name in request.path_params:
                return request.path_params[param_name]
    
    # Look for tenant ID in query parameters
    if hasattr(request, 'query_params'):
        for param_name in ['tenant_id', 'client_id', 'company_id']:
            if param_name in request.query_params:
                return request.query_params[param_name]
    
    # For specific resource types, extract from path
    if resource_type in ["jobs", "candidates", "feedback"] and len(request.url.path.split('/')) > 3:
        path_parts = request.url.path.split('/')
        # Look for patterns like /v1/tenant/{tenant_id}/jobs/{job_id}
        for i, part in enumerate(path_parts):
            if part in ['tenant', 'client', 'company'] and i + 1 < len(path_parts):
                return path_parts[i + 1]
    
    # If no tenant ID found in request, return None
    return None


def setup_role_dependent_auth():
    """
    Set up authentication dependencies that take roles into account.
    
    This function creates authentication dependencies that automatically
    check role permissions based on the endpoint requirements.
    """
    def auth_with_role_check(required_role: Optional[str] = None, 
                           required_permission: Optional[Dict[str, str]] = None):
        """
        Create an authentication dependency with optional role or permission checks.
        """
        async def dependency(request: Request):
            # First, ensure basic authentication
            auth_context = get_enriched_auth_context(request)
            
            if not auth_context.get("authenticated"):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # If a specific role is required, check it
            if required_role:
                user_roles = auth_context.get("user_roles", [])
                if required_role not in user_roles:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Required role '{required_role}' not granted"
                    )
            
            # If a specific permission is required, check it
            if required_permission:
                resource = required_permission.get("resource")
                action = required_permission.get("action")
                
                if resource and action:
                    validate_cross_service_access(request, resource, action)
            
            # Return the authentication context for use in the endpoint
            return auth_context
        
        return dependency
    
    return auth_with_role_check


def apply_tenant_isolation_policy(request: Request, resource_tenant_id: Optional[str] = None):
    """
    Apply tenant isolation policy to ensure data separation.
    
    This function enforces tenant isolation by checking that users can only
    access resources belonging to their own tenant.
    """
    auth_context = get_enriched_auth_context(request)
    
    if not auth_context.get("authenticated"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # API key users have system-level access and bypass tenant isolation
    auth_info = auth_context.get("auth_info", {})
    if auth_info.get("type") == "api_key_secret":
        return True
    
    # If tenant isolation is disabled, allow access
    if not auth_context.get("tenant_isolation_enabled"):
        return True
    
    # Get the user's tenant ID
    user_tenant_id = None
    if auth_context.get("tenant_info"):
        user_tenant_id = auth_context["tenant_info"].get("tenant_id")
    elif auth_info.get("tenant_id"):
        user_tenant_id = auth_info["tenant_id"]
    
    # If no user tenant ID, deny access (untenanted access not allowed)
    if not user_tenant_id:
        raise HTTPException(
            status_code=403, 
            detail="Tenant information required for access"
        )
    
    # If no resource tenant ID provided, assume it belongs to user's tenant
    if not resource_tenant_id:
        return True
    
    # Check if user's tenant matches resource tenant
    if user_tenant_id != resource_tenant_id:
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied: Resource belongs to tenant {resource_tenant_id}, "
                   f"but user belongs to tenant {user_tenant_id}"
        )
    
    return True


# Initialize the integration when module is loaded
integrate_role_auth_tenant()

# Create a reusable authentication dependency with role checking
auth_with_role_check = setup_role_dependent_auth()