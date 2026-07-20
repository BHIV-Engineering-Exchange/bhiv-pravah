# Audit Logging and Traceability

## Overview
This document describes the comprehensive audit logging system in the BHIV Application Framework, which provides complete traceability and accountability for all operations in the multi-tenant environment.

## Audit System Architecture

### Core Components
The audit logging system consists of:

1. **Audit Event Model**: Standardized structure for capturing all audit information
2. **Storage Backends**: Configurable storage options (file-based or in-memory)
3. **Event Processing**: Asynchronous processing for performance
4. **Query Interface**: Retrieval and analysis capabilities
5. **Middleware Integration**: Automatic audit logging for API requests

### Audit Event Structure
Each audit event contains comprehensive provenance information:

```python
# Core audit event fields
- event_id: Unique identifier for the event
- event_type: Categorized type (user_login, api_access, data_modification, etc.)
- timestamp: UTC timestamp with timezone information
- user_id: Identity of the user performing the action
- tenant_id: Tenant context for multi-tenancy
- client_ip: IP address of the client
- user_agent: Browser/device information
- resource: Target resource of the action
- action: Specific action performed
- resource_id: Identifier of the specific resource
- old_values: Previous state before modifications
- new_values: New state after modifications
- metadata: Additional contextual information
- session_id: Associated session identifier
- correlation_id: Request correlation for distributed tracing
- success: Boolean indicating success/failure
- error_message: Error details if action failed
```

## Event Types

### 1. User Management Events
- `USER_LOGIN`: User authentication events
- `USER_LOGOUT`: User session termination
- `USER_REGISTER`: New user registration
- `ROLE_ASSIGNMENT`: Role assignments to users
- `PERMISSION_CHANGE`: Permission modifications

### 2. Data Access Events
- `API_ACCESS`: All API endpoint access
- `DATA_ACCESS`: Data retrieval operations
- `DATA_MODIFICATION`: Data creation, update, deletion
- `FILE_UPLOAD`: File storage operations
- `FILE_DOWNLOAD`: File retrieval operations

### 3. Security Events
- `SECURITY_EVENT`: Security-related incidents
- `CONFIG_CHANGE`: System configuration modifications
- `SYSTEM_ERROR`: System error logging

### 4. Multi-Tenancy Events
- `TENANT_ACCESS`: Tenant access validation
- `TENANT_CREATION`: New tenant creation
- `TENANT_ISOLATION`: Cross-tenant access attempts

## Storage Backends

### File-Based Storage
- **Default**: Primary storage mechanism
- **Structure**: Daily log files (audit_YYYY-MM-DD.log)
- **Persistence**: Permanent storage across application restarts
- **Location**: Configurable directory (default: audit_logs/)
- **Rotation**: Daily rotation for manageability

### In-Memory Storage
- **Use Case**: Development and testing environments
- **Performance**: Higher throughput, lower latency
- **Retention**: Last 10,000 events to prevent memory issues
- **Persistence**: Volatile (lost on restart)

## Configuration Options

### Environment Variables
```bash
# Enable/disable audit logging
AUDIT_LOGGING_ENABLED=true

# Storage backend selection
AUDIT_STORAGE_BACKEND=file  # or memory

# Log retention settings
AUDIT_RETENTION_DAYS=90

# Performance tuning
AUDIT_BATCH_SIZE=100
AUDIT_FLUSH_INTERVAL=5  # seconds
AUDIT_QUEUE_SIZE=1000

# Asynchronous processing
AUDIT_ASYNC_WRITES=true

# Sensitive data logging
AUDIT_LOG_SENSITIVE_DATA=false
```

### Configuration Class
```python
class AuditConfig:
    enabled: bool  # Overall audit logging enablement
    storage_backend: str  # file or memory
    retention_days: int  # Log retention period
    batch_size: int  # Number of events to batch before writing
    flush_interval: int  # Time interval to flush events (seconds)
    log_sensitive_data: bool  # Whether to log sensitive data
    queue_size: int  # Size of the event processing queue
    async_writes: bool  # Whether to use async event processing
```

## Middleware Integration

### Automatic API Auditing
The audit system integrates with FastAPI middleware to automatically log:

- All incoming API requests
- Response status codes
- Request timing and performance
- User authentication context
- Tenant isolation validation

### Manual Event Logging
Applications can manually log custom events using:

