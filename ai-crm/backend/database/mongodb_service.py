#!/usr/bin/env python3
"""
MongoDB Service layer for AI Agent Logistics System
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import json

from .mongodb_connection import get_db, COLLECTIONS
from .mongodb_models import *


class MongoDBService:
    """MongoDB service for AI Agent logistics operations"""
    
    def __init__(self):
        self.db = get_db()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # MongoDB doesn't need explicit session cleanup for basic operations
        return False
    
    # === Order Operations ===
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Get all orders"""
        orders = list(self.db[COLLECTIONS['orders']].find().sort("order_date", -1).limit(limit))
        return [self._serialize_doc(order) for order in orders]
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Get order by ID"""
        order = self.db[COLLECTIONS['orders']].find_one({"order_id": order_id})
        return self._serialize_doc(order) if order else None
    
    def create_order(self, order_data: Dict) -> Dict:
        """Create a new order"""
        order = OrderModel(**order_data)
        result = self.db[COLLECTIONS['orders']].insert_one(order.dict(by_alias=True, exclude={"id"}))
        order.id = result.inserted_id
        return self._serialize_doc(order.dict(by_alias=True))
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        result = self.db[COLLECTIONS['orders']].update_one(
            {"order_id": order_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    # === Return Operations ===
    
    def get_returns(self, processed: Optional[bool] = None) -> List[Dict]:
        """Get returns, optionally filtered by processed status"""
        query = {}
        if processed is not None:
            query["processed"] = processed
        
        returns = list(self.db[COLLECTIONS['returns']].find(query).sort("return_date", -1))
        return [self._serialize_doc(ret) for ret in returns]
    
    def add_return(self, product_id: str, quantity: int, reason: str = None) -> bool:
        """Add a new return"""
        try:
            return_data = ReturnModel(
                product_id=product_id,
                return_quantity=quantity,
                reason=reason
            )
            self.db[COLLECTIONS['returns']].insert_one(return_data.dict(by_alias=True, exclude={"id"}))
            return True
        except Exception as e:
            print(f"Error adding return: {e}")
            return False
    
    def mark_return_processed(self, product_id: str) -> bool:
        """Mark a return as processed"""
        result = self.db[COLLECTIONS['returns']].update_many(
            {"product_id": product_id, "processed": False},
            {"$set": {"processed": True}}
        )
        return result.modified_count > 0
    
    # === Restock Request Operations ===
    
    def get_restock_requests(self, status: Optional[str] = None) -> List[Dict]:
        """Get restock requests"""
        query = {}
        if status:
            query["status"] = status
        
        requests = list(self.db[COLLECTIONS['restock_requests']].find(query).sort("created_at", -1))
        return [self._serialize_doc(req) for req in requests]
    
    def create_restock_request(self, product_id: str, quantity: int, confidence: float = None) -> Dict:
        """Create a restock request"""
        request = RestockRequestModel(
            product_id=product_id,
            restock_quantity=quantity,
            confidence_score=confidence
        )
        result = self.db[COLLECTIONS['restock_requests']].insert_one(request.dict(by_alias=True, exclude={"id"}))
        request.id = result.inserted_id
        return self._serialize_doc(request.dict(by_alias=True))
    
    def update_restock_status(self, product_id: str, status: str) -> bool:
        """Update restock request status"""
        update_data = {"status": status}
        if status == "approved":
            update_data["approved_at"] = datetime.utcnow()
        elif status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        result = self.db[COLLECTIONS['restock_requests']].update_many(
            {"product_id": product_id, "status": {"$ne": "completed"}},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Agent Log Operations ===
    
    def add_agent_log(self, action: str, product_id: str = None, quantity: int = None,
                     confidence: float = None, human_review: bool = False, details: str = None) -> bool:
        """Add an agent log entry"""
        try:
            log = AgentLogModel(
                action=action,
                product_id=product_id,
                quantity=quantity,
                confidence=confidence,
                human_review=human_review,
                details=details
            )
            self.db[COLLECTIONS['agent_logs']].insert_one(log.dict(by_alias=True, exclude={"id"}))
            return True
        except Exception as e:
            print(f"Error adding agent log: {e}")
            return False
    
    def get_agent_logs(self, limit: int = 100) -> List[Dict]:
        """Get agent logs"""
        logs = list(self.db[COLLECTIONS['agent_logs']].find().sort("timestamp", -1).limit(limit))
        return [self._serialize_doc(log) for log in logs]
    
    # === Human Review Operations ===
    
    def create_human_review(self, review_data: Dict) -> Dict:
        """Create a human review request"""
        review = HumanReviewModel(**review_data)
        result = self.db[COLLECTIONS['human_reviews']].insert_one(review.dict(by_alias=True, exclude={"id"}))
        review.id = result.inserted_id
        return self._serialize_doc(review.dict(by_alias=True))
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get pending human reviews"""
        reviews = list(self.db[COLLECTIONS['human_reviews']].find({"status": "pending"}).sort("submitted_at", 1))
        return [self._serialize_doc(review) for review in reviews]
    
    def update_review_status(self, review_id: str, status: str, notes: str = None) -> bool:
        """Update review status"""
        update_data = {
            "status": status,
            "reviewed_at": datetime.utcnow()
        }
        if notes:
            update_data["reviewer_notes"] = notes
        
        result = self.db[COLLECTIONS['human_reviews']].update_one(
            {"review_id": review_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Inventory Operations ===
    
    def get_inventory(self) -> List[Dict]:
        """Get all inventory items"""
        items = list(self.db[COLLECTIONS['inventory']].find())
        return [self._serialize_doc(item) for item in items]
    
    def get_inventory_by_product(self, product_id: str) -> Optional[Dict]:
        """Get inventory for a specific product"""
        item = self.db[COLLECTIONS['inventory']].find_one({"product_id": product_id})
        return self._serialize_doc(item) if item else None
    
    def update_inventory(self, product_id: str, current_stock: int = None, 
                        reserved_stock: int = None) -> bool:
        """Update inventory levels"""
        update_data = {"last_updated": datetime.utcnow()}
        if current_stock is not None:
            update_data["current_stock"] = current_stock
        if reserved_stock is not None:
            update_data["reserved_stock"] = reserved_stock
        
        result = self.db[COLLECTIONS['inventory']].update_one(
            {"product_id": product_id},
            {"$set": update_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    def create_inventory_item(self, inventory_data: Dict) -> Dict:
        """Create a new inventory item"""
        inventory = InventoryModel(**inventory_data)
        result = self.db[COLLECTIONS['inventory']].insert_one(inventory.dict(by_alias=True, exclude={"id"}))
        inventory.id = result.inserted_id
        return self._serialize_doc(inventory.dict(by_alias=True))
    
    # === Purchase Order Operations ===
    
    def create_purchase_order(self, po_data: Dict) -> Dict:
        """Create a purchase order"""
        po = PurchaseOrderModel(**po_data)
        result = self.db[COLLECTIONS['purchase_orders']].insert_one(po.dict(by_alias=True, exclude={"id"}))
        po.id = result.inserted_id
        return self._serialize_doc(po.dict(by_alias=True))
    
    def get_purchase_orders(self, status: Optional[str] = None) -> List[Dict]:
        """Get purchase orders"""
        query = {}
        if status:
            query["status"] = status
        
        orders = list(self.db[COLLECTIONS['purchase_orders']].find(query).sort("created_at", -1))
        return [self._serialize_doc(order) for order in orders]
    
    def update_po_status(self, po_number: str, status: str) -> bool:
        """Update purchase order status"""
        update_data = {"status": status}
        if status == "sent":
            update_data["sent_at"] = datetime.utcnow()
        elif status == "confirmed":
            update_data["confirmed_at"] = datetime.utcnow()
        elif status == "delivered":
            update_data["delivered_at"] = datetime.utcnow()
        
        result = self.db[COLLECTIONS['purchase_orders']].update_one(
            {"po_number": po_number},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Supplier Operations ===
    
    def get_suppliers(self, active_only: bool = True) -> List[Dict]:
        """Get suppliers"""
        query = {"is_active": True} if active_only else {}
        suppliers = list(self.db[COLLECTIONS['suppliers']].find(query))
        return [self._serialize_doc(supplier) for supplier in suppliers]
    
    def get_supplier_by_id(self, supplier_id: str) -> Optional[Dict]:
        """Get supplier by ID"""
        supplier = self.db[COLLECTIONS['suppliers']].find_one({"supplier_id": supplier_id})
        return self._serialize_doc(supplier) if supplier else None
    
    def create_supplier(self, supplier_data: Dict) -> Dict:
        """Create a supplier"""
        supplier = SupplierModel(**supplier_data)
        result = self.db[COLLECTIONS['suppliers']].insert_one(supplier.dict(by_alias=True, exclude={"id"}))
        supplier.id = result.inserted_id
        return self._serialize_doc(supplier.dict(by_alias=True))
    
    # === Product Operations ===
    
    def get_products(self, category: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """Get products"""
        query = {}
        if category:
            query["category"] = category
        if active_only:
            query["is_active"] = True
        
        products = list(self.db[COLLECTIONS['products']].find(query))
        return [self._serialize_doc(product) for product in products]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product by ID"""
        product = self.db[COLLECTIONS['products']].find_one({"product_id": product_id})
        return self._serialize_doc(product) if product else None
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a product"""
        product = ProductModel(**product_data)
        result = self.db[COLLECTIONS['products']].insert_one(product.dict(by_alias=True, exclude={"id"}))
        product.id = result.inserted_id
        return self._serialize_doc(product.dict(by_alias=True))
    
    # === Shipment Operations ===
    
    def create_shipment(self, shipment_data: Dict) -> Dict:
        """Create a shipment"""
        shipment = ShipmentModel(**shipment_data)
        result = self.db[COLLECTIONS['shipments']].insert_one(shipment.dict(by_alias=True, exclude={"id"}))
        shipment.id = result.inserted_id
        return self._serialize_doc(shipment.dict(by_alias=True))
    
    def get_shipments(self, status: Optional[str] = None) -> List[Dict]:
        """Get shipments"""
        query = {}
        if status:
            query["status"] = status
        
        shipments = list(self.db[COLLECTIONS['shipments']].find(query).sort("created_at", -1))
        return [self._serialize_doc(shipment) for shipment in shipments]
    
    def update_shipment_status(self, shipment_id: str, status: str) -> bool:
        """Update shipment status"""
        update_data = {"status": status}
        if status == "picked_up":
            update_data["picked_up_at"] = datetime.utcnow()
        elif status == "delivered":
            update_data["delivered_at"] = datetime.utcnow()
            update_data["actual_delivery"] = datetime.utcnow()
        
        result = self.db[COLLECTIONS['shipments']].update_one(
            {"shipment_id": shipment_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Helper Methods ===
    
    def _serialize_doc(self, doc: Dict) -> Dict:
        """Convert MongoDB document to JSON-serializable dict"""
        if doc is None:
            return None
        
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        
        # Convert any other ObjectId fields
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, datetime):
                doc[key] = value.isoformat()
        
        return doc
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        return {
            "total_orders": self.db[COLLECTIONS['orders']].count_documents({}),
            "pending_restock_requests": self.db[COLLECTIONS['restock_requests']].count_documents({"status": "pending"}),
            "pending_human_reviews": self.db[COLLECTIONS['human_reviews']].count_documents({"status": "pending"}),
            "total_products": self.db[COLLECTIONS['products']].count_documents({"is_active": True}),
            "total_suppliers": self.db[COLLECTIONS['suppliers']].count_documents({"is_active": True}),
            "active_shipments": self.db[COLLECTIONS['shipments']].count_documents({"status": {"$in": ["created", "picked_up", "in_transit", "out_for_delivery"]}}),
        }
    
    def get_low_stock_items(self, threshold: int = 10) -> List[Dict]:
        """Get inventory items with low stock"""
        try:
            items = list(self.db[COLLECTIONS['inventory']].find({
                "quantity": {"$lte": threshold},
                "is_active": True
            }).limit(100))
            return [self._serialize_mongo_doc(item) for item in items]
        except Exception as e:
            print(f"Error getting low stock items: {e}")
            return []
    
    def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get performance metrics for the last N days"""
        try:
            from datetime import datetime, timedelta
            start_date = datetime.now() - timedelta(days=days)
            
            total_orders = self.db[COLLECTIONS['orders']].count_documents({
                "created_at": {"$gte": start_date}
            })
            
            completed_orders = self.db[COLLECTIONS['orders']].count_documents({
                "created_at": {"$gte": start_date},
                "status": "completed"
            })
            
            automation_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            return {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "automation_rate": round(automation_rate, 2),
                "period_days": days
            }
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return {
                "total_orders": 0,
                "completed_orders": 0,
                "automation_rate": 0,
                "period_days": days
            }
