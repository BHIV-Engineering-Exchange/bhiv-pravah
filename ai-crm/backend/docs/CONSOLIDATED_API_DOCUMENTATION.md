# Consolidated API Documentation - AI Agent Logistics + CRM + Infiverse

## Overview

This document provides a comprehensive reference for all APIs in the unified AI Agent Logistics + CRM + Infiverse system.

**Base URL**: `http://localhost:8000` (Unified API - Logistics + CRM + Infiverse)
**API Version**: v1.0

**Note**: All Infiverse endpoints are now proxied through the unified API at `/api/*`. The Complete-Infiverse server should be running on `INFIVERSE_BASE_URL` (default: `http://localhost:5000`).

## Module Grouping

### 1. Logistics Module
- Order management
- Inventory tracking
- Returns processing
- Procurement automation
- Delivery tracking

### 2. CRM Module
- Account management
- Contact management
- Lead management
- Opportunity management
- Activity tracking
- Task management
- Visit tracking

### 3. Infiverse Module
- Employee monitoring
- Task management
- Attendance tracking
- Alert management
- Consent management
- AI insights

## Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

## Endpoint Summary Table

| Module | Endpoint | Method | Description | Authentication |
|--------|----------|--------|-------------|----------------|
| **Auth** | `/auth/login` | POST | User login | None |
| | `/auth/register` | POST | User registration | Admin |
| | `/auth/me` | GET | Get current user | Required |
| | `/auth/users` | GET | List users | Admin |
| **Logistics** | `/orders` | GET | Get orders | Required |
| | `/orders/{id}` | GET | Get order by ID | Required |
| | `/returns` | GET | Get returns | Required |
| | `/restock-requests` | GET | Get restock requests | Required |
| | `/inventory` | GET | Get inventory | Required |
| | `/procurement/purchase-orders` | GET | Get purchase orders | Required |
| | `/delivery/shipments` | GET | Get shipments | Required |
| **CRM** | `/api/accounts` | GET/POST | Account management | Required |
| | `/api/contacts` | GET/POST | Contact management | Required |
| | `/api/leads` | GET/POST | Lead management | Required |
| | `/api/opportunities` | GET/POST | Opportunity management | Required |
| | `/api/activities` | GET/POST | Activity management | Required |
| | `/api/tasks` | GET/POST | Task management | Required |
| | `/api/visits` | GET/POST | Visit tracking | Required |
| **Infiverse** | `/api/auth/register` | POST | Infiverse user registration | None |
| | `/api/auth/login` | POST | Infiverse login | None |
| | `/api/tasks` | GET/POST | Infiverse task management | Required |
| | `/api/tasks/{id}` | GET/PUT/DELETE | Task CRUD operations | Required |
| | `/api/monitoring/start/{id}` | POST | Start monitoring | Admin |
| | `/api/monitoring/stop/{id}` | POST | Stop monitoring | Admin |
| | `/api/monitoring/alerts` | GET | Get alerts | Required |
| | `/api/attendance/{path}` | GET/POST | Attendance management | Required |
| | `/api/consent` | POST | Update consent | Required |
| | `/api/alerts` | GET | Get user alerts | Required |
| | `/api/notifications/broadcast-reminders` | POST | Broadcast task reminders | Admin |
| | `/api/notifications/broadcast-aim-reminders` | POST | Broadcast aim reminders | Admin |
| | `/api/departments` | GET | Get departments | Required |
| | `/api/ai/insights` | GET | Get AI insights | Required |

## Sample API Workflows

### 1. Simulate Alert Workflow

**Scenario**: Monitor employee activity and generate alerts for policy violations

```bash
# 1. Start monitoring session for employee
curl -X POST "http://localhost:8000/api/monitoring/start/employee_123" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json"

# 2. System detects unauthorized website visit
# Alert is automatically generated in Complete-Infiverse

# 3. Get alerts for employee
curl -X GET "http://localhost:8000/api/monitoring/alerts?employeeId=employee_123" \
  -H "Authorization: Bearer <admin_token>"

# Expected Response:
{
  "alerts": [
    {
      "alert_type": "unauthorized_website",
      "severity": "high",
      "title": "Unauthorized Website Access",
      "description": "Employee visited social media during work hours",
      "status": "active",
      "data": {
        "url": "https://facebook.com",
        "timestamp": "2024-01-15T14:30:00Z"
      }
    }
  ]
}
```

