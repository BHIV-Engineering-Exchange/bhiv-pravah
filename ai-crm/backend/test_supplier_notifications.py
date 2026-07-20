#!/usr/bin/env python3
"""
Test Supplier Notification System
Demonstrates how to send restock alerts to suppliers
"""

from supplier_notification_system import notify_supplier_for_restock, SupplierNotificationSystem
from user_product_models import USER_PRODUCT_CATALOG
from inventory_manager import InventoryManager

def test_supplier_notifications():
    """Test sending notifications to suppliers"""
    print("🧪 Testing Supplier Notification System")
    print("=" * 50)
    
    # Get a low stock product for testing
    with InventoryManager() as inv_mgr:
        inventory_report = inv_mgr.get_inventory_report()
        
        # Find a product that needs reordering
        low_stock_product = None
        for _, row in inventory_report.iterrows():
            if row['Needs Reorder']:
                low_stock_product = row
                break
        
        if not low_stock_product:
            # Create a low stock scenario for testing
            print("📦 Creating low stock scenario for testing...")
            test_product = USER_PRODUCT_CATALOG[0]  # Use first product
            
            # Set stock to low level
            result = inv_mgr.set_absolute_quantity(
                test_product.product_id, 
                3,  # Very low stock
                "Test: Setting low stock for supplier notification demo"
            )
            
            if result['success']:
                print(f"✅ Set {test_product.name} stock to 3 units for testing")
                
                # Get updated inventory info
                current_inv = inv_mgr.get_current_inventory(test_product.product_id)
                
                low_stock_product = {
                    'Product ID': test_product.product_id,
                    'Product Name': test_product.name,
                    'Current Stock': current_inv.current_stock,
                    'Reorder Point': current_inv.reorder_point,
                    'Supplier ID': current_inv.supplier_id
                }
    
    if low_stock_product:
        print(f"\n📋 Testing with product: {low_stock_product['Product Name']}")
        print(f"   Current Stock: {low_stock_product['Current Stock']}")
        print(f"   Reorder Point: {low_stock_product['Reorder Point']}")
        print(f"   Supplier: {low_stock_product['Supplier ID']}")
        
        print(f"\n📧 Sending restock alert to supplier...")
        
        # Send notification to supplier
        success = notify_supplier_for_restock(
            product_id=low_stock_product['Product ID'],
            product_name=low_stock_product['Product Name'],
            current_stock=low_stock_product['Current Stock'],
            reorder_point=low_stock_product['Reorder Point'],
            supplier_id=low_stock_product['Supplier ID'],
            requested_quantity=50  # Request 50 units
        )
        
        if success:
            print("✅ SUCCESS: Email sent to supplier!")
            print("📧 The supplier has been notified about the low stock")
            print("📦 They will receive a professional email with:")
            print("   - Product details and current stock levels")
            print("   - Requested reorder quantity")
            print("   - Company contact information")
            print("   - Action items and next steps")
        else:
            print("⚠️  EMAIL NOT SENT: Using console notification instead")
            print("💡 To send real emails, configure these in your .env file:")
            print("   EMAIL_USER=your-email@gmail.com")
            print("   EMAIL_PASSWORD=your-app-password")
            print("   COMPANY_NAME=Your Company Name")
            print("   COMPANY_EMAIL=procurement@yourcompany.com")
            print("   COMPANY_PHONE=+1-555-0123")
            print("   COMPANY_ADDRESS=123 Business St, City, State")
    else:
        print("❌ No low stock products found for testing")
    
    print(f"\n🔧 How to configure email notifications:")
    print("1. Create a .env file in your project directory")
    print("2. Add your email configuration:")
    print("   EMAIL_USER=your-gmail@gmail.com")
    print("   EMAIL_PASSWORD=your-app-password  # Get from Gmail App Passwords")
    print("   COMPANY_EMAIL=procurement@yourcompany.com")
    print("   COMPANY_NAME=Your Company Name")
    print("3. Restart the system")
    print("4. Suppliers will receive professional restock emails!")

def demo_email_content():
    """Show what the email looks like"""
    print("\n📧 SAMPLE EMAIL CONTENT TO SUPPLIER:")
    print("=" * 50)
    
    notifier = SupplierNotificationSystem()
    
    # This will show the console version of what would be emailed
    notifier.send_restock_alert_to_supplier(
        product_id="USR001",
        product_name="BOAST PB-01 BLUE POWER BANK",
        current_stock=3,
        reorder_point=10,
        supplier_id="SUPPLIER_001",
        requested_quantity=50
    )

if __name__ == "__main__":
    test_supplier_notifications()
    print("\n" + "=" * 50)
    demo_email_content()