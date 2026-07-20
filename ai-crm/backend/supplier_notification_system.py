#!/usr/bin/env python3
"""
Supplier Notification System
Sends restock alerts directly to suppliers when their products are low in stock
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class SupplierNotificationSystem:
    """Send notifications directly to suppliers"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.company_email = os.getenv("COMPANY_EMAIL", "procurement@yourcompany.com")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")
        self.company_name = os.getenv("COMPANY_NAME", "Your Company Name")
        self.company_address = os.getenv("COMPANY_ADDRESS", "123 Business St, City, State 12345")
        self.company_phone = os.getenv("COMPANY_PHONE", "+1-555-0123")
        
    def get_supplier_info(self, supplier_id):
        """Get supplier contact information"""
        try:
            from database.models import SessionLocal, Supplier
            db = SessionLocal()
            supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
            db.close()
            
            if supplier:
                return {
                    'supplier_id': supplier.supplier_id,
                    'name': supplier.name,
                    'email': supplier.contact_email,
                    'phone': supplier.contact_phone,
                    'lead_time': supplier.lead_time_days,
                    'minimum_order': supplier.minimum_order
                }
        except Exception as e:
            print(f"Error getting supplier info: {e}")
        
        return None
    
    def send_email_to_supplier(self, supplier_email, subject, message, is_html=False):
        """Send email directly to supplier"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.company_email
            msg['To'] = supplier_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(message, 'html' if is_html else 'plain'))
            
            # SMTP configuration
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login with app password
            if self.email_password:
                server.login(self.company_email, self.email_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.company_email, supplier_email, text)
                server.quit()
                
                print(f"✅ Email sent to supplier {supplier_email}: {subject}")
                return True
            else:
                print("❌ Email password not configured, showing console notification instead")
                self.console_notification_to_supplier(supplier_email, subject, message)
                return False
                
        except Exception as e:
            print(f"❌ Failed to send email to supplier {supplier_email}: {e}")
            # Fallback to console notification
            self.console_notification_to_supplier(supplier_email, subject, message)
            return False
    
    def console_notification_to_supplier(self, supplier_email, subject, message):
        """Console notification when email fails"""
        print(f"\n📧 SUPPLIER NOTIFICATION")
        print(f"To: {supplier_email}")
        print(f"Subject: {subject}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Message Preview: {message[:200]}...")
        print("=" * 60)
    
    def send_restock_alert_to_supplier(self, product_id, product_name, current_stock, reorder_point, supplier_id, requested_quantity=None):
        """Send restock alert directly to supplier"""
        
        # Get supplier information
        supplier_info = self.get_supplier_info(supplier_id)
        if not supplier_info:
            print(f"❌ Supplier {supplier_id} not found")
            return False
        
        # Calculate suggested order quantity
        if not requested_quantity:
            shortage = reorder_point - current_stock
            requested_quantity = max(shortage * 2, supplier_info['minimum_order'])  # Order double the shortage or minimum order
        
        # Ensure we meet minimum order requirements
        if requested_quantity < supplier_info['minimum_order']:
            requested_quantity = supplier_info['minimum_order']
        
        subject = f"🚨 URGENT RESTOCK REQUEST - {product_name}"
        
        # Create professional email message
        message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #dc3545; margin: 0;">🚨 URGENT RESTOCK REQUEST</h2>
                </div>
                
                <p>Dear {supplier_info['name']},</p>
                
                <p>We hope this email finds you well. We are writing to inform you that one of your products in our inventory has reached critically low levels and requires immediate restocking.</p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #856404;">📦 Product Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Product Name:</td>
                            <td style="padding: 8px 0;">{product_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Product ID:</td>
                            <td style="padding: 8px 0;">{product_id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Current Stock:</td>
                            <td style="padding: 8px 0; color: #dc3545; font-weight: bold;">{current_stock} units</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Reorder Point:</td>
                            <td style="padding: 8px 0;">{reorder_point} units</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Requested Quantity:</td>
                            <td style="padding: 8px 0; color: #28a745; font-weight: bold;">{requested_quantity} units</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #0c5460;">📋 Order Information</h3>
                    <p><strong>Alert Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Expected Lead Time:</strong> {supplier_info['lead_time']} days</p>
                    <p><strong>Minimum Order Quantity:</strong> {supplier_info['minimum_order']} units</p>
                </div>
                
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #721c24;">⚡ Action Required</h3>
                    <ul>
                        <li>Please confirm availability of {requested_quantity} units of {product_name}</li>
                        <li>Provide delivery timeline and expected shipping date</li>
                        <li>Send quotation and purchase order confirmation</li>
                        <li>Update us on any potential delays or issues</li>
                    </ul>
                </div>
                
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #155724;">📞 Contact Information</h3>
                    <p><strong>Company:</strong> {self.company_name}</p>
                    <p><strong>Procurement Email:</strong> {self.company_email}</p>
                    <p><strong>Phone:</strong> {self.company_phone}</p>
                    <p><strong>Address:</strong> {self.company_address}</p>
                </div>
                
                <p>Please reply to this email with:</p>
                <ol>
                    <li>Confirmation of product availability</li>
                    <li>Unit price and total quotation</li>
                    <li>Expected delivery date</li>
                    <li>Purchase order acknowledgment</li>
                </ol>
                
                <p>We appreciate your prompt attention to this matter and look forward to your quick response.</p>
                
                <p>Best regards,<br>
                <strong>Procurement Team</strong><br>
                {self.company_name}<br>
                <em>This is an automated message from our AI Logistics System</em></p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d;">
                    <p>This email was automatically generated by our inventory management system when stock levels fell below the reorder point. Please do not reply to this email address if it's automated - use the contact information provided above.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email to supplier
        success = self.send_email_to_supplier(supplier_info['email'], subject, message, is_html=True)
        
        if success:
            # Also log this in the system
            try:
                from database.models import SessionLocal, AgentLog
                db = SessionLocal()
                
                log_entry = AgentLog(
                    timestamp=datetime.utcnow(),
                    action="Supplier Restock Alert Sent",
                    product_id=product_id,
                    quantity=requested_quantity,
                    confidence=0.95,
                    human_review=False,
                    details=f"Restock alert sent to {supplier_info['name']} ({supplier_info['email']}) for {product_name}. Requested {requested_quantity} units."
                )
                
                db.add(log_entry)
                db.commit()
                db.close()
                
            except Exception as e:
                print(f"Warning: Could not log supplier alert: {e}")
        
        return success
    
    def send_order_confirmation_to_supplier(self, supplier_id, po_number, products, total_amount):
        """Send order confirmation to supplier"""
        supplier_info = self.get_supplier_info(supplier_id)
        if not supplier_info:
            return False
        
        subject = f"📋 PURCHASE ORDER CONFIRMATION - PO #{po_number}"
        
        products_html = ""
        for product in products:
            products_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{product['name']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{product['quantity']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${product['unit_price']:.2f}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${product['total']:.2f}</td>
            </tr>
            """
        
        message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #155724; margin: 0;">📋 PURCHASE ORDER CONFIRMATION</h2>
                </div>
                
                <p>Dear {supplier_info['name']},</p>
                
                <p>Thank you for your prompt response to our restock request. This email confirms our purchase order.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>📋 Order Details</h3>
                    <p><strong>PO Number:</strong> {po_number}</p>
                    <p><strong>Order Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                    <p><strong>Expected Delivery:</strong> {(datetime.now()).strftime('%Y-%m-%d')} (+ {supplier_info['lead_time']} days)</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Product</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Quantity</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">Unit Price</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {products_html}
                        <tr style="background-color: #f8f9fa; font-weight: bold;">
                            <td colspan="3" style="padding: 12px; border: 1px solid #ddd; text-align: right;">TOTAL AMOUNT:</td>
                            <td style="padding: 12px; border: 1px solid #ddd; text-align: right;">${total_amount:.2f}</td>
                        </tr>
                    </tbody>
                </table>
                
                <p>Please confirm receipt of this purchase order and provide:</p>
                <ul>
                    <li>Order acknowledgment</li>
                    <li>Confirmed delivery date</li>
                    <li>Tracking information when shipped</li>
                </ul>
                
                <p>Best regards,<br>
                <strong>Procurement Team</strong><br>
                {self.company_name}</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email_to_supplier(supplier_info['email'], subject, message, is_html=True)

# Global instance
supplier_notifier = SupplierNotificationSystem()

def notify_supplier_for_restock(product_id, product_name, current_stock, reorder_point, supplier_id, requested_quantity=None):
    """Quick function to notify supplier for restock"""
    return supplier_notifier.send_restock_alert_to_supplier(
        product_id, product_name, current_stock, reorder_point, supplier_id, requested_quantity
    )

def demo_supplier_notifications():
    """Demo supplier notification system"""
    print("📧 Testing Supplier Notification System...")
    
    # Test restock alert to supplier
    success = notify_supplier_for_restock(
        product_id="USR001",
        product_name="BOAST PB-01 BLUE POWER BANK",
        current_stock=3,
        reorder_point=10,
        supplier_id="SUPPLIER_001",
        requested_quantity=50
    )
    
    if success:
        print("✅ Supplier restock alert sent successfully!")
    else:
        print("⚠️ Supplier alert sent via console (email not configured)")

if __name__ == "__main__":
    demo_supplier_notifications()