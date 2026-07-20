#!/usr/bin/env python3
"""
Mock Supplier API for testing procurement agent
Simulates external supplier systems
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import random
import time
from datetime import datetime, timedelta
import uuid

# Pydantic models for API
class PurchaseOrderRequest(BaseModel):
    product_id: str
    quantity: int
    unit_cost: float
    delivery_address: str = "Warehouse A, 123 Main St"
    priority: str = "normal"  # normal, urgent, expedited

class PurchaseOrderResponse(BaseModel):
    po_number: str
    supplier_order_id: str
    status: str
    estimated_delivery: str
    total_cost: float
    confirmation_message: str

class OrderStatusResponse(BaseModel):
    supplier_order_id: str
    status: str
    tracking_number: Optional[str] = None
    estimated_delivery: str
    actual_delivery: Optional[str] = None
    notes: str

# Mock supplier configurations
SUPPLIERS = {
    "SUPPLIER_001": {
        "name": "TechParts Supply Co.",
        "success_rate": 0.95,
        "avg_response_time": 2,
        "lead_time_days": 5,
        "price_variance": 0.1,  # ±10% price variation
        "stock_availability": 0.9
    },
    "SUPPLIER_002": {
        "name": "Global Components Ltd.", 
        "success_rate": 0.88,
        "avg_response_time": 5,
        "lead_time_days": 7,
        "price_variance": 0.15,
        "stock_availability": 0.85
    },
    "SUPPLIER_003": {
        "name": "FastTrack Logistics",
        "success_rate": 0.92,
        "avg_response_time": 1,
        "lead_time_days": 3,
        "price_variance": 0.2,
        "stock_availability": 0.8
    }
}

# In-memory storage for orders (in production, this would be a database)
supplier_orders = {}

def create_supplier_app(supplier_id: str) -> FastAPI:
    """Create a FastAPI app for a specific supplier"""
    
    if supplier_id not in SUPPLIERS:
        raise ValueError(f"Unknown supplier: {supplier_id}")
    
    supplier_config = SUPPLIERS[supplier_id]
    app = FastAPI(
        title=f"{supplier_config['name']} API",
        description=f"Mock API for {supplier_config['name']}",
        version="1.0.0"
    )
    
    @app.get("/")
    def supplier_info():
        return {
            "supplier_id": supplier_id,
            "name": supplier_config["name"],
            "status": "operational",
            "api_version": "1.0.0",
            "capabilities": [
                "purchase_orders",
                "order_status",
                "inventory_check",
                "pricing"
            ]
        }
    
    @app.post("/api/purchase-order", response_model=PurchaseOrderResponse)
    def create_purchase_order(order: PurchaseOrderRequest):
        """Create a new purchase order"""
        
        # Simulate processing time
        time.sleep(random.uniform(0.5, supplier_config["avg_response_time"]))
        
        # Simulate occasional failures
        if random.random() > supplier_config["success_rate"]:
            raise HTTPException(
                status_code=503,
                detail=f"Supplier {supplier_id} temporarily unavailable"
            )
        
        # Check stock availability
        if random.random() > supplier_config["stock_availability"]:
            raise HTTPException(
                status_code=409,
                detail=f"Product {order.product_id} out of stock"
            )
        
        # Generate order details
        supplier_order_id = f"{supplier_id}_{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate delivery date
        lead_time = supplier_config["lead_time_days"]
        if order.priority == "urgent":
            lead_time = max(1, lead_time - 2)
        elif order.priority == "expedited":
            lead_time = max(1, lead_time - 1)
        
        estimated_delivery = datetime.now() + timedelta(days=lead_time)
        
        # Calculate cost with variance
        price_variance = random.uniform(-supplier_config["price_variance"], supplier_config["price_variance"])
        adjusted_unit_cost = order.unit_cost * (1 + price_variance)
        total_cost = adjusted_unit_cost * order.quantity
        
        # Store order
        supplier_orders[supplier_order_id] = {
            "po_number": order.product_id + "_" + str(int(time.time())),
            "product_id": order.product_id,
            "quantity": order.quantity,
            "unit_cost": adjusted_unit_cost,
            "total_cost": total_cost,
            "status": "confirmed",
            "created_at": datetime.now(),
            "estimated_delivery": estimated_delivery,
            "tracking_number": f"TRK{random.randint(100000, 999999)}"
        }
        
        return PurchaseOrderResponse(
            po_number=supplier_orders[supplier_order_id]["po_number"],
            supplier_order_id=supplier_order_id,
            status="confirmed",
            estimated_delivery=estimated_delivery.isoformat(),
            total_cost=total_cost,
            confirmation_message=f"Order confirmed by {supplier_config['name']}. Expected delivery in {lead_time} days."
        )
    
    @app.get("/api/order-status/{supplier_order_id}", response_model=OrderStatusResponse)
    def get_order_status(supplier_order_id: str):
        """Get order status"""
        
        if supplier_order_id not in supplier_orders:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = supplier_orders[supplier_order_id]
        
        # Simulate status progression
        days_since_order = (datetime.now() - order["created_at"]).days
        lead_time = supplier_config["lead_time_days"]
        
        if days_since_order >= lead_time:
            status = "delivered"
            actual_delivery = order["created_at"] + timedelta(days=lead_time)
            notes = "Package delivered successfully"
        elif days_since_order >= lead_time - 1:
            status = "out_for_delivery"
            actual_delivery = None
            notes = "Package out for delivery"
        elif days_since_order >= 1:
            status = "in_transit"
            actual_delivery = None
            notes = "Package in transit to destination"
        else:
            status = "processing"
            actual_delivery = None
            notes = "Order being processed at warehouse"
        
        return OrderStatusResponse(
            supplier_order_id=supplier_order_id,
            status=status,
            tracking_number=order["tracking_number"],
            estimated_delivery=order["estimated_delivery"].isoformat(),
            actual_delivery=actual_delivery.isoformat() if actual_delivery else None,
            notes=notes
        )
    
    @app.get("/api/inventory/{product_id}")
    def check_inventory(product_id: str):
        """Check product availability and pricing"""
        
        # Simulate inventory check
        available_quantity = random.randint(0, 1000)
        in_stock = available_quantity > 0
        
        base_price = random.uniform(5.0, 50.0)  # Random base price
        
        return {
            "product_id": product_id,
            "in_stock": in_stock,
            "available_quantity": available_quantity,
            "unit_price": round(base_price, 2),
            "minimum_order": supplier_config.get("minimum_order", 1),
            "lead_time_days": supplier_config["lead_time_days"]
        }
    
    @app.get("/api/health")
    def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "supplier_id": supplier_id,
            "timestamp": datetime.now().isoformat(),
            "active_orders": len(supplier_orders)
        }
    
    return app

# Create individual supplier apps
supplier_001_app = create_supplier_app("SUPPLIER_001")
supplier_002_app = create_supplier_app("SUPPLIER_002") 
supplier_003_app = create_supplier_app("SUPPLIER_003")

# Main app that can route to different suppliers
main_app = FastAPI(
    title="Mock Supplier Network",
    description="Mock supplier APIs for testing procurement agent",
    version="1.0.0"
)

@main_app.get("/")
def network_info():
    return {
        "message": "Mock Supplier Network",
        "suppliers": list(SUPPLIERS.keys()),
        "total_orders": len(supplier_orders),
        "status": "operational"
    }

@main_app.get("/suppliers")
def list_suppliers():
    """List all available suppliers"""
    return {
        "suppliers": [
            {
                "supplier_id": sid,
                "name": config["name"],
                "lead_time_days": config["lead_time_days"],
                "success_rate": config["success_rate"]
            }
            for sid, config in SUPPLIERS.items()
        ]
    }

@main_app.get("/orders")
def list_all_orders():
    """List all orders across suppliers"""
    return {
        "orders": [
            {
                "supplier_order_id": oid,
                "product_id": order["product_id"],
                "quantity": order["quantity"],
                "status": order["status"],
                "total_cost": order["total_cost"]
            }
            for oid, order in supplier_orders.items()
        ],
        "total_orders": len(supplier_orders)
    }

if __name__ == "__main__":
    import uvicorn
    print("🏭 Starting Mock Supplier Network")
    print("Available suppliers:")
    for sid, config in SUPPLIERS.items():
        print(f"  - {sid}: {config['name']}")
    
    print("\n🚀 Starting server on port 8001...")
    uvicorn.run(main_app, host="0.0.0.0", port=8001)
