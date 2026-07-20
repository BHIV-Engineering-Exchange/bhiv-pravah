#!/usr/bin/env python3
"""
Database models for AI Agent Logistics System
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os
import random

Base = declarative_base()

class Order(Base):
    """Order model"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False)
    customer_id = Column(String(100))
    product_id = Column(String(50))
    quantity = Column(Integer)
    order_date = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Order(order_id={self.order_id}, status='{self.status}')>"

class Return(Base):
    """Return model"""
    __tablename__ = 'returns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False, index=True)
    return_quantity = Column(Integer, nullable=False)
    reason = Column(String(200))
    return_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Return(product_id='{self.product_id}', quantity={self.return_quantity})>"

class RestockRequest(Base):
    """Restock request model"""
    __tablename__ = 'restock_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), nullable=False, index=True)
    restock_quantity = Column(Integer, nullable=False)
    status = Column(String(50), default='pending')  # pending, approved, completed
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<RestockRequest(product_id='{self.product_id}', quantity={self.restock_quantity}, status='{self.status}')>"

class AgentLog(Base):
    """Agent action log model"""
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(100), nullable=False)
    product_id = Column(String(50))
    quantity = Column(Integer)
    confidence = Column(Float)
    human_review = Column(Boolean, default=False)
    details = Column(Text)
    
    def __repr__(self):
        return f"<AgentLog(action='{self.action}', product_id='{self.product_id}')>"

class HumanReview(Base):
    """Human review model"""
    __tablename__ = 'human_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(100), unique=True, nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    data = Column(Text)  # JSON data
    decision_description = Column(Text)
    confidence = Column(Float)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewer_notes = Column(Text)
    
    def __repr__(self):
        return f"<HumanReview(review_id='{self.review_id}', status='{self.status}')>"

