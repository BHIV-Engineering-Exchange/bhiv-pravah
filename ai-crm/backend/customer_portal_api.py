"""
Customer Portal and Automated Procurement API Endpoints
Handles customer orders and automatic supplier notifications
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from auth_system import get_current_user, User
from database.service import DatabaseService
from ems_automation import EMSAutomationExtended

# Import database extensions
try:
    import database_extensions
except:
    pass

router = APIRouter()
db_service = DatabaseService()
ems = EMSAutomationExtended()

# Models
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float

class CustomerOrder(BaseModel):
    items: List[OrderItem]
    total_amount: float
    shipping_address: Optional[str] = None
    notes: Optional[str] = None

class ProcurementRequest(BaseModel):
    product_id: str
    quantity: int
    supplier_id: str
    reason: str = "Low stock - automatic reorder"

# Customer Portal Endpoints
@router.get("/customer/products")
async def get_customer_products():
    """Get product catalog for customers"""
    try:
        # Get all active products with stock information
        products = db_service.get_all_products()
        return [{
            "id": p.get("id"),
            "name": p.get("name"),
            "description": p.get("description"),
            "price": p.get("price", 0),
            "stock": p.get("stock_quantity", 0),
            "category": p.get("category", "general"),
            "image_url": p.get("image_url"),
            "supplier_id": p.get("supplier_id")
        } for p in products if p.get("status") == "active"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer/orders")
async def place_customer_order(
    order: CustomerOrder,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Place a new customer order and trigger procurement if needed"""
    try:
        # Create order record
        order_data = {
            "customer_id": current_user.id,
            "customer_email": current_user.email,
            "items": [item.dict() for item in order.items],
            "total_amount": order.total_amount,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "shipping_address": order.shipping_address,
            "notes": order.notes
        }
        
        order_id = db_service.create_order(order_data)
        
        # Check inventory and trigger procurement if needed
        for item in order.items:
            product = db_service.get_product(item.product_id)
            if not product:
                continue
                
            current_stock = product.get("stock_quantity", 0)
            reorder_level = product.get("reorder_level", 10)
            
            # Update stock
            new_stock = current_stock - item.quantity
            db_service.update_product_stock(item.product_id, new_stock)
            
            # Trigger automatic procurement if stock is low
            if new_stock <= reorder_level:
                background_tasks.add_task(
                    trigger_automatic_procurement,
                    product,
                    new_stock,
                    reorder_level
                )
        
        # Send order confirmation email to customer
        background_tasks.add_task(
            send_order_confirmation_email,
            current_user.email,
            order_id,
            order_data
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "message": "Order placed successfully",
            "estimated_delivery": "3-5 business days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/orders")
async def get_customer_orders(current_user: User = Depends(get_current_user)):
    """Get order history for customer"""
    try:
        orders = db_service.get_customer_orders(current_user.id)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/orders/{order_id}")
async def get_customer_order_details(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific order details"""
    try:
        order = db_service.get_order(order_id)
        if not order or order.get("customer_id") != current_user.id:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Automatic Procurement Functions
async def trigger_automatic_procurement(product: dict, current_stock: int, reorder_level: int):
    """Automatically trigger procurement and notify supplier via EMS"""
    try:
        product_id = product.get("id")
        product_name = product.get("name")
        supplier_id = product.get("supplier_id")
        
        if not supplier_id:
            print(f"Warning: No supplier assigned for product {product_name}")
            return
        
        # Get supplier details
        supplier = db_service.get_supplier(supplier_id)
        if not supplier:
            print(f"Warning: Supplier not found for product {product_name}")
            return
        
        # Calculate reorder quantity (e.g., 2x reorder level)
        reorder_quantity = max(reorder_level * 2, 50)
        
        # Create procurement request
        procurement_data = {
            "product_id": product_id,
            "product_name": product_name,
            "supplier_id": supplier_id,
            "supplier_name": supplier.get("name"),
            "quantity": reorder_quantity,
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "reason": "Automatic reorder - low stock alert"
        }
        
        procurement_id = db_service.create_procurement_request(procurement_data)
        
        # Send email to supplier via EMS
        supplier_email = supplier.get("email")
        if supplier_email:
            ems.send_procurement_email(
                supplier_email=supplier_email,
                supplier_name=supplier.get("name"),
                product_name=product_name,
                product_id=product_id,
                quantity=reorder_quantity,
                current_stock=current_stock,
                procurement_id=procurement_id
            )
            print(f"✅ Procurement email sent to {supplier.get('name')} for {product_name}")
        
        # Send internal notification
        ems.send_internal_low_stock_alert(
            product_name=product_name,
            current_stock=current_stock,
            reorder_level=reorder_level,
            supplier_name=supplier.get("name"),
            procurement_id=procurement_id
        )
        
    except Exception as e:
        print(f"Error in automatic procurement: {str(e)}")

async def send_order_confirmation_email(customer_email: str, order_id: str, order_data: dict):
    """Send order confirmation email to customer"""
    try:
        ems.send_order_confirmation(
            customer_email=customer_email,
            order_id=order_id,
            order_data=order_data
        )
        print(f"✅ Order confirmation email sent to {customer_email}")
    except Exception as e:
        print(f"Error sending order confirmation: {str(e)}")

# Admin endpoints for procurement management
@router.get("/admin/procurement/requests")
async def get_procurement_requests(current_user: User = Depends(get_current_user)):
    """Get all procurement requests"""
    try:
        requests = db_service.get_all_procurement_requests()
        return requests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/procurement/{procurement_id}/approve")
async def approve_procurement_request(
    procurement_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Approve procurement request and create purchase order"""
    try:
        procurement = db_service.get_procurement_request(procurement_id)
        if not procurement:
            raise HTTPException(status_code=404, detail="Procurement request not found")
        
        # Update status
        db_service.update_procurement_status(procurement_id, "approved")
        
        # Create purchase order
        po_data = {
            "procurement_id": procurement_id,
            "supplier_id": procurement.get("supplier_id"),
            "product_id": procurement.get("product_id"),
            "quantity": procurement.get("quantity"),
            "status": "sent",
            "created_at": datetime.utcnow().isoformat(),
            "approved_by": current_user.id
        }
        
        po_id = db_service.create_purchase_order(po_data)
        
        # Send final PO to supplier
        supplier = db_service.get_supplier(procurement.get("supplier_id"))
        if supplier and supplier.get("email"):
            background_tasks.add_task(
                ems.send_purchase_order_email,
                supplier_email=supplier.get("email"),
                po_number=po_id,
                po_data=po_data
            )
        
        return {
            "success": True,
            "procurement_id": procurement_id,
            "purchase_order_id": po_id,
            "message": "Procurement approved and PO sent to supplier"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
