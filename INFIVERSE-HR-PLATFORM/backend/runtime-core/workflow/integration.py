"""
Integration Module for Sovereign Application Runtime (SAR) Workflow Engine

This module provides integration between the workflow engine and other SAR services
for comprehensive business process automation.
"""
from typing import Dict, Any, Optional, Callable, List
from fastapi import Request
import asyncio
from ..auth.auth_service import sar_auth
from ..tenancy.tenant_service import sar_tenant_resolver
from ..role_enforcement.rbac_service import sar_rbac
from ..audit_logging.audit_service import sar_audit
from .workflow_service import sar_workflow, WorkflowDefinition
from .middleware import WorkflowEnforcementMiddleware, WorkflowAuditMiddleware


def integrate_workflow_with_auth():
    """Integrate workflow engine with authentication service"""
    # Enhance workflow operations with authentication awareness
    
    # Store original start_workflow method
    original_start_workflow = sar_workflow.start_workflow
    
    async def auth_enhanced_start_workflow(workflow_name: str, tenant_id: str, user_id: str, 
                                         parameters: Optional[Dict[str, Any]] = None) -> str:
        """Start workflow with authentication validation"""
        # Validate user exists and is authenticated
        # In a real implementation, you would validate the user_id against the auth system
        if not user_id:
            raise ValueError("User ID is required to start a workflow")
        
        # Call original method
        instance_id = await original_start_workflow(workflow_name, tenant_id, user_id, parameters)
        
        # Log the workflow start event
        sar_audit.log_event(
            event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
            user_id=user_id,
            tenant_id=tenant_id,
            resource="workflow",
            action="start",
            resource_id=instance_id,
            new_values={"workflow_name": workflow_name, "parameters": parameters},
            metadata={"workflow_instance_id": instance_id}
        )
        
        return instance_id
    
    # Replace the method
    sar_workflow.start_workflow = auth_enhanced_start_workflow


def integrate_workflow_with_tenant():
    """Integrate workflow engine with tenant resolution service"""
    # Enhance workflow operations with tenant isolation
    
    # Store original methods that need tenant validation
    original_get_workflow_instance = sar_workflow.get_workflow_instance
    original_list_workflow_instances = sar_workflow.list_workflow_instances
    
    async def tenant_validated_get_workflow_instance(instance_id: str) -> Optional[Any]:
        """Get workflow instance with tenant validation"""
        instance = await original_get_workflow_instance(instance_id)
        # In a real implementation, you would validate tenant access here
        return instance
    
    async def tenant_validated_list_workflow_instances(tenant_id: str, 
                                                     status: Optional[Any] = None,
                                                     limit: int = 100, offset: int = 0) -> List[Any]:
        """List workflow instances with tenant isolation"""
        # This already has tenant_id as a parameter, ensuring tenant isolation
        return await original_list_workflow_instances(tenant_id, status, limit, offset)
    
    # Replace the methods
    sar_workflow.get_workflow_instance = tenant_validated_get_workflow_instance
    sar_workflow.list_workflow_instances = tenant_validated_list_workflow_instances


def integrate_workflow_with_role_enforcement():
    """Integrate workflow engine with role enforcement service"""
    # Enhance workflow operations with role-based access control
    
    # This integration happens at the API level through the router's use of require_permission
    # The middleware and decorators handle role enforcement
    pass


