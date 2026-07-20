#!/usr/bin/env python3
"""
Supplier Communication System
Handle supplier messages, procurement requests, and contact management
"""

from database.models import SessionLocal, Supplier, PurchaseOrder, AgentLog
from user_product_models import get_user_product_by_id
from datetime import datetime, timedelta
import json
import uuid

class SupplierCommunicationSystem:
    """Manage supplier communications and procurement"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def get_all_suppliers(self):
        """Get all suppliers with their information"""
        suppliers = self.db.query(Supplier).filter(Supplier.is_active == True).all()
        return [
            {
                'supplier_id': s.supplier_id,
                'name': s.name,
                'email': s.contact_email,
                'phone': s.contact_phone,
                'lead_time_days': s.lead_time_days,
                'minimum_order': s.minimum_order,
                'api_endpoint': s.api_endpoint
            }
            for s in suppliers
        ]
    
    def get_supplier_by_id(self, supplier_id):
        """Get specific supplier information"""
        supplier = self.db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        if supplier:
            return {
                'supplier_id': supplier.supplier_id,
                'name': supplier.name,
                'email': supplier.contact_email,
                'phone': supplier.contact_phone,
                'lead_time_days': supplier.lead_time_days,
                'minimum_order': supplier.minimum_order,
                'api_endpoint': supplier.api_endpoint
            }
        return None
    
    def send_reorder_request(self, supplier_id, product_id, quantity, urgency="normal", notes=""):
        """Send reorder request to supplier"""
        supplier = self.get_supplier_by_id(supplier_id)
        product = get_user_product_by_id(product_id)
        
        if not supplier or not product:
            return {
                'success': False,
                'error': 'Supplier or product not found'
            }
        
        # Check minimum order quantity
        if quantity < supplier['minimum_order']:
            return {
                'success': False,
                'error': f'Quantity {quantity} is below minimum order of {supplier["minimum_order"]}'
            }
        
        # Create purchase order
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        unit_cost = product.unit_price * 0.7  # Assume cost is 70% of selling price
        total_cost = unit_cost * quantity
        
        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            product_id=product_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            status='pending',
            created_at=datetime.utcnow(),
            notes=notes
        )
        
        self.db.add(purchase_order)
        
        # Create agent log
        agent_log = AgentLog(
            timestamp=datetime.utcnow(),
            action="Purchase Order Created",
            product_id=product_id,
            quantity=quantity,
            confidence=0.95,
            human_review=urgency == "urgent",
            details=f"PO {po_number} created for {product.name} - {quantity} units from {supplier['name']}"
        )
        
        self.db.add(agent_log)
        self.db.commit()
        
        # Simulate sending message (in real system, this would send email/API call)
        message = self.create_reorder_message(supplier, product, quantity, po_number, urgency, notes)
        
        return {
            'success': True,
            'po_number': po_number,
            'supplier': supplier,
            'product': product,
            'quantity': quantity,
            'total_cost': total_cost,
            'message': message,
            'estimated_delivery': datetime.now() + timedelta(days=supplier['lead_time_days'])
        }
    
    def create_reorder_message(self, supplier, product, quantity, po_number, urgency, notes):
        """Create formatted reorder message"""
        urgency_text = "🔴 URGENT" if urgency == "urgent" else "🟡 NORMAL"
        
        message = f"""
Subject: {urgency_text} - Purchase Order {po_number}

Dear {supplier['name']},

We would like to place the following order:

📦 PRODUCT DETAILS:
- Product: {product.name}
- Product ID: {product.product_id}
- Quantity: {quantity} units
- Category: {product.category.value}

📋 ORDER DETAILS:
- PO Number: {po_number}
- Order Date: {datetime.now().strftime('%Y-%m-%d')}
- Urgency: {urgency.upper()}
- Expected Delivery: {(datetime.now() + timedelta(days=supplier['lead_time_days'])).strftime('%Y-%m-%d')}