### 2. Fetch Report Workflow

**Scenario**: Generate productivity report for management

```bash
# 1. Get AI insights
curl -X GET "http://localhost:8000/api/ai/insights" \
  -H "Authorization: Bearer <manager_token>"

# Expected Response:
{
  "insights": [
    {
      "title": "Team Productivity Analysis",
      "description": "Engineering team productivity is 15% above average this week",
      "impact": "high",
      "suggestions": ["Continue current practices", "Share productivity tips"]
    }
  ]
}

# 2. Get attendance data
curl -X GET "http://localhost:8000/api/attendance/user/employee_123?startDate=2024-01-01&endDate=2024-01-31" \
  -H "Authorization: Bearer <manager_token>"

# 3. Get task completion data
curl -X GET "http://localhost:8000/api/tasks?assignee=employee_123" \
  -H "Authorization: Bearer <manager_token>"
```

### 3. Trigger Task Workflow

**Scenario**: Create and assign a new task through the system

```bash
# 1. Create new task
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer <manager_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete API Documentation",
    "description": "Write comprehensive API documentation for the new endpoints",
    "status": "Pending",
    "priority": "High",
    "department": "Engineering",
    "assignee": "employee_123",
    "dueDate": "2024-01-20T17:00:00Z"
  }'

# Expected Response:
{
  "id": "task_12345",
  "title": "Complete API Documentation",
  "status": "Pending",
  "assignee": "employee_123",
  "createdAt": "2024-01-15T10:00:00Z"
}

# 2. Start workday (attendance)
curl -X POST "http://localhost:8000/api/attendance/start-day/employee_123" \
  -H "Authorization: Bearer <employee_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 19.0760,
    "longitude": 72.8777,
    "workFromHome": false
  }'

# 3. Update task status
curl -X PUT "http://localhost:8000/api/tasks/task_12345" \
  -H "Authorization: Bearer <employee_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "In Progress"
  }'
```

## Postman Collection

### Collection Structure
```
AI Agent Unified API
├── Auth
│   ├── Login
│   ├── Register
│   └── Get Profile
├── Logistics
│   ├── Orders
│   ├── Inventory
│   └── Procurement
├── CRM
│   ├── Accounts
│   ├── Leads
│   ├── Opportunities
│   └── Activities
<<<<<<< HEAD
├── Infiverse
│   ├── Monitoring
│   ├── Tasks
│   ├── Attendance
│   └── Alerts
└── Sample Workflows
    ├── Simulate Alert Workflow
    ├── Fetch Report Workflow
    └── Trigger Task Workflow
```

### Download and Import
1. **Download**: [AI_Agent_Unified_API.postman_collection.json](AI_Agent_Unified_API.postman_collection.json)
2. **Import into Postman**: File → Import → Select the downloaded JSON file
3. **Set Variables**: 
   - `base_url`: `http://localhost:8000` (or your deployment URL)
   - `crm_base_url`: `http://localhost:8001`
4. **Authentication**: Use the Login request to get a token, which will be automatically set for other requests

### Quick Start
1. Run "Authentication → Login" to get your auth token
2. Try "System Health & Monitoring → Health Check" to verify system status
3. Explore different modules (Logistics, CRM, Infiverse) based on your needs

=======
└── Infiverse
    ├── Monitoring
    ├── Tasks
    ├── Attendance
    └── Alerts
```

>>>>>>> 9a5d7abfa61aa2769341197651d91d368bfed338
### Sample Postman Request
```json
{
  "info": {
    "name": "AI Agent Unified API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Login",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"email\": \"admin@example.com\", \"password\": \"password\"}"
        },
        "url": {
          "raw": "{{base_url}}/auth/login",
          "host": ["{{base_url}}"],
          "path": ["auth", "login"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "token",
      "value": ""
    }
  ]
}
```

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

## Rate Limiting

- API requests limited to 100 requests per minute per IP
- Auth endpoints: 10 requests per minute
- File upload endpoints: 20 requests per hour

## WebSocket Support

Real-time updates available via WebSocket at `/ws` for:
- Live monitoring data
- Alert notifications
- Task updates
- Attendance changes