# AI Agent Logistics API Documentation

## Overview
The AI Agent Logistics API provides comprehensive automation for logistics operations including inventory management, order processing, procurement, and delivery tracking.

## Authentication
All endpoints (except public ones) require JWT authentication:

```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token
curl -X GET "http://localhost:8000/orders" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info
- `GET /auth/users` - List users (admin only)
- `POST /auth/register` - Register user (admin only)

### Orders Management
- `GET /orders` - Get orders (requires read:orders)
- `GET /orders/{order_id}` - Get specific order
- `POST /orders` - Create order (requires write:orders)

### Inventory Management
- `GET /inventory` - Get inventory status
- `GET /inventory/low-stock` - Get low stock items
- `PUT /inventory/{product_id}` - Update inventory

### Procurement
- `GET /procurement/purchase-orders` - Get purchase orders
- `GET /procurement/suppliers` - Get suppliers
- `POST /procurement/run` - Trigger procurement agent

### Delivery Tracking
- `GET /delivery/shipments` - Get shipments
- `GET /delivery/track/{tracking_number}` - Track shipment
- `GET /delivery/couriers` - Get couriers
- `POST /delivery/run` - Trigger delivery agent

### Dashboard & Analytics
- `GET /dashboard/kpis` - Get KPI metrics
- `GET /dashboard/alerts` - Get system alerts
- `GET /dashboard/activity` - Get recent activity

## Error Handling
All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Rate Limiting
- Development: 100 requests/minute
- Production: 30 requests/minute
- Burst: 10-20 requests

## Security
- JWT tokens expire in 30 minutes (15 in production)
- Refresh tokens expire in 7 days
- All passwords must meet complexity requirements
- Input validation and sanitization applied
