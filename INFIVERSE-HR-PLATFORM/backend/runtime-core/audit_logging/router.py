"""
Audit Logging Router for Sovereign Application Runtime (SAR)

This module provides endpoints for audit log management and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from audit_logging.audit_service import sar_audit, AuditEventType, AuditEvent
from auth.auth_service import get_auth, AuthResult
from tenancy.tenant_service import get_tenant_info
from role_enforcement.rbac_service import require_permission
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuditFilter(BaseModel):
    """Request model for audit log filtering"""
    event_type: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    success: Optional[bool] = None


class AuditEventResponse(BaseModel):
    """Response model for audit events"""
    event_id: str
    event_type: str
    timestamp: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    client_ip: Optional[str]
    resource: str
    action: str
    resource_id: Optional[str]
    success: bool
    metadata: Optional[Dict[str, Any]]


class AuditLogResponse(BaseModel):
    """Response model for audit log queries"""
    events: List[AuditEventResponse]
    total: int
    limit: int
    offset: int


class AuditEventRequest(BaseModel):
    """Request model for logging audit events"""
    event_type: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    resource: str
    action: str
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


router = APIRouter(prefix="/audit", tags=["Audit Logging"])


@router.post("/logs", response_model=Dict[str, Any])
async def log_audit_event(
    request: Request,
    event_data: AuditEventRequest,
    auth: AuthResult = Depends(get_auth)
):
    """Log an audit event - matches services pattern"""
    try:
        # Extract user and tenant info
        user_id = (auth.user_id or auth.client_id or auth.candidate_id)
        tenant_id = auth.tenant_id if hasattr(auth, 'tenant_id') else None
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Validate event type
        try:
            event_type = AuditEventType(event_data.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_data.event_type}")
        
        # Log the event
        success = sar_audit.log_event(
            event_type=event_type,
            user_id=user_id or event_data.user_id,
            tenant_id=tenant_id or event_data.tenant_id,
            client_ip=client_ip,
            resource=event_data.resource,
            action=event_data.action,
            resource_id=event_data.resource_id,
            metadata=event_data.metadata,
            success=event_data.success,
            error_message=event_data.error_message
        )
        
        if success:
            logger.info(f"✅ Audit event logged: {event_type.value} - {event_data.resource}")
            return {
                "status": "success",
                "message": "Audit event logged successfully",
                "event_type": event_type.value,
                "resource": event_data.resource,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"❌ Failed to log audit event: {event_type.value}")
            raise HTTPException(status_code=500, detail="Failed to log audit event")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error logging audit event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/events", response_model=AuditLogResponse)
async def get_audit_events(
    request: Request,
    filter_params: AuditFilter = Depends(),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Retrieve audit events with optional filtering"""
    # Build filters from query parameters
    filters = {}
    
    if filter_params.event_type:
        try:
            filters["event_type"] = AuditEventType(filter_params.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {filter_params.event_type}")
    
    if filter_params.user_id:
        filters["user_id"] = filter_params.user_id
    
    if filter_params.tenant_id:
        filters["tenant_id"] = filter_params.tenant_id
    elif tenant_info and tenant_info.tenant_id:
        # If no tenant filter provided but tenant info is available, filter by current tenant
        # This ensures tenant isolation
        filters["tenant_id"] = tenant_info.tenant_id
    
    if filter_params.resource:
        filters["resource"] = filter_params.resource
    
    if filter_params.action:
        filters["action"] = filter_params.action
    
    if filter_params.success is not None:
        filters["success"] = filter_params.success
    
    # Apply date filtering if needed
    events = sar_audit.get_events(filters=filters, limit=limit, offset=offset)
    
    # Convert to response format
    event_responses = []
    for event in events:
        event_responses.append(AuditEventResponse(
            event_id=event.event_id,
            event_type=event.event_type.value,
            timestamp=event.timestamp.isoformat(),
            user_id=event.user_id,
            tenant_id=event.tenant_id,
            client_ip=event.client_ip,
            resource=event.resource,
            action=event.action,
            resource_id=event.resource_id,
            success=event.success,
            metadata=event.metadata
        ))
    
    return AuditLogResponse(
        events=event_responses,
        total=len(event_responses),  # In a real implementation, this would be the actual total count
        limit=limit,
        offset=offset
    )


@router.get("/events/{event_id}")
async def get_audit_event_by_id(
    event_id: str,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Retrieve a specific audit event by ID"""
    event = sar_audit.get_event_by_id(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Audit event not found")
    
    # Apply tenant isolation - only allow access to events from the current tenant
    if (tenant_info and tenant_info.tenant_id and 
        event.tenant_id and event.tenant_id != tenant_info.tenant_id):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access cross-tenant audit events")
    
    return AuditEventResponse(
        event_id=event.event_id,
        event_type=event.event_type.value,
        timestamp=event.timestamp.isoformat(),
        user_id=event.user_id,
        tenant_id=event.tenant_id,
        client_ip=event.client_ip,
        resource=event.resource,
        action=event.action,
        resource_id=event.resource_id,
        success=event.success,
        metadata=event.metadata
    )


@router.get("/trail/{resource}/{resource_id}")
async def get_resource_audit_trail(
    resource: str,
    resource_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Get the complete audit trail for a specific resource"""
    # Apply tenant isolation
    tenant_id = tenant_info.tenant_id if tenant_info else None
    
    filters = {
        "resource": resource,
        "resource_id": resource_id
    }
    
    if tenant_id:
        filters["tenant_id"] = tenant_id
    
    events = sar_audit.get_events(filters=filters, limit=limit, offset=offset)
    
    event_responses = []
    for event in events:
        event_responses.append(AuditEventResponse(
            event_id=event.event_id,
            event_type=event.event_type.value,
            timestamp=event.timestamp.isoformat(),
            user_id=event.user_id,
            tenant_id=event.tenant_id,
            client_ip=event.client_ip,
            resource=event.resource,
            action=event.action,
            resource_id=event.resource_id,
            success=event.success,
            metadata=event.metadata
        ))
    
    return AuditLogResponse(
        events=event_responses,
        total=len(event_responses),
        limit=limit,
        offset=offset
    )


@router.get("/stats")
async def get_audit_statistics(
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Get audit log statistics"""
    # For now, return basic statistics
    # In a real implementation, this would query aggregated statistics from storage
    
    tenant_id = tenant_info.tenant_id if tenant_info else None
    
    # This is a simplified implementation - in real usage, you'd need to implement
    # aggregation queries against your audit storage backend
    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    
    events = sar_audit.get_events(filters=filters, limit=1000, offset=0)
    
    # Count event types
    event_type_counts = {}
    user_activity = {}
    daily_activity = {}
    
    for event in events:
        # Count event types
        event_type = event.event_type.value
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Track user activity
        if event.user_id:
            user_activity[event.user_id] = user_activity.get(event.user_id, 0) + 1
        
        # Track daily activity
        day = event.timestamp.strftime("%Y-%m-%d")
        daily_activity[day] = daily_activity.get(day, 0) + 1
    
    return {
        "total_events": len(events),
        "event_type_breakdown": event_type_counts,
        "active_users": len(user_activity),
        "top_users": sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10],
        "daily_activity": daily_activity,
        "tenant_id": tenant_id,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/log-custom")
async def log_custom_audit_event(
    request: Request,
    event_type: str,
    resource: str,
    action: str,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Log a custom audit event"""
    try:
        audit_event_type = AuditEventType(event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    # Extract user info from request state
    user_id = None
    auth_info = getattr(request.state, 'auth_info', None)
    if auth_info:
        user_id = (auth_info.get("user_id") or 
                  auth_info.get("client_id") or 
                  auth_info.get("candidate_id"))
    
    tenant_id = tenant_info.tenant_id if tenant_info else None
    
    success = sar_audit.log_event(
        event_type=audit_event_type,
        user_id=user_id,
        tenant_id=tenant_id,
        client_ip=request.client.host if hasattr(request, 'client') else None,
        user_agent=request.headers.get('user-agent'),
        resource=resource,
        action=action,
        resource_id=resource_id,
        metadata=metadata
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log audit event")
    
    return {
        "success": True,
        "message": "Audit event logged successfully",
        "resource": resource,
        "action": action
    }


@router.get("/health")
async def audit_health_check():
    """Health check for the audit logging system"""
    return {
        "status": "healthy",
        "enabled": sar_audit.config.enabled,
        "storage_backend": sar_audit.config.storage_backend,
        "async_writes": sar_audit.config.async_writes,
        "timestamp": datetime.utcnow().isoformat()
    }


# Example of how to use audit logging in application endpoints
@router.get("/example-protected-endpoint")
async def example_protected_endpoint(
    request: Request,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Example endpoint that demonstrates audit logging integration"""
    # Extract user info
    user_id = None
    auth_info = getattr(request.state, 'auth_info', None)
    if auth_info:
        user_id = (auth_info.get("user_id") or 
                  auth_info.get("client_id") or 
                  auth_info.get("candidate_id"))
    
    tenant_id = tenant_info.tenant_id if tenant_info else None
    
    # Log access to this protected endpoint
    sar_audit.log_data_access(
        user_id=user_id,
        tenant_id=tenant_id,
        resource="example_endpoint",
        resource_id="protected_data",
        success=True
    )
    
    return {
        "message": "Access granted to protected endpoint",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat()
    }