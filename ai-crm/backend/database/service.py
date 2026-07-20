#!/usr/bin/env python3
"""
Database service layer for AI Agent
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import (
    SessionLocal, Order, Return, RestockRequest,
    AgentLog, HumanReview, Inventory, PurchaseOrder, Supplier,
    Shipment, Courier, DeliveryEvent
)

class DatabaseService:
    """Database service for AI Agent operations"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    # === Order Operations ===
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Get all orders"""
        orders = self.db.query(Order).order_by(desc(Order.order_date)).limit(limit).all()
        return [
            {
                'OrderID': order.order_id,
                'Status': order.status,
                'CustomerID': order.customer_id,
                'ProductID': order.product_id,
                'Quantity': order.quantity,
                'OrderDate': order.order_date.isoformat() if order.order_date else None
            }
            for order in orders
        ]
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Get order by ID"""
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            return {
                'OrderID': order.order_id,
                'Status': order.status,
                'CustomerID': order.customer_id,
                'ProductID': order.product_id,
                'Quantity': order.quantity,
                'OrderDate': order.order_date.isoformat() if order.order_date else None
            }
        return None
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    # === Return Operations ===
    
    def get_returns(self, processed: Optional[bool] = None) -> List[Dict]:
        """Get returns, optionally filtered by processed status"""
        query = self.db.query(Return)
        if processed is not None:
            query = query.filter(Return.processed == processed)
        
        returns = query.order_by(desc(Return.return_date)).all()
        return [
            {
                'ProductID': ret.product_id,
                'ReturnQuantity': ret.return_quantity,
                'Reason': ret.reason,
                'ReturnDate': ret.return_date.isoformat() if ret.return_date else None,
                'Processed': ret.processed
            }
            for ret in returns
        ]
    
    def add_return(self, product_id: str, quantity: int, reason: str = None) -> bool:
        """Add a new return"""
        try:
            new_return = Return(
                product_id=product_id,
                return_quantity=quantity,
                reason=reason
            )
            self.db.add(new_return)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error adding return: {e}")
            return False
    
    def mark_returns_processed(self, product_id: str) -> int:
        """Mark returns as processed for a product"""
        count = self.db.query(Return).filter(
            Return.product_id == product_id,
            Return.processed == False
        ).update({'processed': True})
        self.db.commit()
        return count
    
    # === Restock Operations ===
    
    def get_restock_requests(self, status: str = None) -> List[Dict]:
        """Get restock requests"""
        query = self.db.query(RestockRequest)
        if status:
            query = query.filter(RestockRequest.status == status)
        
        requests = query.order_by(desc(RestockRequest.created_at)).all()
        return [
            {
                'ProductID': req.product_id,
                'RestockQuantity': req.restock_quantity,
                'Status': req.status,
                'ConfidenceScore': req.confidence_score,
                'CreatedAt': req.created_at.isoformat() if req.created_at else None
            }
            for req in requests
        ]
    
    def create_restock_request(self, product_id: str, quantity: int, confidence: float) -> bool:
        """Create a new restock request"""
        try:
            request = RestockRequest(
                product_id=product_id,
                restock_quantity=quantity,
                confidence_score=confidence
            )
            self.db.add(request)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error creating restock request: {e}")
            return False
    
    def approve_restock_request(self, product_id: str) -> bool:
        """Approve pending restock request"""
        request = self.db.query(RestockRequest).filter(
            RestockRequest.product_id == product_id,
            RestockRequest.status == 'pending'
        ).first()
        
        if request:
            request.status = 'approved'
            request.approved_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    # === Inventory Operations ===
    
    def get_inventory(self) -> List[Dict]:
        """Get all inventory items"""
        items = self.db.query(Inventory).all()
        return [
            {
                'ProductID': item.product_id,
                'CurrentStock': item.current_stock,
                'ReservedStock': item.reserved_stock,
                'AvailableStock': item.available_stock,
                'ReorderPoint': item.reorder_point,
                'MaxStock': item.max_stock,
                'LastUpdated': item.last_updated.isoformat() if item.last_updated else None
            }
            for item in items
        ]
    
    def update_inventory(self, product_id: str, quantity_change: int) -> bool:
        """Update inventory quantity"""
        item = self.db.query(Inventory).filter(Inventory.product_id == product_id).first()
        if item:
            item.current_stock += quantity_change
            item.last_updated = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def get_low_stock_items(self) -> List[Dict]:
        """Get items below reorder point"""
        items = self.db.query(Inventory).filter(
            Inventory.current_stock <= Inventory.reorder_point
        ).all()
        
        return [
            {
                'ProductID': item.product_id,
                'CurrentStock': item.current_stock,
                'ReorderPoint': item.reorder_point,
                'SuggestedOrder': item.max_stock - item.current_stock
            }
            for item in items
        ]
    
    # === Logging Operations ===
    
    def log_agent_action(self, action: str, product_id: str = None, 
                        quantity: int = None, confidence: float = None,
                        human_review: bool = False, details: str = None) -> bool:
        """Log agent action"""
        try:
            log_entry = AgentLog(
                action=action,
                product_id=product_id,
                quantity=quantity,
                confidence=confidence,
                human_review=human_review,
                details=details
            )
            self.db.add(log_entry)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error logging action: {e}")
            return False
    
    def get_agent_logs(self, limit: int = 100) -> List[Dict]:
        """Get agent logs"""
        logs = self.db.query(AgentLog).order_by(desc(AgentLog.timestamp)).limit(limit).all()
        return [
            {
                'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                'action': log.action,
                'ProductID': log.product_id,
                'quantity': log.quantity,
                'confidence': log.confidence,
                'human_review': log.human_review,
                'details': log.details
            }
            for log in logs
        ]
    
    # === Human Review Operations ===
    
    def submit_for_review(self, review_id: str, action_type: str, 
                         data: Dict, decision_description: str, confidence: float) -> bool:
        """Submit item for human review"""
        try:
            review = HumanReview(
                review_id=review_id,
                action_type=action_type,
                data=json.dumps(data),
                decision_description=decision_description,
                confidence=confidence
            )
            self.db.add(review)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error submitting for review: {e}")
            return False
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get pending reviews"""
        reviews = self.db.query(HumanReview).filter(
            HumanReview.status == 'pending'
        ).order_by(HumanReview.submitted_at).all()
        
        return [
            {
                'review_id': review.review_id,
                'action_type': review.action_type,
                'data': json.loads(review.data) if review.data else {},
                'decision_description': review.decision_description,
                'confidence': review.confidence,
                'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None
            }
            for review in reviews
        ]
    
    def approve_review(self, review_id: str, notes: str = None) -> bool:
        """Approve a review"""
        review = self.db.query(HumanReview).filter(
            HumanReview.review_id == review_id
        ).first()
        
        if review:
            review.status = 'approved'
            review.reviewed_at = datetime.utcnow()
            review.reviewer_notes = notes
            self.db.commit()
            return True
        return False
    
    def reject_review(self, review_id: str, notes: str = None) -> bool:
        """Reject a review"""
        review = self.db.query(HumanReview).filter(
            HumanReview.review_id == review_id
        ).first()
        
        if review:
            review.status = 'rejected'
            review.reviewed_at = datetime.utcnow()
            review.reviewer_notes = notes
            self.db.commit()
            return True
        return False
    
    # === Purchase Order Operations ===

    def create_purchase_order(self, po_number: str, supplier_id: str, product_id: str,
                            quantity: int, unit_cost: float, total_cost: float) -> bool:
        """Create a new purchase order"""
        try:
            po = PurchaseOrder(
                po_number=po_number,
                supplier_id=supplier_id,
                product_id=product_id,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=total_cost,
                status='pending'
            )
            self.db.add(po)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error creating purchase order: {e}")
            return False

    def get_purchase_orders(self, status: str = None) -> List[Dict]:
        """Get purchase orders"""
        query = self.db.query(PurchaseOrder)
        if status:
            query = query.filter(PurchaseOrder.status == status)

        orders = query.order_by(desc(PurchaseOrder.created_at)).all()
        return [
            {
                'po_number': po.po_number,
                'supplier_id': po.supplier_id,
                'product_id': po.product_id,
                'quantity': po.quantity,
                'unit_cost': po.unit_cost,
                'total_cost': po.total_cost,
                'status': po.status,
                'created_at': po.created_at.isoformat() if po.created_at else None,
                'expected_delivery': po.expected_delivery.isoformat() if po.expected_delivery else None
            }
            for po in orders
        ]

    def update_purchase_order_status(self, po_number: str, status: str, notes: str = None) -> bool:
        """Update purchase order status"""
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
        if po:
            po.status = status
            if notes:
                po.notes = notes
            if status == 'confirmed':
                po.confirmed_at = datetime.utcnow()
            elif status == 'delivered':
                po.delivered_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    # === Supplier Operations ===

    def get_suppliers(self, active_only: bool = True) -> List[Dict]:
        """Get suppliers"""
        query = self.db.query(Supplier)
        if active_only:
            query = query.filter(Supplier.is_active == True)

        suppliers = query.all()
        return [
            {
                'supplier_id': supplier.supplier_id,
                'name': supplier.name,
                'contact_email': supplier.contact_email,
                'contact_phone': supplier.contact_phone,
                'lead_time_days': supplier.lead_time_days,
                'minimum_order': supplier.minimum_order,
                'is_active': supplier.is_active
            }
            for supplier in suppliers
        ]

    def get_supplier_by_id(self, supplier_id: str) -> Optional[Dict]:
        """Get supplier by ID"""
        supplier = self.db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        if supplier:
            return {
                'supplier_id': supplier.supplier_id,
                'name': supplier.name,
                'contact_email': supplier.contact_email,
                'contact_phone': supplier.contact_phone,
                'api_endpoint': supplier.api_endpoint,
                'lead_time_days': supplier.lead_time_days,
                'minimum_order': supplier.minimum_order,
                'is_active': supplier.is_active
            }
        return None

    # === Shipment Operations ===

    def create_shipment(self, shipment_id: str, order_id: int, courier_id: str,
                       tracking_number: str, origin_address: str, destination_address: str) -> bool:
        """Create a new shipment"""
        try:
            shipment = Shipment(
                shipment_id=shipment_id,
                order_id=order_id,
                courier_id=courier_id,
                tracking_number=tracking_number,
                origin_address=origin_address,
                destination_address=destination_address,
                status='created'
            )
            self.db.add(shipment)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error creating shipment: {e}")
            return False

    def get_shipments(self, status: str = None) -> List[Dict]:
        """Get shipments"""
        query = self.db.query(Shipment)
        if status:
            query = query.filter(Shipment.status == status)

        shipments = query.order_by(desc(Shipment.created_at)).all()
        return [
            {
                'shipment_id': shipment.shipment_id,
                'order_id': shipment.order_id,
                'courier_id': shipment.courier_id,
                'tracking_number': shipment.tracking_number,
                'status': shipment.status,
                'origin_address': shipment.origin_address,
                'destination_address': shipment.destination_address,
                'estimated_delivery': shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
                'actual_delivery': shipment.actual_delivery.isoformat() if shipment.actual_delivery else None,
                'created_at': shipment.created_at.isoformat() if shipment.created_at else None
            }
            for shipment in shipments
        ]

    def get_shipment_by_order(self, order_id: int) -> Optional[Dict]:
        """Get shipment by order ID"""
        shipment = self.db.query(Shipment).filter(Shipment.order_id == order_id).first()
        if shipment:
            return {
                'shipment_id': shipment.shipment_id,
                'order_id': shipment.order_id,
                'courier_id': shipment.courier_id,
                'tracking_number': shipment.tracking_number,
                'status': shipment.status,
                'estimated_delivery': shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
                'actual_delivery': shipment.actual_delivery.isoformat() if shipment.actual_delivery else None
            }
        return None

    def get_shipment_by_tracking(self, tracking_number: str) -> Optional[Dict]:
        """Get shipment by tracking number"""
        shipment = self.db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
        if shipment:
            return {
                'shipment_id': shipment.shipment_id,
                'order_id': shipment.order_id,
                'courier_id': shipment.courier_id,
                'tracking_number': shipment.tracking_number,
                'status': shipment.status,
                'origin_address': shipment.origin_address,
                'destination_address': shipment.destination_address,
                'estimated_delivery': shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
                'actual_delivery': shipment.actual_delivery.isoformat() if shipment.actual_delivery else None
            }
        return None

    def update_shipment_status(self, tracking_number: str, status: str, notes: str = None) -> bool:
        """Update shipment status"""
        shipment = self.db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
        if shipment:
            shipment.status = status
            if notes:
                shipment.notes = notes
            if status == 'delivered':
                shipment.delivered_at = datetime.utcnow()
                shipment.actual_delivery = datetime.utcnow()
            self.db.commit()
            return True
        return False

    # === Courier Operations ===

    def get_couriers(self, active_only: bool = True) -> List[Dict]:
        """Get couriers"""
        query = self.db.query(Courier)
        if active_only:
            query = query.filter(Courier.is_active == True)

        couriers = query.all()
        return [
            {
                'courier_id': courier.courier_id,
                'name': courier.name,
                'service_type': courier.service_type,
                'avg_delivery_days': courier.avg_delivery_days,
                'coverage_area': courier.coverage_area,
                'cost_per_kg': courier.cost_per_kg,
                'is_active': courier.is_active
            }
            for courier in couriers
        ]

    # === Analytics ===

    def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get performance metrics for the last N days"""
        since_date = datetime.utcnow() - timedelta(days=days)

        # Agent actions
        total_actions = self.db.query(AgentLog).filter(
            AgentLog.timestamp >= since_date
        ).count()

        # Human reviews
        total_reviews = self.db.query(HumanReview).filter(
            HumanReview.submitted_at >= since_date
        ).count()

        # Approved reviews
        approved_reviews = self.db.query(HumanReview).filter(
            HumanReview.submitted_at >= since_date,
            HumanReview.status == 'approved'
        ).count()

        # Restock requests
        restock_requests = self.db.query(RestockRequest).filter(
            RestockRequest.created_at >= since_date
        ).count()

        # Purchase orders
        purchase_orders = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.created_at >= since_date
        ).count()

        return {
            'period_days': days,
            'total_actions': total_actions,
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'approval_rate': (approved_reviews / total_reviews * 100) if total_reviews > 0 else 0,
            'restock_requests': restock_requests,
            'purchase_orders': purchase_orders,
            'automation_rate': ((total_actions - total_reviews) / total_actions * 100) if total_actions > 0 else 0
        }
