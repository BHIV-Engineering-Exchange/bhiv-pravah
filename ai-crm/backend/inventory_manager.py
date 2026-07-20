#!/usr/bin/env python3
"""
Inventory Management System
Handle inventory increases/decreases and update database
"""

from database.models import SessionLocal, Inventory, AgentLog
from user_product_models import USER_PRODUCT_CATALOG, get_user_product_by_id
from datetime import datetime
import pandas as pd

class InventoryManager:
    """Manage inventory updates and changes"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def get_current_inventory(self, product_id=None):
        """Get current inventory levels"""
        if product_id:
            return self.db.query(Inventory).filter(Inventory.product_id == product_id).first()
        else:
            return self.db.query(Inventory).all()
    
    def update_inventory(self, product_id, quantity_change, reason="Manual Update", create_log=True):
        """
        Update inventory for a specific product
        
        Args:
            product_id (str): Product ID to update
            quantity_change (int): Positive for increase, negative for decrease
            reason (str): Reason for the change
            create_log (bool): Whether to create an agent log entry
        
        Returns:
            dict: Update result with old/new quantities
        """
        try:
            # Get current inventory
            inventory = self.db.query(Inventory).filter(Inventory.product_id == product_id).first()
            
            if not inventory:
                return {
                    'success': False,
                    'error': f'Product {product_id} not found in inventory',
                    'product_id': product_id
                }
            
            # Store old values
            old_stock = inventory.current_stock
            
            # Calculate new stock
            new_stock = old_stock + quantity_change
            
            # Prevent negative stock
            if new_stock < 0:
                return {
                    'success': False,
                    'error': f'Cannot reduce stock below 0. Current: {old_stock}, Requested change: {quantity_change}',
                    'product_id': product_id,
                    'current_stock': old_stock
                }
            
            # Update inventory
            inventory.current_stock = new_stock
            inventory.last_updated = datetime.utcnow()
            
            # Get product name for logging
            product_name = "Unknown Product"
            product = get_user_product_by_id(product_id)
            if product:
                product_name = product.name
            
            # Create agent log if requested
            if create_log:
                action = "Inventory Increased" if quantity_change > 0 else "Inventory Decreased"
                details = f"{reason}: {abs(quantity_change)} units {'added to' if quantity_change > 0 else 'removed from'} {product_name}"
                
                agent_log = AgentLog(
                    timestamp=datetime.utcnow(),
                    action=action,
                    product_id=product_id,
                    quantity=abs(quantity_change),
                    confidence=1.0,
                    human_review=False,
                    details=details
                )
                self.db.add(agent_log)
            
            # Commit changes
            self.db.commit()
            
            return {
                'success': True,
                'product_id': product_id,
                'product_name': product_name,
                'old_stock': old_stock,
                'new_stock': new_stock,
                'quantity_change': quantity_change,
                'reason': reason,
                'needs_reorder': new_stock <= inventory.reorder_point
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'product_id': product_id
            }
    
    def bulk_update_inventory(self, updates):
        """
        Update multiple products at once
        
        Args:
            updates (list): List of dicts with 'product_id', 'quantity_change', 'reason'
        
        Returns:
            dict: Summary of all updates
        """
        results = []
        successful_updates = 0
        failed_updates = 0
        
        for update in updates:
            result = self.update_inventory(
                product_id=update['product_id'],
                quantity_change=update['quantity_change'],
                reason=update.get('reason', 'Bulk Update'),
                create_log=update.get('create_log', True)
            )
            
            results.append(result)
            
            if result['success']:
                successful_updates += 1
            else:
                failed_updates += 1
        
        return {
            'total_updates': len(updates),
            'successful': successful_updates,
            'failed': failed_updates,
            'results': results
        }
    
    def update_from_excel(self, excel_file_path, quantity_column='NEW_QTY'):
        """
        Update inventory from Excel file
        
        Args:
            excel_file_path (str): Path to Excel file
            quantity_column (str): Column name containing new quantities
        
        Returns:
            dict: Update summary
        """
        try:
            # Read Excel file
            df = pd.read_excel(excel_file_path)
            
            if 'MODEL' not in df.columns or quantity_column not in df.columns:
                return {
                    'success': False,
                    'error': f'Excel file must contain MODEL and {quantity_column} columns'
                }
            
            updates = []
            
            # Process each row
            for _, row in df.iterrows():
                model_name = row['MODEL']
                new_qty = row[quantity_column]
                
                if pd.isna(new_qty) or model_name == 'TOTAL':
                    continue
                
                # Find product ID from model name
                product_id = None
                for product in USER_PRODUCT_CATALOG:
                    if product.name == model_name:
                        product_id = product.product_id
                        break
                
                if product_id:
                    # Get current stock
                    current_inventory = self.get_current_inventory(product_id)
                    if current_inventory:
                        current_stock = current_inventory.current_stock
                        quantity_change = int(new_qty) - current_stock
                        
                        if quantity_change != 0:
                            updates.append({
                                'product_id': product_id,
                                'quantity_change': quantity_change,
                                'reason': f'Excel Update: {model_name}',
                                'create_log': True
                            })
            
            # Perform bulk update
            return self.bulk_update_inventory(updates)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading Excel file: {str(e)}'
            }
    
    def set_absolute_quantity(self, product_id, new_quantity, reason="Absolute Update"):
        """
        Set absolute quantity for a product (not relative change)
        
        Args:
            product_id (str): Product ID
            new_quantity (int): New absolute quantity
            reason (str): Reason for change
        
        Returns:
            dict: Update result
        """
        current_inventory = self.get_current_inventory(product_id)
        
        if not current_inventory:
            return {
                'success': False,
                'error': f'Product {product_id} not found',
                'product_id': product_id
            }
        
        current_stock = current_inventory.current_stock
        quantity_change = new_quantity - current_stock
        
        return self.update_inventory(product_id, quantity_change, reason)
    
    def get_inventory_report(self):
        """Generate inventory report"""
        inventory_items = self.get_current_inventory()
        
        report_data = []
        for item in inventory_items:
            product = get_user_product_by_id(item.product_id)
            product_name = product.name if product else "Unknown Product"
            
            report_data.append({
                'Product ID': item.product_id,
                'Product Name': product_name,
                'Current Stock': item.current_stock,
                'Reorder Point': item.reorder_point,
                'Max Stock': item.max_stock,
                'Available Stock': item.available_stock,
                'Needs Reorder': item.needs_reorder,
                'Stock Status': '🔴 Low Stock' if item.needs_reorder else '🟢 Good Stock',
                'Last Updated': item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return pd.DataFrame(report_data)
    
    def simulate_sales(self, num_sales=5):
        """Simulate sales to decrease inventory"""
        import random
        
        # Get products with sufficient stock
        available_products = [inv for inv in self.get_current_inventory() if inv.current_stock > 5]
        
        if not available_products:
            return {'success': False, 'error': 'No products with sufficient stock for sales'}
        
        sales = []
        for _ in range(num_sales):
            product_inv = random.choice(available_products)
            sale_qty = random.randint(1, min(5, product_inv.current_stock))
            
            result = self.update_inventory(
                product_id=product_inv.product_id,
                quantity_change=-sale_qty,
                reason=f"Sale - Order #{random.randint(400, 500)}",
                create_log=True
            )
            
            sales.append(result)
        
        return {
            'success': True,
            'sales_count': num_sales,
            'sales': sales
        }
    
    def simulate_restocking(self, num_restocks=3):
        """Simulate restocking to increase inventory"""
        import random
        
        # Get products that need reordering
        low_stock_products = [inv for inv in self.get_current_inventory() if inv.needs_reorder]
        
        if not low_stock_products:
            # If no low stock, pick random products
            low_stock_products = random.sample(self.get_current_inventory(), min(num_restocks, 10))
        
        restocks = []
        for i in range(min(num_restocks, len(low_stock_products))):
            product_inv = low_stock_products[i]
            restock_qty = random.randint(20, 50)
            
            result = self.update_inventory(
                product_id=product_inv.product_id,
                quantity_change=restock_qty,
                reason=f"Restock - PO-{random.randint(2000, 3000)}",
                create_log=True
            )
            
            restocks.append(result)
        
        return {
            'success': True,
            'restock_count': len(restocks),
            'restocks': restocks
        }

def main():
    """Demo of inventory management functions"""
    print("🏭 Inventory Management System Demo")
    print("=" * 50)
    
    with InventoryManager() as inv_mgr:
        # Show current inventory status
        print("\n📊 Current Inventory Report:")
        report = inv_mgr.get_inventory_report()
        print(report[['Product ID', 'Product Name', 'Current Stock', 'Stock Status']].head(10))
        
        # Example 1: Single product update
        print("\n🔄 Example 1: Single Product Update")
        result = inv_mgr.update_inventory('USR001', 10, "Manual Adjustment - Found extra stock")
        if result['success']:
            print(f"✅ Updated {result['product_name']}: {result['old_stock']} → {result['new_stock']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Example 2: Simulate sales
        print("\n🛒 Example 2: Simulate Sales")
        sales_result = inv_mgr.simulate_sales(3)
        if sales_result['success']:
            print(f"✅ Simulated {sales_result['sales_count']} sales")
            for sale in sales_result['sales']:
                if sale['success']:
                    print(f"   - Sold {abs(sale['quantity_change'])} units of {sale['product_name']}")
        
        # Example 3: Simulate restocking
        print("\n📦 Example 3: Simulate Restocking")
        restock_result = inv_mgr.simulate_restocking(2)
        if restock_result['success']:
            print(f"✅ Simulated {restock_result['restock_count']} restocks")
            for restock in restock_result['restocks']:
                if restock['success']:
                    print(f"   - Added {restock['quantity_change']} units of {restock['product_name']}")

if __name__ == "__main__":
    main()