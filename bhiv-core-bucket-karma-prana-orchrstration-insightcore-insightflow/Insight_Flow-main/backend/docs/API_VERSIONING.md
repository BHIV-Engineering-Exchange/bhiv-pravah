# API Versioning Strategy

## Overview

InsightFlow implements a comprehensive API versioning strategy to ensure backward compatibility while enabling continuous improvement and feature development.

## Versioning Approach

### Version Detection

API version is detected through multiple methods (in order of priority):

1. **Accept-Version Header** (Recommended)
   ```http
   Accept-Version: v2
   ```

2. **URL Path Version**
   ```
   /api/v1/routing/route
   /api/v2/routing/route
   ```

3. **Default Version**
   - Falls back to v1 for backward compatibility

### Supported Versions

| Version | Status | Description | Removal Date |
|---------|--------|-------------|--------------|
| v1 | Deprecated | Legacy format | 60 days |
| v2 | Active | Enhanced with new features | N/A |

## Version Differences

### Request Format

**v1 Request:**
```json
{
  "input_data": {"text": "Hello"},
  "input_type": "text",
  "strategy": "q_learning",
  "context": {}
}
```

**v2 Request (Enhanced):**
```json
{
  "input_data": {"text": "Hello"},
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

### Response Format

**v1 Response:**
```json
{
  "agent_id": "uuid",
  "agent_name": "NLP Processor",
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
    "processing_time_ms": 12.5,
    "api_version": "v2"
  }
}
```

## New Features in v2

### 1. Enhanced Context Support
- Rich user profiles
- Session data tracking
- Business context integration

### 2. Alternative Agents
- Multiple routing options
- Fallback recommendations
- Performance comparisons

### 3. Batch Processing
```json
{
  "requests": [
    {"input_data": {"text": "Query 1"}, "input_type": "text"},
    {"input_data": {"text": "Query 2"}, "input_type": "text"}
  ],
  "strategy": "q_learning"
}
```

### 4. KSML Format Support
- Knowledge Stream Message Language
- External system integration
- Structured message format

### 5. Enhanced Error Handling
```json
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

## Migration Timeline

### Phase 1: Dual Support (Current)
- Both v1 and v2 available
- Backward compatibility maintained
- Migration tracking enabled

### Phase 2: Deprecation Warnings (30 days)
- v1 endpoints return deprecation headers
- Migration analytics available
- User notifications sent

### Phase 3: v1 Removal (60 days)
- v1 endpoints return 410 Gone
- All traffic redirected to v2
- Migration complete

## Implementation Details

### Version Detection Middleware

```python
from app.api.middleware.version_detector import detect_api_version

@app.middleware("http")
async def version_middleware(request: Request, call_next):
    version = detect_api_version(request)
    request.state.api_version = version
    
    response = await call_next(request)
    response.headers["X-API-Version"] = version
    
    return response
```

### Response Headers

All API responses include version information:

```http
X-API-Version: v2
X-Deprecation-Warning: API v1 is deprecated (if applicable)
```

### Migration Tracking

Usage statistics are automatically tracked:

```python
await migration_service.track_api_usage(
    user_id=user_id,
    api_version=version,
    endpoint=endpoint
)
```

## Client Implementation

### Python Client

```python
# v1 Client
from insightflow import Client
client = Client("http://localhost:8000")

# v2 Client
from insightflow import ClientV2
client = ClientV2("http://localhost:8000", api_version="v2")
```

### JavaScript Client

```javascript
// v1 Client
import { InsightFlowClient } from '@insightflow/client';
const client = new InsightFlowClient('http://localhost:8000');

// v2 Client
import { InsightFlowClientV2 } from '@insightflow/client';
const client = new InsightFlowClientV2({
  baseUrl: 'http://localhost:8000',
  apiVersion: 'v2'
});
```

## Testing Strategy

### Compatibility Testing

```python
def test_version_compatibility():
    # Test v1 endpoint
    v1_response = client.post("/api/v1/routing/route", json=request_data)
    
    # Test v2 endpoint
    v2_response = client.post(
        "/api/v2/routing/route", 
        json=request_data,
        headers={"Accept-Version": "v2"}
    )
    
    assert v1_response.status_code == 200
    assert v2_response.status_code == 200
```

### Migration Testing

```python
def test_migration_conversion():
    v1_request = {"input_data": {"text": "test"}, "input_type": "text"}
    
    # Convert to v2 format
    v2_request = migration_service.convert_v1_to_v2_request(v1_request)
    
    # Verify conversion
    assert "preferences" in v2_request
    assert v2_request["context"]["migrated_from_v1"] == True
```

## Monitoring & Analytics

### Migration Dashboard

Track migration progress through:

- `/api/migration/status` - Individual user progress
- `/api/migration/analytics` - System-wide statistics
- `/api/migration/guide` - Migration resources

### Key Metrics

- API version usage distribution
- User migration percentage
- Endpoint compatibility issues
- Error rates by version

## Best Practices

### For API Consumers

1. **Use Version Headers**
   ```http
   Accept-Version: v2
   ```

2. **Handle Both Formats**
   ```python
   if response.headers.get("X-API-Version") == "v2":
       # Handle v2 response format
       decision = response["routing_decision"]
   else:
       # Handle v1 response format
       decision = response
   ```

3. **Monitor Deprecation Warnings**
   ```python
   warning = response.headers.get("X-Deprecation-Warning")
   if warning:
       logger.warning(f"API Deprecation: {warning}")
   ```

### For API Providers

1. **Maintain Backward Compatibility**
2. **Provide Clear Migration Paths**
3. **Track Usage Analytics**
4. **Communicate Changes Early**

## Support & Resources

- **Migration Guide**: `/docs/MIGRATION_GUIDE.md`
- **API Documentation**: `/docs`
- **Migration Status**: `/api/migration/status`
- **Support Email**: support@insightflow.ai

---

**Note**: This versioning strategy ensures smooth transitions while enabling continuous innovation in the InsightFlow platform.