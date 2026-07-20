"""
Workflow Engine Service for Sovereign Application Runtime (SAR)

This module provides workflow management and business process automation
for multi-tenant applications with proper isolation and security measures.
"""
import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import os
from concurrent.futures import ThreadPoolExecutor
import logging
from enum import Enum
from pymongo import MongoClient
import time

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Enumeration of workflow execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Enumeration of task execution statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowTask:
    """Represents a single task within a workflow"""
    task_id: str
    name: str
    function: Callable
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # List of task IDs this task depends on
    timeout: Optional[int] = None  # Timeout in seconds
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowInstance:
    """Represents an instance of a running workflow"""
    instance_id: str
    workflow_name: str
    tenant_id: str
    user_id: str
    tasks: List[WorkflowTask]
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)  # Shared context for all tasks
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowDefinition:
    """Defines a reusable workflow template"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tasks: List[WorkflowTask] = []
        self.parameters: Dict[str, Any] = {}
    
    def add_task(self, name: str, function: Callable, 
                 args: List[Any] = None, kwargs: Dict[str, Any] = None,
                 dependencies: List[str] = None, timeout: Optional[int] = None) -> 'WorkflowDefinition':
        """Add a task to the workflow definition"""
        task_id = str(uuid.uuid4())
        task = WorkflowTask(
            task_id=task_id,
            name=name,
            function=function,
            args=args or [],
            kwargs=kwargs or {},
            dependencies=dependencies or [],
            timeout=timeout
        )
        self.tasks.append(task)
        return self
    
    def set_parameter(self, name: str, default_value: Any) -> 'WorkflowDefinition':
        """Set a parameter for the workflow"""
        self.parameters[name] = default_value
        return self


class WorkflowStorageBackend(ABC):
    """Abstract base class for workflow storage backends"""
    
    @abstractmethod
    async def store_workflow_instance(self, instance: WorkflowInstance) -> bool:
        """Store a workflow instance"""
        pass

    @abstractmethod
    async def get_workflow_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Retrieve a workflow instance by ID"""
        pass

    @abstractmethod
    async def update_workflow_instance(self, instance: WorkflowInstance) -> bool:
        """Update a workflow instance"""
        pass

    @abstractmethod
    async def list_workflow_instances(self, tenant_id: str, 
                                    status: Optional[WorkflowStatus] = None,
                                    limit: int = 100, offset: int = 0) -> List[WorkflowInstance]:
        """List workflow instances for a tenant"""
        pass


