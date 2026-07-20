"""
Workflow Router for Sovereign Application Runtime (SAR)

This module provides endpoints for workflow management and execution.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from workflow.workflow_service import sar_workflow, WorkflowStatus, TaskStatus, WorkflowInstance, WorkflowDefinition
from auth.auth_service import get_auth, get_api_key
from tenancy.tenant_service import get_tenant_info
from role_enforcement.rbac_service import require_permission
from workflow.middleware import check_workflow_permissions, validate_workflow_tenant_access, enrich_workflow_context
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()


class WorkflowStartRequest(BaseModel):
    """Request model for starting a workflow"""
    workflow_name: str
    parameters: Optional[Dict[str, Any]] = None


class WorkflowTaskResponse(BaseModel):
    """Response model for workflow tasks"""
    task_id: str
    name: str
    status: str
    result: Optional[Any]
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class WorkflowInstanceResponse(BaseModel):
    """Response model for workflow instances"""
    instance_id: str
    workflow_name: str
    tenant_id: str
    user_id: str
    status: str
    tasks: List[WorkflowTaskResponse]
    context: Dict[str, Any]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


class WorkflowDefinitionRequest(BaseModel):
    """Request model for workflow definition"""
    name: str
    description: str
    tasks: List[Dict[str, Any]]


router = APIRouter(prefix="/workflow", tags=["Workflow Engine"])


@router.post("/start")
async def start_workflow(
    request: Request,
    workflow_request: WorkflowStartRequest,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Start a new workflow instance"""
    if not check_workflow_permissions(request, "create", workflow_request.workflow_name):
        raise HTTPException(status_code=403, detail="Insufficient permissions to start workflow")
    
    # Extract user info
    auth_info = getattr(request.state, 'auth_info', None)
    user_id = (auth_info.get("user_id") or 
              auth_info.get("client_id") or 
              auth_info.get("candidate_id"))
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    tenant_id = tenant_info.tenant_id if tenant_info else None
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant information required")
    
    try:
        # Enrich parameters with tenant and user context
        parameters = workflow_request.parameters or {}
        parameters.update({
            'tenant_id': tenant_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Start the workflow
        instance_id = await sar_workflow.start_workflow(
            workflow_name=workflow_request.workflow_name,
            tenant_id=tenant_id,
            user_id=user_id,
            parameters=parameters
        )
        
        return {
            "success": True,
            "instance_id": instance_id,
            "workflow_name": workflow_request.workflow_name,
            "message": f"Workflow '{workflow_request.workflow_name}' started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.get("/instances")
async def list_workflow_instances(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """List workflow instances for the current tenant"""
    if not check_workflow_permissions(request, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to read workflows")
    
    tenant_id = tenant_info.tenant_id if tenant_info else None
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant information required")
    
    # Parse status if provided
    status_enum = None
    if status:
        try:
            status_enum = WorkflowStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    instances = await sar_workflow.list_workflow_instances(
        tenant_id=tenant_id,
        status=status_enum,
        limit=limit,
        offset=offset
    )
    
    # Convert to response format
    instance_responses = []
    for instance in instances:
        task_responses = []
        for task in instance.tasks:
            task_responses.append(WorkflowTaskResponse(
                task_id=task.task_id,
                name=task.name,
                status=task.status.value,
                result=task.result,
                error=task.error,
                started_at=task.started_at.isoformat() if task.started_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None
            ))
        
        instance_responses.append(WorkflowInstanceResponse(
            instance_id=instance.instance_id,
            workflow_name=instance.workflow_name,
            tenant_id=instance.tenant_id,
            user_id=instance.user_id,
            status=instance.status.value,
            tasks=task_responses,
            context=instance.context,
            created_at=instance.created_at.isoformat(),
            started_at=instance.started_at.isoformat() if instance.started_at else None,
            completed_at=instance.completed_at.isoformat() if instance.completed_at else None,
            error=instance.error
        ))
    
    return {
        "instances": instance_responses,
        "total": len(instance_responses),  # In a real implementation, this would be the actual total
        "limit": limit,
        "offset": offset
    }


@router.get("/instances/{instance_id}")
async def get_workflow_instance(
    instance_id: str,
    request: Request,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Get a specific workflow instance"""
    if not check_workflow_permissions(request, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to read workflow")
    
    # Validate tenant access
    if not validate_workflow_tenant_access(instance_id, request):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access cross-tenant workflow")
    
    instance = await sar_workflow.get_workflow_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    
    # Convert to response format
    task_responses = []
    for task in instance.tasks:
        task_responses.append(WorkflowTaskResponse(
            task_id=task.task_id,
            name=task.name,
            status=task.status.value,
            result=task.result,
            error=task.error,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        ))
    
    return WorkflowInstanceResponse(
        instance_id=instance.instance_id,
        workflow_name=instance.workflow_name,
        tenant_id=instance.tenant_id,
        user_id=instance.user_id,
        status=instance.status.value,
        tasks=task_responses,
        context=instance.context,
        created_at=instance.created_at.isoformat(),
        started_at=instance.started_at.isoformat() if instance.started_at else None,
        completed_at=instance.completed_at.isoformat() if instance.completed_at else None,
        error=instance.error
    )


@router.post("/instances/{instance_id}/cancel")
async def cancel_workflow_instance(
    instance_id: str,
    request: Request,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Cancel a running workflow instance"""
    if not check_workflow_permissions(request, "update"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to cancel workflow")
    
    # Validate tenant access
    if not validate_workflow_tenant_access(instance_id, request):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access cross-tenant workflow")
    
    success = await sar_workflow.cancel_workflow(instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow instance not found or cannot be cancelled")
    
    return {
        "success": True,
        "instance_id": instance_id,
        "status": "cancelled",
        "message": "Workflow cancelled successfully"
    }


@router.post("/instances/{instance_id}/pause")
async def pause_workflow_instance(
    instance_id: str,
    request: Request,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Pause a running workflow instance"""
    if not check_workflow_permissions(request, "update"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to pause workflow")
    
    # Validate tenant access
    if not validate_workflow_tenant_access(instance_id, request):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access cross-tenant workflow")
    
    success = await sar_workflow.pause_workflow(instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow instance not found or cannot be paused")
    
    return {
        "success": True,
        "instance_id": instance_id,
        "status": "paused",
        "message": "Workflow paused successfully"
    }


@router.post("/instances/{instance_id}/resume")
async def resume_workflow_instance(
    instance_id: str,
    request: Request,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Resume a paused workflow instance"""
    if not check_workflow_permissions(request, "update"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to resume workflow")
    
    # Validate tenant access
    if not validate_workflow_tenant_access(instance_id, request):
        raise HTTPException(status_code=403, detail="Access denied: Cannot access cross-tenant workflow")
    
    success = await sar_workflow.resume_workflow(instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow instance not found or cannot be resumed")
    
    return {
        "success": True,
        "instance_id": instance_id,
        "status": "running",
        "message": "Workflow resumed successfully"
    }


@router.get("/definitions")
async def list_workflow_definitions(
    request: Request
):
    """List available workflow definitions"""
    if not check_workflow_permissions(request, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to read workflow definitions")
    
    definitions = []
    for name, definition in sar_workflow._workflow_definitions.items():
        definitions.append({
            "name": name,
            "description": definition.description,
            "task_count": len(definition.tasks),
            "parameters": list(definition.parameters.keys())
        })
    
    return {
        "definitions": definitions,
        "count": len(definitions)
    }


@router.get("/health")
async def workflow_health_check():
    """Health check for the workflow engine"""
    return {
        "status": "healthy",
        "enabled": True,
        "running_workflows": len(sar_workflow._running_workflows),
        "registered_definitions": len(sar_workflow._workflow_definitions),
        "storage_backend": sar_workflow.config.storage_backend,
        "timestamp": datetime.utcnow().isoformat()
    }


# Example workflow definition endpoint
@router.post("/examples/candidate-onboarding")
async def create_candidate_onboarding_workflow(
    request: Request,
    tenant_info: Optional[Any] = Depends(get_tenant_info)
):
    """Create an example candidate onboarding workflow"""
    # This is an example that demonstrates how to create and register a workflow
    from .workflow_service import validate_candidate_task, send_email_task, schedule_interview_task
    
    onboarding_wf = WorkflowDefinition(
        name="candidate_onboarding_example",
        description="Example workflow for onboarding new candidates"
    ).add_task(
        "validate_candidate",
        validate_candidate_task,
        args=["$candidate_id"],
        kwargs={"context": "$context"}
    ).add_task(
        "send_welcome_email",
        send_email_task,
        args=["$candidate_email", "Welcome", "Welcome to our platform!"],
        kwargs={"context": "$context"},
        dependencies=["validate_candidate"]
    ).add_task(
        "schedule_interview",
        schedule_interview_task,
        args=["$candidate_id", "$job_id", "$interview_date"],
        kwargs={"context": "$context"},
        dependencies=["validate_candidate"]
    )
    
    sar_workflow.register_workflow(onboarding_wf)
    
    return {
        "success": True,
        "workflow_name": "candidate_onboarding_example",
        "message": "Example workflow registered successfully",
        "task_count": 3
    }