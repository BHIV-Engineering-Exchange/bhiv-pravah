# 📧 Email Notification Setup Guide

## 🎯 **How to Send Real Emails to Suppliers**

Your system is ready to send professional restock alerts to suppliers via email. Here's how to set it up:

---

## 🔧 **Step 1: Configure Email Settings**

### **Create/Update .env File**
Add these settings to your `.env` file:

```bash
# Email Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Company Information (appears in emails)
COMPANY_NAME=Your Company Name
COMPANY_EMAIL=procurement@yourcompany.com
COMPANY_PHONE=+1-555-0123
COMPANY_ADDRESS=123 Business St, City, State 12345
ADMIN_EMAIL=admin@yourcompany.com
```

### **For Gmail Users:**
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL_PASSWORD`

### **For Other Email Providers:**
```bash
# Outlook/Hotmail
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587

# Yahoo
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587

# Custom SMTP
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587
```

---

## 🧪 **Step 2: Test Email Notifications**

### **Run Test Script:**
```bash
cd "/Users/rishabh/Desktop/Voice bot/ai-agent_project"
source venv_new/bin/activate
python test_supplier_notifications.py
```

### **Expected Output:**
```
✅ SUCCESS: Email sent to supplier!
📧 The supplier has been notified about the low stock
```

---

## 📧 **Step 3: What Suppliers Receive**

### **Professional Email Content:**
- **Subject**: 🚨 URGENT RESTOCK REQUEST - [Product Name]
- **Formatted HTML email** with company branding
- **Product details**: ID, name, current stock, reorder point
- **Order information**: Requested quantity, lead time, minimum order
- **Contact details**: Your company info for easy response
- **Action items**: Clear next steps for supplier

### **Sample Email Preview:**
```
🚨 URGENT RESTOCK REQUEST - BOAST PB-01 BLUE POWER BANK

Dear TechParts Supply Co.,

We hope this email finds you well. We are writing to inform you that one of your products in our inventory has reached critically low levels and requires immediate restocking.

📦 Product Details
Product Name: BOAST PB-01 BLUE POWER BANK
Product ID: USR001
Current Stock: 3 units
Reorder Point: 10 units
Requested Quantity: 50 units

📋 Order Information
Alert Generated: 2025-09-03 15:45:23
Expected Lead Time: 5 days
Minimum Order Quantity: 10 units

⚡ Action Required
• Please confirm availability of 50 units
• Provide delivery timeline and expected shipping date
• Send quotation and purchase order confirmation
• Update us on any potential delays or issues

📞 Contact Information
Company: Your Company Name
Procurement Email: procurement@yourcompany.com
Phone: +1-555-0123
```

---

## 🚀 **Step 4: Use in Dashboard**

### **From Enhanced Dashboard:**
1. **Open Dashboard**: http://localhost:8503
2. **Select low stock product** in sidebar
3. **See "⚠️ Reorder Required!" alert**
4. **Enter reorder quantity**
5. **Click "📧 Send Reorder Request to Supplier"**
6. **Email sent automatically to supplier!**

### **From Code:**
```python
from supplier_notification_system import notify_supplier_for_restock

# Send restock alert to supplier
success = notify_supplier_for_restock(
    product_id="USR001",
    product_name="BOAST PB-01 BLUE POWER BANK",
    current_stock=3,
    reorder_point=10,
    supplier_id="SUPPLIER_001",
    requested_quantity=50
)

if success:
    print("✅ Email sent to supplier!")
else:
    print("⚠️ Check email configuration")
```

---

## 🔍 **Step 5: Troubleshooting**

### **Common Issues:**

#### **"Authentication Required" Error:**
- ✅ **Solution**: Use App Password, not regular password
- ✅ **Gmail**: Enable 2FA and generate App Password
- ✅ **Check**: EMAIL_USER and EMAIL_PASSWORD in .env

#### **"Connection Refused" Error:**
- ✅ **Solution**: Check SMTP_SERVER and SMTP_PORT
- ✅ **Gmail**: smtp.gmail.com:587
- ✅ **Firewall**: Ensure port 587 is not blocked

#### **"Email Not Sent" Message:**
- ✅ **Solution**: System falls back to console notifications
- ✅ **Check**: .env file exists and has correct values
- ✅ **Restart**: Restart dashboard after changing .env

### **Test Email Configuration:**
```bash
python -c "
from supplier_notification_system import SupplierNotificationSystem
notifier = SupplierNotificationSystem()
success = notifier.send_email_to_supplier(
    'test@example.com', 
    'Test Email', 
    'This is a test email from your logistics system'
)
print('Email test:', 'SUCCESS' if success else 'FAILED')
"
```

---

## 📊 **Step 6: Monitor Email Activity**

### **Check Logs:**
- All email attempts are logged in the system
- Success/failure status tracked
- Supplier responses can be monitored
- Activity appears in Recent Activity dashboard

### **Dashboard Integration:**
- ✅ **Real-time status** in sidebar
- ✅ **Message history** tracking
- ✅ **Supplier contact** management
- ✅ **Automatic logging** of all communications

---

## 🎉 **Benefits of Email Notifications**

### **For Your Business:**
- ✅ **Automated communication** with suppliers
- ✅ **Professional appearance** with branded emails
- ✅ **Faster response times** from suppliers
- ✅ **Complete audit trail** of all communications
- ✅ **Reduced manual work** in procurement

### **For Suppliers:**
- ✅ **Clear, detailed requests** with all necessary information
- ✅ **Professional communication** builds trust
- ✅ **Easy response** with contact details provided
- ✅ **Automated alerts** ensure nothing is missed
- ✅ **Structured format** makes processing easier

---

## 🚀 **Ready to Go!**

Once configured, your system will:
1. **Monitor inventory levels** automatically
2. **Detect low stock** situations
3. **Send professional emails** to suppliers
4. **Track all communications**
5. **Provide real-time status** updates

**Your suppliers will receive professional, detailed restock requests automatically when inventory runs low!** 📧✨