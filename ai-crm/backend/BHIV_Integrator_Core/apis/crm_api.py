"""
CRM API Router for BHIV Integrator Core
Proxies requests to the CRM system and triggers events
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

CRM_BASE_URL = settings.get("crm_base_url", "http://localhost:8502")

@router.get("/accounts")
async def get_accounts():
    """Get CRM accounts"""
    try:
        response = requests.get(f"{CRM_BASE_URL}/accounts", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CRM API error: {str(e)}")

@router.post("/accounts")
async def create_account(request: Request):
    """Create CRM account and trigger events"""
    try:
        body = await request.json()

        # Validate data privacy
        privacy_result = await compliance.validate_data_privacy(body, "account_data")
        if not privacy_result.get("valid", False):
            raise HTTPException(status_code=403, detail="Data privacy validation failed")

        # Create account in CRM system
        response = requests.post(f"{CRM_BASE_URL}/accounts", json=body, timeout=10)
        response.raise_for_status()
        account_data = response.json()

        # Log transaction
        await logger.log_transaction({
            "system": "crm",
            "type": "account_creation",
            "transaction_id": account_data.get("account_id"),
            "amount": account_data.get("annual_revenue", 0),
            "status": "created",
            "parties": [account_data.get("account_manager")],
            "metadata": account_data
        })

        # Trigger event
        await event_broker.publish_event({
            "event_type": "account_created",
            "source_system": "crm",
            "target_systems": ["task_manager"],
            "payload": account_data,
            "priority": "medium"
        })

        return account_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"CRM service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/leads")
async def get_leads():
    """Get CRM leads"""
    try:
        response = requests.get(f"{CRM_BASE_URL}/leads", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CRM API error: {str(e)}")

@router.post("/leads")
async def create_lead(request: Request):
    """Create CRM lead and trigger events"""
    try:
        body = await request.json()

        # Create lead in CRM system
        response = requests.post(f"{CRM_BASE_URL}/leads", json=body, timeout=10)
        response.raise_for_status()
        lead_data = response.json()

        # Log API call
        await logger.log_api_call({
            "method": "POST",
            "endpoint": "/leads",
            "status_code": 200,
            "source": "integrator",
            "target": "crm",
            "response_time": 0.1
        })

        # Trigger event
        await event_broker.publish_event({
            "event_type": "lead_created",
            "source_system": "crm",
            "target_systems": ["task_manager"],
            "payload": lead_data,
            "priority": "medium"
        })

        return lead_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"CRM service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/opportunities")
async def get_opportunities():
    """Get CRM opportunities"""
    try:
        response = requests.get(f"{CRM_BASE_URL}/opportunities", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CRM API error: {str(e)}")

@router.post("/opportunities")
async def create_opportunity(request: Request):
    """Create CRM opportunity and trigger events"""
    try:
        body = await request.json()

        # Check compliance for opportunity value
        compliance_result = await compliance.check_transaction_compliance({
            "type": "opportunity",
            "amount": body.get("amount", 0),
            "system": "crm",
            "parties": [body.get("account_name")],
            "metadata": body
        })

        if not compliance_result.get("compliant", False):
            raise HTTPException(status_code=403, detail="Compliance check failed for opportunity")

        # Create opportunity in CRM system
        response = requests.post(f"{CRM_BASE_URL}/opportunities", json=body, timeout=10)
        response.raise_for_status()
        opportunity_data = response.json()

        # Log transaction
        await logger.log_transaction({
            "system": "crm",
            "type": "opportunity_creation",
            "transaction_id": opportunity_data.get("opportunity_id"),
            "amount": body.get("amount", 0),
            "status": "created",
            "compliance_records": compliance_result
        })

        # Trigger event
        await event_broker.publish_event({
            "event_type": "opportunity_created",
            "source_system": "crm",
            "target_systems": ["task_manager"],
            "payload": opportunity_data,
            "priority": "high"
        })

        return opportunity_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"CRM service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.put("/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: str, request: Request):
    """Update CRM opportunity and trigger events"""
    try:
        body = await request.json()

        # Update opportunity in CRM system
        response = requests.put(f"{CRM_BASE_URL}/opportunities/{opportunity_id}", json=body, timeout=10)
        response.raise_for_status()
        opportunity_data = response.json()

        # Check if stage changed to closed/won
        if body.get("stage") in ["closed_won", "closed_lost"]:
            event_type = "opportunity_won" if body.get("stage") == "closed_won" else "opportunity_lost"

            await event_broker.publish_event({
                "event_type": event_type,
                "source_system": "crm",
                "target_systems": ["task_manager", "logistics"],
                "payload": opportunity_data,
                "priority": "high"
            })

        # Trigger general update event
        await event_broker.publish_event({
            "event_type": "opportunity_updated",
            "source_system": "crm",
            "target_systems": ["task_manager"],
            "payload": opportunity_data,
            "priority": "medium"
        })

        return opportunity_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"CRM service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhooks/events")
async def receive_crm_events(request: Request):
    """Receive events from CRM system"""
    try:
        event_data = await request.json()

        # Log incoming event
        await logger.log_event({
            "event_type": f"crm_{event_data.get('event_type', 'unknown')}",
            "source_system": "crm",
            "payload": event_data,
            "status": "received"
        })

        # Process specific events
        event_type = event_data.get("event_type")
        if event_type == "lead_converted":
            # Trigger opportunity creation
            await event_broker.publish_event({
                "event_type": "lead_to_opportunity",
                "source_system": "crm",
                "target_systems": ["task_manager"],
                "payload": event_data.get("payload", {}),
                "priority": "high"
            })

        elif event_type == "account_status_changed":
            # Trigger compliance check
            await event_broker.publish_event({
                "event_type": "account_status_changed",
                "source_system": "crm",
                "target_systems": ["compliance", "task_manager"],
                "payload": event_data.get("payload", {}),
                "priority": "medium"
            })

        return {"status": "processed"}

    except Exception as e:
        print(f"❌ Error processing CRM webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")