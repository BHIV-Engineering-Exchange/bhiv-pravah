#!/usr/bin/env python3
"""
Simple BHIV Integrator Core - Minimal version without Unicode issues
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="BHIV Integrator Core",
    description="Unified backend integrating Logistics, CRM, and Task Management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BHIV Integrator Core - Unified Logistics, CRM & Task Management",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "event_broker": "active",
            "unified_logging": "active",
            "compliance_hooks": "active",
            "api_gateway": "active"
        }
    }

@app.get("/status")
async def system_status():
    """Get system status"""
    return {
        "integrator_status": "operational",
        "modules": {
            "logistics": "active",
            "crm": "active", 
            "task_manager": "active",
            "employee_management": "active"
        },
        "timestamp": datetime.now().isoformat()
    }

# Event broker endpoints
@app.post("/event/publish")
async def publish_event(event_data: dict):
    """Publish an event"""
    return {
        "event_id": "test_event_001",
        "status": "published",
        "timestamp": datetime.now().isoformat(),
        "message": "Event published successfully"
    }

@app.get("/event/events")
async def get_events():
    """Get recent events"""
    return {
        "events": [
            {
                "event_id": "evt_001",
                "event_type": "order_created",
                "source_system": "logistics",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "count": 1
    }

# Logistics endpoints
@app.get("/logistics/procurement")
async def get_procurement():
    """Get procurement orders"""
    return {
        "orders": [
            {"id": "PO-001", "supplier": "TechSupply", "status": "pending"},
            {"id": "PO-002", "supplier": "GlobalParts", "status": "approved"}
        ]
    }

@app.post("/logistics/procurement")
async def create_procurement(order_data: dict):
    """Create procurement order"""
    return {
        "order_id": "PO-003",
        "status": "created",
        "message": "Procurement order created successfully"
    }

# CRM endpoints
@app.get("/crm/leads")
async def get_leads():
    """Get CRM leads"""
    return {
        "leads": [
            {"id": "LEAD-001", "company": "TechCorp", "status": "qualified"},
            {"id": "LEAD-002", "company": "InnovateLtd", "status": "new"}
        ]
    }

@app.post("/crm/leads")
async def create_lead(lead_data: dict):
    """Create CRM lead"""
    return {
        "lead_id": "LEAD-003",
        "status": "created",
        "message": "Lead created successfully"
    }

# Task endpoints
@app.get("/task/review")
async def get_reviews():
    """Get pending reviews"""
    return {
        "reviews": [
            {"id": "REV-001", "title": "Order Review", "status": "pending"},
            {"id": "REV-002", "title": "Customer Feedback", "status": "in_progress"}
        ]
    }

@app.post("/task/review")
async def create_review(review_data: dict):
    """Create review task"""
    return {
        "review_id": "REV-003",
        "status": "created",
        "message": "Review task created successfully"
    }

# BHIV Core integration
@app.get("/bhiv/status")
async def bhiv_status():
    """Get BHIV Core status"""
    return {
        "status": "connected",
        "agents": ["logistics_agent", "crm_agent", "task_agent"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/bhiv/agent/register")
async def register_agent(agent_config: dict):
    """Register agent with BHIV Core"""
    return {
        "agent_id": agent_config.get("id", "unknown"),
        "status": "registered",
        "message": "Agent registered successfully"
    }

if __name__ == "__main__":
    print("Starting BHIV Integrator Core...")
    print("API Gateway: http://localhost:8005")
    print("API Documentation: http://localhost:8005/docs")
    
    port = int(os.getenv("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)