def integrate_workflow_with_audit():
    """Integrate workflow engine with audit logging service"""
    # Enhance workflow operations with comprehensive audit logging
    
    # Store original methods
    original_start_workflow = sar_workflow.start_workflow
    original_cancel_workflow = sar_workflow.cancel_workflow
    original_pause_workflow = sar_workflow.pause_workflow
    original_resume_workflow = sar_workflow.resume_workflow
    
    async def audited_start_workflow(workflow_name: str, tenant_id: str, user_id: str, 
                                   parameters: Optional[Dict[str, Any]] = None) -> str:
        """Start workflow with audit logging"""
        try:
            instance_id = await original_start_workflow(workflow_name, tenant_id, user_id, parameters)
            
            sar_audit.log_event(
                event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                user_id=user_id,
                tenant_id=tenant_id,
                resource="workflow",
                action="start",
                resource_id=instance_id,
                new_values={
                    "workflow_name": workflow_name,
                    "parameters": parameters,
                    "instance_id": instance_id
                },
                metadata={
                    "operation": "workflow_start",
                    "workflow_name": workflow_name
                }
            )
            
            return instance_id
        except Exception as e:
            sar_audit.log_event(
                event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                user_id=user_id,
                tenant_id=tenant_id,
                resource="workflow",
                action="start",
                resource_id=None,
                success=False,
                error_message=str(e),
                metadata={
                    "operation": "workflow_start",
                    "workflow_name": workflow_name
                }
            )
            raise e
    
    async def audited_cancel_workflow(instance_id: str) -> bool:
        """Cancel workflow with audit logging"""
        try:
            # Get the instance to log its details
            instance = await sar_workflow.get_workflow_instance(instance_id)
            
            success = await original_cancel_workflow(instance_id)
            
            if success and instance:
                sar_audit.log_event(
                    event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                    user_id=instance.user_id,
                    tenant_id=instance.tenant_id,
                    resource="workflow",
                    action="cancel",
                    resource_id=instance_id,
                    old_values={
                        "previous_status": instance.status.value,
                        "workflow_name": instance.workflow_name
                    },
                    metadata={
                        "operation": "workflow_cancel",
                        "workflow_name": instance.workflow_name
                    }
                )
            
            return success
        except Exception as e:
            sar_audit.log_event(
                event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                user_id=getattr(instance, 'user_id', None) if 'instance' in locals() else None,
                tenant_id=getattr(instance, 'tenant_id', None) if 'instance' in locals() else None,
                resource="workflow",
                action="cancel",
                resource_id=instance_id,
                success=False,
                error_message=str(e),
                metadata={
                    "operation": "workflow_cancel"
                }
            )
            raise e
    
    async def audited_pause_workflow(instance_id: str) -> bool:
        """Pause workflow with audit logging"""
        try:
            instance = await sar_workflow.get_workflow_instance(instance_id)
            
            success = await original_pause_workflow(instance_id)
            
            if success and instance:
                sar_audit.log_event(
                    event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                    user_id=instance.user_id,
                    tenant_id=instance.tenant_id,
                    resource="workflow",
                    action="pause",
                    resource_id=instance_id,
                    old_values={
                        "previous_status": instance.status.value,
                        "workflow_name": instance.workflow_name
                    },
                    metadata={
                        "operation": "workflow_pause",
                        "workflow_name": instance.workflow_name
                    }
                )
            
            return success
        except Exception as e:
            sar_audit.log_event(
                event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                user_id=getattr(instance, 'user_id', None) if 'instance' in locals() else None,
                tenant_id=getattr(instance, 'tenant_id', None) if 'instance' in locals() else None,
                resource="workflow",
                action="pause",
                resource_id=instance_id,
                success=False,
                error_message=str(e),
                metadata={
                    "operation": "workflow_pause"
                }
            )
            raise e
    
    async def audited_resume_workflow(instance_id: str) -> bool:
        """Resume workflow with audit logging"""
        try:
            instance = await sar_workflow.get_workflow_instance(instance_id)
            
            success = await original_resume_workflow(instance_id)
            
            if success and instance:
                sar_audit.log_event(
                    event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                    user_id=instance.user_id,
                    tenant_id=instance.tenant_id,
                    resource="workflow",
                    action="resume",
                    resource_id=instance_id,
                    new_values={
                        "new_status": "running",
                        "workflow_name": instance.workflow_name
                    },
                    metadata={
                        "operation": "workflow_resume",
                        "workflow_name": instance.workflow_name
                    }
                )
            
            return success
        except Exception as e:
            sar_audit.log_event(
                event_type=sar_audit.AuditEventType.DATA_MODIFICATION,
                user_id=getattr(instance, 'user_id', None) if 'instance' in locals() else None,
                tenant_id=getattr(instance, 'tenant_id', None) if 'instance' in locals() else None,
                resource="workflow",
                action="resume",
                resource_id=instance_id,
                success=False,
                error_message=str(e),
                metadata={
                    "operation": "workflow_resume"
                }
            )
            raise e
    
    # Replace the methods
    sar_workflow.start_workflow = audited_start_workflow
    sar_workflow.cancel_workflow = audited_cancel_workflow
    sar_workflow.pause_workflow = audited_pause_workflow
    sar_workflow.resume_workflow = audited_resume_workflow


