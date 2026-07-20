#!/usr/bin/env python3
"""
MongoDB Database Initialization Script
Creates collections and sample data for the AI Agent Logistics + CRM System
"""

import sys
from datetime import datetime, timedelta
from database.mongodb_connection import MongoDBConnection, COLLECTIONS
from database.mongodb_models import create_indexes
from database.mongodb_service import MongoDBService
from database.mongodb_crm_service import MongoDBCRMService


def init_mongodb():
    """Initialize MongoDB database with collections and sample data"""
    
    print("=" * 70)
    print("MongoDB Database Initialization")
    print("=" * 70)
    
    # Test connection
    print("\n[1/4] Testing MongoDB connection...")
    if not MongoDBConnection.test_connection():
        print("[ERROR] Failed to connect to MongoDB. Please check your configuration.")
        print("Make sure MongoDB is running and the connection string in .env is correct.")
        return False
    
    # Get database
    db = MongoDBConnection.get_database()
    
    # Create indexes
    print("\n[2/4] Creating indexes...")
    try:
        create_indexes(db)
    except Exception as e:
        print(f"[ERROR] Failed to create indexes: {e}")
        return False
    
    # Check if data already exists
    print("\n[3/4] Checking for existing data...")
    if db[COLLECTIONS['orders']].count_documents({}) > 0:
        print("[INFO] Database already has data. Skipping sample data initialization.")
        print("[OK] MongoDB initialization complete!")
        return True
    
    # Create sample data
    print("\n[4/4] Creating sample data...")
    try:
        create_sample_data(db)
        print("[OK] Sample data created successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to create sample data: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("MongoDB Initialization Complete!")
    print("=" * 70)
    print("\nDatabase statistics:")
    
    # Print statistics
    logistics_service = MongoDBService()
    crm_service = MongoDBCRMService()
    
    stats = logistics_service.get_statistics()
    crm_stats = crm_service.get_crm_statistics()
    
    print(f"  - Orders: {stats['total_orders']}")
    print(f"  - Products: {stats['total_products']}")
    print(f"  - Suppliers: {stats['total_suppliers']}")
    print(f"  - Accounts: {crm_stats['total_accounts']}")
    print(f"  - Contacts: {crm_stats['total_contacts']}")
    print(f"  - Leads: {crm_stats['total_leads']}")
    print(f"  - Opportunities: {crm_stats['open_opportunities']}")
    
    return True


def create_sample_data(db):
    """Create sample data for demonstration"""
    
    logistics_service = MongoDBService()
    crm_service = MongoDBCRMService()
    
    # Create suppliers
    print("  Creating suppliers...")
    suppliers = [
        {
            "supplier_id": "SUPPLIER_001",
            "name": "TechParts Supply Co.",
            "contact_email": "orders@techparts.com",
            "contact_phone": "+1-555-0101",
            "api_endpoint": "http://localhost:8001/api/supplier",
            "lead_time_days": 5,
            "minimum_order": 10
        },
        {
            "supplier_id": "SUPPLIER_002",
            "name": "Global Components Ltd.",
            "contact_email": "procurement@globalcomp.com",
            "contact_phone": "+1-555-0102",
            "lead_time_days": 7,
            "minimum_order": 5
        },
        {
            "supplier_id": "SUPPLIER_003",
            "name": "FastTrack Logistics",
            "contact_email": "orders@fasttrack.com",
            "contact_phone": "+1-555-0103",
            "lead_time_days": 3,
            "minimum_order": 20
        }
    ]
    
    for supplier in suppliers:
        logistics_service.create_supplier(supplier)
    
    # Create products
    print("  Creating products...")
    products = [
        {
            "product_id": "A101",
            "name": "Wireless Mouse",
            "category": "Electronics",
            "description": "High-precision wireless mouse",
            "unit_price": 29.99,
            "supplier_id": "SUPPLIER_001",
            "reorder_point": 20,
            "max_stock": 200
        },
        {
            "product_id": "B202",
            "name": "USB-C Cable",
            "category": "Accessories",
            "description": "Premium USB-C charging cable",
            "unit_price": 14.99,
            "supplier_id": "SUPPLIER_002",
            "reorder_point": 50,
            "max_stock": 500
        },
        {
            "product_id": "C303",
            "name": "Laptop Stand",
            "category": "Office",
            "description": "Ergonomic aluminum laptop stand",
            "unit_price": 49.99,
            "supplier_id": "SUPPLIER_001",
            "reorder_point": 15,
            "max_stock": 150
        },
        {
            "product_id": "D404",
            "name": "Bluetooth Headphones",
            "category": "Electronics",
            "description": "Noise-cancelling wireless headphones",
            "unit_price": 89.99,
            "supplier_id": "SUPPLIER_003",
            "reorder_point": 10,
            "max_stock": 100
        },
        {
            "product_id": "E505",
            "name": "Mechanical Keyboard",
            "category": "Electronics",
            "description": "RGB mechanical gaming keyboard",
            "unit_price": 129.99,
            "supplier_id": "SUPPLIER_002",
            "reorder_point": 8,
            "max_stock": 80
        }
    ]
    
    for product in products:
        logistics_service.create_product(product)
    
    # Create inventory
    print("  Creating inventory...")
    for product in products:
        logistics_service.create_inventory_item({
            "product_id": product["product_id"],
            "current_stock": 50,
            "reserved_stock": 5,
            "reorder_point": product["reorder_point"],
            "max_stock": product["max_stock"],
            "supplier_id": product["supplier_id"],
            "unit_cost": product["unit_price"] * 0.6  # 60% of retail price
        })
    
    # Create orders
    print("  Creating orders...")
    orders = [
        {
            "order_id": 101,
            "status": "Shipped",
            "customer_id": "CUST001",
            "product_id": "A101",
            "quantity": 2,
            "order_date": datetime.utcnow() - timedelta(days=3)
        },
        {
            "order_id": 102,
            "status": "Delivered",
            "customer_id": "CUST002",
            "product_id": "B202",
            "quantity": 5,
            "order_date": datetime.utcnow() - timedelta(days=7)
        },
        {
            "order_id": 103,
            "status": "Processing",
            "customer_id": "CUST003",
            "product_id": "C303",
            "quantity": 1,
            "order_date": datetime.utcnow() - timedelta(days=1)
        },
        {
            "order_id": 104,
            "status": "Shipped",
            "customer_id": "CUST004",
            "product_id": "D404",
            "quantity": 3,
            "order_date": datetime.utcnow() - timedelta(days=2)
        }
    ]
    
    for order in orders:
        logistics_service.create_order(order)
    
    # Create returns
    print("  Creating returns...")
    logistics_service.add_return("A101", 2, "Defective")
    logistics_service.add_return("B202", 1, "Wrong item")
    
    # Create CRM sample data
    print("  Creating CRM accounts...")
    accounts = [
        {
            "account_id": "ACC_001",
            "name": "Tech Solutions Inc.",
            "account_type": "customer",
            "industry": "Technology",
            "email": "contact@techsolutions.com",
            "phone": "+1-555-1001",
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "status": "active",
            "lifecycle_stage": "customer"
        },
        {
            "account_id": "ACC_002",
            "name": "Global Retail Corp",
            "account_type": "distributor",
            "industry": "Retail",
            "email": "sales@globalretail.com",
            "phone": "+1-555-1002",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "status": "active",
            "lifecycle_stage": "customer"
        }
    ]
    
    for account in accounts:
        crm_service.create_account(account)
    
    # Create contacts
    print("  Creating CRM contacts...")
    contacts = [
        {
            "contact_id": "CON_001",
            "account_id": "ACC_001",
            "first_name": "John",
            "last_name": "Smith",
            "title": "CTO",
            "email": "john.smith@techsolutions.com",
            "phone": "+1-555-2001",
            "contact_role": "decision_maker",
            "is_primary": True,
            "status": "active"
        },
        {
            "contact_id": "CON_002",
            "account_id": "ACC_002",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "title": "Procurement Manager",
            "email": "sarah.j@globalretail.com",
            "phone": "+1-555-2002",
            "contact_role": "decision_maker",
            "is_primary": True,
            "status": "active"
        }
    ]
    
    for contact in contacts:
        crm_service.create_contact(contact)
    
    # Create leads
    print("  Creating CRM leads...")
    leads = [
        {
            "lead_id": "LEAD_001",
            "first_name": "Michael",
            "last_name": "Brown",
            "company": "Startup Innovations",
            "email": "michael@startupinnovations.com",
            "phone": "+1-555-3001",
            "lead_source": "website",
            "lead_status": "new",
            "lead_stage": "inquiry"
        }
    ]
    
    for lead in leads:
        crm_service.create_lead(lead)
    
    # Create opportunities
    print("  Creating CRM opportunities...")
    opportunities = [
        {
            "opportunity_id": "OPP_001",
            "account_id": "ACC_001",
            "primary_contact_id": "CON_001",
            "name": "Q1 2026 Equipment Purchase",
            "description": "Large order of electronics for new office",
            "stage": "proposal",
            "probability": 75.0,
            "amount": 50000.0,
            "currency": "USD",
            "close_date": datetime.utcnow() + timedelta(days=30)
        }
    ]
    
    for opportunity in opportunities:
        crm_service.create_opportunity(opportunity)
    
    # Create activities
    print("  Creating CRM activities...")
    crm_service.create_activity({
        "subject": "Follow-up call with Tech Solutions",
        "description": "Discuss Q1 equipment needs",
        "activity_type": "call",
        "status": "completed",
        "account_id": "ACC_001",
        "contact_id": "CON_001",
        "opportunity_id": "OPP_001",
        "completed_at": datetime.utcnow() - timedelta(days=1)
    })
    
    print("  Sample data creation complete!")


if __name__ == "__main__":
    try:
        success = init_mongodb()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
