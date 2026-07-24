# Admin API Documentation

The Admin API provides endpoints for monitoring, logging, and system management in InsightFlow.

## Authentication

All admin endpoints require authentication via JWT token:

```bash
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### GET /admin/routing-logs

Get routing decision logs with optional filtering.

**Query Parameters:**
- `agent_id` (optional): Filter by specific agent ID
- `date_from` (optional): Start date in ISO format (e.g., 2025-01-21T00:00:00Z)
- `date_to` (optional): End date in ISO format
- `limit` (optional): Maximum results (1-1000, default: 100)

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/admin/routing-logs?agent_id=nlp-001&limit=50"
```

### GET /admin/routing-statistics

Get routing decision statistics.

**Query Parameters:**
- `agent_id` (optional): Filter by specific agent ID

### POST /admin/cleanup-logs

Clean up routing logs older than retention period (30 days).

### GET /admin/system-health

Get comprehensive system health status.

## Integration

The admin endpoints integrate with:
- Existing authentication system
- Routing decision logger
- Feedback service
- Scoring engine
- System health monitoring