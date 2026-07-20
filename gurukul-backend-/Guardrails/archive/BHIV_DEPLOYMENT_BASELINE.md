## Core Principle
**Availability is the highest priority.** If a choice exists between completeness and availability, availability MUST win.

## Mandatory Deployment Rules

### Port Binding
- MUST bind to serving port immediately on startup
- Port binding MUST NOT be blocked by imports, logic, or dependencies
- Core request handling available as soon as binding completes

### Startup Sequencing
- Core startup before non-critical components
- Databases, external services, models initialize AFTER port binding
- Non-critical failures MUST NOT prevent service availability

### Memory Management
- Operate within platform memory limits
- Heavy dependencies NOT required for basic startup
- Model loading deferred until service available
- Memory-intensive features disabled by default in demo builds

### Environment Configuration
- All configuration via environment variables with safe defaults
- Missing non-critical config MUST NOT prevent startup
- Sensitive config NOT hardcoded
- CORS and security settings externally configurable

### Health Checks
- Every backend service exposes health endpoint
- Health checks respond immediately, independent of databases/models
- Reflect process liveness, not system completeness
- Health checks MUST NOT block or perform retries

### Error Handling
- Startup failures ONLY for components required to bind and serve requests
- Non-critical failures degrade functionality, not availability
- External service failures handled gracefully with logging

### CORS and Network Safety
- CORS explicitly defined for production
- NO wildcard origins in production
- Network security applied before serving requests

## Optional Patterns

### Runtime Isolation
- Telemetry/observability initialized asynchronously
- Kill switches to disable without redeploying
- Telemetry failures do NOT affect core functionality

### Database & Caching
- Database connections MAY initialize after startup
- Cache failures have safe fallbacks
- Cache initialization asynchronous

### Background Processing
- Background work in separate services
- Background workers do NOT block main startup
- Worker failures do NOT affect core availability

## Forbidden Practices
- ❌ Blocking operations during import/startup
- ❌ Database queries during startup
- ❌ External API calls blocking startup
- ❌ Model loading during startup
- ❌ Any operation delaying port binding
- ❌ Dependencies exceeding memory constraints
- ❌ Experimental features in demo builds
- ❌ Dependencies blocking startup without fallbacks
- ❌ Any behavior that makes startup nondeterministic

## Isolation Principles
- Experimental/telemetry systems isolated from core availability
- Failures in isolated systems do NOT affect core functionality
- Feature flags default to disabled
- Background services isolated from request-serving services