class Inventory(Base):
    """Inventory model"""
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), unique=True, nullable=False, index=True)
    current_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)  # Stock reserved for orders
    reorder_point = Column(Integer, default=10)
    max_stock = Column(Integer, default=100)
    supplier_id = Column(String(50), default='SUPPLIER_001')
    unit_cost = Column(Float, default=10.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def available_stock(self):
        return self.current_stock - self.reserved_stock

    @property
    def needs_reorder(self):
        return self.current_stock <= self.reorder_point

    def __repr__(self):
        return f"<Inventory(product_id='{self.product_id}', stock={self.current_stock})>"

class PurchaseOrder(Base):
    """Purchase Order model"""
    __tablename__ = 'purchase_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(50), nullable=False)
    product_id = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    status = Column(String(20), default='pending')  # pending, sent, confirmed, delivered, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    expected_delivery = Column(DateTime)
    delivered_at = Column(DateTime)
    notes = Column(Text)

    def __repr__(self):
        return f"<PurchaseOrder(po_number='{self.po_number}', product='{self.product_id}', status='{self.status}')>"

class Supplier(Base):
    """Supplier model"""
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    api_endpoint = Column(String(500))  # For API integration
    api_key = Column(String(200))
    lead_time_days = Column(Integer, default=7)
    minimum_order = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Supplier(supplier_id='{self.supplier_id}', name='{self.name}')>"

class Shipment(Base):
    """Shipment model for delivery tracking"""
    __tablename__ = 'shipments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    courier_id = Column(String(50), nullable=False)
    tracking_number = Column(String(100), unique=True, nullable=False)
    status = Column(String(50), default='created')  # created, picked_up, in_transit, out_for_delivery, delivered, failed
    origin_address = Column(Text)
    destination_address = Column(Text)
    estimated_delivery = Column(DateTime)
    actual_delivery = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    picked_up_at = Column(DateTime)
    delivered_at = Column(DateTime)
    notes = Column(Text)

    def __repr__(self):
        return f"<Shipment(shipment_id='{self.shipment_id}', status='{self.status}')>"

class Courier(Base):
    """Courier/delivery service model"""
    __tablename__ = 'couriers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    courier_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    service_type = Column(String(100))  # standard, express, overnight
    api_endpoint = Column(String(500))
    api_key = Column(String(200))
    avg_delivery_days = Column(Integer, default=3)
    coverage_area = Column(String(200))
    cost_per_kg = Column(Float, default=5.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Courier(courier_id='{self.courier_id}', name='{self.name}')>"

class Product(Base):
    """Product catalog model with image support"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text)
    unit_price = Column(Float, nullable=False)
    weight_kg = Column(Float, default=0.0)
    dimensions = Column(String(100))
    supplier_id = Column(String(50), nullable=False)
    reorder_point = Column(Integer, default=10)
    max_stock = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Image fields
    primary_image_url = Column(String(500))  # Main product image
    gallery_images = Column(Text)  # JSON array of additional image URLs
    thumbnail_url = Column(String(500))  # Optimized thumbnail
    
    # Marketing fields for suppliers/salesmen
    marketing_description = Column(Text)  # Detailed marketing copy
    key_features = Column(Text)  # JSON array of key features
    specifications = Column(Text)  # JSON object with detailed specs
    
    def __repr__(self):
        return f"<Product(product_id='{self.product_id}', name='{self.name}')>"

class DeliveryEvent(Base):
    """Delivery tracking events"""
    __tablename__ = 'delivery_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # status_update, location_update, delivery_attempt
    event_description = Column(Text)
    location = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow)
    courier_notes = Column(Text)

    def __repr__(self):
        return f"<DeliveryEvent(shipment_id='{self.shipment_id}', event='{self.event_type}')>"

class Alert(Base):
    """System alerts and notifications"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # stockout, delay, error, threshold
    severity = Column(String(20), default='medium')  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    entity_type = Column(String(50))  # order, product, shipment, supplier
    entity_id = Column(String(50))
    status = Column(String(20), default='active')  # active, acknowledged, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    resolved_by = Column(String(100))

    def __repr__(self):
        return f"<Alert(alert_id='{self.alert_id}', type='{self.alert_type}', severity='{self.severity}')>"

class KPIMetric(Base):
    """KPI metrics tracking"""
    __tablename__ = 'kpi_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # percentage, count, currency, time
    category = Column(String(50))  # performance, efficiency, quality, financial
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    period_type = Column(String(20), default='daily')  # hourly, daily, weekly, monthly

    def __repr__(self):
        return f"<KPIMetric(name='{self.metric_name}', value={self.metric_value})>"

class NotificationLog(Base):
    """Notification delivery log"""
    __tablename__ = 'notification_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(String(50), unique=True, nullable=False)
    notification_type = Column(String(50), nullable=False)  # email, sms, push, console
    recipient = Column(String(200))
    subject = Column(String(200))
    message = Column(Text)
    status = Column(String(20), default='pending')  # pending, sent, delivered, failed
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    error_message = Column(Text)

    def __repr__(self):
        return f"<NotificationLog(id='{self.notification_id}', type='{self.notification_type}', status='{self.status}')>"

# ===== CRM MODELS =====

class Account(Base):
    """Account/Company model for CRM"""
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    account_type = Column(String(50), default='customer')  # customer, distributor, dealer, supplier, partner
    industry = Column(String(100))
    website = Column(String(200))
    phone = Column(String(50))
    email = Column(String(200))
    
    # Address fields
    billing_address = Column(Text)
    shipping_address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Business details
    annual_revenue = Column(Float)
    employee_count = Column(Integer)
    territory = Column(String(100))
    
    # Hierarchy and relationships
    parent_account_id = Column(String(50), ForeignKey('accounts.account_id'))
    account_manager_id = Column(String(50))  # User ID of account manager
    
    # Status and lifecycle
    status = Column(String(50), default='active')  # active, inactive, prospect, customer
    lifecycle_stage = Column(String(50), default='prospect')  # prospect, customer, partner, inactive
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    contacts = relationship("Contact", back_populates="account")
    opportunities = relationship("Opportunity", back_populates="account")
    leads = relationship("Lead", back_populates="account")
    activities = relationship("Activity", back_populates="account")
    
    def __repr__(self):
        return f"<Account(account_id='{self.account_id}', name='{self.name}', type='{self.account_type}')>"

class Contact(Base):
    """Contact/Person model for CRM"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(String(50), ForeignKey('accounts.account_id'), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))  # Job title
    department = Column(String(100))
    
    # Contact information
    email = Column(String(200))
    phone = Column(String(50))
    mobile = Column(String(50))
    
    # Role and hierarchy
    contact_role = Column(String(50), default='contact')  # decision_maker, influencer, contact, distributor, dealer
    is_primary = Column(Boolean, default=False)
    reports_to_id = Column(String(50), ForeignKey('contacts.contact_id'))
    
    # Status
    status = Column(String(50), default='active')  # active, inactive, do_not_contact
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="contacts")
    opportunities = relationship("Opportunity", back_populates="primary_contact")
    activities = relationship("Activity", back_populates="contact")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<Contact(contact_id='{self.contact_id}', name='{self.full_name}', role='{self.contact_role}')>"

class Lead(Base):
    """Lead model for CRM"""
    __tablename__ = 'leads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Lead information
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(300))
    title = Column(String(100))
    email = Column(String(200))
    phone = Column(String(50))
    
    # Lead source and qualification
    lead_source = Column(String(100))  # website, trade_show, referral, cold_call, social_media
    lead_status = Column(String(50), default='new')  # new, contacted, qualified, unqualified, converted
    lead_stage = Column(String(50), default='inquiry')  # inquiry, qualified, proposal, negotiation
    
    # Qualification details
    budget = Column(Float)
    timeline = Column(String(100))
    authority = Column(String(100))  # decision_maker, influencer, none
    need = Column(Text)
    
    # Assignment and ownership
    assigned_to = Column(String(50))  # User ID of assigned sales rep
    territory = Column(String(100))
    
    # Conversion tracking
    converted = Column(Boolean, default=False)
    converted_at = Column(DateTime)
    converted_to_account_id = Column(String(50), ForeignKey('accounts.account_id'))
    converted_to_opportunity_id = Column(String(50), ForeignKey('opportunities.opportunity_id'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="leads")
    activities = relationship("Activity", back_populates="lead")
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or "Unknown"
    
    def __repr__(self):
        return f"<Lead(lead_id='{self.lead_id}', name='{self.full_name}', status='{self.lead_status}')>"

class Opportunity(Base):
    """Opportunity/Deal model for CRM"""
    __tablename__ = 'opportunities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(String(50), ForeignKey('accounts.account_id'), nullable=False)
    primary_contact_id = Column(String(50), ForeignKey('contacts.contact_id'))
    
    # Opportunity details
    name = Column(String(300), nullable=False)
    description = Column(Text)
    opportunity_type = Column(String(50), default='new_business')  # new_business, existing_business, renewal
    
    # Sales process
    stage = Column(String(50), default='prospecting')  # prospecting, qualification, proposal, negotiation, closed_won, closed_lost
    probability = Column(Float, default=0.0)  # 0-100%
    
    # Financial details
    amount = Column(Float)
    currency = Column(String(10), default='USD')
    expected_revenue = Column(Float)
    
    # Timeline
    close_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Assignment
    owner_id = Column(String(50))  # User ID of opportunity owner
    
    # Customer requirements
    requirements = Column(Text)  # JSON or text describing customer requirements
    products_interested = Column(Text)  # JSON array of product IDs
    
    # Competition and risks
    competitors = Column(Text)
    risks = Column(Text)
    
    # Status tracking
    is_closed = Column(Boolean, default=False)
    is_won = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    closed_reason = Column(Text)
    
    # Metadata
    created_by = Column(String(50))
    notes = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="opportunities")
    primary_contact = relationship("Contact", back_populates="opportunities")
    activities = relationship("Activity", back_populates="opportunity")
    
    def __repr__(self):
        return f"<Opportunity(opportunity_id='{self.opportunity_id}', name='{self.name}', stage='{self.stage}')>"

class Activity(Base):
    """Activity/Task/Event model for CRM"""
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Activity details
    subject = Column(String(300), nullable=False)
    description = Column(Text)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, task, note, visit
    status = Column(String(50), default='planned')  # planned, in_progress, completed, cancelled
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    
    # Timing
    due_date = Column(DateTime)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    
    # Relationships
    account_id = Column(String(50), ForeignKey('accounts.account_id'))
    contact_id = Column(String(50), ForeignKey('contacts.contact_id'))
    opportunity_id = Column(String(50), ForeignKey('opportunities.opportunity_id'))
    lead_id = Column(String(50), ForeignKey('leads.lead_id'))
    
    # Assignment
    assigned_to = Column(String(50))  # User ID
    created_by = Column(String(50))
    
    # Communication details (for calls, emails, meetings)
    communication_type = Column(String(50))  # inbound, outbound
    outcome = Column(Text)
    next_steps = Column(Text)
    
    # Location (for visits/meetings)
    location = Column(String(300))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    account = relationship("Account", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")
    opportunity = relationship("Opportunity", back_populates="activities")
    lead = relationship("Lead", back_populates="activities")
    
    def __repr__(self):
        return f"<Activity(activity_id='{self.activity_id}', type='{self.activity_type}', subject='{self.subject}')>"

class CommunicationLog(Base):
    """Communication log for emails, calls, messages"""
    __tablename__ = 'communication_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    communication_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Communication details
    communication_type = Column(String(50), nullable=False)  # email, call, sms, internal_message
    direction = Column(String(20), nullable=False)  # inbound, outbound
    subject = Column(String(300))
    content = Column(Text)
    
    # Participants
    from_address = Column(String(200))
    to_addresses = Column(Text)  # JSON array
    cc_addresses = Column(Text)  # JSON array
    
    # Status
    status = Column(String(50), default='sent')  # sent, delivered, read, failed
    
    # Relationships
    account_id = Column(String(50), ForeignKey('accounts.account_id'))
    contact_id = Column(String(50), ForeignKey('contacts.contact_id'))
    opportunity_id = Column(String(50), ForeignKey('opportunities.opportunity_id'))
    lead_id = Column(String(50), ForeignKey('leads.lead_id'))
    
    # Integration details
    external_id = Column(String(200))  # ID from external system (Office 365, etc.)
    integration_source = Column(String(50))  # office365, gmail, internal
    
    # Metadata
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(50))
    
    def __repr__(self):
        return f"<CommunicationLog(communication_id='{self.communication_id}', type='{self.communication_type}')>"

class Task(Base):
    """Task/Reminder model integrated with CRM"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Task details
    title = Column(String(300), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), default='general')  # general, follow_up, reminder, deadline
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    status = Column(String(50), default='pending')  # pending, in_progress, completed, cancelled
    
    # Timing
    due_date = Column(DateTime)
    reminder_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Assignment
    assigned_to = Column(String(50), nullable=False)  # User ID
    created_by = Column(String(50))
    
    # CRM relationships
    account_id = Column(String(50), ForeignKey('accounts.account_id'))
    contact_id = Column(String(50), ForeignKey('contacts.contact_id'))
    opportunity_id = Column(String(50), ForeignKey('opportunities.opportunity_id'))
    lead_id = Column(String(50), ForeignKey('leads.lead_id'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Task(task_id='{self.task_id}', title='{self.title}', status='{self.status}')>"

class Note(Base):
    """Note model for CRM entities"""
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Note content
    title = Column(String(300))
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default='general')  # general, meeting_notes, call_notes, internal
    
    # Relationships
    account_id = Column(String(50), ForeignKey('accounts.account_id'))
    contact_id = Column(String(50), ForeignKey('contacts.contact_id'))
    opportunity_id = Column(String(50), ForeignKey('opportunities.opportunity_id'))
    lead_id = Column(String(50), ForeignKey('leads.lead_id'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))
    
    def __repr__(self):
        return f"<Note(note_id='{self.note_id}', type='{self.note_type}')>"

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///logistics_agent.db')

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created successfully")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with sample data using product catalog"""
    create_tables()
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Order).first():
            print("[INFO] Database already has data, skipping initialization")
            return
        
        # Import user product catalog
        try:
            from user_product_models import (
                USER_PRODUCT_CATALOG, 
                generate_sample_orders, 
                generate_sample_returns, 
                generate_sample_shipments,
                get_user_product_quantities
            )
            print("[OK] Loaded user product catalog from Excel file")
        except ImportError:
            print("[WARN] User product catalog not found, using default products")
            USER_PRODUCT_CATALOG = []
        
        # Generate sample orders using user product catalog
        if USER_PRODUCT_CATALOG:
            sample_order_data = generate_sample_orders()
            sample_orders = []
            for order_data in sample_order_data:
                order = Order(
                    order_id=order_data['order_id'],
                    status=order_data['status'],
                    customer_id=order_data['customer_id'],
                    product_id=order_data['product_id'],
                    quantity=order_data['quantity'],
                    order_date=order_data['order_date']
                )
                sample_orders.append(order)
        else:
            # Fallback to old product IDs
            sample_orders = [
                Order(order_id=101, status='Shipped', customer_id='CUST001', product_id='A101', quantity=2),
                Order(order_id=102, status='Delivered', customer_id='CUST002', product_id='B202', quantity=1),
                Order(order_id=103, status='Processing', customer_id='CUST003', product_id='C303', quantity=3),
                Order(order_id=104, status='Cancelled', customer_id='CUST004', product_id='D404', quantity=1),
                Order(order_id=105, status='In Transit', customer_id='CUST005', product_id='E505', quantity=2),
            ]
        
        # Generate sample returns using user product catalog
        if USER_PRODUCT_CATALOG:
            sample_return_data = generate_sample_returns()
            sample_returns = []
            for return_data in sample_return_data:
                return_item = Return(
                    product_id=return_data['product_id'],
                    return_quantity=return_data['return_quantity'],
                    reason=return_data['reason'],
                    return_date=return_data['return_date']
                )
                sample_returns.append(return_item)
        else:
            # Fallback to old product IDs
            sample_returns = [
                Return(product_id='A101', return_quantity=6, reason='Defective'),
                Return(product_id='B202', return_quantity=3, reason='Wrong size'),
                Return(product_id='C303', return_quantity=25, reason='Bulk return'),
                Return(product_id='D404', return_quantity=2, reason='Not needed'),
                Return(product_id='E505', return_quantity=12, reason='Damaged'),
            ]
        
        # Add sample suppliers
        sample_suppliers = [
            Supplier(
                supplier_id='SUPPLIER_001',
                name='TechParts Supply Co.',
                contact_email='orders@techparts.com',
                contact_phone='+1-555-0101',
                api_endpoint='http://localhost:8001/api/supplier',
                lead_time_days=5,
                minimum_order=10
            ),
            Supplier(
                supplier_id='SUPPLIER_002',
                name='Global Components Ltd.',
                contact_email='procurement@globalcomp.com',
                contact_phone='+1-555-0102',
                api_endpoint='http://localhost:8002/api/supplier',
                lead_time_days=7,
                minimum_order=5
            ),
            Supplier(
                supplier_id='SUPPLIER_003',
                name='FastTrack Logistics',
                contact_email='orders@fasttrack.com',
                contact_phone='+1-555-0103',
                api_endpoint='http://localhost:8003/api/supplier',
                lead_time_days=3,
                minimum_order=20
            )
        ]

        # Add sample couriers
        sample_couriers = [
            Courier(
                courier_id='COURIER_001',
                name='FastShip Express',
                service_type='express',
                api_endpoint='http://localhost:9001/api/courier',
                avg_delivery_days=2,
                coverage_area='National',
                cost_per_kg=8.50
            ),
            Courier(
                courier_id='COURIER_002',
                name='Standard Delivery Co.',
                service_type='standard',
                api_endpoint='http://localhost:9002/api/courier',
                avg_delivery_days=5,
                coverage_area='Regional',
                cost_per_kg=4.25
            ),
            Courier(
                courier_id='COURIER_003',
                name='Overnight Rush',
                service_type='overnight',
                api_endpoint='http://localhost:9003/api/courier',
                avg_delivery_days=1,
                coverage_area='Metro',
                cost_per_kg=15.00
            )
        ]

        # Add inventory based on user product catalog
        if USER_PRODUCT_CATALOG:
            sample_inventory = []
            for product in USER_PRODUCT_CATALOG:
                inventory_item = Inventory(
                    product_id=product.product_id,
                    current_stock=product.current_qty,
                    reorder_point=product.reorder_point,
                    max_stock=product.max_stock,
                    supplier_id=product.supplier_id,
                    unit_cost=product.unit_price * 0.7  # Cost is 70% of selling price
                )
                sample_inventory.append(inventory_item)
        else:
            # Fallback inventory
            sample_inventory = [
                Inventory(product_id='A101', current_stock=8, reorder_point=10, supplier_id='SUPPLIER_001', unit_cost=15.50),
                Inventory(product_id='B202', current_stock=3, reorder_point=5, supplier_id='SUPPLIER_002', unit_cost=22.00),
                Inventory(product_id='C303', current_stock=100, reorder_point=20, supplier_id='SUPPLIER_001', unit_cost=8.75),
                Inventory(product_id='D404', current_stock=15, reorder_point=8, supplier_id='SUPPLIER_003', unit_cost=45.00),
                Inventory(product_id='E505', current_stock=2, reorder_point=15, supplier_id='SUPPLIER_002', unit_cost=12.25),
            ]
        
        # Generate sample shipments using user product catalog
        if USER_PRODUCT_CATALOG:
            sample_shipment_data = generate_sample_shipments()
            sample_shipments = []
            for shipment_data in sample_shipment_data:
                shipment = Shipment(
                    shipment_id=shipment_data['shipment_id'],
                    order_id=shipment_data['order_id'],
                    courier_id=shipment_data['courier_id'],
                    tracking_number=shipment_data['tracking_number'],
                    status=shipment_data['status'],
                    origin_address=shipment_data['origin_address'],
                    destination_address=shipment_data['destination_address'],
                    estimated_delivery=shipment_data['estimated_delivery']
                )
                sample_shipments.append(shipment)
        else:
            # Fallback shipments
            sample_shipments = [
                Shipment(
                    shipment_id='SHIP_001',
                    order_id=101,
                    courier_id='COURIER_001',
                    tracking_number='FS123456789',
                    status='in_transit',
                    origin_address='Warehouse A, 123 Main St',
                    destination_address='Customer Address 1',
                    estimated_delivery=datetime.utcnow() + timedelta(days=2)
                ),
                Shipment(
                    shipment_id='SHIP_002',
                    order_id=102,
                    courier_id='COURIER_002',
                    tracking_number='SD987654321',
                    status='delivered',
                    origin_address='Warehouse A, 123 Main St',
                    destination_address='Customer Address 2',
                    estimated_delivery=datetime.utcnow() - timedelta(days=1),
                    actual_delivery=datetime.utcnow() - timedelta(days=1)
                ),
                Shipment(
                    shipment_id='SHIP_003',
                    order_id=103,
                    courier_id='COURIER_003',
                    tracking_number='OR555666777',
                    status='out_for_delivery',
                    origin_address='Warehouse A, 123 Main St',
                    destination_address='Customer Address 3',
                    estimated_delivery=datetime.utcnow()
                )
            ]

        # Generate sample agent logs using user product catalog
        sample_agent_logs = []
        if USER_PRODUCT_CATALOG:
            import random
            
            # Create realistic agent activities over the past few days
            base_time = datetime.utcnow()
            
            # Sample activities for different products
            activities = [
                "Inventory Check", "Stock Alert Generated", "Restock Request Created", 
                "Purchase Order Approved", "Shipment Created", "Delivery Scheduled",
                "Return Processed", "Stock Updated", "Low Stock Alert", "Supplier Contacted",
                "Order Fulfilled", "Inventory Replenished", "Quality Check", "Stock Audit",
                "Procurement Initiated", "Delivery Confirmed", "Return Authorized", "Stock Transfer"
            ]
            
            details_templates = [
                "Automated inventory check completed successfully",
                "Stock level below reorder point, alert generated",
                "Restock request created for {} units",
                "Purchase order PO-{} approved and sent to supplier",
                "Shipment {} created for order #{}",
                "Delivery scheduled with {} courier service",
                "Return request processed, {} units returned",
                "Stock level updated after delivery receipt",
                "Low stock alert: only {} units remaining",
                "Supplier {} contacted for urgent restock",
                "Order #{} fulfilled and ready for shipment",
                "Inventory replenished with {} new units",
                "Quality check passed for incoming stock",
                "Monthly stock audit completed",
                "Procurement process initiated for {} units",
                "Delivery confirmed by customer",
                "Return authorized due to quality issues",
                "Stock transfer between warehouses completed"
            ]
            
            # Generate 25 agent log entries
            for i in range(25):
                product = random.choice(USER_PRODUCT_CATALOG)
                activity = random.choice(activities)
                detail_template = random.choice(details_templates)
                
                # Generate realistic details based on activity
                if "{}" in detail_template:
                    if "units" in detail_template:
                        quantity = random.randint(5, 50)
                        details = detail_template.format(quantity)
                    elif "PO-" in detail_template:
                        po_num = f"PO-{random.randint(1000, 9999)}"
                        details = detail_template.format(po_num)
                    elif "Shipment" in detail_template:
                        ship_id = f"SHIP_{random.randint(100, 999)}"
                        order_id = random.randint(200, 300)
                        details = detail_template.format(ship_id, order_id)
                    elif "courier" in detail_template:
                        courier = random.choice(['FastShip Express', 'Standard Delivery', 'Overnight Rush'])
                        details = detail_template.format(courier)
                    elif "Supplier" in detail_template:
                        supplier = random.choice(['SUPPLIER_001', 'SUPPLIER_002', 'SUPPLIER_003'])
                        details = detail_template.format(supplier)
                    elif "Order #" in detail_template:
                        order_id = random.randint(200, 300)
                        details = detail_template.format(order_id)
                    else:
                        details = detail_template.format(random.randint(10, 100))
                else:
                    details = detail_template
                
                # Create timestamp (spread over last 7 days)
                hours_ago = random.randint(1, 168)  # 1 hour to 7 days ago
                timestamp = base_time - timedelta(hours=hours_ago)
                
                agent_log = AgentLog(
                    timestamp=timestamp,
                    action=activity,
                    product_id=product.product_id,
                    quantity=random.randint(1, 20) if random.random() > 0.3 else None,
                    confidence=round(random.uniform(0.7, 0.99), 2),
                    human_review=random.random() < 0.1,  # 10% require human review
                    details=details
                )
                sample_agent_logs.append(agent_log)
        
        # Add sample restock requests
        sample_restock_requests = []
        if USER_PRODUCT_CATALOG:
            # Create restock requests for some low stock items
            low_stock_products = [p for p in USER_PRODUCT_CATALOG if p.current_qty <= p.reorder_point][:5]
            
            for product in low_stock_products:
                restock_qty = random.randint(product.reorder_point * 2, product.max_stock)
                restock_request = RestockRequest(
                    product_id=product.product_id,
                    restock_quantity=restock_qty,
                    status=random.choice(['pending', 'approved', 'completed']),
                    confidence_score=round(random.uniform(0.8, 0.95), 2),
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                )
                sample_restock_requests.append(restock_request)

        # === CRM SAMPLE DATA ===
        
        # Add sample accounts
        sample_accounts = [
            Account(
                account_id='ACC_001',
                name='TechCorp Industries',
                account_type='customer',
                industry='Technology',
                website='https://techcorp.com',
                phone='+1-555-0201',
                email='info@techcorp.com',
                billing_address='123 Tech Street, Silicon Valley, CA 94000',
                city='Palo Alto',
                state='California',
                country='USA',
                postal_code='94000',
                annual_revenue=5000000.0,
                employee_count=250,
                territory='West Coast',
                account_manager_id='USER_001',
                status='active',
                lifecycle_stage='customer',
                created_by='system',
                notes='Major technology client with high growth potential'
            ),
            Account(
                account_id='ACC_002',
                name='Global Manufacturing Ltd',
                account_type='distributor',
                industry='Manufacturing',
                website='https://globalmanuf.com',
                phone='+1-555-0202',
                email='orders@globalmanuf.com',
                billing_address='456 Industrial Blvd, Detroit, MI 48000',
                city='Detroit',
                state='Michigan',
                country='USA',
                postal_code='48000',
                annual_revenue=15000000.0,
                employee_count=500,
                territory='Midwest',
                account_manager_id='USER_002',
                status='active',
                lifecycle_stage='partner',
                created_by='system',
                notes='Key distributor partner for manufacturing sector'
            ),
            Account(
                account_id='ACC_003',
                name='Retail Solutions Inc',
                account_type='customer',
                industry='Retail',
                website='https://retailsolutions.com',
                phone='+1-555-0203',
                email='procurement@retailsolutions.com',
                billing_address='789 Commerce Ave, New York, NY 10001',
                city='New York',
                state='New York',
                country='USA',
                postal_code='10001',
                annual_revenue=8000000.0,
                employee_count=150,
                territory='East Coast',
                account_manager_id='USER_001',
                status='active',
                lifecycle_stage='customer',
                created_by='system',
                notes='Growing retail chain with expansion plans'
            )
        ]
        
        # Add sample contacts
        sample_contacts = [
            Contact(
                contact_id='CON_001',
                account_id='ACC_001',
                first_name='John',
                last_name='Smith',
                title='CTO',
                department='Technology',
                email='john.smith@techcorp.com',
                phone='+1-555-0301',
                mobile='+1-555-0302',
                contact_role='decision_maker',
                is_primary=True,
                status='active',
                created_by='system',
                notes='Primary technical decision maker'
            ),
            Contact(
                contact_id='CON_002',
                account_id='ACC_001',
                first_name='Sarah',
                last_name='Johnson',
                title='Procurement Manager',
                department='Operations',
                email='sarah.johnson@techcorp.com',
                phone='+1-555-0303',
                contact_role='influencer',
                is_primary=False,
                status='active',
                created_by='system',
                notes='Handles procurement decisions'
            ),
            Contact(
                contact_id='CON_003',
                account_id='ACC_002',
                first_name='Mike',
                last_name='Wilson',
                title='VP of Operations',
                department='Operations',
                email='mike.wilson@globalmanuf.com',
                phone='+1-555-0304',
                contact_role='decision_maker',
                is_primary=True,
                status='active',
                created_by='system',
                notes='Key operations decision maker'
            ),
            Contact(
                contact_id='CON_004',
                account_id='ACC_003',
                first_name='Lisa',
                last_name='Davis',
                title='Head of Procurement',
                department='Procurement',
                email='lisa.davis@retailsolutions.com',
                phone='+1-555-0305',
                contact_role='decision_maker',
                is_primary=True,
                status='active',
                created_by='system',
                notes='Procurement head for retail operations'
            )
        ]
        
        # Add sample leads
        sample_leads = [
            Lead(
                lead_id='LEAD_001',
                first_name='David',
                last_name='Brown',
                company='StartupTech Co',
                title='CEO',
                email='david@startuptech.com',
                phone='+1-555-0401',
                lead_source='website',
                lead_status='new',
                lead_stage='inquiry',
                budget=100000.0,
                timeline='Q2 2024',
                authority='decision_maker',
                need='Looking for logistics automation solution',
                assigned_to='USER_001',
                territory='West Coast',
                created_by='system',
                notes='Promising startup with funding'
            ),
            Lead(
                lead_id='LEAD_002',
                first_name='Emma',
                last_name='Garcia',
                company='MidSize Corp',
                title='Operations Director',
                email='emma@midsize.com',
                phone='+1-555-0402',
                lead_source='trade_show',
                lead_status='contacted',
                lead_stage='qualified',
                budget=250000.0,
                timeline='Q1 2024',
                authority='influencer',
                need='Inventory management system upgrade',
                assigned_to='USER_002',
                territory='Midwest',
                created_by='system',
                notes='Met at logistics trade show, very interested'
            ),
            Lead(
                lead_id='LEAD_003',
                first_name='Robert',
                last_name='Taylor',
                company='Enterprise Solutions',
                title='VP Technology',
                email='robert@enterprise.com',
                phone='+1-555-0403',
                lead_source='referral',
                lead_status='qualified',
                lead_stage='proposal',
                budget=500000.0,
                timeline='Q3 2024',
                authority='decision_maker',
                need='Complete logistics platform overhaul',
                assigned_to='USER_001',
                territory='East Coast',
                created_by='system',
                notes='Referred by existing customer, high value opportunity'
            )
        ]
        
        # Add sample opportunities
        sample_opportunities = [
            Opportunity(
                opportunity_id='OPP_001',
                account_id='ACC_001',
                primary_contact_id='CON_001',
                name='TechCorp Logistics Upgrade',
                description='Complete logistics system upgrade for TechCorp',
                opportunity_type='existing_business',
                stage='proposal',
                probability=75.0,
                amount=300000.0,
                currency='USD',
                expected_revenue=300000.0,
                close_date=datetime.utcnow() + timedelta(days=45),
                owner_id='USER_001',
                requirements='Inventory management, order tracking, automated restocking',
                products_interested='["A101", "B202", "C303"]',
                competitors='CompetitorX, CompetitorY',
                risks='Budget approval pending',
                created_by='system',
                notes='High priority opportunity with existing customer'
            ),
            Opportunity(
                opportunity_id='OPP_002',
                account_id='ACC_002',
                primary_contact_id='CON_003',
                name='Global Manufacturing Partnership',
                description='Strategic partnership for distribution network',
                opportunity_type='new_business',
                stage='negotiation',
                probability=60.0,
                amount=750000.0,
                currency='USD',
                expected_revenue=750000.0,
                close_date=datetime.utcnow() + timedelta(days=60),
                owner_id='USER_002',
                requirements='Multi-location inventory, real-time tracking, API integration',
                products_interested='["D404", "E505"]',
                competitors='LogisticsPro',
                risks='Long decision cycle, multiple stakeholders',
                created_by='system',
                notes='Strategic partnership opportunity'
            ),
            Opportunity(
                opportunity_id='OPP_003',
                account_id='ACC_003',
                primary_contact_id='CON_004',
                name='Retail Chain Expansion',
                description='Support retail expansion with logistics platform',
                opportunity_type='new_business',
                stage='prospecting',
                probability=25.0,
                amount=450000.0,
                currency='USD',
                expected_revenue=450000.0,
                close_date=datetime.utcnow() + timedelta(days=90),
                owner_id='USER_001',
                requirements='Multi-store inventory, POS integration, delivery tracking',
                products_interested='["A101", "C303", "E505"]',
                competitors='RetailLogistics Inc',
                risks='Expansion timeline uncertain',
                created_by='system',
                notes='Expansion-driven opportunity'
            )
        ]
        
        # Add sample activities
        sample_activities = []
        activity_types = ['call', 'email', 'meeting', 'visit', 'task']
        subjects = [
            'Initial discovery call',
            'Product demonstration',
            'Proposal presentation',
            'Contract negotiation',
            'Follow-up meeting',
            'Site visit',
            'Technical requirements review',
            'Pricing discussion'
        ]
        
        for i in range(15):
            activity = Activity(
                activity_id=f'ACT_{str(i+1).zfill(3)}',
                subject=random.choice(subjects),
                description=f'Activity description for {random.choice(subjects)}',
                activity_type=random.choice(activity_types),
                status=random.choice(['planned', 'completed', 'in_progress']),
                priority=random.choice(['low', 'medium', 'high']),
                due_date=datetime.utcnow() + timedelta(days=random.randint(-30, 30)),
                account_id=random.choice(['ACC_001', 'ACC_002', 'ACC_003']),
                opportunity_id=random.choice(['OPP_001', 'OPP_002', 'OPP_003']) if random.random() > 0.5 else None,
                assigned_to=random.choice(['USER_001', 'USER_002']),
                created_by='system'
            )
            sample_activities.append(activity)
        
        # Add sample tasks
        sample_tasks = []
        task_titles = [
            'Prepare proposal document',
            'Schedule follow-up call',
            'Send product brochure',
            'Review contract terms',
            'Coordinate demo session',
            'Update CRM records',
            'Prepare pricing quote',
            'Schedule site visit'
        ]
        
        for i in range(10):
            task = Task(
                task_id=f'TASK_{str(i+1).zfill(3)}',
                title=random.choice(task_titles),
                description=f'Task description for {random.choice(task_titles)}',
                task_type=random.choice(['general', 'follow_up', 'reminder']),
                priority=random.choice(['low', 'medium', 'high', 'urgent']),
                status=random.choice(['pending', 'in_progress', 'completed']),
                due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
                assigned_to=random.choice(['USER_001', 'USER_002']),
                account_id=random.choice(['ACC_001', 'ACC_002', 'ACC_003']) if random.random() > 0.3 else None,
                opportunity_id=random.choice(['OPP_001', 'OPP_002', 'OPP_003']) if random.random() > 0.5 else None,
                created_by='system'
            )
            sample_tasks.append(task)

        # Add to database
        db.add_all(sample_orders)
        db.add_all(sample_returns)
        db.add_all(sample_suppliers)
        db.add_all(sample_couriers)
        db.add_all(sample_inventory)
        db.add_all(sample_shipments)
        db.add_all(sample_agent_logs)
        db.add_all(sample_restock_requests)
        
        # Add CRM data
        db.add_all(sample_accounts)
        db.add_all(sample_contacts)
        db.add_all(sample_leads)
        db.add_all(sample_opportunities)
        db.add_all(sample_activities)
        db.add_all(sample_tasks)
        
        db.commit()

        print("[OK] Database initialized with sample data")
        print(f"   - {len(sample_orders)} orders")
        print(f"   - {len(sample_returns)} returns")
        print(f"   - {len(sample_suppliers)} suppliers")
        print(f"   - {len(sample_couriers)} couriers")
        print(f"   - {len(sample_inventory)} inventory items")
        print(f"   - {len(sample_shipments)} shipments")
        print(f"   - {len(sample_agent_logs)} agent activities")
        print(f"   - {len(sample_restock_requests)} restock requests")
        print(f"   - {sum(1 for inv in sample_inventory if inv.needs_reorder)} items need reordering")
        print("[CRM] CRM Data:")
        print(f"   - {len(sample_accounts)} accounts")
        print(f"   - {len(sample_contacts)} contacts")
        print(f"   - {len(sample_leads)} leads")
        print(f"   - {len(sample_opportunities)} opportunities")
        print(f"   - {len(sample_activities)} activities")
        print(f"   - {len(sample_tasks)} tasks")
        
    except Exception as e:
        print(f"[ERROR] Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
