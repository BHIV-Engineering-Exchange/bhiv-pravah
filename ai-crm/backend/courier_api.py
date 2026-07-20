#!/usr/bin/env python3
"""
Mock Courier API for testing delivery agent
Simulates external courier/shipping services
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import random
import time
from datetime import datetime, timedelta
import uuid

# Pydantic models for API
class ShipmentRequest(BaseModel):
    order_id: int
    pickup_address: str
    delivery_address: str
    package_weight: float = 1.0
    service_type: str = "standard"  # standard, express, overnight
    special_instructions: str = ""

class ShipmentResponse(BaseModel):
    shipment_id: str
    tracking_number: str
    status: str
    estimated_delivery: str
    cost: float
    confirmation_message: str

class TrackingResponse(BaseModel):
    tracking_number: str
    status: str
    current_location: str
    estimated_delivery: str
    actual_delivery: Optional[str] = None
    delivery_events: List[Dict]

# Mock courier configurations
COURIERS = {
    "COURIER_001": {
        "name": "FastShip Express",
        "service_type": "express",
        "success_rate": 0.95,
        "avg_response_time": 1,
        "delivery_days": 2,
        "cost_per_kg": 8.50,
        "coverage": "National"
    },
    "COURIER_002": {
        "name": "Standard Delivery Co.",
        "service_type": "standard", 
        "success_rate": 0.92,
        "avg_response_time": 3,
        "delivery_days": 5,
        "cost_per_kg": 4.25,
        "coverage": "Regional"
    },
    "COURIER_003": {
        "name": "Overnight Rush",
        "service_type": "overnight",
        "success_rate": 0.98,
        "avg_response_time": 0.5,
        "delivery_days": 1,
        "cost_per_kg": 15.00,
        "coverage": "Metro"
    }
}

# In-memory storage for shipments
courier_shipments = {}

def create_courier_app(courier_id: str) -> FastAPI:
    """Create a FastAPI app for a specific courier"""
    
    if courier_id not in COURIERS:
        raise ValueError(f"Unknown courier: {courier_id}")
    
    courier_config = COURIERS[courier_id]
    app = FastAPI(
        title=f"{courier_config['name']} API",
        description=f"Mock API for {courier_config['name']}",
        version="1.0.0"
    )
    
    @app.get("/")
    def courier_info():
        return {
            "courier_id": courier_id,
            "name": courier_config["name"],
            "service_type": courier_config["service_type"],
            "status": "operational",
            "api_version": "1.0.0",
            "capabilities": [
                "shipment_creation",
                "package_tracking",
                "delivery_updates",
                "cost_calculation"
            ]
        }
    
    @app.post("/api/create-shipment", response_model=ShipmentResponse)
    def create_shipment(shipment: ShipmentRequest):
        """Create a new shipment"""
        
        # Simulate processing time
        time.sleep(random.uniform(0.2, courier_config["avg_response_time"]))
        
        # Simulate occasional failures
        if random.random() > courier_config["success_rate"]:
            raise HTTPException(
                status_code=503,
                detail=f"Courier {courier_id} temporarily unavailable"
            )
        
        # Generate shipment details
        shipment_id = f"{courier_id}_{uuid.uuid4().hex[:8].upper()}"
        tracking_number = f"{courier_id[:2]}{random.randint(100000000, 999999999)}"
        
        # Calculate delivery date
        delivery_days = courier_config["delivery_days"]
        if shipment.service_type == "overnight":
            delivery_days = 1
        elif shipment.service_type == "express":
            delivery_days = max(1, delivery_days - 1)
        
        estimated_delivery = datetime.now() + timedelta(days=delivery_days)
        
        # Calculate cost
        cost = shipment.package_weight * courier_config["cost_per_kg"]
        if shipment.service_type == "express":
            cost *= 1.5
        elif shipment.service_type == "overnight":
            cost *= 2.0
        
        # Store shipment
        courier_shipments[tracking_number] = {
            "shipment_id": shipment_id,
            "order_id": shipment.order_id,
            "tracking_number": tracking_number,
            "status": "created",
            "pickup_address": shipment.pickup_address,
            "delivery_address": shipment.delivery_address,
            "package_weight": shipment.package_weight,
            "service_type": shipment.service_type,
            "cost": cost,
            "created_at": datetime.now(),
            "estimated_delivery": estimated_delivery,
            "events": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "status": "created",
                    "location": "Processing Center",
                    "description": "Shipment created and ready for pickup"
                }
            ]
        }
        
        return ShipmentResponse(
            shipment_id=shipment_id,
            tracking_number=tracking_number,
            status="created",
            estimated_delivery=estimated_delivery.isoformat(),
            cost=round(cost, 2),
            confirmation_message=f"Shipment created with {courier_config['name']}. Estimated delivery in {delivery_days} days."
        )
    
    @app.get("/api/track/{tracking_number}", response_model=TrackingResponse)
    def track_shipment(tracking_number: str):
        """Track shipment status"""
        
        if tracking_number not in courier_shipments:
            raise HTTPException(status_code=404, detail="Tracking number not found")
        
        shipment = courier_shipments[tracking_number]
        
        # Simulate status progression
        hours_since_creation = (datetime.now() - shipment["created_at"]).total_seconds() / 3600
        delivery_days = courier_config["delivery_days"]
        
        # Update status based on time elapsed
        if hours_since_creation >= delivery_days * 24:
            current_status = "delivered"
            current_location = "Delivered"
            actual_delivery = shipment["created_at"] + timedelta(days=delivery_days)
            
            # Add delivery event if not already added
            if not any(event["status"] == "delivered" for event in shipment["events"]):
                shipment["events"].append({
                    "timestamp": actual_delivery.isoformat(),
                    "status": "delivered",
                    "location": "Customer Address",
                    "description": "Package delivered successfully"
                })
                
        elif hours_since_creation >= (delivery_days * 24) - 4:
            current_status = "out_for_delivery"
            current_location = "Local Delivery Hub"
            actual_delivery = None
            
            if not any(event["status"] == "out_for_delivery" for event in shipment["events"]):
                shipment["events"].append({
                    "timestamp": datetime.now().isoformat(),
                    "status": "out_for_delivery",
                    "location": "Local Delivery Hub",
                    "description": "Package out for delivery"
                })
                
        elif hours_since_creation >= 12:
            current_status = "in_transit"
            current_location = "Distribution Center"
            actual_delivery = None
            
            if not any(event["status"] == "in_transit" for event in shipment["events"]):
                shipment["events"].append({
                    "timestamp": (shipment["created_at"] + timedelta(hours=12)).isoformat(),
                    "status": "in_transit",
                    "location": "Distribution Center",
                    "description": "Package in transit to destination"
                })
                
        elif hours_since_creation >= 2:
            current_status = "picked_up"
            current_location = "Origin Facility"
            actual_delivery = None
            
            if not any(event["status"] == "picked_up" for event in shipment["events"]):
                shipment["events"].append({
                    "timestamp": (shipment["created_at"] + timedelta(hours=2)).isoformat(),
                    "status": "picked_up",
                    "location": "Origin Facility",
                    "description": "Package picked up from sender"
                })
        else:
            current_status = "created"
            current_location = "Processing Center"
            actual_delivery = None
        
        # Update shipment status
        shipment["status"] = current_status
        
        return TrackingResponse(
            tracking_number=tracking_number,
            status=current_status,
            current_location=current_location,
            estimated_delivery=shipment["estimated_delivery"].isoformat(),
            actual_delivery=actual_delivery.isoformat() if actual_delivery else None,
            delivery_events=shipment["events"]
        )
    
    @app.get("/api/quote")
    def get_shipping_quote(weight: float = 1.0, service_type: str = "standard"):
        """Get shipping cost quote"""
        
        base_cost = weight * courier_config["cost_per_kg"]
        
        if service_type == "express":
            cost = base_cost * 1.5
            delivery_days = max(1, courier_config["delivery_days"] - 1)
        elif service_type == "overnight":
            cost = base_cost * 2.0
            delivery_days = 1
        else:
            cost = base_cost
            delivery_days = courier_config["delivery_days"]
        
        return {
            "courier": courier_config["name"],
            "service_type": service_type,
            "weight_kg": weight,
            "cost": round(cost, 2),
            "estimated_delivery_days": delivery_days,
            "coverage": courier_config["coverage"]
        }
    
    @app.get("/api/health")
    def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "courier_id": courier_id,
            "timestamp": datetime.now().isoformat(),
            "active_shipments": len([s for s in courier_shipments.values() if s["status"] != "delivered"])
        }
    
    return app

# Create individual courier apps
courier_001_app = create_courier_app("COURIER_001")
courier_002_app = create_courier_app("COURIER_002")
courier_003_app = create_courier_app("COURIER_003")

# Main app that can route to different couriers
main_app = FastAPI(
    title="Mock Courier Network",
    description="Mock courier APIs for testing delivery agent",
    version="1.0.0"
)

@main_app.get("/")
def network_info():
    return {
        "message": "Mock Courier Network",
        "couriers": list(COURIERS.keys()),
        "total_shipments": len(courier_shipments),
        "status": "operational"
    }

@main_app.get("/couriers")
def list_couriers():
    """List all available couriers"""
    return {
        "couriers": [
            {
                "courier_id": cid,
                "name": config["name"],
                "service_type": config["service_type"],
                "delivery_days": config["delivery_days"],
                "cost_per_kg": config["cost_per_kg"]
            }
            for cid, config in COURIERS.items()
        ]
    }

@main_app.get("/shipments")
def list_all_shipments():
    """List all shipments across couriers"""
    return {
        "shipments": [
            {
                "tracking_number": tracking,
                "order_id": shipment["order_id"],
                "status": shipment["status"],
                "cost": shipment["cost"]
            }
            for tracking, shipment in courier_shipments.items()
        ],
        "total_shipments": len(courier_shipments)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚚 Starting Mock Courier Network")
    print("Available couriers:")
    for cid, config in COURIERS.items():
        print(f"  - {cid}: {config['name']} ({config['service_type']})")
    
    print("\n🚀 Starting server on port 9001...")
    uvicorn.run(main_app, host="0.0.0.0", port=9001)
