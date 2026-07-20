# Integration Adapters Documentation

## Overview
The BHIV Application Framework includes a pluggable adapter system that enables integration with external systems while maintaining the core platform's independence. All adapters follow the same interface and are designed to be optional, pluggable, and fail-safe.

## Architecture

### Base Adapter Pattern
All adapters inherit from the `BaseIntegrationAdapter` class, which provides:

- **Optional**: System works without any adapters
- **Pluggable**: Can be enabled/disabled via configuration
- **Fail-safe**: If an adapter fails, it doesn't break the main system
- **Standardized Interface**: Consistent interface across all adapters

### Adapter Lifecycle
1. **Initialization**: Adapters are initialized with configuration parameters
2. **Execution**: Adapters receive events and process them accordingly
3. **Error Handling**: All errors are caught and logged without affecting the main system
4. **Result Processing**: Results are returned to the calling system

## Available Adapters

### 1. Artha Adapter
**Purpose**: Payroll and finance system integration  
**Namespace**: `artha`  
**Functionality**:
- Handles payroll data synchronization
- Processes salary-related events
- Integrates with finance systems
- Logs financial transactions

**Configuration Example**:
```python
{
    "name": "Artha Adapter",
    "enabled": True,
    "artha_api_url": "https://artha-api.example.com",
    "artha_api_key": "your-key"
}
```

**Events Processed**:
- `payroll_processed`
- `salary_updated`
- `finance_transaction`

### 2. Karya Adapter
**Purpose**: Task and workflow management integration  
**Namespace**: `karya`  
**Functionality**:
- Handles task creation and updates
- Manages workflow state changes
- Processes approval events
- Integrates with workflow engines

**Configuration Example**:
```python
{
    "name": "Karya Adapter",
    "enabled": True,
    "karya_api_url": "https://karya-api.example.com",
    "karya_api_key": "your-key"
}
```

**Events Processed**:
- `task_created`
- `workflow_started`
- `approval_granted`
- `task_completed`

### 3. InsightFlow Adapter
**Purpose**: Analytics and metrics collection  
**Namespace**: `insightflow`  
**Functionality**:
- Collects system metrics
- Processes analytical data
- Generates insights from events
- Integrates with analytics platforms

**Configuration Example**:
```python
{
    "name": "InsightFlow Adapter",
    "enabled": True,
    "insightflow_api_url": "https://insightflow-api.example.com",
    "insightflow_api_key": "your-key"
}
```

**Events Processed**:
- `metric_collected`
- `analytics_processed`
- `insight_generated`
- `performance_data`

### 4. Bucket Adapter
**Purpose**: Storage and artifact management  
**Namespace**: `bucket`  
**Functionality**:
- Manages file and document storage
- Handles artifact archiving
- Processes storage events
- Integrates with cloud storage

**Configuration Example**:
```python
{
    "name": "Bucket Adapter",
    "enabled": True,
    "bucket_api_url": "https://bucket-api.example.com",
    "bucket_api_key": "your-key"
}
```

**Events Processed**:
- `file_uploaded`
- `document_stored`
- `artifact_archived`
- `storage_cleanup`

## Implementation Pattern

### Creating New Adapters
To create a new adapter, follow this pattern:

```python
from .base_adapter import BaseIntegrationAdapter
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NewAdapterName(BaseIntegrationAdapter):
    """
    Adapter for [system_name] integration.
    """
    
    def _execute_internal(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute [system_name]-specific integration logic.
        
        Args:
            event: Event data containing information about the action that occurred
            
        Returns:
            Result of the [system_name] integration, or None if not applicable
        """
        action = event.get('action', '')
        
        # Only process relevant events for this adapter
        if '[relevant_keyword]' in action:
            logger.info(f"Processing {action} event for [system_name] integration")
            
            # Implement specific integration logic
            result = self._send_to_[system_name](event)
            
            return {
                'adapter': '[adapter_name]',
                'event_action': action,
                'success': True,
                'response': result
            }
        
        logger.debug(f"Event {action} not relevant for [system_name], skipping")
        return None
    
    def _send_to_[system_name](self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send event data to [system_name].
        """
        # Implementation specific to [system_name]
        pass
```

### Adapter Configuration
Adapters are configured through a dictionary with the following standard keys:

- `name`: Display name for the adapter
- `enabled`: Boolean indicating if the adapter is active
- `[system_specific_key]`: System-specific configuration parameters

## Adapter Manager

### Usage
The `AdapterManager` class provides centralized management of all adapters:

```python
from integration.adapter_manager import AdapterManager

# Initialize with configurations
configs = {
    'artha': {
        "name": "Artha Adapter",
        "enabled": True,
        "artha_api_url": "https://artha-api.example.com",
        "artha_api_key": "your-key"
    },
    # ... other adapter configs
}

manager = AdapterManager(configs)

# Execute all adapters for an event
event = {
    "event_id": "evt_123",
    "action": "payroll_processed",
    "tenant_id": "tenant_abc",
    "user_id": "user_123",
    "timestamp": "2026-01-10T17:00:00Z"
}

results = manager.execute_all_adapters(event)
```

### Methods
- `execute_all_adapters(event)`: Executes all enabled adapters for the event
- `execute_adapter(adapter_name, event)`: Executes a specific adapter
- `get_active_adapters()`: Returns list of enabled adapters
- `toggle_adapter(adapter_name, enabled)`: Enable/disable an adapter at runtime

## Security Considerations

### Authentication
- Each adapter should implement appropriate authentication mechanisms
- API keys should be stored securely and not hardcoded
- Use environment variables for sensitive configuration

### Data Protection
- Encrypt sensitive data transmitted to external systems
- Implement proper error handling to prevent information leakage
- Log only necessary information without exposing sensitive data

### Tenant Isolation
- Adapters should respect tenant boundaries
- Ensure data from one tenant doesn't leak to another
- Include tenant context in all external communications

## Error Handling

### Fail-Safe Principle
All adapters implement the fail-safe principle:
- If an adapter fails, the main application continues to function
- Errors are logged for monitoring and debugging
- Graceful degradation when external systems are unavailable

### Retry Logic
Consider implementing retry logic for transient failures:
- Exponential backoff for failed requests
- Circuit breaker pattern for persistent failures
- Dead letter queue for permanently failed events

## Performance Considerations

### Async Operations
- Use asynchronous operations when interacting with external systems
- Implement timeouts to prevent hanging requests
- Consider batching operations for better performance

### Resource Management
- Close connections properly
- Implement connection pooling if applicable
- Monitor resource usage during adapter operations

## Testing

### Unit Tests
Each adapter should have comprehensive unit tests covering:
- Normal operation scenarios
- Error conditions and failure modes
- Configuration validation
- Tenant isolation verification

### Integration Tests
Test adapters with actual external systems in controlled environments:
- Mock external services during development
- Use staging environments for real integrations
- Monitor performance impact of adapter operations

---

**Document Version**: 1.0  
**Last Updated**: January 17, 2026  
**Owner**: BHIV Development Team  
**Review Cycle**: Quarterly