class MongoWorkflowStorage(WorkflowStorageBackend):
    """MongoDB-based workflow storage for persistent workflow management"""
    
    def __init__(self, mongodb_uri: str = None, db_name: str = None, collection_name: str = None):
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME", "bhiv_hr")
        self.collection_name = collection_name or os.getenv("WORKFLOW_COLLECTION", "workflows")
        self._client = None
        self._db = None
        self._collection = None
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        try:
            self._client = MongoClient(self.mongodb_uri)
            self._db = self._client[self.db_name]
            self._collection = self._db[self.collection_name]
            # Create indexes for efficient queries
            self._collection.create_index([("instance_id", 1)], unique=True)
            self._collection.create_index([("tenant_id", 1)])
            self._collection.create_index([("workflow_name", 1)])
            self._collection.create_index([("status", 1)])
            self._collection.create_index([("created_at", -1)])
            logger.info(f"✅ Connected to MongoDB workflow collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB for workflow storage: {e}")
            self._client = None
            self._db = None
            self._collection = None
    
    def _serialize_instance(self, instance: WorkflowInstance) -> Dict[str, Any]:
        """Serialize a WorkflowInstance to a dictionary for MongoDB storage"""
        return {
            "instance_id": instance.instance_id,
            "workflow_name": instance.workflow_name,
            "tenant_id": instance.tenant_id,
            "user_id": instance.user_id,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "args": task.args,
                    "kwargs": task.kwargs,
                    "dependencies": task.dependencies,
                    "timeout": task.timeout,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                } for task in instance.tasks
            ],
            "status": instance.status.value,
            "context": instance.context,
            "created_at": instance.created_at.isoformat(),
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "error": instance.error,
        }
    
    def _deserialize_instance(self, data: Dict[str, Any]) -> WorkflowInstance:
        """Deserialize a dictionary from MongoDB to a WorkflowInstance"""
        # Deserialize tasks
        tasks = []
        for task_data in data["tasks"]:
            task = WorkflowTask(
                task_id=task_data["task_id"],
                name=task_data["name"],
                function=None,  # We can't serialize functions, so they need to be re-assigned
                args=task_data["args"],
                kwargs=task_data["kwargs"],
                dependencies=task_data["dependencies"],
                timeout=task_data["timeout"],
                retry_count=task_data["retry_count"],
                max_retries=task_data["max_retries"],
                status=TaskStatus(task_data["status"]),
                result=task_data["result"],
                error=task_data["error"],
                started_at=datetime.fromisoformat(task_data["started_at"]) if task_data["started_at"] else None,
                completed_at=datetime.fromisoformat(task_data["completed_at"]) if task_data["completed_at"] else None,
            )
            tasks.append(task)
        
        return WorkflowInstance(
            instance_id=data["instance_id"],
            workflow_name=data["workflow_name"],
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            tasks=tasks,
            status=WorkflowStatus(data["status"]),
            context=data["context"],
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            error=data["error"],
        )
    
    async def store_workflow_instance(self, instance: WorkflowInstance) -> bool:
        """Store a workflow instance in MongoDB"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for workflow storage")
            return False
        
        try:
            doc = self._serialize_instance(instance)
            result = self._collection.insert_one(doc)
            logger.debug(f"✅ Workflow instance stored: {instance.instance_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store workflow instance: {e}")
            return False
    
    async def get_workflow_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Retrieve a workflow instance from MongoDB"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for workflow storage")
            return None
        
        try:
            doc = self._collection.find_one({"instance_id": instance_id})
            if doc:
                return self._deserialize_instance(doc)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve workflow instance: {e}")
            return None
    
    async def update_workflow_instance(self, instance: WorkflowInstance) -> bool:
        """Update a workflow instance in MongoDB"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for workflow storage")
            return False
        
        try:
            doc = self._serialize_instance(instance)
            result = self._collection.replace_one(
                {"instance_id": instance.instance_id}, doc
            )
            logger.debug(f"✅ Workflow instance updated: {instance.instance_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to update workflow instance: {e}")
            return False
    
    async def list_workflow_instances(self, tenant_id: str, 
                                    status: Optional[WorkflowStatus] = None,
                                    limit: int = 100, offset: int = 0) -> List[WorkflowInstance]:
        """List workflow instances for a tenant from MongoDB"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for workflow storage")
            return []
        
        try:
            query = {"tenant_id": tenant_id}
            if status:
                query["status"] = status.value
            
            cursor = self._collection.find(query).skip(offset).limit(limit)
            instances = []
            
            for doc in cursor:
                try:
                    instance = self._deserialize_instance(doc)
                    instances.append(instance)
                except Exception as e:
                    logger.error(f"❌ Failed to deserialize workflow instance: {e}")
                    continue
            
            logger.debug(f"✅ Retrieved {len(instances)} workflow instances for tenant {tenant_id}")
            return instances
        except Exception as e:
            logger.error(f"❌ Failed to list workflow instances: {e}")
            return []


class InMemoryWorkflowStorage(WorkflowStorageBackend):
    """In-memory workflow storage for development/testing purposes"""
    
    def __init__(self):
        self._instances: Dict[str, WorkflowInstance] = {}
    
    async def store_workflow_instance(self, instance: WorkflowInstance) -> bool:
        self._instances[instance.instance_id] = instance
        return True
    
    async def get_workflow_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        return self._instances.get(instance_id)
    
    async def update_workflow_instance(self, instance: WorkflowInstance) -> bool:
        if instance.instance_id in self._instances:
            self._instances[instance.instance_id] = instance
            return True
        return False
    
    async def list_workflow_instances(self, tenant_id: str, 
                                    status: Optional[WorkflowStatus] = None,
                                    limit: int = 100, offset: int = 0) -> List[WorkflowInstance]:
        instances = []
        for instance in self._instances.values():
            if instance.tenant_id == tenant_id:
                if status is None or instance.status == status:
                    instances.append(instance)
        
        # Apply offset and limit
        return instances[offset:offset + limit]


class WorkflowConfig:
    """Configuration for the workflow engine"""
    def __init__(self):
        self.storage_backend = os.getenv("WORKFLOW_STORAGE_BACKEND", "mongodb")
        self.max_concurrent_workflows = int(os.getenv("WORKFLOW_MAX_CONCURRENT", "10"))
        self.task_timeout = int(os.getenv("WORKFLOW_TASK_TIMEOUT", "300"))  # 5 minutes
        self.workflow_timeout = int(os.getenv("WORKFLOW_TIMEOUT", "3600"))  # 1 hour
        self.retry_delay = int(os.getenv("WORKFLOW_RETRY_DELAY", "5"))  # 5 seconds
        self.enable_persistence = os.getenv("WORKFLOW_PERSISTENCE", "false").lower() == "true"
        self.executor_workers = int(os.getenv("WORKFLOW_EXECUTOR_WORKERS", "20"))
        # MongoDB configuration
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")
        self.workflows_collection_name = os.getenv("WORKFLOW_COLLECTION", "workflows")


class SARWorkflowEngine:
    """Main workflow engine service class for the Sovereign Application Runtime"""
    
    def __init__(self):
        self.config = WorkflowConfig()
        self._setup_storage_backend()
        self._executor = ThreadPoolExecutor(max_workers=self.config.executor_workers)
        self._running_workflows: Dict[str, asyncio.Task] = {}
        self._workflow_definitions: Dict[str, WorkflowDefinition] = {}
        
    def _setup_storage_backend(self):
        """Initialize the appropriate storage backend based on configuration"""
        if self.config.storage_backend == "memory":
            self.storage = InMemoryWorkflowStorage()
        elif self.config.storage_backend == "mongodb":
            self.storage = MongoWorkflowStorage(
                mongodb_uri=self.config.mongodb_uri,
                db_name=self.config.mongodb_db_name,
                collection_name=self.config.workflows_collection_name
            )
        else:
            # Default to in-memory for unknown storage types
            self.storage = InMemoryWorkflowStorage()
    
    def register_workflow(self, definition: WorkflowDefinition):
        """Register a workflow definition"""
        self._workflow_definitions[definition.name] = definition
    
    def get_workflow_definition(self, name: str) -> Optional[WorkflowDefinition]:
        """Get a registered workflow definition"""
        return self._workflow_definitions.get(name)
    
    async def start_workflow(self, workflow_name: str, tenant_id: str, user_id: str, 
                           parameters: Optional[Dict[str, Any]] = None) -> str:
        """Start a new workflow instance"""
        definition = self.get_workflow_definition(workflow_name)
        if not definition:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # Create a new workflow instance
        instance_id = str(uuid.uuid4())
        
        # Initialize tasks for this instance
        instance_tasks = []
        for task_def in definition.tasks:
            task = WorkflowTask(
                task_id=task_def.task_id,
                name=task_def.name,
                function=task_def.function,
                args=task_def.args,
                kwargs=task_def.kwargs,
                dependencies=task_def.dependencies,
                timeout=task_def.timeout or self.config.task_timeout,
                max_retries=task_def.max_retries
            )
            instance_tasks.append(task)
        
        # Create context with parameters
        context = {**(parameters or {}), **(definition.parameters)}
        
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_name=workflow_name,
            tenant_id=tenant_id,
            user_id=user_id,
            tasks=instance_tasks,
            context=context
        )
        
        # Store the instance
        await self.storage.store_workflow_instance(instance)
        
        # Start execution in background
        workflow_task = asyncio.create_task(self._execute_workflow(instance))
        self._running_workflows[instance_id] = workflow_task
        
        return instance_id
    
    async def _execute_workflow(self, instance: WorkflowInstance):
        """Execute a workflow instance"""
        try:
            # Update workflow status
            instance.status = WorkflowStatus.RUNNING
            instance.started_at = datetime.now(timezone.utc)
            await self.storage.update_workflow_instance(instance)
            
            # Execute tasks in dependency order
            remaining_tasks = {task.task_id: task for task in instance.tasks}
            completed_tasks = set()
            
            while remaining_tasks and instance.status == WorkflowStatus.RUNNING:
                # Find tasks that can be executed (dependencies satisfied)
                executable_tasks = []
                for task_id, task in remaining_tasks.items():
                    # Check if all dependencies are completed
                    deps_satisfied = all(dep_id in completed_tasks for dep_id in task.dependencies)
                    
                    if deps_satisfied:
                        executable_tasks.append(task)
                
                if not executable_tasks:
                    # If no tasks can be executed but we still have remaining tasks,
                    # there might be a circular dependency
                    if remaining_tasks:
                        raise RuntimeError("Circular dependency detected in workflow")
                    break
                
                # Execute executable tasks concurrently
                for task in executable_tasks:
                    try:
                        # Update task status
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.now(timezone.utc)
                        await self.storage.update_workflow_instance(instance)
                        
                        # Execute the task
                        result = await self._execute_task(task, instance)
                        
                        # Update task result
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        task.completed_at = datetime.now(timezone.utc)
                        completed_tasks.add(task.task_id)
                        
                    except Exception as e:
                        # Handle task failure
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task.completed_at = datetime.now(timezone.utc)
                        
                        # If task allows retries, retry it
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            task.status = TaskStatus.PENDING
                            # Reset execution times for retry
                            task.started_at = None
                            task.completed_at = None
                            await asyncio.sleep(self.config.retry_delay)
                            continue
                        else:
                            # Task failed permanently, fail the entire workflow
                            instance.status = WorkflowStatus.FAILED
                            instance.error = f"Task '{task.name}' failed: {str(e)}"
                            break
                
                # Remove completed tasks from remaining
                for task in executable_tasks:
                    if task.status == TaskStatus.COMPLETED:
                        remaining_tasks.pop(task.task_id, None)
            
            # Update workflow status when all tasks are done
            if instance.status != WorkflowStatus.FAILED:
                if not remaining_tasks:
                    instance.status = WorkflowStatus.COMPLETED
                else:
                    # Some tasks couldn't be executed
                    instance.status = WorkflowStatus.FAILED
                    instance.error = "Some tasks could not be executed due to dependency issues"
            
            instance.completed_at = datetime.now(timezone.utc)
            await self.storage.update_workflow_instance(instance)
            
        except Exception as e:
            # Handle workflow-level error
            instance.status = WorkflowStatus.FAILED
            instance.error = str(e)
            instance.completed_at = datetime.now(timezone.utc)
            await self.storage.update_workflow_instance(instance)
        
        finally:
            # Remove from running workflows
            self._running_workflows.pop(instance.instance_id, None)
    
    async def _execute_task(self, task: WorkflowTask, instance: WorkflowInstance) -> Any:
        """Execute a single workflow task"""
        try:
            # Prepare arguments with context
            args = [instance.context.get(arg) if isinstance(arg, str) and arg.startswith('$') else arg for arg in task.args]
            
            # Prepare keyword arguments with context
            kwargs = {}
            for key, value in task.kwargs.items():
                if isinstance(value, str) and value.startswith('$'):
                    # This is a context reference
                    kwargs[key] = instance.context.get(value[1:], value)  # Remove '$' prefix
                else:
                    kwargs[key] = value
            
            # Execute the task function
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    lambda: task.function(*args, **kwargs)
                )
            
            return result
        except Exception as e:
            raise e
    
    async def get_workflow_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by ID"""
        return await self.storage.get_workflow_instance(instance_id)
    
    async def list_workflow_instances(self, tenant_id: str, 
                                    status: Optional[WorkflowStatus] = None,
                                    limit: int = 100, offset: int = 0) -> List[WorkflowInstance]:
        """List workflow instances for a tenant"""
        return await self.storage.list_workflow_instances(tenant_id, status, limit, offset)
    
    async def cancel_workflow(self, instance_id: str) -> bool:
        """Cancel a running workflow"""
        instance = await self.storage.get_workflow_instance(instance_id)
        if not instance or instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False
        
        # Update status to cancelled
        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.now(timezone.utc)
        await self.storage.update_workflow_instance(instance)
        
        # Cancel the running task if it exists
        running_task = self._running_workflows.get(instance_id)
        if running_task:
            running_task.cancel()
            self._running_workflows.pop(instance_id, None)
        
        return True
    
    async def pause_workflow(self, instance_id: str) -> bool:
        """Pause a running workflow"""
        instance = await self.storage.get_workflow_instance(instance_id)
        if not instance or instance.status != WorkflowStatus.RUNNING:
            return False
        
        instance.status = WorkflowStatus.PAUSED
        await self.storage.update_workflow_instance(instance)
        
        return True
    
    async def resume_workflow(self, instance_id: str) -> bool:
        """Resume a paused workflow"""
        instance = await self.storage.get_workflow_instance(instance_id)
        if not instance or instance.status != WorkflowStatus.PAUSED:
            return False
        
        # Restart the workflow execution
        workflow_task = asyncio.create_task(self._execute_workflow(instance))
        self._running_workflows[instance_id] = workflow_task
        
        instance.status = WorkflowStatus.RUNNING
        await self.storage.update_workflow_instance(instance)
        
        return True
    
    def shutdown(self):
        """Shutdown the workflow engine"""
        # Cancel all running workflows
        for workflow_task in self._running_workflows.values():
            workflow_task.cancel()
        
        # Shutdown the executor
        self._executor.shutdown(wait=True)


# Global instance for the SAR Workflow Engine
sar_workflow = SARWorkflowEngine()


# Example workflow task functions
async def send_email_task(recipient: str, subject: str, body: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Example task: Send an email"""
    print(f"Sending email to {recipient}: {subject}")
    # In a real implementation, this would send an actual email
    return {
        "status": "sent",
        "recipient": recipient,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def validate_candidate_task(candidate_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Example task: Validate a candidate"""
    print(f"Validating candidate: {candidate_id}")
    # In a real implementation, this would perform actual validation
    return {
        "candidate_id": candidate_id,
        "status": "validated",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def schedule_interview_task(candidate_id: str, job_id: str, date: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Example task: Schedule an interview"""
    print(f"Scheduling interview for candidate {candidate_id} for job {job_id} on {date}")
    # In a real implementation, this would schedule an actual interview
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "date": date,
        "status": "scheduled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Register some example workflows
def register_example_workflows():
    """Register example workflows for demonstration"""
    # Candidate onboarding workflow
    candidate_onboarding_wf = WorkflowDefinition(
        name="candidate_onboarding",
        description="Workflow for onboarding new candidates"
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
    
    sar_workflow.register_workflow(candidate_onboarding_wf)


# Register example workflows when module is loaded
register_example_workflows()