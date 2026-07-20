"""
Integration Module for Sovereign Application Runtime (SAR) Audit Logging

This module provides integration between audit logging and other SAR services
for comprehensive provenance tracking.
"""
from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
import asyncio
from ..auth.auth_service import get_auth, AuthResult
from ..tenancy.tenant_service import sar_tenant_resolver
from ..role_enforcement.rbac_service import sar_rbac
from .audit_service import sar_audit, AuditEventType
from .middleware import AuditLoggingMiddleware, DetailedAuditMiddleware
import logging

logger = logging.getLogger(__name__)


def integrate_audit_with_auth():
    """Integrate audit logging with authentication service"""
    # Enhance the authentication service with audit capabilities
    
    # Store original auth method
    original_get_auth = get_auth
    
    def audited_get_auth(request: Request) -> AuthResult:
        """Authentication method with audit logging"""
        client_ip = request.client.host if hasattr(request, 'client') else None
        user_agent = request.headers.get('user-agent')
        
        try:
            result = original_get_auth(request)
            
            # Log successful authentication
            if result.success:
                user_id = (result.user_id or result.client_id or result.candidate_id)
                sar_audit.log_event(
                    event_type=AuditEventType.USER_LOGIN,
                    user_id=user_id,
                    tenant_id=getattr(result, 'tenant_id', None),
                    client_ip=client_ip,
                    user_agent=user_agent,
                    resource="authentication",
                    action="login",
                    success=True,
                    metadata={
                        "auth_method": "api_key" if result.user_id else "jwt",
                        "client_id": result.client_id,
                        "candidate_id": result.candidate_id
                    }
                )
            
            return result
        except Exception as e:
            # Log failed authentication
            sar_audit.log_event(
                event_type=AuditEventType.USER_LOGIN,
                client_ip=client_ip,
                user_agent=user_agent,
                resource="authentication",
                action="login",
                success=False,
                error_message=str(e)
            )
            raise e
    
    # Replace the auth method
    get_auth = audited_get_auth


def integrate_audit_with_tenant():
    """Integrate audit logging with tenant resolution service"""
    # Enhance tenant operations with audit capabilities
    
    # Store original tenant validation method
    original_validate_tenant = sar_tenant_resolver.validate_tenant_access
    
    def audited_validate_tenant(tenant_info, resource_tenant_id):
        """Tenant validation with audit logging"""
        try:
            result = original_validate_tenant(tenant_info, resource_tenant_id)
            
            # Log tenant access validation
            sar_audit.log_event(
                event_type=AuditEventType.TENANT_ACCESS,
                user_id=tenant_info.user_id if hasattr(tenant_info, 'user_id') else None,
                tenant_id=tenant_info.tenant_id if hasattr(tenant_info, 'tenant_id') else None,
                resource="tenant",
                action="validate_access",
                resource_id=resource_tenant_id,
                success=result,
                metadata={
                    "requested_tenant_id": resource_tenant_id,
                    "user_tenant_id": tenant_info.tenant_id if hasattr(tenant_info, 'tenant_id') else None
                }
            )
            
            return result
        except Exception as e:
            # Log validation failure
            sar_audit.log_event(
                event_type=AuditEventType.TENANT_ACCESS,
                user_id=tenant_info.user_id if hasattr(tenant_info, 'user_id') else None,
                tenant_id=tenant_info.tenant_id if hasattr(tenant_info, 'tenant_id') else None,
                resource="tenant",
                action="validate_access",
                resource_id=resource_tenant_id,
                success=False,
                error_message=str(e)
            )
            raise e
    
    # Replace the validation method
    sar_tenant_resolver.validate_tenant_access = audited_validate_tenant


def integrate_audit_with_role_enforcement():
    """Integrate audit logging with role enforcement service"""
    # Enhance role operations with audit capabilities
    
    # Store original permission check method
    original_has_permission = sar_rbac.has_permission
    
    def audited_has_permission(user_id: str, resource: str, action: str, 
                              tenant_id: Optional[str] = None, 
                              user_tenant_id: Optional[str] = None) -> bool:
        """Permission check with audit logging"""
        try:
            result = original_has_permission(user_id, resource, action, tenant_id, user_tenant_id)
            
            # Log permission check
            sar_audit.log_event(
                event_type=AuditEventType.PERMISSION_CHANGE,
                user_id=user_id,
                tenant_id=user_tenant_id,
                resource=resource,
                action=f"check_permission_{action}",
                success=result,
                metadata={
                    "requested_action": action,
                    "requested_resource": resource,
                    "tenant_id": tenant_id,
                    "user_tenant_id": user_tenant_id
                }
            )
            
            return result
        except Exception as e:
            # Log permission check failure
            sar_audit.log_event(
                event_type=AuditEventType.PERMISSION_CHANGE,
                user_id=user_id,
                tenant_id=user_tenant_id,
                resource=resource,
                action=f"check_permission_{action}",
                success=False,
                error_message=str(e)
            )
            raise e
    
    # Replace the permission check method
    sar_rbac.has_permission = audited_has_permission


