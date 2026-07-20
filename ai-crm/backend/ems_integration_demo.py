#!/usr/bin/env python3
"""
EMS Integration Demo
Demonstrates how Parth's EMS automation integrates with the existing AI agents
"""

import time
from datetime import datetime, timedelta
from ems_automation import (
    trigger_restock_alert, 
    trigger_purchase_order, 
    trigger_shipment_notification, 
    trigger_delivery_delay,
    ems_automation,
    process_scheduled_emails
)

def demo_restock_integration():
    """Demo restock agent triggering EMS alerts"""
    print("🔄 RESTOCK AGENT + EMS INTEGRATION DEMO")
    print("=" * 50)
    
    # Simulate restock agent detecting low stock
    low_stock_items = [
        {"product_id": "A101", "name": "Wireless Mouse", "current_stock": 3, "restock_qty": 25},
        {"product_id": "B205", "name": "USB Cable", "current_stock": 8, "restock_qty": 50},
        {"product_id": "C330", "name": "Keyboard", "current_stock": 2, "restock_qty": 15}
    ]
    
    print("📦 Restock Agent detected low stock items:")
    for item in low_stock_items:
        print(f"   - {item['name']} (ID: {item['product_id']}): {item['current_stock']} units")
    
    print("\n📧 Triggering EMS restock alerts...")
    for item in low_stock_items:
        success = trigger_restock_alert(
            item['product_id'], 
            item['name'], 
            item['current_stock'], 
            item['restock_qty']
        )
        if success:
            print(f"   ✅ Alert sent for {item['name']}")
        else:
            print(f"   ❌ Failed to send alert for {item['name']}")
    
    print("\n" + "=" * 50)

def demo_procurement_integration():
    """Demo procurement agent triggering purchase order emails"""
    print("🏭 PROCUREMENT AGENT + EMS INTEGRATION DEMO")
    print("=" * 50)
    
    # Simulate procurement agent creating purchase orders
    purchase_orders = [
        {
            "po_number": "PO-2025-001",
            "supplier_email": "supplier@techparts.com",
            "product_name": "Wireless Mouse",
            "quantity": 25,
            "unit_cost": 15.50,
            "expected_delivery": "2025-02-01"
        },
        {
            "po_number": "PO-2025-002", 
            "supplier_email": "cables@supplier.com",
            "product_name": "USB Cable",
            "quantity": 50,
            "unit_cost": 3.25,
            "expected_delivery": "2025-01-30"
        }
    ]
    
    print("📋 Procurement Agent created purchase orders:")
    for po in purchase_orders:
        total_cost = po['quantity'] * po['unit_cost']
        print(f"   - PO {po['po_number']}: {po['quantity']} x {po['product_name']} = ${total_cost:.2f}")
    
    print("\n📧 Triggering EMS purchase order emails...")
    for po in purchase_orders:
        total_cost = po['quantity'] * po['unit_cost']
        success = trigger_purchase_order(
            po['supplier_email'],
            po['po_number'],
            po['product_name'],
            po['quantity'],
            po['unit_cost'],
            total_cost,
            po['expected_delivery']
        )
        if success:
            print(f"   ✅ PO email sent to {po['supplier_email']}")
        else:
            print(f"   ❌ Failed to send PO email to {po['supplier_email']}")
    
    print("\n" + "=" * 50)

def demo_delivery_integration():
    """Demo delivery agent triggering shipment notifications"""
    print("🚚 DELIVERY AGENT + EMS INTEGRATION DEMO")
    print("=" * 50)
    
    # Simulate delivery agent processing shipments
    shipments = [
        {
            "order_id": "ORD-12345",
            "customer_email": "john.doe@example.com",
            "tracking_number": "FS123456789",
            "courier": "FastShip Express",
            "estimated_delivery": "2025-01-28"
        },
        {
            "order_id": "ORD-12346",
            "customer_email": "jane.smith@example.com", 
            "tracking_number": "FS987654321",
            "courier": "QuickDelivery Co",
            "estimated_delivery": "2025-01-29"
        }
    ]
    
    print("📦 Delivery Agent processed shipments:")
    for shipment in shipments:
        print(f"   - Order {shipment['order_id']}: Tracking {shipment['tracking_number']}")
    
    print("\n📧 Triggering EMS shipment notifications...")
    for shipment in shipments:
        success = trigger_shipment_notification(
            shipment['customer_email'],
            shipment['order_id'],
            shipment['tracking_number'],
            shipment['courier'],
            shipment['estimated_delivery'],
            f"https://tracking.example.com/{shipment['tracking_number']}"
        )
        if success:
            print(f"   ✅ Notification sent to {shipment['customer_email']}")
        else:
            print(f"   ❌ Failed to send notification to {shipment['customer_email']}")
    
    print("\n" + "=" * 50)

