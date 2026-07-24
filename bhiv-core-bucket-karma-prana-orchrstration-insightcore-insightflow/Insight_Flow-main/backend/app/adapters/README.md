# KSML Adapter

The KSML (Knowledge Stream Message Language) Adapter provides standardized message format conversion for external system integration with InsightFlow.

## Overview

KSML is Core's standard message format that wraps InsightFlow data with metadata for reliable transmission and processing. The adapter handles:

- **Serialization**: Converting InsightFlow data to KSML format
- **Deserialization**: Converting KSML packets back to InsightFlow format
- **Validation**: Ensuring packet integrity and structure
- **Checksum**: Data integrity verification

## KSML Packet Structure

```json
{
  "meta": {
    "version": "1.0",
    "packet_type": "routing_request",
    "timestamp": "2025-01-15T10:30:00Z",
    "source": "insightflow",
    "destination": "core",
    "message_id": "msg-abc123def456",
    "checksum": "hash123"
  },
  "payload": {
    "data": {
      "input_data": {"text": "Hello world"},
      "input_type": "text",
      "strategy": "q_learning"
    }
  }
}
```

## Packet Types

- `routing_request`: Agent routing requests
- `routing_response`: Agent routing responses
- `feedback_log`: Feedback and performance data
- `metrics_update`: System metrics updates
- `health_check`: Health status information

## Usage Examples

### Basic Wrapping/Unwrapping

```python
from app.adapters.ksml_adapter import KSMLAdapter, KSMLPacketType

# Wrap data
data = {"input_data": {"text": "Hello"}, "input_type": "text"}
ksml_packet = KSMLAdapter.wrap(data, KSMLPacketType.ROUTING_REQUEST)

# Unwrap data
original_data = KSMLAdapter.unwrap(ksml_packet)
```

### Validation

```python
# Validate packet structure
is_valid = KSMLAdapter.validate_ksml_structure(ksml_packet)
```

### Bytes Conversion

```python
# Convert to bytes for transmission
ksml_bytes = KSMLAdapter.convert_to_ksml_bytes(data, KSMLPacketType.FEEDBACK_LOG)

# Convert from bytes
recovered_data = KSMLAdapter.convert_from_ksml_bytes(ksml_bytes)
```

### Service Integration

```python
from app.services.ksml_service import ksml_service

# Process KSML routing request
ksml_response = await ksml_service.process_routing_request(ksml_packet)

# Create metrics update
metrics_ksml = ksml_service.create_metrics_update(metrics_data)
```

## API Endpoints

### KSML Routing

```bash
POST /api/v1/routing/ksml/route
Content-Type: application/json

{
  "meta": {...},
  "payload": {
    "data": {
      "input_data": {"text": "Route this request"},
      "input_type": "text",
      "strategy": "q_learning"
    }
  }
}
```

### KSML Health Check

```bash
GET /health/ksml
```

## Error Handling

The adapter raises `KSMLFormatError` for:
- Invalid packet types
- Missing required fields
- Malformed packet structure
- Checksum mismatches (logged as warnings)

## Integration Points

1. **Routing Service**: Automatic KSML wrapping for responses
2. **WebSocket Events**: KSML format for real-time updates
3. **External APIs**: KSML endpoints for system integration
4. **Metrics Collection**: KSML format for analytics data

## Testing

Run the KSML adapter tests:

```bash
pytest tests/test_ksml_adapter.py -v
```

Run usage examples:

```bash
python examples/ksml_usage_example.py
```