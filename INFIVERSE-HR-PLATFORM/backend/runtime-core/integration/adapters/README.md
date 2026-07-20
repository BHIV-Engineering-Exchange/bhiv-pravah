# Integration Adapters

This directory contains the pluggable adapter layer for external system integrations. All adapters follow the same interface and are designed to be optional and fail-safe.

## Available Adapters

### 1. Artha Adapter
- Handles payroll and finance integrations
- Processes events related to payroll, salary, and finance actions

### 2. Karya Adapter
- Handles task and workflow integrations
- Processes events related to tasks, workflows, and approvals

### 3. InsightFlow Adapter
- Handles analytics and metrics collection
- Processes all events for analytics purposes

### 4. Bucket Adapter
- Handles storage and artifact management
- Processes events for file/document storage and log archival

## Architecture

All adapters inherit from `BaseIntegrationAdapter` which ensures:

- **Optional**: System works without any adapters
- **Pluggable**: Can be enabled/disabled via configuration
- **Fail-safe**: If an adapter fails, it doesn't break the main system

## Usage

To use an adapter:

```python
from integration.adapters import ArthaAdapter

# Configure the adapter
config = {
    "name": "Artha Adapter",
    "enabled": True,
    "artha_api_url": "https://artha-api.example.com",
    "artha_api_key": "your-key"
}

# Initialize adapter
adapter = ArthaAdapter(config)

# Execute with an event
event = {
    "event_id": "evt_123",
    "action": "payroll_processed",
    "tenant_id": "tenant_abc",
    "user_id": "user_123",
    "timestamp": "2026-01-10T17:00:00Z"
}

result = adapter.execute(event)
```

## Configuration

All adapters can be configured via environment variables or configuration files. Each adapter can be enabled/disabled independently.

## Adding New Adapters

To add a new adapter:

1. Create a new class inheriting from `BaseIntegrationAdapter`
2. Implement the `_execute_internal` method
3. Add the adapter to the `__init__.py` exports if needed

## Status

All 4 required adapters have been implemented as per Task 8 requirements:

- [x] Base adapter framework
- [x] Artha adapter
- [x] Karya adapter
- [x] InsightFlow adapter
- [x] Bucket adapter