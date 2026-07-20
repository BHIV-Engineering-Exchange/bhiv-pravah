# Complete Framework Handover Package

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Quick Start Guide](#quick-start-guide)
3. [Architecture Overview](#architecture-overview)
4. [Module Development Guide](#module-development-guide)
5. [Configuration Guide](#configuration-guide)
6. [Security & Compliance](#security--compliance)
7. [Deployment Guide](#deployment-guide)
8. [Troubleshooting](#troubleshooting)
9. [Team Contacts](#team-contacts)
10. [Support & Maintenance](#support--maintenance)

## Executive Summary

The Sovereign Application Runtime (SAR) is a production-ready, multi-tenant application platform that provides essential infrastructure services for building secure, scalable SaaS applications with complete tenant isolation, robust security measures, and integrated MongoDB Atlas database backend. **Note**: The production BHIV HR Platform has 111 operational endpoints across 6 services with MongoDB Atlas integration and operates in single-tenant mode with multi-tenant framework ready. **Current System Status**: MongoDB Atlas migration complete, 111 endpoints operational, production-ready single-tenant system.

### Key Features
- **Authentication Service**: Triple authentication system with API Key, Client JWT, and Candidate JWT tokens, plus 2FA and password management
- **Tenancy Service**: Robust tenant isolation with cross-tenant access prevention
- **Role Enforcement**: Comprehensive RBAC with 5 predefined roles
- **Audit Logging**: Complete audit trails with provenance tracking and MongoDB storage
- **Workflow Engine**: Business process automation with instance management and MongoDB persistence
- **Integration Adapters**: Pluggable adapters for external systems with secure API communication
- **Database**: MongoDB Atlas integration as primary database backend with elastic scaling, auto-backup, and monitoring

### Business Value
- **Reusable Infrastructure**: <10% glue code needed for new product integration
- **Consistent Experience**: Uniform auth, authorization, and audit across products
- **Compliance Ready**: Built-in audit trails and tenant isolation
- **Scalable Foundation**: Ready for multi-product deployment strategy

## Quick Start Guide

### Prerequisites
- Python 3.12+
- pip package manager
- Docker (optional, for containerized deployment)
- MongoDB Atlas instance (production) or local MongoDB (development)

### Installation
```bash
# Clone the repository
git clone https://github.com/Shashank-0208/BHIV-HR-PLATFORM.git

cd BHIV-HR-PLATFORM/backend/runtime-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your specific values
# Generate secure secrets with: openssl rand -hex 32
```

### Running the Framework
```bash
# Start the application
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Access
- **Swagger UI**: http://localhost:8000/docs
- **API Root**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **Ready Check**: http://localhost:8000/ready
- **Default API Key**: `default_sar_api_key`

## Architecture Overview

### Core Services

The framework consists of 5 core microservices:

#### 1. Authentication Service
- Handles user authentication and session management
- Supports JWT tokens and API key authentication
- Implements 2FA with TOTP and QR code generation
- Manages password policies and validation

#### 2. Tenancy Service
- Provides tenant identification and isolation
- Ensures cross-tenant data access prevention
- Injects tenant context automatically in requests
- Validates tenant access permissions

#### 3. Role Enforcement Service
- Implements comprehensive RBAC system
- Manages 5 predefined roles with granular permissions
- Enforces permissions at middleware level
- Provides real-time permission checking

#### 4. Audit Logging Service
- Captures comprehensive audit trails
- Maintains provenance tracking for data modifications
- Provides search and analysis capabilities
- Stores data in MongoDB with configurable retention

#### 5. Workflow Engine
- Automates business processes with dependency management
- Manages workflow definitions and instances
- Provides lifecycle controls (start, pause, resume, cancel)
- Supports tenant-isolated workflow execution with MongoDB persistence

### Integration Layer

#### Adapter System
The framework includes a pluggable adapter layer for external system integrations:

- **Artha Adapter**: Payroll and finance system integration
- **Karya Adapter**: Task and workflow management
- **InsightFlow Adapter**: Analytics and metrics collection
- **Bucket Adapter**: Storage and artifact management

All adapters follow the same interface and are designed to be optional and fail-safe.

## Module Development Guide

### Adding a New Module (CRM/ERP/etc.)

1. **Create Module Directory**
   ```bash
   mkdir modules/new_module
   cd modules/new_module
   ```

2. **Follow Reference Pattern**
   - Examine the runtime-core services for implementation patterns
   - Use the same authentication and tenancy services
   - Leverage the shared services from the runtime-core

3. **Ensure Tenant Isolation**
   - Include tenant_id scoping in all data access
   - Use tenant resolution service for context
   - Validate tenant access before operations

4. **API Endpoint Patterns**
   - Follow RESTful API design principles
   - Use consistent authentication patterns
   - Implement proper error handling
   - Document endpoints with proper schemas

### Best Practices
- Use dependency injection for service access
- Implement proper logging and monitoring
- Follow security best practices
- Maintain backward compatibility
- Write comprehensive tests

## Configuration Guide

### Environment Variables

The framework relies on environment variables for configuration:

#### Authentication
- `API_KEY_SECRET`: Secret for API key authentication
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `CANDIDATE_JWT_SECRET_KEY`: Secret for candidate tokens

#### Database
- `MONGODB_URI`: Connection string for MongoDB (default: mongodb://localhost:27017)
- `MONGODB_DB_NAME`: Database name in MongoDB (default: bhiv_hr)

#### Services
- `AUDIT_LOGGING_ENABLED`: Enable/disable audit logging
- `AUDIT_STORAGE_BACKEND`: Storage backend for audit logs (mongodb/file/memory)
- `TENANT_ISOLATION_ENABLED`: Enable/disable tenant isolation
- `WORKFLOW_STORAGE_BACKEND`: Storage backend for workflows (mongodb/memory)

#### Integration Adapters
- `ARTHRA_API_URL`: Artha payroll system API endpoint
- `ARTHRA_API_KEY`: API key for Artha system
- `KARYA_API_URL`: Karya task system API endpoint
- `KARYA_API_KEY`: API key for Karya system
- `INSIGHTFLOW_API_URL`: InsightFlow analytics API endpoint
- `INSIGHTFLOW_API_KEY`: API key for InsightFlow system
- `BUCKET_API_URL`: Bucket storage API endpoint
- `BUCKET_CREDENTIALS`: Credentials for Bucket storage system

#### Security Settings
- `MAX_LOGIN_ATTEMPTS`: Maximum failed login attempts before lockout
- `JWT_EXPIRATION_HOURS`: JWT token expiration time
- `REQUIRE_PASSWORD_COMPLEXITY`: Whether to enforce password complexity

### Configuration Best Practices
- Use different secrets for development/staging/production
- Rotate secrets regularly (recommended every 90 days)
- Never commit .env files to version control
- Use infrastructure-specific configurations for different environments

## Security & Compliance

### Security Measures

#### Authentication
- Dual authentication (API key and JWT tokens)
- 2FA with TOTP implementation
- Secure password hashing and validation
- Session management with proper expiration

#### Authorization
- Role-based access control with granular permissions
- Tenant isolation preventing cross-tenant access
- Permission checking at middleware level
- Resource-action based access control

#### Data Protection
- Tenant isolation for all data access
- Audit logging for all operations
- Secure token validation
- Input sanitization and validation

### Compliance Features

#### Audit Trail
- Comprehensive logging of all user actions
- Provenance tracking for data modifications
- Configurable retention policies
- Search and analysis capabilities

#### Data Privacy
- Tenant isolation ensuring data separation
- Right to deletion implementation
- Data minimization principles

### Security Best Practices
- Regular security audits
- Vulnerability scanning
- Secure coding practices
- Access control reviews

## Deployment Guide

### Production Deployment

#### Environment Preparation
1. Set up production environment with appropriate hardware
2. Configure firewall and network security
3. Set up SSL certificates for HTTPS
4. Prepare database infrastructure (MongoDB)

#### Configuration
1. Update environment variables for production
2. Configure security settings appropriately
3. Set up monitoring and logging infrastructure
4. Configure backup and recovery procedures

#### Deployment Process
1. Deploy the framework to production servers
2. Start all services
3. Perform smoke tests
4. Monitor initial operation

### Docker Deployment

#### Building the Image
```bash
docker build -t sar-runtime .
```

#### Running with Docker
```bash
docker run -p 8000:8000 --env-file .env sar-runtime
```

#### Docker Compose
```bash
docker-compose -f docker-compose.yml up -d
```

### Scaling Considerations
- Horizontal scaling capabilities planned
- Database connection pooling
- Memory management optimization
- Load balancing configuration

## Troubleshooting

### Common Issues

#### 1. Authentication Issues
- **Problem**: Unable to authenticate
- **Solution**: Verify API_KEY_SECRET, JWT_SECRET_KEY, and CANDIDATE_JWT_SECRET_KEY in environment variables. Check MongoDB connection for user data storage.

#### 2. Tenant Isolation Not Working
- **Problem**: Cross-tenant data access
- **Solution**: Verify all database queries include tenant_id filters. Check MongoDB collection indexes for tenant_id fields.

#### 3. Adapter Not Loading
- **Problem**: Integration adapters not initializing
- **Solution**: Check adapter configuration in environment variables. Verify MongoDB connection for adapter event logging.

#### 4. Performance Issues
- **Problem**: Slow response times
- **Solution**: Check MongoDB connection pool settings, optimize database indexes, monitor resource usage.

#### 5. MongoDB Connection Issues
- **Problem**: Cannot connect to database
- **Solution**: Verify MONGODB_URI and MONGODB_DB_NAME environment variables. Check that MongoDB service is running and accessible.

### Diagnostic Commands

```bash
# Check service health
curl http://localhost:8000/health

# Check service readiness
curl http://localhost:8000/ready

# Check all endpoints
python test/test_all_endpoints.py --verbose

# View logs
tail -f logs/application.log

# Check MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print('MongoDB connection:', 'OK' if client.admin.command('ping')['ok'] else 'FAILED')"
```

### Monitoring
- Implement health checks for production
- Monitor response times and error rates
- Track resource utilization
- Set up alerts for critical issues

## Team Contacts

### Core Framework
- **Framework Architect**: Development team
- **Platform Engineer**: DevOps team

### Module Development
- **Frontend/UI**: UI/UX team
- **Backend Services**: Backend development team

### Support Channels
- **Technical Queries**: runtime-core-support@company.com
- **Security Issues**: security@company.com
- **Urgent Issues**: escalation@company.com

## Support & Maintenance

### Ongoing Maintenance
- Regular security updates
- Performance monitoring and optimization
- Feature enhancements based on user feedback
- Documentation updates

### Version Management
- Semantic versioning for releases
- Backward compatibility maintained
- Migration guides for major versions
- Deprecation notices in advance

### Support Levels
- **Critical Issues**: 2-hour response time
- **High Priority**: 24-hour response time
- **Medium Priority**: 3-business day response time
- **Low Priority**: 5-business day response time

---

**Handover Date**: January 23, 2026  
**Framework Version**: Sovereign Application Runtime (SAR) v2.0  
**Document Version**: 2.0