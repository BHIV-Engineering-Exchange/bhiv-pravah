# Routing Decision Logging Integration

This document describes the integration of routing decision logging into the InsightFlow system.

## Overview

The routing decision logger captures detailed information about every routing decision made by the system, providing comprehensive audit trails and analytics capabilities.

## Integration Points

### 1. Route-Agent Endpoint (`/api/v1/routing/route-agent`)

The main routing endpoint now includes:
- **Timing measurement**: Tracks response time for each request
- **Decision logging**: Logs all routing decisions with detailed breakdowns
- **Score tracking**: Records confidence scores and component breakdowns

### 2. Admin API Endpoints (`/admin/*`)

New admin endpoints for monitoring and management:
- `GET /admin/routing-logs` - Query routing decision logs
- `GET /admin/routing-statistics` - Get routing statistics
- `POST /admin/cleanup-logs` - Clean up old logs
- `GET /admin/system-health` - System health check

### 3. Public Endpoints (Legacy)

Existing endpoints for backward compatibility:
- `GET /api/routing/decisions` - Get routing decisions (no auth)
- `GET /api/routing/statistics` - Get statistics (no auth)

## Logged Information

Each routing decision logs:

```json
{
  "timestamp": "2025-01-21T10:00:00.123Z",
  "request_id": "req-abc123",
  "agent_selected": "nlp-001",
  "confidence_score": 0.87,
  "score_breakdown": {
    "rule_based": 0.8,
    "feedback": 0.9,
    "availability": 1.0
  },
  "alternatives": ["nlp-002", "nlp-003"],
  "context_summary": "nlp_task, priority=normal",
  "decision_reasoning": "Best match based on weighted scores",
  "response_time_ms": 45.2
}
```

## Usage Examples

### Making a Routing Request

```bash
curl -X POST http://localhost:8000/api/v1/routing/route-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "nlp",
    "context": {"priority": "high"},
    "confidence_threshold": 0.7,
    "request_id": "my-request-123"
  }'
```

### Querying Logs

```bash
# Get recent decisions
curl http://localhost:8000/api/routing/decisions?limit=10

# Get statistics
curl http://localhost:8000/api/routing/statistics

# Admin endpoints (require authentication)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/admin/routing-logs?agent_id=nlp-001
```

## Testing Integration

Run the integration test:

```bash
cd backend
python examples/test_integration.py
```

This will:
1. Make a routing request
2. Verify the decision was logged
3. Check statistics are updated
4. Test admin endpoint protection

## Configuration

Logging configuration in `.env`:

```bash
# Routing Decision Logging
ROUTING_LOG_DIR=logs
ROUTING_LOG_RETENTION_DAYS=30
```

## File Structure

```
logs/
└── routing_decisions.jsonl    # JSON Lines format log file

app/
├── api/routes/admin.py        # Admin API endpoints
├── utils/routing_decision_logger.py  # Logger implementation
└── routers/routing.py         # Enhanced route-agent endpoint
```

## Monitoring

The system provides multiple ways to monitor routing decisions:

1. **Real-time**: Check recent decisions via API
2. **Analytics**: Use statistics endpoints for trends
3. **Health**: Monitor system health via admin endpoints
4. **Logs**: Direct access to JSON Lines log files

## Maintenance

- **Automatic cleanup**: Old logs are cleaned based on retention period
- **Manual cleanup**: Use `/admin/cleanup-logs` endpoint
- **Log rotation**: Handled automatically by the logger
- **Storage**: Logs stored in configurable directory