def demo_delay_handling():
    """Demo handling delivery delays"""
    print("⚠️ DELIVERY DELAY HANDLING DEMO")
    print("=" * 50)
    
    # Simulate delivery delays
    delays = [
        {
            "order_id": "ORD-12345",
            "customer_email": "john.doe@example.com",
            "tracking_number": "FS123456789",
            "original_delivery": "2025-01-28",
            "new_delivery": "2025-01-30",
            "reason": "Weather conditions causing delays"
        }
    ]
    
    print("🌧️ Delivery delays detected:")
    for delay in delays:
        print(f"   - Order {delay['order_id']}: Delayed from {delay['original_delivery']} to {delay['new_delivery']}")
        print(f"     Reason: {delay['reason']}")
    
    print("\n📧 Triggering EMS delay notifications...")
    for delay in delays:
        success = trigger_delivery_delay(
            delay['customer_email'],
            delay['order_id'],
            delay['tracking_number'],
            delay['original_delivery'],
            delay['new_delivery'],
            delay['reason']
        )
        if success:
            print(f"   ✅ Delay notice sent to {delay['customer_email']}")
        else:
            print(f"   ❌ Failed to send delay notice to {delay['customer_email']}")
    
    print("\n" + "=" * 50)

def demo_scheduled_processing():
    """Demo scheduled email processing"""
    print("📅 SCHEDULED EMAIL PROCESSING DEMO")
    print("=" * 50)
    
    print(f"📧 Current scheduled emails: {len(ems_automation.scheduled_emails)}")
    
    if ems_automation.scheduled_emails:
        print("Scheduled emails:")
        for i, email in enumerate(ems_automation.scheduled_emails, 1):
            print(f"   {i}. {email['subject']} - {email['scheduled_time'][:16]}")
    
    print("\n🔄 Processing scheduled emails...")
    processed = process_scheduled_emails()
    
    if processed > 0:
        print(f"   ✅ Processed {processed} scheduled emails")
    else:
        print("   ℹ️ No emails were due for processing")
    
    print(f"📧 Remaining scheduled emails: {len(ems_automation.scheduled_emails)}")
    print("\n" + "=" * 50)

def demo_ems_statistics():
    """Show EMS statistics"""
    print("📊 EMS AUTOMATION STATISTICS")
    print("=" * 50)
    
    print(f"📧 Email Templates: {len(ems_automation.templates)}")
    print("Available templates:")
    for template_id in ems_automation.templates.keys():
        print(f"   - {template_id}")
    
    print(f"\n🔔 Trigger Configurations: {len(ems_automation.triggers)}")
    print("Configured triggers:")
    for event_type, config in ems_automation.triggers.items():
        print(f"   - {event_type.value}: Priority {config['priority'].value}")
    
    print(f"\n📅 Scheduled Emails: {len(ems_automation.scheduled_emails)}")
    
    print("\n" + "=" * 50)

def main():
    """Run the complete EMS integration demo"""
    print("🚀 PARTH'S EMS AUTOMATION INTEGRATION DEMO")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all demos
    demo_ems_statistics()
    time.sleep(1)
    
    demo_restock_integration()
    time.sleep(1)
    
    demo_procurement_integration()
    time.sleep(1)
    
    demo_delivery_integration()
    time.sleep(1)
    
    demo_delay_handling()
    time.sleep(1)
    
    demo_scheduled_processing()
    
    print("🎉 EMS INTEGRATION DEMO COMPLETED")
    print("=" * 60)
    print("✅ All AI agents are now integrated with EMS automation!")
    print("📧 Email notifications will be sent automatically for:")
    print("   • Restock alerts when inventory is low")
    print("   • Purchase orders to suppliers")
    print("   • Shipment notifications to customers")
    print("   • Delivery delay notices")
    print("\n🎯 Next Steps:")
    print("   1. Configure SMTP settings in .env file")
    print("   2. Customize email templates as needed")
    print("   3. Set up trigger priorities and delays")
    print("   4. Monitor email activity in the dashboard")
    print("=" * 60)

if __name__ == "__main__":
    main()