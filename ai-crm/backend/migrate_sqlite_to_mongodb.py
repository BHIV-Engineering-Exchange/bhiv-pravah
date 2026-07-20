#!/usr/bin/env python3
"""
Migration Script: SQLite to MongoDB
Migrates all data from SQLite database to MongoDB
"""

import sys
from datetime import datetime
from database.mongodb_connection import MongoDBConnection, COLLECTIONS
from database.mongodb_service import MongoDBService
from database.mongodb_crm_service import MongoDBCRMService

# Import SQLite models
try:
    from database.models import SessionLocal as SQLiteSession
    from database.models import (
        Order, Return, RestockRequest, AgentLog, HumanReview,
        Inventory, PurchaseOrder, Supplier, Shipment, Courier, Product,
        Account, Contact, Lead, Opportunity, Activity, Task
    )
    SQLITE_AVAILABLE = True
except Exception as e:
    print(f"[WARN] SQLite models not available: {e}")
    SQLITE_AVAILABLE = False


def migrate_sqlite_to_mongodb():
    """Migrate all data from SQLite to MongoDB"""
    
    if not SQLITE_AVAILABLE:
        print("[ERROR] SQLite database models not available. Cannot perform migration.")
        return False
    
    print("=" * 70)
    print("SQLite to MongoDB Migration")
    print("=" * 70)
    
    # Test MongoDB connection
    print("\n[1/3] Testing MongoDB connection...")
    if not MongoDBConnection.test_connection():
        print("[ERROR] Failed to connect to MongoDB. Aborting migration.")
        return False
    
    # Get services
    mongo_logistics = MongoDBService()
    mongo_crm = MongoDBCRMService()
    sqlite_db = SQLiteSession()
    
    try:
        # Migrate logistics data
        print("\n[2/3] Migrating logistics data...")
        
        # Migrate suppliers
        print("  Migrating suppliers...")
        suppliers = sqlite_db.query(Supplier).all()
        for supplier in suppliers:
            try:
                mongo_logistics.create_supplier({
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "contact_email": supplier.contact_email,
                    "contact_phone": supplier.contact_phone,
                    "api_endpoint": supplier.api_endpoint,
                    "api_key": supplier.api_key,
                    "lead_time_days": supplier.lead_time_days,
                    "minimum_order": supplier.minimum_order,
                    "is_active": supplier.is_active,
                    "created_at": supplier.created_at
                })
            except Exception as e:
                print(f"    Error migrating supplier {supplier.supplier_id}: {e}")
        
        # Migrate products
        print("  Migrating products...")
        products = sqlite_db.query(Product).all()
        for product in products:
            try:
                mongo_logistics.create_product({
                    "product_id": product.product_id,
                    "name": product.name,
                    "category": product.category,
                    "description": product.description,
                    "unit_price": product.unit_price,
                    "weight_kg": product.weight_kg,
                    "dimensions": product.dimensions,
                    "supplier_id": product.supplier_id,
                    "reorder_point": product.reorder_point,
                    "max_stock": product.max_stock,
                    "is_active": product.is_active,
                    "created_at": product.created_at,
                    "updated_at": product.updated_at,
                    "primary_image_url": product.primary_image_url,
                    "gallery_images": product.gallery_images,
                    "thumbnail_url": product.thumbnail_url,
                    "marketing_description": product.marketing_description,
                    "key_features": product.key_features,
                    "specifications": product.specifications
                })
            except Exception as e:
                print(f"    Error migrating product {product.product_id}: {e}")
        
        # Migrate inventory
        print("  Migrating inventory...")
        inventory_items = sqlite_db.query(Inventory).all()
        for item in inventory_items:
            try:
                mongo_logistics.create_inventory_item({
                    "product_id": item.product_id,
                    "current_stock": item.current_stock,
                    "reserved_stock": item.reserved_stock,
                    "reorder_point": item.reorder_point,
                    "max_stock": item.max_stock,
                    "supplier_id": item.supplier_id,
                    "unit_cost": item.unit_cost,
                    "last_updated": item.last_updated
                })
            except Exception as e:
                print(f"    Error migrating inventory for {item.product_id}: {e}")
        
        # Migrate orders
        print("  Migrating orders...")
        orders = sqlite_db.query(Order).all()
        for order in orders:
            try:
                mongo_logistics.create_order({
                    "order_id": order.order_id,
                    "status": order.status,
                    "customer_id": order.customer_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "order_date": order.order_date,
                    "updated_at": order.updated_at
                })
            except Exception as e:
                print(f"    Error migrating order {order.order_id}: {e}")
        
        # Migrate returns
        print("  Migrating returns...")
        returns = sqlite_db.query(Return).all()
        for ret in returns:
            try:
                mongo_logistics.add_return(
                    ret.product_id,
                    ret.return_quantity,
                    ret.reason
                )
            except Exception as e:
                print(f"    Error migrating return: {e}")
        
        # Migrate restock requests
        print("  Migrating restock requests...")
        restock_requests = sqlite_db.query(RestockRequest).all()
        for req in restock_requests:
            try:
                mongo_logistics.create_restock_request(
                    req.product_id,
                    req.restock_quantity,
                    req.confidence_score
                )
            except Exception as e:
                print(f"    Error migrating restock request: {e}")
        
        # Migrate purchase orders
        print("  Migrating purchase orders...")
        purchase_orders = sqlite_db.query(PurchaseOrder).all()
        for po in purchase_orders:
            try:
                mongo_logistics.create_purchase_order({
                    "po_number": po.po_number,
                    "supplier_id": po.supplier_id,
                    "product_id": po.product_id,
                    "quantity": po.quantity,
                    "unit_cost": po.unit_cost,
                    "total_cost": po.total_cost,
                    "status": po.status,
                    "created_at": po.created_at,
                    "sent_at": po.sent_at,
                    "confirmed_at": po.confirmed_at,
                    "expected_delivery": po.expected_delivery,
                    "delivered_at": po.delivered_at,
                    "notes": po.notes
                })
            except Exception as e:
                print(f"    Error migrating PO {po.po_number}: {e}")
        
        # Migrate shipments
        print("  Migrating shipments...")
        shipments = sqlite_db.query(Shipment).all()
        for shipment in shipments:
            try:
                mongo_logistics.create_shipment({
                    "shipment_id": shipment.shipment_id,
                    "order_id": shipment.order_id,
                    "courier_id": shipment.courier_id,
                    "tracking_number": shipment.tracking_number,
                    "status": shipment.status,
                    "origin_address": shipment.origin_address,
                    "destination_address": shipment.destination_address,
                    "estimated_delivery": shipment.estimated_delivery,
                    "actual_delivery": shipment.actual_delivery,
                    "created_at": shipment.created_at,
                    "picked_up_at": shipment.picked_up_at,
                    "delivered_at": shipment.delivered_at,
                    "notes": shipment.notes
                })
            except Exception as e:
                print(f"    Error migrating shipment {shipment.shipment_id}: {e}")
        
        # Migrate CRM data
        print("\n[3/3] Migrating CRM data...")
        
        # Migrate accounts
        print("  Migrating accounts...")
        accounts = sqlite_db.query(Account).all()
        for account in accounts:
            try:
                mongo_crm.create_account({
                    "account_id": account.account_id,
                    "name": account.name,
                    "account_type": account.account_type,
                    "industry": account.industry,
                    "website": account.website,
                    "phone": account.phone,
                    "email": account.email,
                    "billing_address": account.billing_address,
                    "shipping_address": account.shipping_address,
                    "city": account.city,
                    "state": account.state,
                    "country": account.country,
                    "postal_code": account.postal_code,
                    "annual_revenue": account.annual_revenue,
                    "employee_count": account.employee_count,
                    "territory": account.territory,
                    "parent_account_id": account.parent_account_id,
                    "account_manager_id": account.account_manager_id,
                    "status": account.status,
                    "lifecycle_stage": account.lifecycle_stage,
                    "created_at": account.created_at,
                    "updated_at": account.updated_at,
                    "created_by": account.created_by,
                    "notes": account.notes
                })
            except Exception as e:
                print(f"    Error migrating account {account.account_id}: {e}")
        
        # Migrate contacts
        print("  Migrating contacts...")
        contacts = sqlite_db.query(Contact).all()
        for contact in contacts:
            try:
                mongo_crm.create_contact({
                    "contact_id": contact.contact_id,
                    "account_id": contact.account_id,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "title": contact.title,
                    "department": contact.department,
                    "email": contact.email,
                    "phone": contact.phone,
                    "mobile": contact.mobile,
                    "contact_role": contact.contact_role,
                    "is_primary": contact.is_primary,
                    "reports_to_id": contact.reports_to_id,
                    "status": contact.status,
                    "created_at": contact.created_at,
                    "updated_at": contact.updated_at,
                    "created_by": contact.created_by,
                    "notes": contact.notes
                })
            except Exception as e:
                print(f"    Error migrating contact {contact.contact_id}: {e}")
        
        # Migrate leads
        print("  Migrating leads...")
        leads = sqlite_db.query(Lead).all()
        for lead in leads:
            try:
                mongo_crm.create_lead({
                    "lead_id": lead.lead_id,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "company": lead.company,
                    "title": lead.title,
                    "email": lead.email,
                    "phone": lead.phone,
                    "lead_source": lead.lead_source,
                    "lead_status": lead.lead_status,
                    "lead_stage": lead.lead_stage,
                    "budget": lead.budget,
                    "timeline": lead.timeline,
                    "authority": lead.authority,
                    "need": lead.need,
                    "assigned_to": lead.assigned_to,
                    "territory": lead.territory,
                    "converted": lead.converted,
                    "converted_at": lead.converted_at,
                    "converted_to_account_id": lead.converted_to_account_id,
                    "converted_to_opportunity_id": lead.converted_to_opportunity_id,
                    "created_at": lead.created_at,
                    "updated_at": lead.updated_at,
                    "created_by": lead.created_by,
                    "notes": lead.notes
                })
            except Exception as e:
                print(f"    Error migrating lead {lead.lead_id}: {e}")
        
        # Migrate opportunities
        print("  Migrating opportunities...")
        opportunities = sqlite_db.query(Opportunity).all()
        for opp in opportunities:
            try:
                mongo_crm.create_opportunity({
                    "opportunity_id": opp.opportunity_id,
                    "account_id": opp.account_id,
                    "primary_contact_id": opp.primary_contact_id,
                    "name": opp.name,
                    "description": opp.description,
                    "opportunity_type": opp.opportunity_type,
                    "stage": opp.stage,
                    "probability": opp.probability,
                    "amount": opp.amount,
                    "currency": opp.currency,
                    "expected_revenue": opp.expected_revenue,
                    "close_date": opp.close_date,
                    "created_at": opp.created_at,
                    "updated_at": opp.updated_at,
                    "owner_id": opp.owner_id,
                    "requirements": opp.requirements,
                    "products_interested": opp.products_interested,
                    "competitors": opp.competitors,
                    "risks": opp.risks,
                    "is_closed": opp.is_closed,
                    "is_won": opp.is_won,
                    "closed_at": opp.closed_at,
                    "closed_reason": opp.closed_reason,
                    "created_by": opp.created_by,
                    "notes": opp.notes
                })
            except Exception as e:
                print(f"    Error migrating opportunity {opp.opportunity_id}: {e}")
        
        # Migrate activities
        print("  Migrating activities...")
        activities = sqlite_db.query(Activity).all()
        for activity in activities:
            try:
                mongo_crm.create_activity({
                    "activity_id": activity.activity_id,
                    "subject": activity.subject,
                    "description": activity.description,
                    "activity_type": activity.activity_type,
                    "status": activity.status,
                    "priority": activity.priority,
                    "due_date": activity.due_date,
                    "start_time": activity.start_time,
                    "end_time": activity.end_time,
                    "duration_minutes": activity.duration_minutes,
                    "account_id": activity.account_id,
                    "contact_id": activity.contact_id,
                    "opportunity_id": activity.opportunity_id,
                    "lead_id": activity.lead_id,
                    "assigned_to": activity.assigned_to,
                    "created_by": activity.created_by,
                    "communication_type": activity.communication_type,
                    "outcome": activity.outcome,
                    "next_steps": activity.next_steps,
                    "location": activity.location,
                    "latitude": activity.latitude,
                    "longitude": activity.longitude,
                    "created_at": activity.created_at,
                    "updated_at": activity.updated_at,
                    "completed_at": activity.completed_at
                })
            except Exception as e:
                print(f"    Error migrating activity {activity.activity_id}: {e}")
        
        # Migrate tasks
        print("  Migrating tasks...")
        tasks = sqlite_db.query(Task).all()
        for task in tasks:
            try:
                mongo_crm.create_task({
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "priority": task.priority,
                    "status": task.status,
                    "due_date": task.due_date,
                    "reminder_date": task.reminder_date,
                    "completed_at": task.completed_at,
                    "assigned_to": task.assigned_to,
                    "created_by": task.created_by,
                    "account_id": task.account_id,
                    "contact_id": task.contact_id,
                    "opportunity_id": task.opportunity_id,
                    "lead_id": task.lead_id,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at
                })
            except Exception as e:
                print(f"    Error migrating task {task.task_id}: {e}")
        
        print("\n" + "=" * 70)
        print("Migration Complete!")
        print("=" * 70)
        
        # Print statistics
        print("\nMigration statistics:")
        stats = mongo_logistics.get_statistics()
        crm_stats = mongo_crm.get_crm_statistics()
        
        print(f"  Logistics:")
        print(f"    - Orders: {stats['total_orders']}")
        print(f"    - Products: {stats['total_products']}")
        print(f"    - Suppliers: {stats['total_suppliers']}")
        print(f"  CRM:")
        print(f"    - Accounts: {crm_stats['total_accounts']}")
        print(f"    - Contacts: {crm_stats['total_contacts']}")
        print(f"    - Leads: {crm_stats['total_leads']}")
        print(f"    - Opportunities: {crm_stats['open_opportunities']}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sqlite_db.close()


if __name__ == "__main__":
    try:
        success = migrate_sqlite_to_mongodb()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
