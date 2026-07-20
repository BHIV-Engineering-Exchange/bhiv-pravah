#!/usr/bin/env python3
"""
Email Notification System for AI Agent Logistics
Sends real-time email alerts for critical events
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EmailNotificationSystem:
    """Handle email notifications for logistics events"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER", "logistics@company.com")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@company.com")
        
    def send_email(self, to_email, subject, message, is_html=False):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(message, 'html' if is_html else 'plain'))
            
            # Gmail SMTP configuration
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login with app password (for Gmail)
            if self.email_password:
                server.login(self.email_user, self.email_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            # Fallback to console notification
            self.console_notification(subject, message)
            return False
    
    def console_notification(self, subject, message):
        """Fallback console notification"""
        print(f"\n🔔 NOTIFICATION: {subject}")
        print(f"📧 To: {self.admin_email}")
        print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 Message: {message}")
        print("-" * 50)
    
    def send_low_stock_alert(self, product_id, product_name, current_stock, reorder_point):
        """Send low stock alert"""
        subject = f"🚨 LOW STOCK ALERT: {product_name}"
        
        message = f"""
        <h2>🚨 Low Stock Alert</h2>
        <p><strong>Product:</strong> {product_name}</p>
        <p><strong>Product ID:</strong> {product_id}</p>
        <p><strong>Current Stock:</strong> {current_stock} units</p>
        <p><strong>Reorder Point:</strong> {reorder_point} units</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3>Action Required:</h3>
        <ul>
            <li>Review current stock levels</li>
            <li>Create purchase order if needed</li>
            <li>Contact supplier for restock</li>
        </ul>
        
        <p>This is an automated alert from the AI Logistics System.</p>
        """
        
        return self.send_email(self.admin_email, subject, message, is_html=True)
    
    def send_reorder_confirmation(self, product_name, quantity, supplier, po_number):
        """Send reorder confirmation"""
        subject = f"✅ REORDER CONFIRMED: {product_name}"
        
        message = f"""
        <h2>✅ Purchase Order Confirmed</h2>
        <p><strong>Product:</strong> {product_name}</p>
        <p><strong>Quantity:</strong> {quantity} units</p>
        <p><strong>Supplier:</strong> {supplier}</p>
        <p><strong>PO Number:</strong> {po_number}</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <p>Purchase order has been automatically generated and sent to supplier.</p>
        """
        
        return self.send_email(self.admin_email, subject, message, is_html=True)
    
    def send_delivery_delay_alert(self, order_id, tracking_number, expected_date):
        """Send delivery delay alert"""
        subject = f"⚠️ DELIVERY DELAY: Order #{order_id}"
        
        message = f"""
        <h2>⚠️ Delivery Delay Alert</h2>
        <p><strong>Order ID:</strong> #{order_id}</p>
        <p><strong>Tracking Number:</strong> {tracking_number}</p>
        <p><strong>Expected Delivery:</strong> {expected_date}</p>
        <p><strong>Alert Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3>Action Required:</h3>
        <ul>
            <li>Contact courier for status update</li>
            <li>Notify customer of delay</li>
            <li>Update delivery timeline</li>
        </ul>
        """
        
        return self.send_email(self.admin_email, subject, message, is_html=True)
    
    def send_system_alert(self, alert_type, message, severity="medium"):
        """Send general system alert"""
        severity_emoji = {"low": "ℹ️", "medium": "⚠️", "high": "🚨", "critical": "🔴"}
        emoji = severity_emoji.get(severity, "ℹ️")
        
        subject = f"{emoji} SYSTEM ALERT: {alert_type}"
        
        html_message = f"""
        <h2>{emoji} System Alert</h2>
        <p><strong>Alert Type:</strong> {alert_type}</p>
        <p><strong>Severity:</strong> {severity.upper()}</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3>Details:</h3>
        <p>{message}</p>
        
        <p>This is an automated alert from the AI Logistics System.</p>
        """
        
        return self.send_email(self.admin_email, subject, html_message, is_html=True)

# Global notification instance
notification_system = EmailNotificationSystem()

def send_low_stock_alert(product_id, product_name, current_stock, reorder_point):
    """Quick function to send low stock alert"""
    return notification_system.send_low_stock_alert(product_id, product_name, current_stock, reorder_point)

def send_reorder_confirmation(product_name, quantity, supplier, po_number):
    """Quick function to send reorder confirmation"""
    return notification_system.send_reorder_confirmation(product_name, quantity, supplier, po_number)

def send_delivery_delay_alert(order_id, tracking_number, expected_date):
    """Quick function to send delivery delay alert"""
    return notification_system.send_delivery_delay_alert(order_id, tracking_number, expected_date)

def send_system_alert(alert_type, message, severity="medium"):
    """Quick function to send system alert"""
    return notification_system.send_system_alert(alert_type, message, severity)

# Demo function
def demo_notifications():
    """Demo the notification system"""
    print("📧 Testing Email Notification System...")
    
    # Test low stock alert
    send_low_stock_alert("USR001", "BOAST PB-01 BLUE POWER BANK", 3, 10)
    
    # Test reorder confirmation
    send_reorder_confirmation("SYSKA Power Bank", 50, "TechParts Supply Co.", "PO-2025-001")
    
    # Test delivery delay
    send_delivery_delay_alert("12345", "FS123456789", "2025-09-05")
    
    # Test system alert
    send_system_alert("Database Connection", "Database connection restored after brief outage", "medium")
    
    print("✅ Notification demo completed!")

if __name__ == "__main__":
    demo_notifications()