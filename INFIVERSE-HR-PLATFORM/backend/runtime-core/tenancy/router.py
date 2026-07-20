"""
Sovereign Application Runtime (SAR) - Tenant Router

This module provides a reusable FastAPI router with tenant management endpoints
that can be plugged into any BHIV service.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .tenant_service import sar_tenant_resolver, TenantInfo, TenantType, get_tenant_info
from .middleware import get_tenant_from_request
from auth.auth_service import get_auth, get_api_key
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


router = APIRouter(prefix="/tenants", tags=["Sovereign Tenancy"])


class TenantCreateRequest(BaseModel):
    tenant_id: str
    tenant_type: TenantType
    name: str
    metadata: Optional[Dict[str, Any]] = None


class TenantUpdateRequest(BaseModel):
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/current")
async def get_current_tenant(tenant_info: TenantInfo = Depends(get_tenant_info), auth: dict = Depends(get_auth)):
    """Get information about the current tenant"""
    if not tenant_info:
        raise HTTPException(status_code=400, detail="No tenant information available")
    
    return {
        "tenant": tenant_info.to_dict(),
        "isolation_enabled": sar_tenant_resolver.config.tenant_isolation_enabled,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health")
async def tenant_health_check():
    """Health check for the tenant resolution service"""
    return {
        "status": "healthy",
        "service": "Sovereign Application Runtime - Tenant Resolution Service",
        "features": [
            "Tenant resolution from JWT and headers",
            "Tenant isolation enforcement",
            "Cross-tenant access validation",
            "Tenant-scoped query filtering"
        ],
        "config": {
            "tenant_isolation_enabled": sar_tenant_resolver.config.tenant_isolation_enabled,
            "require_tenant_header": sar_tenant_resolver.config.require_tenant_header,
            "tenant_header_name": sar_tenant_resolver.config.tenant_header_name,
            "default_tenant_id": sar_tenant_resolver.config.default_tenant_id
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/isolation-check/{resource_tenant_id}")
async def check_tenant_access(
    resource_tenant_id: str,
    request: Request,
    tenant_info: TenantInfo = Depends(get_tenant_info),
    auth: dict = Depends(get_auth)
):
    """Check if the current tenant has access to a specific resource"""
    has_access = sar_tenant_resolver.validate_tenant_access(tenant_info, resource_tenant_id)
    
    return {
        "requesting_tenant_id": tenant_info.tenant_id,
        "resource_tenant_id": resource_tenant_id,
        "has_access": has_access,
        "access_granted": has_access,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/query-filter/{table_name}")
async def get_query_filter(
    table_name: str,
    tenant_info: TenantInfo = Depends(get_tenant_info),
    auth: dict = Depends(get_auth)
):
    """Get the SQL query filter for tenant isolation for a specific table"""
    filter_clause = sar_tenant_resolver.get_tenant_isolation_query_filter(tenant_info, table_name)
    
    return {
        "tenant_id": tenant_info.tenant_id,
        "table_name": table_name,
        "filter_clause": filter_clause,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/shared-resource-access/{resource_type}")
async def check_shared_resource_access(
    resource_type: str,
    tenant_info: TenantInfo = Depends(get_tenant_info),
    auth: dict = Depends(get_auth)
):
    """Check if the current tenant has access to shared resources of a specific type"""
    has_access = sar_tenant_resolver.get_shared_resource_access(tenant_info, resource_type)
    
    return {
        "tenant_id": tenant_info.tenant_id,
        "resource_type": resource_type,
        "has_access_to_shared_resource": has_access,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Import datetime for use in the functions
from datetime import datetime, timezone