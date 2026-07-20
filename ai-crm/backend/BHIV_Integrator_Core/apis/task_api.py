"""
Task Manager API Router for BHIV Integrator Core
Handles task management, review, feedback, and workflow state
"""

from fastapi import APIRouter, HTTPException, Request
import requests
from typing import Dict, Any
from datetime import datetime
from config.settings import settings
from event_broker.event_broker import EventBroker
from unified_logging.logger import UnifiedLogger
from compliance.compliance_hooks import ComplianceHooks

router = APIRouter()
event_broker = EventBroker()
logger = UnifiedLogger()
compliance = ComplianceHooks()

TASK_BASE_URL = settings.get("task_base_url", "http://localhost:8000")

@router.get("/review")
async def get_pending_reviews():
    """Get pending reviews"""
    try:
        response = requests.get(f"{TASK_BASE_URL}/reviews/pending", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task API error: {str(e)}")

@router.post("/review")
async def create_review_task(request: Request):
    """Create review task and trigger events"""
    try:
        body = await request.json()
        
        # Create review task
        response = requests.post(f"{TASK_BASE_URL}/reviews", json=body, timeout=10)
        response.raise_for_status()
        review_data = response.json()
        
        # Log transaction
        await logger.log_transaction({
            "system": "task_manager",
            "type": "review_creation",
            "transaction_id": review_data.get("review_id"),
            "status": "created",
            "metadata": review_data
        })
        
        # Trigger event
        await event_broker.publish_event({
            "event_type": "review_created",
            "source_system": "task_manager",
            "target_systems": ["crm"],
            "payload": review_data,
            "priority": "medium"
        })
        
        return review_data
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Task service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/feedback")
async def submit_feedback(request: Request):
    """Submit feedback and trigger events"""
    try:
        body = await request.json()
        
        # Submit feedback
        response = requests.post(f"{TASK_BASE_URL}/feedback", json=body, timeout=10)
        response.raise_for_status()
        feedback_data = response.json()
        
        # Log API call
        await logger.log_api_call({
            "method": "POST",
            "endpoint": "/feedback",
            "status_code": 200,
            "source": "integrator",
            "target": "task_manager",
            "response_time": 0.1
        })
        
        # Trigger event based on feedback type
        priority = "high" if body.get("rating", 5) < 3 else "medium"
        
        await event_broker.publish_event({
            "event_type": "feedback_submitted",
            "source_system": "task_manager",
            "target_systems": ["crm", "logistics"],
            "payload": feedback_data,
            "priority": priority
        })
        
        return feedback_data
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Task service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/workflow-state")
async def get_workflow_state():
    """Get current workflow state"""
    try:
        response = requests.get(f"{TASK_BASE_URL}/workflow/state", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow API error: {str(e)}")

@router.put("/workflow-state")
async def update_workflow_state(request: Request):
    """Update workflow state and trigger events"""
    try:
        body = await request.json()
        
        # Update workflow state
        response = requests.put(f"{TASK_BASE_URL}/workflow/state", json=body, timeout=10)
        response.raise_for_status()
        workflow_data = response.json()
        
        # Check for state transitions that need compliance
        if body.get("status") in ["completed", "escalated"]:
            compliance_result = await compliance.check_transaction_compliance({
                "type": "workflow_transition",
                "system": "task_manager",
                "metadata": body
            })
            
            if not compliance_result.get("compliant", False):
                raise HTTPException(status_code=403, detail="Workflow transition compliance failed")
        
        # Trigger workflow state change event
        await event_broker.publish_event({
            "event_type": "workflow_state_changed",
            "source_system": "task_manager",
            "target_systems": ["crm", "logistics"],
            "payload": workflow_data,
            "priority": "medium"
        })
        
        return workflow_data
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Task service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhooks/events")
async def receive_task_events(request: Request):
    """Receive events from task management system"""
    try:
        event_data = await request.json()
        
        # Log incoming event
        await logger.log_event({
            "event_type": f"task_{event_data.get('event_type', 'unknown')}",
            "source_system": "task_manager",
            "payload": event_data,
            "status": "received"
        })
        
        # Process specific events
        event_type = event_data.get("event_type")
        if event_type == "task_escalated":
            # Trigger high priority alert
            await event_broker.publish_event({
                "event_type": "task_escalated",
                "source_system": "task_manager",
                "target_systems": ["crm", "logistics"],
                "payload": event_data.get("payload", {}),
                "priority": "high"
            })
            
        elif event_type == "task_completed":
            # Trigger completion workflow
            await event_broker.publish_event({
                "event_type": "task_completed",
                "source_system": "task_manager",
                "target_systems": ["crm"],
                "payload": event_data.get("payload", {}),
                "priority": "medium"
            })
        
        return {"status": "processed"}
        
    except Exception as e:
        print(f"❌ Error processing task webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")