"""
Sovereign Application Runtime (SAR) - Workflow Engine

This module provides comprehensive workflow management and business process automation for the SAR.

Features:
- Multi-tenant workflow support with tenant isolation
- Persistent workflow storage with MongoDB Atlas integration
- Task dependency management with DAG execution
- Workflow lifecycle management (start, pause, resume, cancel)
- Retry mechanisms with configurable delays
- Status tracking for workflows and individual tasks
- Integration with authentication and tenant services

Workflow Execution:
- Asynchronous workflow execution with thread pools
- Task-level status tracking (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- Dependency-aware execution with topological sorting
- Context sharing between workflow tasks

Storage Backends:
- MongoDB Atlas (default) - Production ready with indexing
- In-memory storage - For development and testing

Dependencies:
- Requires MongoDB Atlas connection
- Integrates with authentication and tenant services
- Uses the same authentication patterns as the services

Usage:
from workflow.workflow_service import sar_workflow, WorkflowDefinition
"""