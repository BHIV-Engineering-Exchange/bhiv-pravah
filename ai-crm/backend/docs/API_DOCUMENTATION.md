# AI Agent Logistics System - API Documentation

## Overview
The AI Agent Logistics System provides RESTful APIs for managing orders, returns, restocks, and agent operations.

**Base URL**: `http://localhost:8000`
**API Version**: v1.0

## Authentication
Currently, the API uses basic authentication. In production, JWT tokens are recommended.

## Endpoints

### Health Check
```
GET /health
```
Returns system health status.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

### Orders

#### Get All Orders
```
GET /get_orders
```
Retrieve all orders from the system.

**Response**:
```json
{
  "count": 5,
  "orders": [
    {
      "OrderID": 101,
      "CustomerID": "CUST001",
      "ProductID": "A101",
      "Status": "Shipped",
      "OrderDate": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### Get Order by ID
```
GET /orders/{order_id}
```
Retrieve a specific order by ID.

**Parameters**:
- `order_id` (integer): The order ID

**Response**:
```json
{
  "OrderID": 101,
  "CustomerID": "CUST001",
  "ProductID": "A101",
  "Status": "Shipped",
  "OrderDate": "2025-01-01T10:00:00Z"
}
```

### Returns

#### Get All Returns
```
GET /get_returns
```
Retrieve all product returns.

**Response**:
```json
{
  "count": 10,
  "returns": [
    {
      "ProductID": "A101",
      "ReturnQuantity": 2,
      "ReturnDate": "2025-01-01T14:00:00Z",
      "Reason": "Defective"
    }
  ]
}
```

### Restocks

#### Get Restock Requests
```
GET /get_restocks
```
Retrieve all restock requests.

**Response**:
```json
{
  "count": 3,
  "restocks": [
    {
      "ProductID": "A101",
      "RestockQuantity": 10,
      "RequestDate": "2025-01-01T15:00:00Z",
      "Status": "Pending"
    }
  ]
}
```

#### Create Restock Request
```
POST /restocks
```
Create a new restock request.

**Request Body**:
```json
{
  "ProductID": "A101",
  "RestockQuantity": 10,
  "Priority": "high"
}
```

### Agent Operations

#### Run Agent Cycle
```
POST /run_agent
```
Manually trigger an agent processing cycle.

**Response**:
```json
{
  "status": "completed",
  "processed_returns": 5,
  "created_restocks": 2,
  "execution_time": 1.23
}
```

#### Get Agent Logs
```
GET /agent_logs
```
Retrieve agent activity logs.

**Query Parameters**:
- `limit` (integer, optional): Number of logs to return (default: 100)
- `since` (string, optional): ISO timestamp to filter logs from

### Chatbot

#### Chat Query
```
POST /chat
```
Send a query to the chatbot.

**Request Body**:
```json
{
  "message": "Where is my order #101?"
}
```

**Response**:
```json
{
  "response": "📦 Your order #101 is: Shipped.",
  "confidence": 0.95,
  "escalated": false
}
```

### Human Review

#### Get Pending Reviews
```
GET /reviews/pending
```
Get all pending human reviews.

**Response**:
```json
{
  "count": 2,
  "reviews": [
    {
      "review_id": "restock_20250101_120000",
      "action_type": "restock",
      "confidence": 0.45,
      "data": {
        "ProductID": "X999",
        "quantity": 50
      },
      "agent_decision": "High quantity restock",
      "status": "pending"
    }
  ]
}
```

#### Approve/Reject Review
```
POST /reviews/{review_id}/approve
POST /reviews/{review_id}/reject
```

**Request Body**:
```json
{
  "notes": "Approved after supplier confirmation"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

Error responses include details:
```json
{
  "error": "Order not found",
  "code": "ORDER_NOT_FOUND",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Rate Limiting
API requests are limited to 100 requests per minute per IP address.

## WebSocket Support
Real-time updates are available via WebSocket at `/ws`.

## SDK and Examples
Python SDK and usage examples are available in the `/examples` directory.
