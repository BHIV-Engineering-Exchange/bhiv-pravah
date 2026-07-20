"""
Database Extensions for Customer Portal and Procurement
Add methods to existing DatabaseService for customer orders and procurement
"""

def extend_database_service():
    """Add customer portal and procurement methods to DatabaseService"""
    from database.service import DatabaseService
    
    # Add methods to DatabaseService class
    def get_all_products(self):
        """Get all products"""
        try:
            if hasattr(self.db, 'products'):
                # MongoDB
                products = list(self.db.products.find({}))
                for p in products:
                    p['id'] = str(p.get('_id', ''))
                return products
            else:
                # SQLite
                from database.models import Product
                from sqlalchemy.orm import Session
                with Session(self.engine) as session:
                    products = session.query(Product).all()
                    return [p.__dict__ for p in products]
        except:
            return []
    
    def get_product(self, product_id: str):
        """Get single product"""
        try:
            if hasattr(self.db, 'products'):
                # MongoDB
                from bson import ObjectId
                product = self.db.products.find_one({"_id": ObjectId(product_id)})
                if product:
                    product['id'] = str(product['_id'])
                return product
            else:
                # SQLite
                from database.models import Product
                from sqlalchemy.orm import Session
                with Session(self.engine) as session:
                    product = session.query(Product).filter(Product.id == product_id).first()
                    return product.__dict__ if product else None
        except:
            return None
    
    def update_product_stock(self, product_id: str, new_stock: int):
        """Update product stock quantity"""
        try:
            if hasattr(self.db, 'products'):
                # MongoDB
                from bson import ObjectId
                self.db.products.update_one(
                    {"_id": ObjectId(product_id)},
                    {"$set": {"stock_quantity": new_stock}}
                )
            else:
                # SQLite
                from database.models import Product
                from sqlalchemy.orm import Session
                with Session(self.engine) as session:
                    product = session.query(Product).filter(Product.id == product_id).first()
                    if product:
                        product.stock_quantity = new_stock
                        session.commit()
            return True
        except:
            return False
    
    def create_order(self, order_data: dict):
        """Create customer order"""
        try:
            if hasattr(self.db, 'customer_orders'):
                # MongoDB
                result = self.db.customer_orders.insert_one(order_data)
                return str(result.inserted_id)
            else:
                # SQLite - store in JSON or create table
                import json
                order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                order_data['id'] = order_id
                # Store in file or create table as needed
                return order_id
        except:
            return None
    
    def get_customer_orders(self, customer_id: str):
        """Get orders for a customer"""
        try:
            if hasattr(self.db, 'customer_orders'):
                # MongoDB
                orders = list(self.db.customer_orders.find({"customer_id": customer_id}).sort("created_at", -1))
                for o in orders:
                    o['id'] = str(o['_id'])
                return orders
            else:
                return []
        except:
            return []
    
    def get_order(self, order_id: str):
        """Get single order"""
        try:
            if hasattr(self.db, 'customer_orders'):
                # MongoDB
                from bson import ObjectId
                order = self.db.customer_orders.find_one({"_id": ObjectId(order_id)})
                if order:
                    order['id'] = str(order['_id'])
                return order
            else:
                return None
        except:
            return None
    
    def create_procurement_request(self, procurement_data: dict):
        """Create procurement request"""
        try:
            if hasattr(self.db, 'procurement_requests'):
                # MongoDB
                result = self.db.procurement_requests.insert_one(procurement_data)
                return str(result.inserted_id)
            else:
                # SQLite
                procurement_id = f"PROC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                return procurement_id
        except:
            return None
    
    def get_procurement_request(self, procurement_id: str):
        """Get procurement request"""
        try:
            if hasattr(self.db, 'procurement_requests'):
                # MongoDB
                from bson import ObjectId
                request = self.db.procurement_requests.find_one({"_id": ObjectId(procurement_id)})
                if request:
                    request['id'] = str(request['_id'])
                return request
            else:
                return None
        except:
            return None
    
    def get_all_procurement_requests(self):
        """Get all procurement requests"""
        try:
            if hasattr(self.db, 'procurement_requests'):
                # MongoDB
                requests = list(self.db.procurement_requests.find({}).sort("created_at", -1))
                for r in requests:
                    r['id'] = str(r['_id'])
                return requests
            else:
                return []
        except:
            return []
    
    def update_procurement_status(self, procurement_id: str, status: str):
        """Update procurement request status"""
        try:
            if hasattr(self.db, 'procurement_requests'):
                # MongoDB
                from bson import ObjectId
                self.db.procurement_requests.update_one(
                    {"_id": ObjectId(procurement_id)},
                    {"$set": {"status": status}}
                )
            return True
        except:
            return False
    
    def create_purchase_order(self, po_data: dict):
        """Create purchase order"""
        try:
            if hasattr(self.db, 'purchase_orders'):
                # MongoDB
                result = self.db.purchase_orders.insert_one(po_data)
                return str(result.inserted_id)
            else:
                po_id = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                return po_id
        except:
            return None
    
    def get_supplier(self, supplier_id: str):
        """Get supplier details"""
        try:
            if hasattr(self.db, 'suppliers'):
                # MongoDB
                from bson import ObjectId
                supplier = self.db.suppliers.find_one({"_id": ObjectId(supplier_id)})
                if supplier:
                    supplier['id'] = str(supplier['_id'])
                return supplier
            else:
                return None
        except:
            return None
    
    # Add methods to class
    DatabaseService.get_all_products = get_all_products
    DatabaseService.get_product = get_product
    DatabaseService.update_product_stock = update_product_stock
    DatabaseService.create_order = create_order
    DatabaseService.get_customer_orders = get_customer_orders
    DatabaseService.get_order = get_order
    DatabaseService.create_procurement_request = create_procurement_request
    DatabaseService.get_procurement_request = get_procurement_request
    DatabaseService.get_all_procurement_requests = get_all_procurement_requests
    DatabaseService.update_procurement_status = update_procurement_status
    DatabaseService.create_purchase_order = create_purchase_order
    DatabaseService.get_supplier = get_supplier

# Call on import
try:
    extend_database_service()
    print("[OK] Database service extended for customer portal and procurement")
except Exception as e:
    print(f"[WARNING] Could not extend database service: {e}")