def create_audited_endpoint(endpoint_func: Callable, resource: str, action: str):
    """Decorator to create an endpoint with automatic audit logging"""
    async def wrapper(*args, **kwargs):
        # Extract request from arguments (typically the first argument if it's a Request object)
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        # Extract user and tenant info
        user_id = None
        tenant_id = None
        
        if request:
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
        
        client_ip = request.client.host if request and hasattr(request, 'client') else None
        user_agent = request.headers.get('user-agent') if request else None
        
        try:
            # Execute the original endpoint
            result = await endpoint_func(*args, **kwargs) if asyncio.iscoroutinefunction(endpoint_func) else endpoint_func(*args, **kwargs)
            
            # Log successful operation
            sar_audit.log_event(
                event_type=AuditEventType.API_ACCESS,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=client_ip,
                user_agent=user_agent,
                resource=resource,
                action=action,
                success=True,
                metadata={
                    "endpoint_function": endpoint_func.__name__,
                    "resource": resource,
                    "action": action
                }
            )
            
            return result
        except Exception as e:
            # Log failed operation
            sar_audit.log_event(
                event_type=AuditEventType.API_ACCESS,
                user_id=user_id,
                tenant_id=tenant_id,
                client_ip=client_ip,
                user_agent=user_agent,
                resource=resource,
                action=action,
                success=False,
                error_message=str(e),
                metadata={
                    "endpoint_function": endpoint_func.__name__,
                    "resource": resource,
                    "action": action
                }
            )
            raise e
    
    return wrapper


def setup_comprehensive_audit_trail():
    """Setup comprehensive audit trail across all SAR services"""
    # Integrate audit logging with all services
    integrate_audit_with_auth()
    integrate_audit_with_tenant()
    integrate_audit_with_role_enforcement()
    
    print("SAR Integration: Audit logging successfully integrated with all services")
    print(f"Authentication service: {type(sar_auth).__name__}")
    print(f"Tenant resolver service: {type(sar_tenant_resolver).__name__}")
    print(f"Role enforcement service: {type(sar_rbac).__name__}")
    print(f"Audit logging service: {type(sar_audit).__name__}")


def log_provenance_event(operation: str, user_id: str, tenant_id: str, 
                        resource_type: str, resource_id: str,
                        old_values: Optional[Dict[str, Any]] = None,
                        new_values: Optional[Dict[str, Any]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log a provenance tracking event for data lineage"""
    return sar_audit.log_event(
        event_type=AuditEventType.DATA_MODIFICATION,
        user_id=user_id,
        tenant_id=tenant_id,
        resource=resource_type,
        action=operation,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        metadata=metadata or {}
    )


def get_comprehensive_audit_trail(resource_type: str, resource_id: str, 
                                 tenant_id: str, include_related: bool = False) -> Dict[str, Any]:
    """Get a comprehensive audit trail for a resource with provenance tracking"""
    # Get the main audit trail for the resource
    main_events = sar_audit.get_events({
        "resource": resource_type,
        "resource_id": resource_id,
        "tenant_id": tenant_id
    }, limit=1000)
    
    result = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "tenant_id": tenant_id,
        "events": [event.to_dict() for event in main_events],
        "provenance_map": {},
        "related_resources": []
    }
    
    # If requested, also get related resources (for complete provenance tracking)
    if include_related:
        # This would include related resources that were affected by operations on this resource
        # In a real implementation, this would require maintaining relationships between resources
        pass
    
    return result


def log_security_incident(user_id: Optional[str], tenant_id: Optional[str], 
                         incident_type: str, description: str, 
                         severity: str = "high", client_ip: Optional[str] = None) -> bool:
    """Log a security incident with full provenance tracking"""
    return sar_audit.log_security_event(
        event_subtype=f"security_incident_{incident_type}",
        user_id=user_id,
        tenant_id=tenant_id,
        client_ip=client_ip,
        description=description,
        severity=severity
    )


def log_config_change(user_id: str, tenant_id: str, config_key: str, 
                     old_value: Any, new_value: Any, 
                     change_reason: str = "") -> bool:
    """Log configuration changes with provenance tracking"""
    return sar_audit.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        user_id=user_id,
        tenant_id=tenant_id,
        resource="configuration",
        action="update",
        resource_id=config_key,
        old_values={"value": old_value} if old_value is not None else None,
        new_values={"value": new_value} if new_value is not None else None,
        metadata={"change_reason": change_reason},
        success=True
    )


# Initialize the audit integration when module is loaded
setup_comprehensive_audit_trail()


# Create a function to add audit middleware to FastAPI apps
def add_audit_middleware(app, detailed: bool = False):
    """Add audit logging middleware to a FastAPI application"""
    if detailed:
        app.add_middleware(DetailedAuditMiddleware)
    else:
        app.add_middleware(AuditLoggingMiddleware)
    
    return app