```python
# Direct event logging
sar_audit.log_event(
    event_type=AuditEventType.DATA_MODIFICATION,
    user_id="user_123",
    tenant_id="tenant_abc",
    resource="job",
    action="create",
    resource_id="job_456",
    old_values=None,
    new_values={"title": "Software Engineer", "department": "Engineering"}
)

# Helper functions for common events
sar_audit.log_api_access(request, response_status=200)
sar_audit.log_data_access(user_id, tenant_id, resource, resource_id)
sar_audit.log_user_login(user_id, client_ip, user_agent)
```

## Multi-Tenancy and Isolation

### Tenant-Aware Auditing
- All audit events include tenant context
- Tenant isolation violations are logged as security events
- Cross-tenant access attempts are tracked
- Audit logs are isolated by tenant

### Data Provenance
- Old and new values tracked for all modifications
- Complete change history for audit trails
- Immutable audit records
- Tamper-evident logging

## Query and Analysis

### Event Retrieval
```python
# Get events with filters
filters = {
    "user_id": "user_123",
    "event_type": "api_access",
    "timestamp_from": "2026-01-01T00:00:00Z"
}
events = sar_audit.get_events(filters, limit=100, offset=0)

# Get specific event by ID
event = sar_audit.get_event_by_id("event_uuid")

# Get audit trail for specific resource
trail = get_audit_trail("job", "job_123", tenant_id="tenant_abc")
```

### Audit Trail Generation
- Complete chronological history of resource changes
- Before/after state comparison
- User attribution for all changes
- Tenant context preservation

## Security and Compliance

### Data Protection
- Sensitive data logging configurable
- Encrypted storage options available
- Access controls for audit data
- Immutable audit records

### Compliance Features
- Sarbanes-Oxley (SOX) compliance ready
- GDPR audit trail capabilities
- HIPAA compliance support
- Financial services audit requirements

### Security Event Tracking
- Failed authentication attempts
- Unauthorized access attempts
- Privilege escalation detection
- Configuration change tracking

## Performance Considerations

### Asynchronous Processing
- Non-blocking audit event recording
- Configurable batch sizes for efficiency
- Queue-based event processing
- Performance impact minimization

### Scalability Features
- Horizontal scaling support
- Distributed audit collection
- Partitioned storage by tenant/time
- Efficient querying mechanisms

## Integration with Other Services

### Authentication Integration
- Automatic user context capture
- Session management tracking
- 2FA verification logging
- Password change tracking

### Workflow Integration
- Workflow execution logging
- State transition tracking
- Task completion auditing
- Approval process tracking

### Role Enforcement Integration
- Permission check logging
- Role assignment tracking
- Access violation detection
- Policy change auditing

## Best Practices

### Event Classification
- Use appropriate event types for categorization
- Include relevant metadata for context
- Capture tenant information consistently
- Log both successful and failed operations

### Performance Optimization
- Use asynchronous logging in production
- Configure appropriate batch sizes
- Monitor queue lengths
- Tune flush intervals based on load

### Data Retention
- Configure appropriate retention periods
- Implement log rotation
- Archive older data when needed
- Plan for storage capacity

## Monitoring and Alerting

### Health Checks
- Storage backend connectivity
- Event processing queue status
- Disk space monitoring
- Performance metrics

### Alert Conditions
- Failed audit event writes
- Queue overflow situations
- Storage space exhaustion
- Unusual access patterns

## Testing and Validation

### Audit Completeness Verification
- All user actions are logged
- API access is comprehensively tracked
- Data modifications include provenance
- Security events are captured appropriately

### Compliance Validation
- Audit trails are complete and accurate
- Tenant isolation is maintained
- Sensitive data handling is appropriate
- Access controls are enforced

## Troubleshooting

### Common Issues
- **Queue Overflow**: Increase queue size or improve processing performance
- **Disk Space**: Monitor log directory and implement rotation
- **Performance Impact**: Adjust batch sizes and flush intervals
- **Missing Events**: Verify audit logging is enabled

### Diagnostic Steps
1. Check audit configuration settings
2. Verify storage backend connectivity
3. Monitor event processing queue
4. Review application logs for errors

---

**Document Version**: 1.0  
**Last Updated**: January 17, 2026  
**Owner**: BHIV Development Team  
**Review Cycle**: Quarterly