📞 CONTACT INFO:
- Email: {supplier['email']}
- Phone: {supplier['phone']}

💬 ADDITIONAL NOTES:
{notes if notes else 'No additional notes'}

Please confirm receipt and provide delivery timeline.

Best regards,
AI Logistics System
        """
        
        return message.strip()
    
    def send_quality_issue_report(self, supplier_id, product_id, issue_type, description, affected_quantity=0):
        """Send quality issue report to supplier"""
        supplier = self.get_supplier_by_id(supplier_id)
        product = get_user_product_by_id(product_id)
        
        if not supplier or not product:
            return {'success': False, 'error': 'Supplier or product not found'}
        
        # Create agent log
        agent_log = AgentLog(
            timestamp=datetime.utcnow(),
            action="Quality Issue Reported",
            product_id=product_id,
            quantity=affected_quantity,
            confidence=0.90,
            human_review=True,
            details=f"Quality issue reported for {product.name}: {issue_type} - {description}"
        )
        
        self.db.add(agent_log)
        self.db.commit()
        
        message = f"""
Subject: 🔴 QUALITY ISSUE REPORT - {product.name}

Dear {supplier['name']},

We have identified a quality issue with the following product:

📦 PRODUCT DETAILS:
- Product: {product.name}
- Product ID: {product.product_id}
- Issue Type: {issue_type}
- Affected Quantity: {affected_quantity} units

🔍 ISSUE DESCRIPTION:
{description}

📅 REPORT DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Please investigate this issue and provide:
1. Root cause analysis
2. Corrective action plan
3. Timeline for resolution
4. Replacement/refund options

We look forward to your prompt response.

Best regards,
Quality Control Team
        """
        
        return {
            'success': True,
            'supplier': supplier,
            'product': product,
            'issue_type': issue_type,
            'message': message.strip()
        }
    
    def send_delivery_inquiry(self, supplier_id, po_number):
        """Send delivery status inquiry"""
        supplier = self.get_supplier_by_id(supplier_id)
        
        # Get PO details
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
        
        if not supplier or not po:
            return {'success': False, 'error': 'Supplier or PO not found'}
        
        product = get_user_product_by_id(po.product_id)
        
        message = f"""
Subject: Delivery Status Inquiry - PO {po_number}

Dear {supplier['name']},

We would like to inquire about the delivery status of the following order:

📋 ORDER DETAILS:
- PO Number: {po_number}
- Product: {product.name if product else po.product_id}
- Quantity: {po.quantity} units
- Order Date: {po.created_at.strftime('%Y-%m-%d')}
- Expected Delivery: {(po.created_at + timedelta(days=supplier['lead_time_days'])).strftime('%Y-%m-%d')}

Could you please provide:
1. Current status of the order
2. Expected shipping date
3. Tracking information (if available)
4. Any potential delays

Thank you for your assistance.

