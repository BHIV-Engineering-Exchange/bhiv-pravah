# STP (Structured Token Protocol) Implementation

## Overview

The STP (Structured Token Protocol) layer provides a standardized format for wrapping routing decisions and feedback packets in InsightFlow. This implementation ensures interoperability with external systems while maintaining full backward compatibility with existing endpoints.

## Features

- **Lightweight Wrapping**: Minimal overhead STP packet format
- **Non-blocking Operations**: Async support for high performance
- **Checksum Verification**: Data integrity validation
- **Backward Compatibility**: Graceful fallback for non-STP systems
- **Priority-based Routing**: Automatic priority determination
- **Comprehensive Metrics**: Detailed operation tracking

## STP Packet Format

```json
{
    "stp_version": "1.0",
    "stp_token": "stp-abc123def456",
    "stp_timestamp": "2025-01-08T09:00:00.000Z",
    "stp_type": "routing_decision" | "feedback_packet" | "health_check",
    "stp_metadata": {
        "source": "insightflow",
        "destination": "sovereign_core",
        "priority": "normal" | "high" | "critical",
        "requires_ack": true | false
    },
    "payload": {
        // Original JSON data
    },
    "stp_checksum": "hash_value"
}
```

## Configuration

### Environment Variables

```bash
# STP Layer Configuration
STP_ENABLED=True                    # Enable/disable STP wrapping
STP_DEFAULT_DESTINATION=sovereign_core  # Default target system
STP_DEFAULT_PRIORITY=normal         # Default packet priority
STP_REQUIRE_CHECKSUM=True          # Enable checksum verification
```

### Application Settings

```python
# In app/core/config.py
STP_ENABLED: bool = True
STP_DEFAULT_DESTINATION: str = "sovereign_core"
STP_DEFAULT_PRIORITY: str = "normal"
STP_REQUIRE_CHECKSUM: bool = True
```

## Usage

### Basic STP Middleware

```python
from app.middleware.stp_middleware import get_stp_middleware, STPPacketType

# Get middleware instance
stp_middleware = get_stp_middleware(enable_stp=True)

# Wrap data
wrapped = stp_middleware.wrap(
    payload={"agent_id": "test", "confidence": 0.8},
    packet_type=STPPacketType.ROUTING_DECISION.value,
    priority="high"
)

# Unwrap data
payload, metadata = stp_middleware.unwrap(wrapped)
```

### STP Service (Recommended)

```python
from app.services.stp_service import get_stp_service

# Get service instance
stp_service = get_stp_service()

# Wrap routing decision (automatic priority)
wrapped = await stp_service.wrap_routing_decision(
    routing_decision=decision_data,
    requires_ack=True
)

# Wrap feedback packet
wrapped = await stp_service.wrap_feedback_packet(
    feedback_data=feedback,
    priority="critical"
)

# Wrap health check
wrapped = await stp_service.wrap_health_check(health_data)
```

## Integration Points

### 1. Decision Engine Integration

The STP service is automatically integrated into the decision engine:

```python
# In app/services/decision_engine.py
routing_decision = {
    "request_id": request_id,
    "agent_id": agent_id,
    # ... other fields
}

# Automatically wrapped in STP format if enabled
wrapped_decision = await self.stp_service.wrap_routing_decision(
    routing_decision=routing_decision,
    requires_ack=context.get("requires_ack", False)
)
```

### 2. API Endpoint Integration

#### V2 Routing Endpoint

```python
# Optional STP wrapping via header
# Request: X-STP-Format: true
if http_request.headers.get("X-STP-Format", "false").lower() == "true":
    wrapped_response = await stp_service.wrap_routing_decision(response)
    return wrapped_response
```

#### Health Check Endpoint

```python
# Automatic STP wrapping for health checks
wrapped_health = await stp_service.wrap_health_check(health_data)
return wrapped_health
```

### 3. Feedback Processing

```python
# Feedback automatically wrapped for external systems
wrapped_feedback = await self.stp_service.wrap_feedback_packet(
    feedback_data=feedback_record,
    requires_ack=True
)
```

## Priority Determination

The STP service automatically determines packet priorities based on content:

### Routing Decisions
- **HIGH**: Confidence score ≥ 0.9
- **CRITICAL**: Confidence score ≤ 0.3
- **NORMAL**: All other cases

### Feedback Packets
- **CRITICAL**: Failed requests OR latency > 5000ms
- **HIGH**: Latency > 1000ms
- **NORMAL**: Successful requests with good performance

### Health Checks
- **CRITICAL**: Status = "unhealthy"
- **HIGH**: Status = "degraded"
- **NORMAL**: Status = "healthy"

## API Endpoints

### STP Metrics
```
GET /api/stp/metrics
```

Response:
```json
{
    "stp_metrics": {
        "enabled": true,
        "packets_wrapped": 1250,
        "packets_unwrapped": 890,
        "errors": 2,
        "checksum_failures": 0
    },
    "timestamp": "2025-01-08T09:00:00.000Z"
}
```

