"""
Employee Management API Router for BHIV Integrator Core
Handles employee monitoring, attendance, and performance tracking
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

EMPLOYEE_BASE_URL = settings.get("employee_base_url", "http://localhost:8000")

@router.get("/monitoring")
async def get_employee_monitoring():
    """Get employee monitoring data with consent validation"""
    try:
        response = requests.get(f"{EMPLOYEE_BASE_URL}/employee/monitoring", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Employee API error: {str(e)}")

@router.post("/monitoring")
async def create_monitoring_record(request: Request):
    """Create employee monitoring record with privacy compliance"""
    try:
        body = await request.json()
        
        # Validate data privacy and consent
        privacy_result = await compliance.validate_data_privacy(body, "employee_monitoring")
        if not privacy_result.get("valid", False):
            raise HTTPException(status_code=403, detail="Employee monitoring consent required")
        
        # Create monitoring record
        response = requests.post(f"{EMPLOYEE_BASE_URL}/employee/monitoring", json=body, timeout=10)
        response.raise_for_status()
        monitoring_data = response.json()
        
        # Log transaction with compliance
        await logger.log_transaction({
            "system": "employee_management",
            "type": "monitoring_record",
            "transaction_id": monitoring_data.get("record_id"),
            "status": "created",
            "compliance_records": privacy_result,
            "metadata": monitoring_data
        })
        
        # Trigger event
        await event_broker.publish_event({
            "event_type": "monitoring_record_created",
            "source_system": "employee_management",
            "target_systems": ["task_manager"],
            "payload": monitoring_data,
            "priority": "low"
        })
        
        return monitoring_data
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Employee service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/attendance")
async def get_attendance_records():
    """Get employee attendance records"""
    try:
        response = requests.get(f"{EMPLOYEE_BASE_URL}/employee/attendance", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attendance API error: {str(e)}")

@router.post("/attendance")
async def record_attendance(request: Request):
    """Record employee attendance"""
    try:
        body = await request.json()
        
        # Record attendance
        response = requests.post(f"{EMPLOYEE_BASE_URL}/employee/attendance", json=body, timeout=10)
        response.raise_for_status()
        attendance_data = response.json()
        
        # Log API call
        await logger.log_api_call({
            "method": "POST",
            "endpoint": "/attendance",
            "status_code": 200,
            "source": "integrator",
            "target": "employee_management",
            "response_time": 0.1
        })
        
        # Check for attendance anomalies
        if body.get("status") in ["late", "absent"]:
            await event_broker.publish_event({
                "event_type": "attendance_anomaly",
                "source_system": "employee_management",
                "target_systems": ["task_manager"],
                "payload": attendance_data,
                "priority": "medium"
            })
        
        return attendance_data
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Employee service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/performance")
async def get_performance_metrics():
    """Get employee performance metrics"""
    try:
        response = requests.get(f"{EMPLOYEE_BASE_URL}/employee/performance", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance API error: {str(e)}")

@router.post("/alerts")
async def create_employee_alert(request: Request):
    """Create employee alert with compliance logging"""
    try:
        body = await request.json()
        
        # Create alert
        response = requests.post(f"{EMPLOYEE_BASE_URL}/employee/alerts", json=body, timeout=10)
        response.raise_for_status()
        alert_data = response.json()
        
        # Log compliance audit trail
        await compliance.audit_trail_log(
            action="employee_alert_created",
            user_id=body.get("employee_id", "system"),
            resource="employee_alert",
            details=alert_data
        )
        
        # Trigger high priority event for policy violations
        priority = "high" if body.get("alert_type") == "policy_violation" else "medium"
        
        await event_broker.publish_event({
            "event_type": "employee_alert_created",
            "source_system": "employee_management",
            "target_systems": ["task_manager", "crm"],
            "payload": alert_data,
            "priority": priority
        })
        
        return alert_data
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Employee service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhooks/events")
async def receive_employee_events(request: Request):
    """Receive events from employee management system"""
    try:
        event_data = await request.json()
        
        # Log incoming event
        await logger.log_event({
            "event_type": f"employee_{event_data.get('event_type', 'unknown')}",
            "source_system": "employee_management",
            "payload": event_data,
            "status": "received"
        })
        
        # Process specific events
        event_type = event_data.get("event_type")
        if event_type == "productivity_alert":
            # Trigger task assignment optimization
            await event_broker.publish_event({
                "event_type": "productivity_alert",
                "source_system": "employee_management",
                "target_systems": ["task_manager", "logistics"],
                "payload": event_data.get("payload", {}),
                "priority": "medium"
            })
            
        elif event_type == "policy_violation":
            # Trigger compliance workflow
            await event_broker.publish_event({
                "event_type": "policy_violation",
                "source_system": "employee_management",
                "target_systems": ["compliance", "task_manager"],
                "payload": event_data.get("payload", {}),
                "priority": "high"
            })
        
        return {"status": "processed"}
        
    except Exception as e:
        print(f"❌ Error processing employee webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")