Best regards,
Procurement Team
        """
        
        return {
            'success': True,
            'supplier': supplier,
            'po_number': po_number,
            'message': message.strip()
        }
    
    def get_purchase_orders_by_supplier(self, supplier_id, status=None):
        """Get purchase orders for a specific supplier"""
        query = self.db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == supplier_id)
        
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        pos = query.order_by(PurchaseOrder.created_at.desc()).all()
        
        result = []
        for po in pos:
            product = get_user_product_by_id(po.product_id)
            result.append({
                'po_number': po.po_number,
                'product_id': po.product_id,
                'product_name': product.name if product else 'Unknown',
                'quantity': po.quantity,
                'unit_cost': po.unit_cost,
                'total_cost': po.total_cost,
                'status': po.status,
                'created_at': po.created_at,
                'expected_delivery': po.expected_delivery,
                'notes': po.notes
            })
        
        return result
    
    def update_po_status(self, po_number, new_status, notes=""):
        """Update purchase order status"""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
        
        if not po:
            return {'success': False, 'error': 'Purchase order not found'}
        
        old_status = po.status
        po.status = new_status
        
        if new_status == 'confirmed':
            po.confirmed_at = datetime.utcnow()
        elif new_status == 'delivered':
            po.delivered_at = datetime.utcnow()
        
        if notes:
            po.notes = f"{po.notes}\n{datetime.now().strftime('%Y-%m-%d')}: {notes}" if po.notes else notes
        
        # Create agent log
        agent_log = AgentLog(
            timestamp=datetime.utcnow(),
            action="PO Status Updated",
            product_id=po.product_id,
            quantity=po.quantity,
            confidence=0.95,
            human_review=False,
            details=f"PO {po_number} status changed from {old_status} to {new_status}"
        )
        
        self.db.add(agent_log)
        self.db.commit()
        
        return {
            'success': True,
            'po_number': po_number,
            'old_status': old_status,
            'new_status': new_status,
            'notes': notes
        }
    
    def get_supplier_performance_report(self, supplier_id, days=30):
        """Generate supplier performance report"""
        supplier = self.get_supplier_by_id(supplier_id)
        if not supplier:
            return {'success': False, 'error': 'Supplier not found'}
        
        # Get POs from last N days
        since_date = datetime.utcnow() - timedelta(days=days)
        pos = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.created_at >= since_date
        ).all()
        
        total_orders = len(pos)
        total_value = sum(po.total_cost for po in pos)
        delivered_orders = len([po for po in pos if po.status == 'delivered'])
        pending_orders = len([po for po in pos if po.status in ['pending', 'sent', 'confirmed']])
        
        # Calculate average delivery time for delivered orders
        delivered_pos = [po for po in pos if po.status == 'delivered' and po.delivered_at]
        avg_delivery_days = 0
        if delivered_pos:
            delivery_times = [(po.delivered_at - po.created_at).days for po in delivered_pos]
            avg_delivery_days = sum(delivery_times) / len(delivery_times)
        
        return {
            'success': True,
            'supplier': supplier,
            'period_days': days,
            'total_orders': total_orders,
            'total_value': total_value,
            'delivered_orders': delivered_orders,
            'pending_orders': pending_orders,
            'delivery_rate': (delivered_orders / total_orders * 100) if total_orders > 0 else 0,
            'avg_delivery_days': round(avg_delivery_days, 1),
            'performance_score': min(100, (delivered_orders / max(1, total_orders)) * 100 + (100 - min(100, avg_delivery_days * 5)))
        }

def demo_supplier_communication():
    """Demo of supplier communication system"""
    print("📞 Supplier Communication System Demo")
    print("=" * 50)
    
    with SupplierCommunicationSystem() as scs:
        # Get all suppliers
        suppliers = scs.get_all_suppliers()
        print(f"\n📋 Available Suppliers: {len(suppliers)}")
        for supplier in suppliers:
            print(f"  - {supplier['supplier_id']}: {supplier['name']}")
        
        # Send a reorder request
        print("\n📦 Sending Reorder Request...")
        result = scs.send_reorder_request(
            supplier_id="SUPPLIER_001",
            product_id="USR001",
            quantity=25,
            urgency="normal",
            notes="Regular restock order"
        )
        
        if result['success']:
            print(f"✅ PO Created: {result['po_number']}")
            print(f"📧 Message Preview:")
            print(result['message'][:200] + "...")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Get supplier performance
        print("\n📊 Supplier Performance Report...")
        perf = scs.get_supplier_performance_report("SUPPLIER_001", days=30)
        if perf['success']:
            print(f"  - Total Orders: {perf['total_orders']}")
            print(f"  - Delivery Rate: {perf['delivery_rate']:.1f}%")
            print(f"  - Avg Delivery: {perf['avg_delivery_days']} days")
            print(f"  - Performance Score: {perf['performance_score']:.1f}/100")

if __name__ == "__main__":
    demo_supplier_communication()