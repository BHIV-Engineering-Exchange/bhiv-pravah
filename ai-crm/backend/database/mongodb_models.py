#!/usr/bin/env python3
"""
MongoDB Models and Schemas for AI Agent Logistics System
Defines document structures for all collections
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
    """Validate ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Custom type for ObjectId with validation
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


# ===== LOGISTICS MODELS =====

class OrderModel(BaseModel):
    """Order document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    order_id: int
    status: str
    customer_id: str
    product_id: str
    quantity: int
    order_date: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ReturnModel(BaseModel):
    """Return document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    product_id: str
    return_quantity: int
    reason: Optional[str] = None
    return_date: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class RestockRequestModel(BaseModel):
    """Restock request document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    product_id: str
    restock_quantity: int
    status: str = "pending"  # pending, approved, completed
    confidence_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class AgentLogModel(BaseModel):
    """Agent log document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    product_id: Optional[str] = None
    quantity: Optional[int] = None
    confidence: Optional[float] = None
    human_review: bool = False
    details: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class HumanReviewModel(BaseModel):
    """Human review document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    review_id: str
    action_type: str
    data: Optional[str] = None  # JSON string
    decision_description: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "pending"  # pending, approved, rejected
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class InventoryModel(BaseModel):
    """Inventory document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    product_id: str
    current_stock: int = 0
    reserved_stock: int = 0
    reorder_point: int = 10
    max_stock: int = 100
    supplier_id: str = "SUPPLIER_001"
    unit_cost: float = 10.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class PurchaseOrderModel(BaseModel):
    """Purchase order document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    po_number: str
    supplier_id: str
    product_id: str
    quantity: int
    unit_cost: float
    total_cost: float
    status: str = "pending"  # pending, sent, confirmed, delivered, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class SupplierModel(BaseModel):
    """Supplier document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    supplier_id: str
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    lead_time_days: int = 7
    minimum_order: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ProductModel(BaseModel):
    """Product document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    product_id: str
    name: str
    category: str
    description: Optional[str] = None
    unit_price: float
    weight_kg: float = 0.0
    dimensions: Optional[str] = None
    supplier_id: str
    reorder_point: int = 10
    max_stock: int = 100
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Image fields
    primary_image_url: Optional[str] = None
    gallery_images: Optional[str] = None  # JSON string
    thumbnail_url: Optional[str] = None
    
    # Marketing fields
    marketing_description: Optional[str] = None
    key_features: Optional[str] = None  # JSON string
    specifications: Optional[str] = None  # JSON string

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ShipmentModel(BaseModel):
    """Shipment document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    shipment_id: str
    order_id: int
    courier_id: str
    tracking_number: str
    status: str = "created"  # created, picked_up, in_transit, out_for_delivery, delivered, failed
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class CourierModel(BaseModel):
    """Courier document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    courier_id: str
    name: str
    service_type: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    avg_delivery_days: int = 3
    coverage_area: Optional[str] = None
    cost_per_kg: float = 5.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


# ===== CRM MODELS =====

class AccountModel(BaseModel):
    """Account document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    account_id: str
    name: str
    account_type: str = "customer"
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Address fields
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Business details
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    territory: Optional[str] = None
    
    # Hierarchy
    parent_account_id: Optional[str] = None
    account_manager_id: Optional[str] = None
    
    # Status
    status: str = "active"
    lifecycle_stage: str = "prospect"
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ContactModel(BaseModel):
    """Contact document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    contact_id: str
    account_id: str
    
    # Personal info
    first_name: str
    last_name: str
    title: Optional[str] = None
    department: Optional[str] = None
    
    # Contact info
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    
    # Role
    contact_role: str = "contact"
    is_primary: bool = False
    reports_to_id: Optional[str] = None
    
    # Status
    status: str = "active"
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class LeadModel(BaseModel):
    """Lead document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    lead_id: str
    
    # Lead info
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Lead source and qualification
    lead_source: Optional[str] = None
    lead_status: str = "new"
    lead_stage: str = "inquiry"
    
    # Qualification
    budget: Optional[float] = None
    timeline: Optional[str] = None
    authority: Optional[str] = None
    need: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    territory: Optional[str] = None
    
    # Conversion
    converted: bool = False
    converted_at: Optional[datetime] = None
    converted_to_account_id: Optional[str] = None
    converted_to_opportunity_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class OpportunityModel(BaseModel):
    """Opportunity document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    opportunity_id: str
    account_id: str
    primary_contact_id: Optional[str] = None
    
    # Opportunity details
    name: str
    description: Optional[str] = None
    opportunity_type: str = "new_business"
    
    # Sales process
    stage: str = "prospecting"
    probability: float = 0.0
    
    # Financial
    amount: Optional[float] = None
    currency: str = "USD"
    expected_revenue: Optional[float] = None
    
    # Timeline
    close_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Assignment
    owner_id: Optional[str] = None
    
    # Requirements
    requirements: Optional[str] = None
    products_interested: Optional[str] = None  # JSON string
    
    # Competition
    competitors: Optional[str] = None
    risks: Optional[str] = None
    
    # Status
    is_closed: bool = False
    is_won: bool = False
    closed_at: Optional[datetime] = None
    closed_reason: Optional[str] = None
    
    # Metadata
    created_by: Optional[str] = None
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ActivityModel(BaseModel):
    """Activity document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    activity_id: str
    
    # Activity details
    subject: str
    description: Optional[str] = None
    activity_type: str
    status: str = "planned"
    priority: str = "medium"
    
    # Timing
    due_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    
    # Relationships
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    lead_id: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    
    # Communication details
    communication_type: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    
    # Location
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class TaskModel(BaseModel):
    """Task document model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    task_id: str
    
    # Task details
    title: str
    description: Optional[str] = None
    task_type: str = "general"
    priority: str = "medium"
    status: str = "pending"
    
    # Timing
    due_date: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Assignment
    assigned_to: str
    created_by: Optional[str] = None
    
    # CRM relationships
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    lead_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


# Helper function to create indexes
def create_indexes(db):
    """Create indexes for all collections"""
    
    # Logistics indexes
    db.orders.create_index("order_id", unique=True)
    db.orders.create_index("status")
    db.orders.create_index("product_id")
    
    db.returns.create_index("product_id")
    db.returns.create_index("processed")
    
    db.restock_requests.create_index("product_id")
    db.restock_requests.create_index("status")
    
    db.inventory.create_index("product_id", unique=True)
    
    db.purchase_orders.create_index("po_number", unique=True)
    db.purchase_orders.create_index("product_id")
    db.purchase_orders.create_index("status")
    
    db.suppliers.create_index("supplier_id", unique=True)
    
    db.products.create_index("product_id", unique=True)
    db.products.create_index("category")
    
    db.shipments.create_index("shipment_id", unique=True)
    db.shipments.create_index("tracking_number", unique=True)
    db.shipments.create_index("order_id")
    
    # CRM indexes
    db.accounts.create_index("account_id", unique=True)
    db.accounts.create_index("account_type")
    db.accounts.create_index("status")
    
    db.contacts.create_index("contact_id", unique=True)
    db.contacts.create_index("account_id")
    db.contacts.create_index("email")
    
    db.leads.create_index("lead_id", unique=True)
    db.leads.create_index("lead_status")
    db.leads.create_index("email")
    
    db.opportunities.create_index("opportunity_id", unique=True)
    db.opportunities.create_index("account_id")
    db.opportunities.create_index("stage")
    
    db.activities.create_index("activity_id", unique=True)
    db.activities.create_index([("account_id", 1), ("created_at", -1)])
    
    db.tasks.create_index("task_id", unique=True)
    db.tasks.create_index("assigned_to")
    db.tasks.create_index("status")
    
    db.agent_logs.create_index([("timestamp", -1)])
    db.human_reviews.create_index("review_id", unique=True)

    # SETU indexes
    db.setu_trace_lineage.create_index("execution_id", unique=True)
    db.setu_trace_lineage.create_index([("trace_id", 1), ("tenant_id", 1)])
    db.setu_trace_lineage.create_index("tenant_id")

    db.setu_trace_logs.create_index([("trace_id", 1), ("timestamp", -1)])
    db.setu_trace_logs.create_index("event")

    db.setu_lineage_events.create_index("lineage_event_id", unique=True)
    db.setu_lineage_events.create_index([("trace_id", 1), ("sequence", 1)])

    db.setu_telemetry_events.create_index([("trace_id", 1), ("timestamp", 1)])
    db.setu_telemetry_events.create_index("event_type")
    
    print("[OK] MongoDB indexes created successfully")
