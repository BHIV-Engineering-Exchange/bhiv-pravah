#!/usr/bin/env python3
"""
CRM API endpoints for AI Agent Logistics + CRM System
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from database.crm_service import CRMService
from database.models import create_tables
from integrations.llm_query_system import LLMQuerySystem
from integrations.google_maps_integration import GoogleMapsIntegration, VisitTracker
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json

# Pydantic models for request/response
class AccountCreate(BaseModel):
    name: str
    account_type: Optional[str] = 'customer'
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    territory: Optional[str] = None
    parent_account_id: Optional[str] = None
    account_manager_id: Optional[str] = None
    status: Optional[str] = 'active'
    lifecycle_stage: Optional[str] = 'prospect'
    created_by: Optional[str] = None
    notes: Optional[str] = None

class ContactCreate(BaseModel):
    account_id: str
    first_name: str
    last_name: str
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    contact_role: Optional[str] = 'contact'
    is_primary: Optional[bool] = False
    reports_to_id: Optional[str] = None
    status: Optional[str] = 'active'
    created_by: Optional[str] = None
    notes: Optional[str] = None

class LeadCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    lead_status: Optional[str] = 'new'
    lead_stage: Optional[str] = 'inquiry'
    budget: Optional[float] = None
    timeline: Optional[str] = None
    authority: Optional[str] = None
    need: Optional[str] = None
    assigned_to: Optional[str] = None
    territory: Optional[str] = None
    created_by: Optional[str] = None
    notes: Optional[str] = None

class OpportunityCreate(BaseModel):
    account_id: str
    primary_contact_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    opportunity_type: Optional[str] = 'new_business'
    stage: Optional[str] = 'prospecting'
    probability: Optional[float] = 0.0
    amount: Optional[float] = None
    currency: Optional[str] = 'USD'
    expected_revenue: Optional[float] = None
    close_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    requirements: Optional[str] = None
    products_interested: Optional[str] = None
    competitors: Optional[str] = None
    risks: Optional[str] = None
    created_by: Optional[str] = None
    notes: Optional[str] = None

class ActivityCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    activity_type: str  # call, email, meeting, task, note, visit
    status: Optional[str] = 'planned'
    priority: Optional[str] = 'medium'
    due_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    lead_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    communication_type: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = 'general'
    priority: Optional[str] = 'medium'
    status: Optional[str] = 'pending'
    due_date: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    assigned_to: str
    created_by: Optional[str] = None
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    lead_id: Optional[str] = None

# Create FastAPI app for CRM
crm_app = FastAPI(
    title="AI Agent CRM API",
    description="CRM API for managing accounts, contacts, leads, and opportunities",
    version="1.0.0"
)

# Add CORS middleware
crm_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM Query System
llm_query_system = LLMQuerySystem()

# Initialize Google Maps and Visit Tracker
google_maps = GoogleMapsIntegration()
visit_tracker = VisitTracker(google_maps)

# Initialize database on startup
@crm_app.on_event("startup")
async def startup_event():
    create_tables()
    print("CRM Database initialized")

@crm_app.get("/")
def read_root():
    return {
        "message": "AI Agent CRM API",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Account management",
            "Contact management", 
            "Lead management",
            "Opportunity management",
            "Activity tracking",
            "Task management",
            "CRM analytics"
        ]
    }

@crm_app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with CRMService() as crm_service:
            # Test database connection
            crm_service.get_accounts(limit=1)
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# === ACCOUNT ENDPOINTS ===

@crm_app.post("/accounts", response_model=dict)
def create_account(account: AccountCreate):
    """Create a new account"""
    try:
        with CRMService() as crm_service:
            return crm_service.create_account(account.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@crm_app.get("/accounts", response_model=dict)
def get_accounts(
    account_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    territory: Optional[str] = Query(None),
    account_manager_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get accounts with optional filters"""
    try:
        filters = {}
        if account_type:
            filters['account_type'] = account_type
        if status:
            filters['status'] = status
        if territory:
            filters['territory'] = territory
        if account_manager_id:
            filters['account_manager_id'] = account_manager_id
        
        with CRMService() as crm_service:
            accounts = crm_service.get_accounts(filters=filters, limit=limit)
            return {"accounts": accounts, "count": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/accounts/{account_id}", response_model=dict)
def get_account(account_id: str):
    """Get account by ID with full details"""
    try:
        with CRMService() as crm_service:
            account = crm_service.get_account_by_id(account_id)
            if account:
                return account
            else:
                raise HTTPException(status_code=404, detail="Account not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.put("/accounts/{account_id}", response_model=dict)
def update_account(account_id: str, update_data: dict):
    """Update account"""
    try:
        with CRMService() as crm_service:
            account = crm_service.update_account(account_id, update_data)
            if account:
                return account
            else:
                raise HTTPException(status_code=404, detail="Account not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === CONTACT ENDPOINTS ===

@crm_app.post("/contacts", response_model=dict)
def create_contact(contact: ContactCreate):
    """Create a new contact"""
    try:
        with CRMService() as crm_service:
            return crm_service.create_contact(contact.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@crm_app.get("/contacts", response_model=dict)
def get_contacts(
    account_id: Optional[str] = Query(None),
    contact_role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get contacts with optional filters"""
    try:
        filters = {}
        if contact_role:
            filters['contact_role'] = contact_role
        if status:
            filters['status'] = status
        
        with CRMService() as crm_service:
            contacts = crm_service.get_contacts(account_id=account_id, filters=filters, limit=limit)
            return {"contacts": contacts, "count": len(contacts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/contacts/{contact_id}", response_model=dict)
def get_contact(contact_id: str):
    """Get contact by ID"""
    try:
        with CRMService() as crm_service:
            contact = crm_service.get_contact_by_id(contact_id)
            if contact:
                return contact
            else:
                raise HTTPException(status_code=404, detail="Contact not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === LEAD ENDPOINTS ===

@crm_app.post("/leads", response_model=dict)
def create_lead(lead: LeadCreate):
    """Create a new lead"""
    try:
        with CRMService() as crm_service:
            return crm_service.create_lead(lead.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@crm_app.get("/leads", response_model=dict)
def get_leads(
    lead_status: Optional[str] = Query(None),
    lead_source: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    converted: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get leads with optional filters"""
    try:
        filters = {}
        if lead_status:
            filters['lead_status'] = lead_status
        if lead_source:
            filters['lead_source'] = lead_source
        if assigned_to:
            filters['assigned_to'] = assigned_to
        if converted is not None:
            filters['converted'] = converted
        
        with CRMService() as crm_service:
            leads = crm_service.get_leads(filters=filters, limit=limit)
            return {"leads": leads, "count": len(leads)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/leads/{lead_id}", response_model=dict)
def get_lead(lead_id: str):
    """Get lead by ID"""
    try:
        with CRMService() as crm_service:
            lead = crm_service.get_lead_by_id(lead_id)
            if lead:
                return lead
            else:
                raise HTTPException(status_code=404, detail="Lead not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.post("/leads/{lead_id}/convert", response_model=dict)
def convert_lead(lead_id: str, opportunity_data: OpportunityCreate):
    """Convert lead to opportunity"""
    try:
        with CRMService() as crm_service:
            result = crm_service.convert_lead_to_opportunity(lead_id, opportunity_data.dict())
            return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === OPPORTUNITY ENDPOINTS ===

@crm_app.post("/opportunities", response_model=dict)
def create_opportunity(opportunity: OpportunityCreate):
    """Create a new opportunity"""
    try:
        with CRMService() as crm_service:
            return crm_service.create_opportunity(opportunity.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@crm_app.get("/opportunities", response_model=dict)
def get_opportunities(
    stage: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    is_closed: Optional[bool] = Query(None),
    close_date_from: Optional[datetime] = Query(None),
    close_date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get opportunities with optional filters"""
    try:
        filters = {}
        if stage:
            filters['stage'] = stage
        if owner_id:
            filters['owner_id'] = owner_id
        if account_id:
            filters['account_id'] = account_id
        if is_closed is not None:
            filters['is_closed'] = is_closed
        if close_date_from:
            filters['close_date_from'] = close_date_from
        if close_date_to:
            filters['close_date_to'] = close_date_to
        
        with CRMService() as crm_service:
            opportunities = crm_service.get_opportunities(filters=filters, limit=limit)
            return {"opportunities": opportunities, "count": len(opportunities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/opportunities/{opportunity_id}", response_model=dict)
def get_opportunity(opportunity_id: str):
    """Get opportunity by ID"""
    try:
        with CRMService() as crm_service:
            opportunity = crm_service.get_opportunity_by_id(opportunity_id)
            if opportunity:
                return opportunity
            else:
                raise HTTPException(status_code=404, detail="Opportunity not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.put("/opportunities/{opportunity_id}/stage", response_model=dict)
def update_opportunity_stage(opportunity_id: str, stage_data: dict):
    """Update opportunity stage and probability"""
    try:
        stage = stage_data.get('stage')
        probability = stage_data.get('probability')
        
        if not stage:
            raise HTTPException(status_code=400, detail="Stage is required")
        
        with CRMService() as crm_service:
            opportunity = crm_service.update_opportunity_stage(opportunity_id, stage, probability)
            if opportunity:
                return opportunity
            else:
                raise HTTPException(status_code=404, detail="Opportunity not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === ACTIVITY ENDPOINTS ===

@crm_app.post("/activities", response_model=dict)
def create_activity(activity: ActivityCreate):
    """Create a new activity"""
    try:
        with CRMService() as crm_service:
            return crm_service.create_activity(activity.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@crm_app.get("/activities", response_model=dict)
def get_activities(
    activity_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    opportunity_id: Optional[str] = Query(None),
    lead_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get activities with optional filters"""
    try:
        filters = {}
        if activity_type:
            filters['activity_type'] = activity_type
        if status:
            filters['status'] = status
        if assigned_to:
            filters['assigned_to'] = assigned_to
        if account_id:
            filters['account_id'] = account_id
        if opportunity_id:
            filters['opportunity_id'] = opportunity_id
        if lead_id:
            filters['lead_id'] = lead_id
        
        with CRMService() as crm_service:
            activities = crm_service.get_activities(filters=filters, limit=limit)
            return {"activities": activities, "count": len(activities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.put("/activities/{activity_id}/complete", response_model=dict)
def complete_activity(activity_id: str, completion_data: dict):
    """Mark activity as completed"""
    try:
        outcome = completion_data.get('outcome')
        next_steps = completion_data.get('next_steps')
        
        with CRMService() as crm_service:
            activity = crm_service.complete_activity(activity_id, outcome, next_steps)
            if activity:
                return activity
            else:
                raise HTTPException(status_code=404, detail="Activity not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === TASK ENDPOINTS ===

@crm_app.post("/tasks", response_model=dict)
def create_task(task: TaskCreate):
    """Create a new task"""
    try:
        with CRMService() as crm_service:
            return crm_service.create_task(task.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@crm_app.get("/tasks", response_model=dict)
def get_tasks(
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    opportunity_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get tasks with optional filters"""
    try:
        filters = {}
        if status:
            filters['status'] = status
        if assigned_to:
            filters['assigned_to'] = assigned_to
        if priority:
            filters['priority'] = priority
        if account_id:
            filters['account_id'] = account_id
        if opportunity_id:
            filters['opportunity_id'] = opportunity_id
        
        with CRMService() as crm_service:
            tasks = crm_service.get_tasks(filters=filters, limit=limit)
            return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === VISIT TRACKING ENDPOINTS ===

@crm_app.post("/visits", response_model=dict)
def plan_visit(visit_data: dict):
    """Plan a new visit to an account"""
    try:
        account_id = visit_data.get('account_id')
        if not account_id:
            raise HTTPException(status_code=400, detail="Account ID is required")
        
        # Get account data
        with CRMService() as crm_service:
            account = crm_service.get_account_by_id(account_id)
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
        
        purpose = visit_data.get('purpose', 'Business visit')
        scheduled_time_str = visit_data.get('scheduled_time')
        
        if not scheduled_time_str:
            raise HTTPException(status_code=400, detail="Scheduled time is required")
        
        scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        
        visit_plan = visit_tracker.plan_visit(account, purpose, scheduled_time)
        
        return visit_plan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/visits", response_model=dict)
def get_visits(
    account_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    upcoming_days: Optional[int] = Query(None)
):
    """Get visits with optional filters"""
    try:
        if account_id:
            visits = visit_tracker.get_visits_by_account(account_id)
        elif upcoming_days is not None:
            visits = visit_tracker.get_upcoming_visits(upcoming_days)
        else:
            # Get all visits (implement this method if needed)
            visits = visit_tracker.get_upcoming_visits(365)  # Default to next year
        
        # Filter by status if provided
        if status:
            visits = [v for v in visits if v.get('status') == status]
        
        return {"visits": visits, "count": len(visits)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/visits/{visit_id}", response_model=dict)
def get_visit(visit_id: str):
    """Get visit by ID"""
    try:
        visit = visit_tracker.get_visit_by_id(visit_id)
        if visit:
            return visit
        else:
            raise HTTPException(status_code=404, detail="Visit not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.post("/visits/{visit_id}/start", response_model=dict)
def start_visit(visit_id: str, location_data: dict):
    """Start a visit and log arrival"""
    try:
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        
        if latitude is None or longitude is None:
            raise HTTPException(status_code=400, detail="Current location (latitude, longitude) is required")
        
        visit = visit_tracker.start_visit(visit_id, (latitude, longitude))
        return visit
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.post("/visits/{visit_id}/complete", response_model=dict)
def complete_visit(visit_id: str, completion_data: dict):
    """Complete a visit and log details"""
    try:
        notes = completion_data.get('notes', '')
        outcome = completion_data.get('outcome', '')
        next_steps = completion_data.get('next_steps')
        
        if not notes or not outcome:
            raise HTTPException(status_code=400, detail="Notes and outcome are required")
        
        visit = visit_tracker.complete_visit(visit_id, notes, outcome, next_steps)
        return visit
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.post("/visits/optimize-route", response_model=dict)
def optimize_visit_route(route_data: dict):
    """Optimize route for multiple visits"""
    try:
        visit_ids = route_data.get('visit_ids', [])
        start_location = route_data.get('start_location', '')
        
        if not visit_ids:
            raise HTTPException(status_code=400, detail="Visit IDs are required")
        
        if not start_location:
            raise HTTPException(status_code=400, detail="Start location is required")
        
        optimized_route = visit_tracker.optimize_visit_route(visit_ids, start_location)
        return optimized_route
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === LLM QUERY ENDPOINTS ===

@crm_app.post("/query/natural", response_model=dict)
def process_natural_language_query(query_data: dict):
    """Process natural language queries against CRM data"""
    try:
        query = query_data.get('query', '').strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        user_context = query_data.get('context', {})
        
        # Process the query
        result = llm_query_system.process_query(query, user_context)
        
        # Generate natural language response
        natural_response = llm_query_system.generate_natural_response(result)
        
        return {
            'query': query,
            'result': result,
            'natural_response': natural_response,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@crm_app.get("/query/examples", response_model=dict)
def get_query_examples():
    """Get example natural language queries"""
    return {
        'examples': [
            {
                'query': 'Show me all opportunities closing this month',
                'description': 'Find opportunities with close dates in the current month'
            },
            {
                'query': 'What are the pending tasks for TechCorp?',
                'description': 'Find all pending tasks related to TechCorp account'
            },
            {
                'query': 'List all leads from trade shows not yet converted',
                'description': 'Find unconverted leads from trade show sources'
            },
            {
                'query': 'Account summary for GlobalTech Industries',
                'description': 'Get comprehensive summary of specific account'
            },
            {
                'query': 'Pipeline analysis',
                'description': 'Analyze current sales pipeline performance'
            },
            {
                'query': 'Recent activities',
                'description': 'Show recent activities from the last 30 days'
            }
        ],
        'query_types': [
            'opportunities_closing',
            'pending_tasks',
            'leads_by_source',
            'account_summary',
            'pipeline_analysis',
            'activity_summary'
        ]
    }

# === DASHBOARD AND ANALYTICS ===

@crm_app.get("/dashboard", response_model=dict)
def get_crm_dashboard():
    """Get CRM dashboard data"""
    try:
        with CRMService() as crm_service:
            return crm_service.get_crm_dashboard_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === INTEGRATION ENDPOINTS ===

@crm_app.post("/integrations/bos/order", response_model=dict)
def create_order_from_opportunity(order_data: dict):
    """Create order from opportunity (BOS integration)"""
    try:
        # This would integrate with the existing logistics system
        # For now, return a placeholder response
        return {
            "message": "Order created from opportunity",
            "order_id": f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "opportunity_id": order_data.get('opportunity_id'),
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting CRM API Server...")
    print("CRM API: http://localhost:8001")
    print("CRM Docs: http://localhost:8001/docs")
    uvicorn.run(crm_app, host="0.0.0.0", port=8001)