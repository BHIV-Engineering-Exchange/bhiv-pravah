"""
Logistics API Router for BHIV Integrator Core
Proxies requests to the logistics system and triggers events
"""

from fastapi import APIRouter, HTTPException, Request
import requests
from typing import Dict, Any
from datetime import datetime
import json
import random
from config.settings import settings
from event_broker.event_broker import EventBroker
from unified_logging.logger import UnifiedLogger
from compliance.compliance_hooks import ComplianceHooks

router = APIRouter()
event_broker = EventBroker()
logger = UnifiedLogger()
compliance = ComplianceHooks()

LOGISTICS_BASE_URL = settings.get("logistics_base_url", "http://localhost:8000")

@router.get("/procurement")
async def get_procurement_orders():
    """Get procurement orders"""
    try:
        response = requests.get(f"{LOGISTICS_BASE_URL}/procurement/orders", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Procurement API error: {str(e)}")

@router.post("/procurement")
async def create_procurement_order(request: Request):
    """Create procurement order and trigger events"""
    try:
        body = await request.json()

        # Check compliance
        compliance_result = await compliance.check_transaction_compliance({
            "type": "procurement_order",
            "amount": body.get("total_value", 0),
            "system": "logistics",
            "parties": [body.get("supplier_id")],
            "metadata": body
        })

        if not compliance_result.get("compliant", False):
            raise HTTPException(status_code=403, detail="Compliance check failed")

        # Create order in logistics system
        response = requests.post(f"{LOGISTICS_BASE_URL}/procurement/orders", json=body, timeout=10)
        response.raise_for_status()
        order_data = response.json()

        # Log transaction
        await logger.log_transaction({
            "system": "logistics",
            "type": "procurement_order",
            "transaction_id": order_data.get("order_id"),
            "amount": body.get("total_value", 0),
            "status": "created",
            "compliance_records": compliance_result
        })

        # Trigger event
        await event_broker.publish_event({
            "event_type": "procurement_order_created",
            "source_system": "logistics",
            "target_systems": ["crm", "task_manager"],
            "payload": order_data,
            "priority": "high"
        })

        return order_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Logistics service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/delivery")
async def get_deliveries():
    """Get deliveries"""
    try:
        response = requests.get(f"{LOGISTICS_BASE_URL}/delivery/orders", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delivery API error: {str(e)}")

@router.post("/delivery")
async def create_delivery(request: Request):
    """Create delivery and trigger events with performance-based assignment"""
    try:
        body = await request.json()

        # Assign delivery based on employee performance scores
        assigned_employee = await assign_delivery_to_employee(body)

        # Add assignment to delivery data
        body["assigned_employee"] = assigned_employee

        # Create delivery in logistics system
        response = requests.post(f"{LOGISTICS_BASE_URL}/delivery/orders", json=body, timeout=10)
        response.raise_for_status()
        delivery_data = response.json()

        # Log API call
        await logger.log_api_call({
            "method": "POST",
            "endpoint": "/delivery",
            "status_code": 200,
            "source": "integrator",
            "target": "logistics",
            "response_time": 0.1  # Simplified
        })

        # Trigger event with assignment info
        await event_broker.publish_event({
            "event_type": "delivery_created",
            "source_system": "logistics",
            "target_systems": ["crm", "task_manager"],
            "payload": {
                **delivery_data,
                "assigned_employee": assigned_employee,
                "assignment_reason": "performance_based"
            },
            "priority": "medium"
        })

        return delivery_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Logistics service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/inventory")
async def get_inventory():
    """Get inventory levels"""
    try:
        response = requests.get(f"{LOGISTICS_BASE_URL}/inventory", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory API error: {str(e)}")

@router.put("/inventory/{product_id}")
async def update_inventory(product_id: str, request: Request):
    """Update inventory and trigger low stock alerts"""
    try:
        body = await request.json()

        # Update inventory in logistics system
        response = requests.put(f"{LOGISTICS_BASE_URL}/inventory/{product_id}", json=body, timeout=10)
        response.raise_for_status()
        inventory_data = response.json()

        # Check for low stock
        current_stock = inventory_data.get("current_stock", 0)
        min_stock = inventory_data.get("min_stock_level", 10)

        if current_stock <= min_stock:
            # Trigger low stock event
            await event_broker.publish_event({
                "event_type": "inventory_low",
                "source_system": "logistics",
                "target_systems": ["procurement", "crm"],
                "payload": {
                    "product_id": product_id,
                    "current_stock": current_stock,
                    "min_stock_level": min_stock,
                    "product_name": inventory_data.get("product_name")
                },
                "priority": "high"
            })

        return inventory_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Logistics service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhooks/events")
async def receive_logistics_events(request: Request):
    """Receive events from logistics system"""
    try:
        event_data = await request.json()

        # Log incoming event
        await logger.log_event({
            "event_type": f"logistics_{event_data.get('event_type', 'unknown')}",
            "source_system": "logistics",
            "payload": event_data,
            "status": "received"
        })

        # Process specific events
        event_type = event_data.get("event_type")
        if event_type == "order_delivered":
            # Trigger CRM opportunity update
            await event_broker.publish_event({
                "event_type": "delivery_completed",
                "source_system": "logistics",
                "target_systems": ["crm"],
                "payload": event_data.get("payload", {}),
                "priority": "medium"
            })

        elif event_type == "order_delayed":
            # Trigger task escalation
            await event_broker.publish_event({
                "event_type": "delivery_delayed",
                "source_system": "logistics",
                "target_systems": ["task_manager", "crm"],
                "payload": event_data.get("payload", {}),
                "priority": "high"
            })

        return {"status": "processed"}

    except Exception as e:
        print(f"❌ Error processing logistics webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

async def assign_delivery_to_employee(delivery_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assign delivery to employee based on performance scores"""
    try:
        # Mock employee performance data (in production, fetch from database/CRM)
        employees = [
            {"id": "emp_001", "name": "John Doe", "performance_score": 95, "current_load": 3},
            {"id": "emp_002", "name": "Jane Smith", "performance_score": 88, "current_load": 2},
            {"id": "emp_003", "name": "Bob Johnson", "performance_score": 92, "current_load": 4},
            {"id": "emp_004", "name": "Alice Brown", "performance_score": 85, "current_load": 1}
        ]

        # Filter available employees (current_load < 5)
        available_employees = [emp for emp in employees if emp["current_load"] < 5]

        if not available_employees:
            # Fallback to any employee if all are busy
            available_employees = employees

        # Sort by performance score (descending) and current load (ascending)
        sorted_employees = sorted(
            available_employees,
            key=lambda x: (x["performance_score"], -x["current_load"]),
            reverse=True
        )

        # Select top performer
        assigned_employee = sorted_employees[0]

        # Update load (in production, this would be persisted)
        assigned_employee["current_load"] += 1

        return {
            "employee_id": assigned_employee["id"],
            "employee_name": assigned_employee["name"],
            "performance_score": assigned_employee["performance_score"],
            "current_load": assigned_employee["current_load"] - 1,  # Return previous load
            "assignment_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error assigning delivery: {str(e)}")
        # Fallback assignment
        return {
            "employee_id": "emp_fallback",
            "employee_name": "System Assignment",
            "performance_score": 0,
            "current_load": 0,
            "assignment_timestamp": datetime.now().isoformat()
        }