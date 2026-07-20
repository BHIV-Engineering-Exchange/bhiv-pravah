#!/usr/bin/env python3
"""
Simple test for supplier notifications
"""

def test_supplier_notification():
    """Test sending notification to supplier"""
    print("📧 Testing Supplier Notification System")
    print("=" * 50)
    
    try:
        from supplier_notification_system import notify_supplier_for_restock
        
        # Test with sample data
        success = notify_supplier_for_restock(
            product_id="USR001",
            product_name="BOAST PB-01 BLUE POWER BANK",
            current_stock=3,
            reorder_point=10,
            supplier_id="SUPPLIER_001",
            requested_quantity=50
        )
        
        if success:
            print("✅ SUCCESS: Email would be sent to supplier!")
            print("📧 Professional restock alert generated")
        else:
            print("⚠️  EMAIL CONFIGURATION NEEDED")
            print("📧 Notification sent to console instead")
            print()
            print("🔧 To send real emails, add to .env file:")
            print("EMAIL_USER=your-email@gmail.com")
            print("EMAIL_PASSWORD=your-app-password")
            print("COMPANY_NAME=Your Company Name")
            print("COMPANY_EMAIL=procurement@yourcompany.com")
        
        print()
        print("🎯 WHAT HAPPENS:")
        print("1. System detects low stock (3 units < 10 reorder point)")
        print("2. Generates professional email to supplier")
        print("3. Email includes product details, quantities, contact info")
        print("4. Supplier receives clear restock request")
        print("5. Activity is logged in the system")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure all required files are present")

def show_email_preview():
    """Show what the email looks like"""
    print("\n📧 EMAIL PREVIEW (What supplier receives):")
    print("=" * 60)
    print("Subject: 🚨 URGENT RESTOCK REQUEST - BOAST PB-01 BLUE POWER BANK")
    print("To: orders@techparts.com")
    print("From: procurement@yourcompany.com")
    print()
    print("Dear TechParts Supply Co.,")
    print()
    print("We are writing to inform you that one of your products")
    print("has reached critically low levels and requires restocking.")
    print()
    print("📦 PRODUCT DETAILS:")
    print("Product: BOAST PB-01 BLUE POWER BANK")
    print("Product ID: USR001")
    print("Current Stock: 3 units")
    print("Reorder Point: 10 units")
    print("Requested Quantity: 50 units")
    print()
    print("⚡ ACTION REQUIRED:")
    print("• Confirm availability of 50 units")
    print("• Provide delivery timeline")
    print("• Send quotation and PO confirmation")
    print()
    print("📞 CONTACT: procurement@yourcompany.com")
    print()
    print("Best regards,")
    print("Procurement Team")
    print("=" * 60)

if __name__ == "__main__":
    test_supplier_notification()
    show_email_preview()
    
    print("\n🚀 NEXT STEPS:")
    print("1. Configure email settings in .env file")
    print("2. Use dashboard to send real alerts to suppliers")
    print("3. Monitor supplier responses and restock status")
    print("4. System will automatically track all communications")