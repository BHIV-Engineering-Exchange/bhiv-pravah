# API Migration Guide: v1 → v2

## Overview

InsightFlow now supports both API v1 (legacy) and v2 (Core-integrated) with backward compatibility during the transition period.

### Timeline

- **NOW**: Both versions working (backward compatible)
- **30 days**: Deprecation warnings for v1
- **60 days**: v1 endpoints removed

## Migration Steps

### Step 1: Update API Version in Client

**Before (v1):**
```python
# No version header
response = client.post("http://localhost:8000/api/v1/routing/route", json={...})
```

**After (v2):**
```python
headers = {"Accept-Version": "v2"}
response = client.post(
    "http://localhost:8000/api/v2/routing/route",
    json={...},
    headers=headers
)
```

### Step 2: Update Request Format

**v1 Format:**
```json
{
  "input_data": {"text": "Hello world"},
  "input_type": "text",
  "strategy": "q_learning"
}
```

**v2 Format (Enhanced):**
```json
{
  "input_data": {"text": "Hello world"},
  "input_type": "text",
  "strategy": "q_learning",
  "context": {
    "priority": "high",
    "domain": "customer_service"
  },
  "preferences": {
    "max_latency_ms": 500,
    "min_confidence": 0.8
  }
}
```

### Step 3: Handle Response Changes

**v1 Response:**
```json
{
  "agent_id": "uuid",
  "confidence_score": 0.85,
  "routing_reason": "Best match"
}
```

**v2 Response (Enhanced):**
```json
{
  "routing_decision": {
    "agent_id": "uuid",
    "agent_name": "NLP Processor",
    "confidence_score": 0.85,
    "routing_reason": "Q-learning optimal selection",
    "estimated_latency_ms": 150
  },
  "alternatives": [
    {
      "agent_id": "uuid2",
      "confidence_score": 0.78,
      "reason": "Secondary option"
    }
  ],
  "metadata": {
    "request_id": "req_123",
    "processing_time_ms": 12.5
  }
}
```

## Endpoint Mapping

| v1 Endpoint | v2 Endpoint | Status |
|-------------|-------------|---------|
| `POST /api/v1/routing/route` | `POST /api/v2/routing/route` | ✅ Available |
| `POST /api/v1/routing/feedback` | `POST /api/v2/routing/feedback` | ✅ Available |
| `GET /api/v1/agents/` | `GET /api/v2/agents/` | ✅ Available |
| `GET /api/v1/analytics/overview` | `GET /api/v2/analytics/overview` | ✅ Available |

## New v2 Features

### 1. KSML Format Support
```python
# KSML routing request
ksml_packet = {
    "meta": {
        "version": "1.0",
        "packet_type": "routing_request",
        "timestamp": "2024-01-01T00:00:00Z",
        "source": "client",
        "destination": "insightflow"
    },
    "payload": {
        "data": {
            "input_data": {"text": "Hello"},
            "input_type": "text"
        }
    }
}

response = client.post("/api/v2/routing/ksml/route", json=ksml_packet)
```

### 2. Enhanced Context Support
```python
# Rich context for better routing decisions
context = {
    "user_profile": {
        "experience_level": "expert",
        "preferred_language": "en"
    },
    "session_data": {
        "previous_agents": ["agent1", "agent2"],
        "conversation_history": 5
    },
    "business_context": {
        "department": "sales",
        "priority": "high"
    }
}
```

### 3. Batch Processing
```python
# Process multiple requests at once
batch_request = {
    "requests": [
        {"input_data": {"text": "Query 1"}, "input_type": "text"},
        {"input_data": {"text": "Query 2"}, "input_type": "text"}
    ],
    "strategy": "q_learning"
}

response = client.post("/api/v2/routing/batch", json=batch_request)
```

## Client Library Updates

### Python Client

**Install Updated Client:**
```bash
pip install insightflow-client>=2.0.0
```

**v1 Usage:**
```python
from insightflow import Client

client = Client("http://localhost:8000")
result = client.route({"text": "Hello"}, "text")
```

**v2 Usage:**
```python
from insightflow import ClientV2

client = ClientV2("http://localhost:8000", api_version="v2")
result = client.route(
    input_data={"text": "Hello"},
    input_type="text",
    context={"priority": "high"}
)
```

## Breaking Changes in v2

### 1. Response Structure
- Wrapped in `routing_decision` object
- Added `alternatives` array
- Enhanced `metadata` section

### 2. Error Handling
```json
// v1 Error
{
  "detail": "Agent not found"
}

// v2 Error (Enhanced)
{
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent not found",
    "details": {
      "agent_id": "uuid",
      "available_agents": ["uuid1", "uuid2"]
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123"
  }
}
```

### 3. Authentication
```python
# v2 requires explicit version header
headers = {
    "Authorization": "Bearer token",
    "Accept-Version": "v2",
    "Content-Type": "application/json"
}
```

## Testing Your Migration

### 1. Compatibility Test
```python
import requests

# Test v1 endpoint still works
v1_response = requests.post(
    "http://localhost:8000/api/v1/routing/route",
    json={"input_data": {"text": "test"}, "input_type": "text"}
)

# Test v2 endpoint
v2_response = requests.post(
    "http://localhost:8000/api/v2/routing/route",
    json={"input_data": {"text": "test"}, "input_type": "text"},
    headers={"Accept-Version": "v2"}
)

print(f"v1 status: {v1_response.status_code}")
print(f"v2 status: {v2_response.status_code}")
```

## Migration Checklist

- [ ] Update client library to v2
- [ ] Add version headers to requests
- [ ] Update response parsing logic
- [ ] Test all endpoints in staging
- [ ] Update error handling
- [ ] Monitor performance metrics
- [ ] Plan rollback strategy
- [ ] Train team on new features
- [ ] Update documentation
- [ ] Schedule v1 deprecation

---

**Migration Timeline**: Complete migration within 60 days to avoid service disruption.