### STP Packet Unwrapping
```
POST /api/stp/unwrap
```

Request:
```json
{
    "stp_version": "1.0",
    "stp_token": "stp-abc123",
    "payload": {...},
    // ... other STP fields
}
```

Response:
```json
{
    "success": true,
    "payload": {...},
    "metadata": {
        "stp_token": "stp-abc123",
        "stp_type": "routing_decision",
        // ... other metadata
    }
}
```

## Backward Compatibility

### Graceful Degradation

1. **STP Disabled**: When `STP_ENABLED=False`, all operations pass through unchanged
2. **Error Fallback**: If STP wrapping fails, original data is returned
3. **Header-based**: V2 endpoints only wrap when `X-STP-Format: true` header is present

### Migration Strategy

1. **Phase 1**: Deploy with `STP_ENABLED=False` (pass-through mode)
2. **Phase 2**: Enable STP with `STP_ENABLED=True` for internal testing
3. **Phase 3**: External systems request STP format via headers
4. **Phase 4**: Full STP adoption

## Error Handling

### Middleware Level
- Invalid packet types raise `STPLayerError`
- Checksum mismatches log warnings but continue processing
- Missing fields raise `STPLayerError`

### Service Level
- Wrapping errors fall back to original data
- Unwrapping errors return original packet as payload
- All errors are logged for monitoring

### Application Level
- STP failures don't break existing functionality
- Metrics track error rates for monitoring
- Health checks include STP service status

## Testing

### Unit Tests
```bash
# Run STP middleware tests
pytest tests/test_stp_middleware.py -v

# Run STP service tests
pytest tests/test_stp_service.py -v
```

### Integration Tests
```python
# Test STP integration in routing
response = client.post(
    "/api/v2/routing/route",
    headers={"X-STP-Format": "true"},
    json=routing_request
)
assert "stp_token" in response.json()
```

## Monitoring

### Metrics to Monitor
- `packets_wrapped`: Total STP packets created
- `packets_unwrapped`: Total STP packets processed
- `errors`: STP operation failures
- `checksum_failures`: Data integrity issues

### Health Checks
- STP service initialization status
- Middleware operation success rates
- Error rate thresholds

### Logging
- Debug: Individual packet operations
- Info: Service initialization and configuration
- Warning: Checksum mismatches and fallbacks
- Error: Critical STP failures

## Performance Considerations

### Overhead
- Minimal JSON structure overhead (~200 bytes)
- Checksum calculation: O(n) where n = payload size
- Token generation: O(1) hash operation

### Optimization
- Async operations prevent blocking
- Pass-through mode for disabled STP
- Lazy initialization of services
- Efficient JSON serialization

### Scalability
- Stateless design for horizontal scaling
- No persistent storage requirements
- Thread-safe operations
- Memory-efficient implementation

## Security

### Data Integrity
- SHA-256 checksums for payload verification
- Timestamp validation for replay protection
- Token uniqueness for tracking

### Access Control
- STP wrapping respects existing authentication
- No additional security layers required
- Transparent to existing security measures

## Future Enhancements

### Planned Features
1. **Acknowledgment System**: Track packet delivery confirmations
2. **Compression**: Optional payload compression for large packets
3. **Encryption**: Optional payload encryption for sensitive data
4. **Routing**: Multi-destination packet routing
5. **Batching**: Batch multiple packets for efficiency

### Extension Points
- Custom packet types via enum extension
- Pluggable checksum algorithms
- Custom metadata fields
- External destination adapters

## Troubleshooting

### Common Issues

1. **STP Not Working**
   - Check `STP_ENABLED=True` in configuration
   - Verify service initialization in logs
   - Test with `/api/stp/metrics` endpoint

2. **Checksum Failures**
   - Check for data corruption in transit
   - Verify JSON serialization consistency
   - Monitor `checksum_failures` metric

3. **Performance Issues**
   - Monitor STP operation latency
   - Consider disabling checksums if not needed
   - Use pass-through mode for high-throughput scenarios

### Debug Commands

```bash
# Check STP configuration
curl http://localhost:8000/api/stp/metrics

# Test packet unwrapping
curl -X POST http://localhost:8000/api/stp/unwrap \
  -H "Content-Type: application/json" \
  -d '{"stp_version":"1.0","stp_token":"test","payload":{}}'

# Monitor STP in routing
curl -X POST http://localhost:8000/api/v2/routing/route \
  -H "X-STP-Format: true" \
  -H "Content-Type: application/json" \
  -d '{"input_data":{"text":"test"},"input_type":"text"}'
```

## Conclusion

The STP implementation provides a robust, backward-compatible protocol layer for InsightFlow that enables seamless integration with external systems while maintaining the integrity and performance of existing functionality. The modular design allows for gradual adoption and easy maintenance.