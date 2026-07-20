#!/usr/bin/env python3
"""
Procurement Agent for Autonomous Purchase Order Generation
Monitors inventory levels and automatically creates purchase orders when stock is low
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.service import DatabaseService
from database.models import PurchaseOrder, Supplier, Inventory

class ProcurementAgent:
    """Autonomous procurement agent"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        
    def scan_inventory_levels(self) -> List[Dict]:
        """Scan inventory for items that need reordering"""
        print("🔍 Scanning inventory levels...")
        
        with DatabaseService() as db_service:
            inventory_items = db_service.get_inventory()
            low_stock_items = []
            
            for item in inventory_items:
                current_stock = item['CurrentStock']
                reorder_point = item['ReorderPoint']
                
                if current_stock <= reorder_point:
                    # Calculate suggested order quantity (more reasonable amounts)
                    max_stock = item['MaxStock']
                    deficit = reorder_point - current_stock
                    # Order enough to reach optimal stock level (between reorder point and max)
                    optimal_stock = reorder_point + (max_stock - reorder_point) * 0.6
                    suggested_qty = max(deficit, int(optimal_stock - current_stock))
                    
                    low_stock_items.append({
                        'product_id': item['ProductID'],
                        'current_stock': current_stock,
                        'reorder_point': reorder_point,
                        'max_stock': max_stock,
                        'suggested_quantity': suggested_qty,
                        'urgency': 'critical' if current_stock == 0 else 'high' if current_stock < reorder_point * 0.5 else 'normal'
                    })
                    
                    print(f"📉 Low stock: {item['ProductID']} ({current_stock}/{reorder_point}) - Suggested order: {suggested_qty}")
            
            print(f"🎯 Found {len(low_stock_items)} items needing reorder")
            return low_stock_items
    
    def get_supplier_for_product(self, product_id: str) -> Optional[Dict]:
        """Get supplier information for a product"""
        with DatabaseService() as db_service:
            # Get inventory item to find supplier
            inventory = db_service.get_inventory()
            product_inventory = next((item for item in inventory if item['ProductID'] == product_id), None)
            
            if not product_inventory:
                return None
            
            # In a real system, we'd query the suppliers table
            # For now, we'll use the supplier_id from inventory
            supplier_id = getattr(product_inventory, 'supplier_id', 'SUPPLIER_001')
            
            # Mock supplier data (in production, this would come from database)
            suppliers = {
                'SUPPLIER_001': {
                    'supplier_id': 'SUPPLIER_001',
                    'name': 'TechParts Supply Co.',
                    'api_endpoint': 'http://localhost:8001/api',
                    'lead_time_days': 5,
                    'minimum_order': 10
                },
                'SUPPLIER_002': {
                    'supplier_id': 'SUPPLIER_002',
                    'name': 'Global Components Ltd.',
                    'api_endpoint': 'http://localhost:8001/api',
                    'lead_time_days': 7,
                    'minimum_order': 5
                },
                'SUPPLIER_003': {
                    'supplier_id': 'SUPPLIER_003',
                    'name': 'FastTrack Logistics',
                    'api_endpoint': 'http://localhost:8001/api',
                    'lead_time_days': 3,
                    'minimum_order': 20
                }
            }
            
            return suppliers.get(supplier_id)
    
    def calculate_procurement_confidence(self, product_id: str, quantity: int, urgency: str) -> float:
        """Calculate confidence score for procurement decision"""
        base_confidence = 0.8
        
        # Adjust based on urgency
        if urgency == 'critical':
            base_confidence += 0.1
        elif urgency == 'high':
            base_confidence += 0.05
        
        # Adjust based on quantity (very large orders need review)
        if quantity > 100:
            base_confidence -= 0.3
        elif quantity > 50:
            base_confidence -= 0.2
        elif quantity > 30:
            base_confidence -= 0.1
        
        # Check historical procurement success
        with DatabaseService() as db_service:
            # In production, we'd check historical PO success rates
            # For now, we'll use a simple heuristic
            pass
        
        return max(0.1, min(1.0, base_confidence))
    
    def create_purchase_order(self, product_id: str, quantity: int, supplier: Dict, urgency: str = 'normal') -> Optional[str]:
        """Create purchase order with supplier"""
        print(f"📋 Creating purchase order: {product_id} x{quantity} from {supplier['name']}")

        try:
            # Get product pricing (mock data for now)
            unit_cost = self.get_product_cost(product_id, supplier)
            total_cost = unit_cost * quantity

            # Generate mock PO response (simulating successful supplier API call)
            import uuid
            po_number = f"PO_{product_id}_{int(datetime.now().timestamp())}"
            supplier_order_id = f"{supplier['supplier_id']}_{uuid.uuid4().hex[:8].upper()}"

            po_response = {
                "po_number": po_number,
                "supplier_order_id": supplier_order_id,
                "status": "confirmed",
                "estimated_delivery": (datetime.now() + timedelta(days=supplier['lead_time_days'])).isoformat(),
                "total_cost": total_cost,
                "confirmation_message": f"Order confirmed by {supplier['name']}"
            }

            # Store PO in database
            with DatabaseService() as db_service:
                success = self.store_purchase_order(
                    po_response,
                    product_id,
                    quantity,
                    unit_cost,
                    supplier['supplier_id']
                )

                if success:
                    # Log the procurement action
                    db_service.log_agent_action(
                        action="purchase_order_created",
                        product_id=product_id,
                        quantity=quantity,
                        confidence=self.calculate_procurement_confidence(product_id, quantity, urgency),
                        human_review=False,
                        details=f"PO {po_response['po_number']} created with {supplier['name']} (SIMULATED)"
                    )

                    print(f"✅ Purchase order created: {po_response['po_number']} (SIMULATED)")
                    return po_response['supplier_order_id']
                else:
                    print(f"❌ Failed to store purchase order in database")
                    return None

        except Exception as e:
            print(f"❌ Error creating purchase order: {e}")
            return None
    
    def get_product_cost(self, product_id: str, supplier: Dict) -> float:
        """Get product cost from supplier or database"""
        # In production, this would query supplier API or database
        # For now, return mock pricing
        base_costs = {
            'A101': 15.50,
            'B202': 22.00,
            'C303': 8.75,
            'D404': 45.00,
            'E505': 12.25
        }
        return base_costs.get(product_id, 20.00)
    
    def store_purchase_order(self, po_response: Dict, product_id: str, quantity: int, unit_cost: float, supplier_id: str) -> bool:
        """Store purchase order in database"""
        try:
            with DatabaseService() as db_service:
                # Create PO record (simplified - in production we'd use proper ORM)
                po_data = {
                    'po_number': po_response['po_number'],
                    'supplier_id': supplier_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_cost': unit_cost,
                    'total_cost': po_response['total_cost'],
                    'status': 'sent',
                    'supplier_order_id': po_response['supplier_order_id'],
                    'expected_delivery': po_response['estimated_delivery']
                }
                
                # In production, we'd use proper ORM insert
                # For now, we'll log it as an agent action
                db_service.log_agent_action(
                    action="purchase_order_stored",
                    product_id=product_id,
                    quantity=quantity,
                    details=f"PO stored: {json.dumps(po_data)}"
                )
                
                return True
        except Exception as e:
            print(f"Error storing PO: {e}")
            return False
    
    def run_procurement_cycle(self) -> Dict:
        """Run complete procurement cycle"""
        print("🤖 Starting Procurement Agent Cycle")
        print("=" * 50)
        
        results = {
            'items_scanned': 0,
            'items_needing_reorder': 0,
            'purchase_orders_created': 0,
            'items_submitted_for_review': 0,
            'errors': []
        }
        
        try:
            # Step 1: Scan inventory levels
            low_stock_items = self.scan_inventory_levels()
            results['items_needing_reorder'] = len(low_stock_items)
            
            # Step 2: Process each low stock item
            for item in low_stock_items:
                product_id = item['product_id']
                quantity = item['suggested_quantity']
                urgency = item['urgency']
                
                # Calculate confidence
                confidence = self.calculate_procurement_confidence(product_id, quantity, urgency)
                
                # Check if human review is needed (adjust thresholds for demo)
                if confidence < self.confidence_threshold or quantity > 20:
                    # Log for human review using DatabaseService
                    with DatabaseService() as db_service:
                        db_service.log_agent_action(
                            action="procurement_review_needed",
                            product_id=product_id,
                            quantity=quantity,
                            confidence=confidence,
                            human_review=True,
                            details=f"Procurement decision for {product_id}: order {quantity} units (urgency: {urgency})"
                        )
                    
                    results['items_submitted_for_review'] += 1
                    print(f"⚠️  {product_id} submitted for human review (confidence: {confidence:.2f})")
                    
                else:
                    # Auto-execute high confidence procurement
                    supplier = self.get_supplier_for_product(product_id)
                    
                    if supplier:
                        order_id = self.create_purchase_order(product_id, quantity, supplier, urgency)
                        
                        if order_id:
                            results['purchase_orders_created'] += 1
                        else:
                            results['errors'].append(f"Failed to create PO for {product_id}")
                    else:
                        results['errors'].append(f"No supplier found for {product_id}")
            
            # Step 3: Log completion
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action="procurement_cycle_completed",
                    details=f"Cycle results: {json.dumps(results)}"
                )
            
            print("=" * 50)
            print("✅ Procurement cycle completed")
            print(f"📊 Results: {results['purchase_orders_created']} POs created, {results['items_submitted_for_review']} items for review")
            
            return results
            
        except Exception as e:
            error_msg = f"Procurement cycle error: {str(e)}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            
            # Log error
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action="procurement_error",
                    details=error_msg,
                    human_review=True
                )
            
            return results

def run_procurement_agent():
    """Main function to run procurement agent"""
    agent = ProcurementAgent()
    return agent.run_procurement_cycle()

if __name__ == "__main__":
    print("🏭 AI Procurement Agent")
    print("Autonomous Purchase Order Generation System")
    print()
    
    results = run_procurement_agent()
    
    print(f"\n📈 Final Results:")
    print(f"   - Purchase Orders Created: {results['purchase_orders_created']}")
    print(f"   - Items for Human Review: {results['items_submitted_for_review']}")
    print(f"   - Errors: {len(results['errors'])}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n🚀 Procurement agent cycle complete!")
