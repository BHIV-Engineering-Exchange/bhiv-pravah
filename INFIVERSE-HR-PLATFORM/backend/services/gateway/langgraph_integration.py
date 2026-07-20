"""
LangGraph Integration Module for Gateway Service
Provides workflow endpoints and integration with LangGraph service
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import os
import asyncio
from datetime import datetime, timezone

router = APIRouter()

class WorkflowTrigger(BaseModel):
    candidate_id: str
    job_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    job_title: str
    trigger_type: str = "candidate_applied"

class WorkflowStatus(BaseModel):
    workflow_id: str

# LangGraph service configuration  
LANGGRAPH_SERVICE_URL = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")

def get_langgraph_service_url():
    """Get LangGraph service URL"""
    return LANGGRAPH_SERVICE_URL

async def call_langgraph_service(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None):
    """Helper function to call LangGraph service with API key authentication"""
    try:
        # Get API key from environment
        api_key = os.getenv("API_KEY_SECRET", "<YOUR_API_KEY>")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{get_langgraph_service_url()}{endpoint}"
            
            if method == "POST":
                response = await client.post(url, json=data, headers=headers)
            else:
                response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"LangGraph service error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"LangGraph connection failed: {str(e)}"}

@router.post("/workflow/trigger", tags=["LangGraph Workflows"])
async def trigger_workflow(workflow_data: WorkflowTrigger):
    """Trigger LangGraph Workflow"""
    try:
        # Transform data to match LangGraph expected format
        langgraph_data = {
            "candidate_id": workflow_data.candidate_id,
            "job_id": workflow_data.job_id,
            "application_id": workflow_data.candidate_id,  # Use candidate_id as application_id for now
            "candidate_email": workflow_data.candidate_email,
            "candidate_phone": workflow_data.candidate_phone or "",
            "candidate_name": workflow_data.candidate_name,
            "job_title": workflow_data.job_title
        }
        
        # Call LangGraph service to start workflow
        result = await call_langgraph_service("/workflows/application/start", "POST", langgraph_data)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "workflow_id": None,
                "status": "failed"
            }
        
        return {
            "success": True,
            "message": "Workflow triggered successfully",
            "workflow_id": result.get("workflow_id"),
            "status": result.get("status", "started"),
            "trigger_type": workflow_data.trigger_type,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow_id": None,
            "status": "error"
        }

@router.get("/workflow/status/{workflow_id}", tags=["LangGraph Workflows"])
async def get_workflow_status(workflow_id: str):
    """Get Workflow Status"""
    try:
        result = await call_langgraph_service(f"/workflows/{workflow_id}/status")
        
        if "error" in result:
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": result["error"]
            }
        
        return {
            "workflow_id": workflow_id,
            "status": result.get("status", "unknown"),
            "current_stage": result.get("current_stage"),
            "progress": result.get("progress", {}),
            "results": result.get("results", {}),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "workflow_id": workflow_id,
            "status": "error",
            "error": str(e)
        }

@router.get("/workflow/list", tags=["LangGraph Workflows"])
async def list_workflows():
    """List All Workflows"""
    try:
        result = await call_langgraph_service("/workflows")
        
        if "error" in result:
            return {
                "workflows": [],
                "count": 0,
                "error": result["error"]
            }
        
        return {
            "workflows": result.get("workflows", []),
            "count": len(result.get("workflows", [])),
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "workflows": [],
            "count": 0,
            "error": str(e)
        }

@router.get("/workflows", tags=["LangGraph Workflows"])
async def list_workflows_alt():
    """List All Workflows (Alternative endpoint)"""
    return await list_workflows()

@router.get("/workflow/health", tags=["LangGraph Workflows"])
async def check_langgraph_health():
    """Check LangGraph Service Health"""
    try:
        result = await call_langgraph_service("/health")
        
        if "error" in result:
            return {
                "langgraph_status": "disconnected",
                "error": result["error"],
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        
        return {
            "langgraph_status": "connected",
            "service_status": result.get("status", "unknown"),
            "version": result.get("version"),
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "langgraph_status": "error",
            "error": str(e),
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

# Webhook endpoints for workflow automation
@router.post("/webhooks/candidate-applied", tags=["LangGraph Workflows"])
async def webhook_candidate_applied(workflow_data: WorkflowTrigger):
    """Webhook: Candidate Applied - Workflow Automation"""
    workflow_data.trigger_type = "candidate_applied"
    return await trigger_workflow(workflow_data)

@router.post("/webhooks/candidate-shortlisted", tags=["LangGraph Workflows"])
async def webhook_candidate_shortlisted(workflow_data: WorkflowTrigger):
    """Webhook: Candidate Shortlisted - Workflow Automation"""
    workflow_data.trigger_type = "candidate_shortlisted"
    # Use the app folder integration for notifications
    try:
        notification_payload = {
            "candidate_id": workflow_data.candidate_id,
            "candidate_email": workflow_data.candidate_email,
            "candidate_phone": workflow_data.candidate_phone,
            "candidate_name": workflow_data.candidate_name,
            "job_title": workflow_data.job_title,
            "application_status": "shortlisted",
            "message": f"🎉 Congratulations! You've been shortlisted for {workflow_data.job_title}",
            "channels": ["email", "whatsapp"]
        }
        
        result = await call_langgraph_service("/tools/send-notification", "POST", notification_payload)
        return {
            "success": True,
            "message": "Shortlist notification triggered",
            "workflow_id": None,
            "status": "notification_sent",
            "trigger_type": workflow_data.trigger_type,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow_id": None,
            "status": "error"
        }

@router.post("/webhooks/interview-scheduled", tags=["LangGraph Workflows"])
async def webhook_interview_scheduled(workflow_data: WorkflowTrigger):
    """Webhook: Interview Scheduled - Workflow Automation"""
    workflow_data.trigger_type = "interview_scheduled"
    # Use the app folder integration for notifications
    try:
        notification_payload = {
            "candidate_id": workflow_data.candidate_id,
            "candidate_email": workflow_data.candidate_email,
            "candidate_phone": workflow_data.candidate_phone,
            "candidate_name": workflow_data.candidate_name,
            "job_title": workflow_data.job_title,
            "application_status": "interview_scheduled",
            "message": f"📅 Interview scheduled for {workflow_data.job_title}",
            "channels": ["email", "whatsapp"]
        }
        
        result = await call_langgraph_service("/tools/send-notification", "POST", notification_payload)
        return {
            "success": True,
            "message": "Interview notification triggered",
            "workflow_id": None,
            "status": "notification_sent",
            "trigger_type": workflow_data.trigger_type,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow_id": None,
            "status": "error"
        }