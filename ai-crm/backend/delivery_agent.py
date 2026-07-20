#!/usr/bin/env python3
"""
Delivery Agent for Autonomous Shipment Management
Monitors orders and automatically creates shipments with courier integration
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.service import DatabaseService

class DeliveryAgent:
    """Autonomous delivery agent"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        
    def scan_orders_for_shipment(self) -> List[Dict]:
        """Scan orders that need shipment creation"""
        print("📦 Scanning orders for shipment creation...")
        
        with DatabaseService() as db_service:
            orders = db_service.get_orders()
            shipment_needed = []
            
            for order in orders:
                order_id = order['OrderID']
                status = order['Status']
                
                # Check if order needs shipment (Processing status and no existing shipment)
                if status == 'Processing':
                    # Check if shipment already exists
                    existing_shipment = self.get_shipment_for_order(order_id)
                    
                    if not existing_shipment:
                        shipment_needed.append({
                            'order_id': order_id,
                            'customer_id': order.get('CustomerID', 'UNKNOWN'),
                            'product_id': order.get('ProductID', 'UNKNOWN'),
                            'quantity': order.get('Quantity', 1),
                            'urgency': self.determine_urgency(order)
                        })
                        
                        print(f"📋 Order needs shipment: #{order_id} ({order.get('ProductID', 'N/A')})")
            
            print(f"🎯 Found {len(shipment_needed)} orders needing shipment")
            return shipment_needed
    
    def get_shipment_for_order(self, order_id: int) -> Optional[Dict]:
        """Check if shipment exists for order"""
        # In production, this would query the shipments table
        # For now, we'll simulate by checking our mock data
        return None  # Assume no existing shipments for demo
    
    def determine_urgency(self, order: Dict) -> str:
        """Determine shipment urgency based on order details"""
        # Simple urgency logic - in production this would be more sophisticated
        quantity = order.get('Quantity', 1)
        
        if quantity >= 5:
            return 'high'
        elif quantity >= 3:
            return 'medium'
        else:
            return 'normal'
    
    def select_courier(self, order: Dict, urgency: str) -> Dict:
        """Select best courier for the order"""
        # Mock courier selection logic
        couriers = {
            'COURIER_001': {
                'courier_id': 'COURIER_001',
                'name': 'FastShip Express',
                'service_type': 'express',
                'api_endpoint': 'http://localhost:9001/api',
                'delivery_days': 2,
                'cost_per_kg': 8.50
            },
            'COURIER_002': {
                'courier_id': 'COURIER_002',
                'name': 'Standard Delivery Co.',
                'service_type': 'standard',
                'api_endpoint': 'http://localhost:9001/api',
                'delivery_days': 5,
                'cost_per_kg': 4.25
            },
            'COURIER_003': {
                'courier_id': 'COURIER_003',
                'name': 'Overnight Rush',
                'service_type': 'overnight',
                'api_endpoint': 'http://localhost:9001/api',
                'delivery_days': 1,
                'cost_per_kg': 15.00
            }
        }
        
        # Select courier based on urgency
        if urgency == 'high':
            return couriers['COURIER_001']  # Express
        elif urgency == 'medium':
            return couriers['COURIER_002']  # Standard
        else:
            return couriers['COURIER_002']  # Standard (cost-effective)
    
    def calculate_delivery_confidence(self, order: Dict, courier: Dict) -> float:
        """Calculate confidence score for delivery decision"""
        base_confidence = 0.8
        
        # Adjust based on order value/quantity
        quantity = order.get('quantity', 1)
        if quantity > 10:
            base_confidence -= 0.2  # High value orders need review
        elif quantity > 5:
            base_confidence -= 0.1
        
        # Adjust based on courier reliability
        if courier['service_type'] == 'overnight':
            base_confidence += 0.1  # Premium service
        elif courier['service_type'] == 'express':
            base_confidence += 0.05
        
        return max(0.1, min(1.0, base_confidence))
    
    def create_shipment(self, order: Dict, courier: Dict, urgency: str = 'normal') -> Optional[str]:
        """Create shipment with courier"""
        print(f"🚚 Creating shipment: Order #{order['order_id']} via {courier['name']}")
        
        try:
            # Prepare shipment request
            shipment_request = {
                "order_id": order['order_id'],
                "pickup_address": "Warehouse A, 123 Main St, City, State 12345",
                "delivery_address": f"Customer {order['customer_id']} Address",
                "package_weight": order['quantity'] * 0.5,  # Assume 0.5kg per item
                "service_type": courier['service_type'],
                "special_instructions": f"Order #{order['order_id']} - Handle with care"
            }
            
            # For demo, simulate successful courier API response
            import uuid
            tracking_number = f"{courier['courier_id'][:2]}{random.randint(100000000, 999999999)}"
            shipment_id = f"{courier['courier_id']}_{uuid.uuid4().hex[:8].upper()}"
            
            # Calculate cost and delivery date
            cost = shipment_request["package_weight"] * courier['cost_per_kg']
            estimated_delivery = datetime.now() + timedelta(days=courier['delivery_days'])
            
            shipment_response = {
                "shipment_id": shipment_id,
                "tracking_number": tracking_number,
                "status": "created",
                "estimated_delivery": estimated_delivery.isoformat(),
                "cost": cost,
                "confirmation_message": f"Shipment created with {courier['name']}"
            }
            
            # Store shipment in database
            success = self.store_shipment(
                shipment_response,
                order['order_id'],
                courier['courier_id']
            )
            
            if success:
                # Update order status to 'Shipped'
                with DatabaseService() as db_service:
                    db_service.update_order_status(order['order_id'], 'Shipped')
                    
                    # Log the delivery action
                    db_service.log_agent_action(
                        action="shipment_created",
                        product_id=order.get('product_id'),
                        quantity=order.get('quantity'),
                        confidence=self.calculate_delivery_confidence(order, courier),
                        human_review=False,
                        details=f"Shipment {tracking_number} created with {courier['name']} (SIMULATED)"
                    )
                
                print(f"✅ Shipment created: {tracking_number}")
                return tracking_number
            else:
                print(f"❌ Failed to store shipment in database")
                return None
                
        except Exception as e:
            print(f"❌ Error creating shipment: {e}")
            return None
    
    def store_shipment(self, shipment_response: Dict, order_id: int, courier_id: str) -> bool:
        """Store shipment in database"""
        try:
            with DatabaseService() as db_service:
                # Store shipment data (simplified - in production we'd use proper ORM)
                shipment_data = {
                    'shipment_id': shipment_response['shipment_id'],
                    'order_id': order_id,
                    'courier_id': courier_id,
                    'tracking_number': shipment_response['tracking_number'],
                    'status': 'created',
                    'estimated_delivery': shipment_response['estimated_delivery'],
                    'cost': shipment_response['cost']
                }
                
                # Log shipment creation
                db_service.log_agent_action(
                    action="shipment_stored",
                    details=f"Shipment stored: {json.dumps(shipment_data)}"
                )
                
                return True
        except Exception as e:
            print(f"Error storing shipment: {e}")
            return False
    
    def update_shipment_status(self, tracking_number: str) -> Dict:
        """Update shipment status from courier"""
        print(f"🔄 Updating status for tracking: {tracking_number}")
        
        try:
            # In production, this would call the actual courier API
            # For demo, simulate status update
            import random
            
            statuses = ['created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered']
            current_status = random.choice(statuses)
            
            status_update = {
                'tracking_number': tracking_number,
                'status': current_status,
                'current_location': 'Distribution Center',
                'timestamp': datetime.now().isoformat(),
                'estimated_delivery': (datetime.now() + timedelta(days=2)).isoformat()
            }
            
            # Store status update
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action="shipment_status_updated",
                    details=f"Status update: {json.dumps(status_update)}"
                )
            
            print(f"✅ Status updated: {tracking_number} -> {current_status}")
            return status_update
            
        except Exception as e:
            print(f"❌ Error updating shipment status: {e}")
            return {}
    
    def run_delivery_cycle(self) -> Dict:
        """Run complete delivery cycle"""
        print("🚚 Starting Delivery Agent Cycle")
        print("=" * 50)
        
        results = {
            'orders_scanned': 0,
            'orders_needing_shipment': 0,
            'shipments_created': 0,
            'shipments_updated': 0,
            'items_submitted_for_review': 0,
            'errors': []
        }
        
        try:
            # Step 1: Scan orders for shipment needs
            orders_needing_shipment = self.scan_orders_for_shipment()
            results['orders_needing_shipment'] = len(orders_needing_shipment)
            
            # Step 2: Process each order
            for order in orders_needing_shipment:
                order_id = order['order_id']
                urgency = order['urgency']
                
                # Select courier
                courier = self.select_courier(order, urgency)
                
                # Calculate confidence
                confidence = self.calculate_delivery_confidence(order, courier)
                
                # Check if human review is needed
                if confidence < self.confidence_threshold or order.get('quantity', 1) > 10:
                    # Log for human review using DatabaseService
                    with DatabaseService() as db_service:
                        db_service.log_agent_action(
                            action="delivery_review_needed",
                            product_id=order.get('product_id'),
                            quantity=order.get('quantity', 1),
                            confidence=confidence,
                            human_review=True,
                            details=f"Delivery decision for Order #{order_id}: ship via {courier['name']} (urgency: {urgency})"
                        )
                    
                    results['items_submitted_for_review'] += 1
                    print(f"⚠️  Order #{order_id} submitted for human review (confidence: {confidence:.2f})")
                    
                else:
                    # Auto-execute high confidence delivery
                    tracking_number = self.create_shipment(order, courier, urgency)
                    
                    if tracking_number:
                        results['shipments_created'] += 1
                    else:
                        results['errors'].append(f"Failed to create shipment for Order #{order_id}")
            
            # Step 3: Update existing shipment statuses (sample)
            # In production, this would query all active shipments
            sample_tracking_numbers = ['FS123456789', 'SD987654321', 'OR555666777']
            for tracking in sample_tracking_numbers:
                status_update = self.update_shipment_status(tracking)
                if status_update:
                    results['shipments_updated'] += 1
            
            # Step 4: Log completion
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action="delivery_cycle_completed",
                    details=f"Cycle results: {json.dumps(results)}"
                )
            
            print("=" * 50)
            print("✅ Delivery cycle completed")
            print(f"📊 Results: {results['shipments_created']} shipments created, {results['items_submitted_for_review']} items for review")
            
            return results
            
        except Exception as e:
            error_msg = f"Delivery cycle error: {str(e)}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            
            # Log error
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action="delivery_error",
                    details=error_msg,
                    human_review=True
                )
            
            return results

def run_delivery_agent():
    """Main function to run delivery agent"""
    agent = DeliveryAgent()
    return agent.run_delivery_cycle()

if __name__ == "__main__":
    import random  # Add this import
    
    print("🚚 AI Delivery Agent")
    print("Autonomous Shipment Management System")
    print()
    
    results = run_delivery_agent()
    
    print(f"\n📈 Final Results:")
    print(f"   - Shipments Created: {results['shipments_created']}")
    print(f"   - Shipments Updated: {results['shipments_updated']}")
    print(f"   - Items for Human Review: {results['items_submitted_for_review']}")
    print(f"   - Errors: {len(results['errors'])}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n🚀 Delivery agent cycle complete!")
