# Customer Portal & Automated Procurement System

## 🎯 Overview

A comprehensive customer-facing dashboard with automated inventory management and supplier communication system.

## ✨ Features

### Customer Portal
- **Product Catalog**: Browse all available products with real-time stock information
- **Shopping Cart**: Add/remove products, adjust quantities
- **Order Placement**: Quick checkout with automatic order confirmation
- **Order History**: Track all previous orders and their status
- **Search & Filter**: Find products by name, category, or description

### Automated Procurement System
- **Low Stock Detection**: Monitors inventory levels automatically
- **Auto-Reordering**: Triggers procurement when stock falls below reorder level
- **Supplier Notifications**: Sends automated emails via EMS to suppliers
- **Purchase Order Management**: Creates and tracks POs automatically
- **Internal Alerts**: Notifies procurement team of low stock situations

## 🚀 How It Works

### Customer Order Flow
1. Customer browses product catalog at `/customer-portal`
2. Adds products to shopping cart
3. Places order (triggers backend API)
4. Receives confirmation email
5. Order is processed and stock is updated

### Automated Procurement Flow
1. **Stock Check**: System monitors inventory after each order
2. **Low Stock Alert**: When stock ≤ reorder_level:
   - Creates procurement request automatically
   - Sends email to supplier with order details
   - Sends internal alert to procurement team
3. **Supplier Response**: Supplier receives automated email with:
   - Product details and quantities needed
   - Current stock status
   - Procurement request ID
4. **Approval**: Admin approves procurement request
5. **Purchase Order**: System creates formal PO and sends to supplier

## 📧 EMS Email Automation

The system automatically sends:

### To Suppliers
- **Procurement Request Email**: When stock is low
  - Product details
  - Quantity needed
  - Current stock level
  - Request ID
- **Purchase Order Email**: When request is approved
  - Official PO number
  - Delivery instructions

### To Customers
- **Order Confirmation**: Immediately after order placement
  - Order summary
  - Estimated delivery
  - Tracking information

### Internal
- **Low Stock Alerts**: To procurement team
  - Product information
  - Stock levels
  - Automated actions taken

## 🔧 API Endpoints

### Customer Endpoints
```
GET  /customer/products          - Get product catalog
POST /customer/orders            - Place new order
GET  /customer/orders            - Get order history
GET  /customer/orders/{id}       - Get order details
```

### Admin/Procurement Endpoints
```
GET  /admin/procurement/requests                 - View all requests
PUT  /admin/procurement/{id}/approve            - Approve and create PO
```

## 💻 Frontend Access

Navigate to: **http://localhost:3000/customer-portal**

## ⚙️ Configuration

### Set Reorder Levels
Products should have these fields in database:
- `stock_quantity`: Current stock
- `reorder_level`: Threshold for auto-reorder (default: 10)
- `supplier_id`: Associated supplier

### Email Configuration
EMS uses the email notification system configured in `backend/email_notifications.py`

## 🎨 Customization

### Product Display
Edit `frontend/src/pages/CustomerDashboard.jsx`:
- Modify product card layout
- Change category filters
- Customize cart UI

### Email Templates
Edit `backend/ems_automation.py`:
- Customize email HTML
- Modify subject lines
- Add company branding

### Procurement Rules
Edit `backend/customer_portal_api.py`:
- Adjust reorder quantity calculation
- Modify low stock threshold logic
- Add approval workflows

## 📊 Business Benefits

1. **Reduced Stockouts**: Automatic reordering prevents inventory gaps
2. **Faster Response**: Suppliers notified immediately when stock is low
3. **Better Customer Experience**: Real-time product availability
4. **Labor Savings**: Eliminates manual procurement emails
5. **Audit Trail**: Complete history of orders and procurement
6. **Scalability**: Handles growing product catalog and customer base

## 🔐 Security

- JWT authentication for customer orders
- Role-based access for procurement approval
- Input validation on all endpoints
- SQL injection prevention
- XSS protection in frontend

## 📈 Monitoring

Track these metrics:
- Orders per day
- Average cart value
- Procurement requests generated
- Stock turnover rate
- Supplier response time

## 🚧 Future Enhancements

- Multi-warehouse support
- Supplier portal for PO confirmation
- SMS notifications
- Payment gateway integration
- Product recommendations
- Loyalty program
- Bulk ordering discounts
- Scheduled deliveries

## 📞 Support

For issues or questions:
- Email: support@company.com
- Procurement Team: procurement@company.com
- Inventory Team: inventory@company.com

---

**Status**: ✅ Active and Production-Ready
**Last Updated**: February 6, 2026
