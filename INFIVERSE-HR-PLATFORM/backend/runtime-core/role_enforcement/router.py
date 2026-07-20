"""
Role-Based Router for Sovereign Application Runtime (SAR)

This module provides a router with role-protected endpoints for the SAR.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from auth.auth_service import get_auth, get_api_key
from tenancy.tenant_service import get_tenant_info
from role_enforcement.rbac_service import sar_rbac, require_permission, get_current_user_permissions
from role_enforcement.middleware import get_user_auth_info, get_user_tenant_info
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


class RoleAssignmentRequest(BaseModel):
    """Request model for role assignment"""
    user_id: str
    role_name: str
    tenant_id: Optional[str] = None


class PermissionCheckRequest(BaseModel):
    """Request model for permission checking"""
    resource: str
    action: str
    tenant_id: Optional[str] = None


class RoleInfo(BaseModel):
    """Response model for role information"""
    name: str
    role_type: str
    description: str
    permissions: List[Dict[str, str]]
    created_at: str


class PermissionInfo(BaseModel):
    """Response model for permission information"""
    resource: str
    action: str
    scope: str


router = APIRouter(prefix="/role", tags=["Role Enforcement"])


@router.get("/health")
async def health_check():
    """Health check endpoint for the role enforcement service"""
    return {
        "status": "healthy",
        "service": "Sovereign Application Runtime - Role Enforcement Service",
        "features": [
            "Role-Based Access Control (RBAC)",
            "Permission Management",
            "Role Assignment",
            "Multi-tenant Role Isolation",
            "Dynamic Permission Checking"
        ],
        "available_roles": list(sar_rbac._roles.keys()),
        "total_assignments": len(sar_rbac._role_assignments),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/assign")
async def assign_role(
    request: RoleAssignmentRequest,
    auth_info: Dict[str, Any] = Depends(get_user_auth_info)
):
    """Assign a role to a user"""
    # API key authentication grants full access to role operations
    if auth_info and auth_info.get("type") == "api_key_secret":
        has_permission = True
    else:
        # Only system admins or users with role management permissions can assign roles
        has_permission = sar_rbac.has_permission(
            user_id=auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id"),
            resource="roles",
            action="assign",
            tenant_id=None,  # Role assignment is a system-level operation
            user_tenant_id=None
        )
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions to assign roles")
    
    try:
        assignment = sar_rbac.assign_role(
            user_id=request.user_id,
            role_name=request.role_name,
            tenant_id=request.tenant_id,
            assigned_by=auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id")
        )
        
        return {
            "success": True,
            "message": f"Role '{request.role_name}' assigned to user '{request.user_id}'",
            "assignment_id": f"{assignment.user_id}_{assignment.role.name}",
            "assigned_at": assignment.assigned_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_roles(
    user_id: str,
    tenant_id: Optional[str] = None,
    auth_info: Dict[str, Any] = Depends(get_user_auth_info)
):
    """Get all roles assigned to a user"""
    # Check if the requesting user has permission to view roles
    requesting_user_id = auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id")
    
    # Users can view their own roles, admins can view any user's roles
    if user_id != requesting_user_id:
        if not sar_rbac.has_permission(
            user_id=requesting_user_id,
            resource="roles",
            action="read",
            tenant_id=tenant_id,
            user_tenant_id=auth_info.get("tenant_id")
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view user roles")
    
    assignments = sar_rbac.get_user_roles(user_id, tenant_id)
    
    role_list = []
    for assignment in assignments:
        role_list.append({
            "role_name": assignment.role.name,
            "role_type": assignment.role.role_type.value,
            "assigned_at": assignment.assigned_at.isoformat(),
            "tenant_id": assignment.tenant_id,
            "assigned_by": assignment.assigned_by
        })
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "roles": role_list,
        "count": len(role_list)
    }


@router.post("/check-permission")
async def check_permission(
    request: PermissionCheckRequest,
    auth_info: Dict[str, Any] = Depends(get_user_auth_info),
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Check if a user has specific permission"""
    user_id = auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id")
    user_tenant_id = tenant_info.tenant_id if tenant_info else auth_info.get("tenant_id")
    
    has_permission = sar_rbac.has_permission(
        user_id=user_id,
        resource=request.resource,
        action=request.action,
        tenant_id=request.tenant_id,
        user_tenant_id=user_tenant_id
    )
    
    return {
        "user_id": user_id,
        "resource": request.resource,
        "action": request.action,
        "tenant_id": request.tenant_id,
        "has_permission": has_permission
    }