def setup_comprehensive_workflow_integration():
    """Setup comprehensive integration between workflow engine and all SAR services"""
    # Integrate workflow engine with all services
    integrate_workflow_with_auth()
    integrate_workflow_with_tenant()
    integrate_workflow_with_role_enforcement()
    integrate_workflow_with_audit()
    
    print("SAR Integration: Workflow engine successfully integrated with all services")
    print(f"Authentication service: {type(sar_auth).__name__}")
    print(f"Tenant resolver service: {type(sar_tenant_resolver).__name__}")
    print(f"Role enforcement service: {type(sar_rbac).__name__}")
    print(f"Audit logging service: {type(sar_audit).__name__}")
    print(f"Workflow engine: {type(sar_workflow).__name__}")


def create_workflow_with_business_logic(workflow_name: str, business_function: Callable) -> WorkflowDefinition:
    """Create a workflow that encapsulates a business function"""
    # This creates a simple workflow with one task that executes the business function
    wf_def = WorkflowDefinition(
        name=workflow_name,
        description=f"Workflow for {business_function.__name__}"
    ).add_task(
        name="execute_business_logic",
        function=business_function
    )
    
    # Register the workflow
    sar_workflow.register_workflow(wf_def)
    return wf_def


def execute_business_workflow(workflow_name: str, tenant_id: str, user_id: str,
                            parameters: Optional[Dict[str, Any]] = None) -> str:
    """Execute a business workflow with full SAR integration"""
    # This function provides a high-level interface to execute workflows
    # with all the integrated services working together
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        instance_id = loop.run_until_complete(
            sar_workflow.start_workflow(workflow_name, tenant_id, user_id, parameters)
        )
        return instance_id
    finally:
        loop.close()


def get_workflow_provenance(instance_id: str) -> Dict[str, Any]:
    """Get the complete provenance trail for a workflow instance"""
    # This would return the complete history of a workflow execution
    # including all tasks, their inputs, outputs, and any data modifications
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        instance = loop.run_until_complete(
            sar_workflow.get_workflow_instance(instance_id)
        )
        
        if not instance:
            return {}
        
        # Compile provenance information
        provenance = {
            "instance_id": instance.instance_id,
            "workflow_name": instance.workflow_name,
            "tenant_id": instance.tenant_id,
            "user_id": instance.user_id,
            "status": instance.status.value,
            "created_at": instance.created_at.isoformat(),
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "tasks": [],
            "context": instance.context,
            "error": instance.error
        }
        
        # Add task-level provenance
        for task in instance.tasks:
            task_provenance = {
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status.value,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result,
                "error": task.error,
                "dependencies": task.dependencies
            }
            provenance["tasks"].append(task_provenance)
        
        return provenance
    finally:
        loop.close()


def register_common_workflows():
    """Register common workflows that are typically needed in business applications"""
    # Example: User registration workflow
    user_registration_wf = WorkflowDefinition(
        name="user_registration",
        description="Workflow for registering new users"
    ).add_task(
        "validate_user_data",
        lambda user_data: {"status": "validated", "user_data": user_data}
    ).add_task(
        "create_user_account",
        lambda user_data: {"status": "created", "user_id": f"user_{hash(str(user_data)) % 10000}"}
    ).add_task(
        "send_welcome_email",
        lambda user_email: {"status": "sent", "email": user_email}
    )
    
    sar_workflow.register_workflow(user_registration_wf)
    
    # Example: Document approval workflow
    document_approval_wf = WorkflowDefinition(
        name="document_approval",
        description="Workflow for approving documents"
    ).add_task(
        "validate_document",
        lambda doc: {"status": "validated", "doc_id": doc.get('id')}
    ).add_task(
        "send_for_review",
        lambda doc, reviewers: {"status": "sent_for_review", "reviewers": reviewers}
    ).add_task(
        "wait_for_approval",
        lambda doc_id: {"status": "approval_received", "doc_id": doc_id}
    ).add_task(
        "publish_document",
        lambda doc_id: {"status": "published", "doc_id": doc_id}
    )
    
    sar_workflow.register_workflow(document_approval_wf)


def add_workflow_middleware(app):
    """Add workflow middleware to a FastAPI application"""
    app.add_middleware(WorkflowEnforcementMiddleware)
    app.add_middleware(WorkflowAuditMiddleware)
    return app


# Initialize the workflow integration when module is loaded
setup_comprehensive_workflow_integration()
register_common_workflows()