@router.get("/permissions")
async def get_user_permissions(
    auth_info: Optional[Dict[str, Any]] = Depends(get_user_auth_info),
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Get all permissions for the current user"""
    if not auth_info:
        return {
            "user_id": None,
            "tenant_id": None,
            "permissions": [],
            "count": 0
        }
    
    user_id = auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id")
    user_tenant_id = tenant_info.tenant_id if tenant_info else auth_info.get("tenant_id")
    
    permissions = sar_rbac.get_user_permissions(user_id, user_tenant_id)
    
    permission_list = []
    for perm in permissions:
        permission_list.append({
            "resource": perm.resource,
            "action": perm.action,
            "scope": perm.scope
        })
    
    return {
        "user_id": user_id,
        "tenant_id": user_tenant_id,
        "permissions": permission_list,
        "count": len(permission_list)
    }


@router.get("/available-roles")
async def get_available_roles(
    auth_info: Optional[Dict[str, Any]] = Depends(get_user_auth_info)
):
    """Get all available roles in the system"""
    # Check if user is authenticated
    if not auth_info:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    # Allow all authenticated users to view available roles
    # In a production system, you might want to restrict this
    
    role_list = []
    for role_name, role in sar_rbac._roles.items():
        if role.is_active:
            permission_list = []
            for perm in role.permissions:
                permission_list.append({
                    "resource": perm.resource,
                    "action": perm.action,
                    "scope": perm.scope,
                    "description": perm.description
                })
            
            role_list.append({
                "name": role.name,
                "role_type": role.role_type.value,
                "description": role.description,
                "permissions": permission_list,
                "created_at": role.created_at.isoformat(),
                "is_active": role.is_active
            })
    
    return {
        "roles": role_list,
        "count": len(role_list)
    }


@router.get("/current")
async def get_current_user_info(
    auth_info: Optional[Dict[str, Any]] = Depends(get_user_auth_info),
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Get information about the current authenticated user and their permissions"""
    if not auth_info or not auth_info.get("user_id") and not auth_info.get("client_id") and not auth_info.get("candidate_id"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id")
    user_tenant_id = tenant_info.tenant_id if tenant_info else auth_info.get("tenant_id")
    
    # Get user roles
    user_assignments = sar_rbac.get_user_roles(user_id, user_tenant_id)
    roles = []
    for assignment in user_assignments:
        roles.append({
            "role_name": assignment.role.name,
            "role_type": assignment.role.role_type.value,
            "assigned_at": assignment.assigned_at.isoformat()
        })
    
    # Get user permissions
    permissions = sar_rbac.get_user_permissions(user_id, user_tenant_id)
    permission_list = []
    for perm in permissions:
        permission_list.append({
            "resource": perm.resource,
            "action": perm.action,
            "scope": perm.scope
        })
    
    return {
        "user_info": auth_info,
        "tenant_info": tenant_info.to_dict() if tenant_info else None,
        "roles": roles,
        "permissions": permission_list,
        "timestamp": datetime.now().isoformat()
    }


# Example protected endpoints using role enforcement
@router.get("/protected-example")
@require_permission(resource="system", action="read")
async def protected_example_endpoint(
    auth_info: Optional[Dict[str, Any]] = Depends(get_user_auth_info)
):
    """Example of a protected endpoint that requires specific permissions"""
    return {
        "message": "This is a protected endpoint",
        "user_id": auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id"),
        "access_granted": True
    }


@router.post("/admin-only")
@require_permission(resource="admin", action="create")
async def admin_only_endpoint(
    request: Request,
    auth_info: Optional[Dict[str, Any]] = Depends(get_user_auth_info)
):
    """Example of an admin-only endpoint"""
    return {
        "message": "Admin-only operation successful",
        "user_id": auth_info.get("user_id") or auth_info.get("client_id") or auth_info.get("candidate_id"),
        "operation": "admin_task"
    }