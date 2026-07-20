# Sovereign Application Runtime (SAR) - LEGACY REFERENCE IMPLEMENTATION

⚠️ **IMPORTANT**: This is a LEGACY REFERENCE IMPLEMENTATION only. The production BHIV HR Platform is located in the main `backend/` directory with 111 operational endpoints across 6 services using MongoDB Atlas.

The Sovereign Application Runtime (SAR) is a comprehensive, reusable platform extracted from the BHIV HR Platform and evolved to support multiple domains (HR, CRM, ERP, etc.). It provides core infrastructure services including authentication, tenant isolation, role enforcement, audit logging, workflow management, and pluggable integration capabilities for reference purposes.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Core Components](#core-components)
- [Quick Links](#quick-links)
- [Test Files](#test-files)
- [Setup Guide](#setup-guide)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)
- [Project Structure](#project-structure)

## Overview

The Sovereign Application Runtime (SAR) is a modular, multi-tenant framework designed for sovereign cloud deployments that can be deployed in KSA/UAE infrastructure, ensuring data sovereignty and compliance with local regulations. The framework provides enterprise-grade infrastructure services that can be reused across multiple business domains.

⚠️ **NOTE**: This is a LEGACY REFERENCE IMPLEMENTATION. The production BHIV HR Platform has been migrated to MongoDB Atlas with 111 operational endpoints across 6 services (Gateway: 80 endpoints, Agent: 6 endpoints, LangGraph: 25 endpoints) and is located in the main `backend/` directory.

### Features
- **Multi-tenant SaaS Architecture**: Complete tenant isolation with no cross-tenant data access
- **Triple Authentication System**: Support for API keys, Client JWT tokens, and Candidate JWT tokens with 2FA capabilities
- **Role-Based Access Control (RBAC)**: Comprehensive permission system with flexible role assignments
- **Comprehensive Audit Logging**: Complete audit trails with provenance tracking for all operations
- **Workflow Engine**: Business process automation with dependency management
- **Integration Adapters**: Pluggable adapters for external systems (Artha, Karya, InsightFlow, Bucket)
- **Reusable Architecture**: Framework designed for multiple business domains (HR, CRM, ERP, etc.)
- **Rate Limiting and Security Measures**: Built-in protection against abuse and attacks
- **MongoDB Atlas Integration**: Scalable document-based database storage (Production: MongoDB Atlas, Reference: Local MongoDB)
- **Configurable Storage Backends**: Support for multiple storage options
- **Asynchronous Processing**: Non-blocking operations for improved performance
- **Event-Driven Architecture**: Scalable and responsive system design

## Architecture

The framework follows a modular architecture with the following core components:

1. **Authentication Service** - Handles user authentication and session management
2. **Tenant Resolution Service** - Manages tenant identification and isolation
3. **Role Enforcement Service** - Implements role-based access control
4. **Audit Logging Service** - Provides comprehensive audit trails
5. **Workflow Engine** - Automates business processes
6. **Integration Adapters** - Pluggable adapters for external systems

Each component is designed to work independently while providing seamless integration when used together.

## Core Components

### Authentication Service (`auth/`)

The authentication service provides comprehensive user authentication capabilities:

- **JWT Token Management**: Secure token generation and validation
- **API Key Authentication**: System-level access with API keys (default: `default_sar_api_key`)
- **Two-Factor Authentication**: TOTP-based 2FA with QR code generation and manual entry
- **Password Management**: Secure password hashing, validation, generation, and policy enforcement
- **Email and Phone Validation**: Verification mechanisms for contact information
- **Session Management**: Secure session handling and lifecycle management
- **Security Measures**: Rate limiting, brute force protection, and secure token storage

**API Endpoints**:
- `/auth/login` - User login with optional 2FA
- `/auth/2fa/setup` - Setup 2FA for user (requires API key)
- `/auth/2fa/verify` - Verify TOTP code (requires API key)
- `/auth/2fa/status/{user_id}` - Get 2FA status for user
- `/auth/password/validate` - Validate password strength (requires API key)
- `/auth/password/change` - Change password (requires JWT)
- `/auth/password/generate` - Generate secure password (requires API key)
- `/auth/password/policy` - Get password policy (requires API key)
- `/auth/health` - Authentication service health check

### Tenant Resolution Service (`tenancy/`)

The tenant resolution service ensures proper multi-tenancy with complete isolation:

- **Tenant Identification**: Automatic tenant resolution from JWT tokens and headers
- **Isolation Enforcement**: Prevents cross-tenant data access
- **Context Injection**: Automatic tenant context injection in requests
- **Validation Mechanisms**: Tenant access validation and verification
- **Scalable Architecture**: Designed to handle thousands of tenants
- **Configurable Isolation**: Flexible isolation policies based on requirements

**API Endpoints**:
- `/tenants/current` - Get current tenant information
- `/tenants/isolation-check/{resource_tenant_id}` - Check cross-tenant access
- `/tenants/query-filter/{table_name}` - Get SQL query filters for tenant isolation
- `/tenants/shared-resource-access/{resource_type}` - Check shared resource access
- `/tenants/health` - Tenant service health check

### Role Enforcement Service (`role_enforcement/`)

The role enforcement service provides comprehensive access control:

- **Role Definitions**: Predefined roles (system_admin, client_admin, client_user, candidate, api_key_user)
- **Permission System**: Resource-action based permissions with scope control (tenant, system, global, own, public)
- **Dynamic Assignment**: Role assignment with tenant scoping and expiration
- **Middleware Integration**: Request-level access control enforcement
- **Permission Inheritance**: Hierarchical permission management
- **Real-time Validation**: On-demand permission checking

**API Endpoints**:
- `/role/health` - Role enforcement service health check
- `/role/available-roles` - Get all available roles in the system
- `/role/current` - Get current user's roles and permissions
- `/role/permissions` - Get current user's permissions
- `/role/user/{user_id}` - Get roles assigned to a specific user
- `/role/assign` - Assign a role to a user (requires admin permissions)
- `/role/check-permission` - Check if user has specific permission
- `/role/protected-example` - Example of protected endpoint
- `/role/admin-only` - Example of admin-only endpoint

### Audit Logging Service (`audit_logging/`)

The audit logging service provides complete operational transparency:

- **Comprehensive Event Tracking**: User logins, API access, data modifications, security events
- **Provenance Tracking**: Maintains old/new values for data modifications
- **Multi-Tenancy Support**: Tenant-isolated audit logs with cross-tenant access prevention
- **MongoDB Storage**: Persistent audit logs stored in MongoDB
- **Real-time Monitoring**: Middleware for automatic request/response logging
- **Search and Analysis**: Comprehensive API for audit trail retrieval and analysis
- **Retention Policies**: Configurable log retention and archival
- **Asynchronous Processing**: Non-blocking audit logging with configurable flush intervals

**API Endpoints**:
- `/audit/health` - Audit logging service health check
- `/audit/events` - Retrieve audit events with filtering and pagination
- `/audit/events/{event_id}` - Get specific audit event by ID
- `/audit/trail/{resource}/{resource_id}` - Get complete audit trail for a resource
- `/audit/stats` - Get audit log statistics
- `/audit/log-custom` - Log custom audit event (requires valid event type)
- `/audit/example-protected-endpoint` - Example of audit-logged protected endpoint

### Workflow Engine (`workflow/`)

The workflow engine automates business processes:

- **Workflow Definitions**: Reusable templates for business processes
- **Task Management**: Dependency-aware task execution with error handling
- **State Management**: Persistent workflow state with pause/resume capabilities
- **Multi-Tenancy Support**: Tenant-isolated workflow execution
- **Event-Driven**: Asynchronous task execution with timeout and retry mechanisms
- **MongoDB Storage**: Persistent workflow state stored in MongoDB
- **Scalable Execution**: Concurrent workflow processing
- **Monitoring and Control**: Workflow lifecycle management

**API Endpoints**:
- `/workflow/health` - Workflow engine health check
- `/workflow/definitions` - Get available workflow definitions
- `/workflow/start` - Start a new workflow instance
- `/workflow/instances` - Get all workflow instances
- `/workflow/instances/{instance_id}` - Get specific workflow instance
- `/workflow/instances/{instance_id}/cancel` - Cancel workflow instance
- `/workflow/instances/{instance_id}/pause` - Pause workflow instance
- `/workflow/instances/{instance_id}/resume` - Resume workflow instance
- `/workflow/examples/candidate-onboarding` - Register example workflow definition

### Integration Adapters (`integration/`)

The framework includes a pluggable adapter layer for connecting with external systems:

- **Artha Adapter**: Payroll and finance system integration
- **Karya Adapter**: Task and workflow management integration
- **InsightFlow Adapter**: Analytics and metrics collection
- **Bucket Adapter**: Storage and artifact management

All adapters follow the same interface and are designed to be optional and fail-safe, ensuring the core system operates even when external integrations are unavailable.

## Quick Links

- [Dockerfile](Dockerfile) - Container configuration
- [docker-compose.yml](docker-compose.yml) - Local development environment setup
- [requirements.txt](requirements.txt) - Python dependencies
- [Framework Handover](handover/FRAMEWORK_HANDOVER.md) - Complete handover documentation
- [Test Files](test/) - Comprehensive test suite
- [Documentation](docs/) - Additional documentation

## Test Files

The runtime-core includes a comprehensive test suite:

- **test/test_all_endpoints.py**: Validates all 42 unique endpoints with 49 test scenarios
- **test/test_rbac_bootstrap.py**: Bootstrap script to assign system_admin role to testuser
- **test/comprehensive_validation.py**: Asynchronous validation framework for testing API endpoints
- **test/e2e_validation_test.py**: End-to-end validation tests for all services
- **test_suite/**: Modular test files for individual services
  - **test_auth_service.py**: Authentication service tests
  - **test_tenant_service.py**: Tenant service tests
  - **test_role_service.py**: Role service tests
  - **test_audit_service.py**: Audit service tests
  - **test_workflow_service.py**: Workflow service tests
  - **test_adapters 1.py & test_adapters 2.py**: Integration adapter tests
  - **test_system_integration.py**: Cross-service integration tests
  - **test_unit_tests.py**: Unit tests for framework components
  - **test_runner.py**: Comprehensive test runner for all test suites

## Setup Guide

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- MongoDB instance (local or remote)

### Virtual Environment Setup

Using a virtual environment is strongly recommended to isolate dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip (recommended)
python -m pip install --upgrade pip
```

Once activated, your virtual environment will be used for installing all dependencies.

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd backend/runtime-core
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows:
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   # Set environment variables as needed (see Configuration section)
   ```

## Configuration

The SAR is highly configurable through environment variables. Create a `.env` file by copying the example:

```bash
# On Windows:
copy .env.example .env

# On macOS/Linux:
cp .env.example .env
```

Then edit the `.env` file to set your specific values:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=bhiv_hr

# Authentication Secrets (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
API_KEY_SECRET=your-api-key-secret
CANDIDATE_JWT_SECRET_KEY=your-candidate-jwt-key-change-in-production

# Service Configuration
AUDIT_LOGGING_ENABLED=true
AUDIT_STORAGE_BACKEND=mongodb
TENANT_ISOLATION_ENABLED=true
WORKFLOW_STORAGE_BACKEND=mongodb

# External Service APIs (if using integration adapters)
ARTHRA_API_URL=https://artha-api.example.com
ARTHRA_API_KEY=your-artha-key
KARYA_API_URL=https://karya-api.example.com
KARYA_API_KEY=your-karya-key
INSIGHTFLOW_API_URL=https://insightflow-api.example.com
INSIGHTFLOW_API_KEY=your-insightflow-key
BUCKET_API_URL=https://bucket-api.example.com
BUCKET_CREDENTIALS=your-bucket-credentials
```

### Key Environment Variables:

- `MONGODB_URI` - MongoDB connection string (default: `mongodb://localhost:27017`)
- `MONGODB_DB_NAME` - MongoDB database name (default: `bhiv_hr`)
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `API_KEY_SECRET` - System-level API key (default: `default_sar_api_key`)
- `CANDIDATE_JWT_SECRET_KEY` - Secret key for candidate JWT tokens
- `AUDIT_LOGGING_ENABLED` - Enable/disable audit logging
- `AUDIT_STORAGE_BACKEND` - Storage backend for audit logs (mongodb/file/memory)
- `TENANT_ISOLATION_ENABLED` - Enable/disable tenant isolation
- `WORKFLOW_STORAGE_BACKEND` - Storage backend for workflows (mongodb/memory)
- `ARTHRA_API_URL`, `KARYA_API_URL`, `INSIGHTFLOW_API_URL`, `BUCKET_API_URL` - External service URLs
- `ARTHRA_API_KEY`, `KARYA_API_KEY`, `INSIGHTFLOW_API_KEY`, `BUCKET_CREDENTIALS` - External service credentials

## Running the Application

### Option 1: Direct Python Execution
```bash
cd backend/runtime-core
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker
```bash
cd backend/runtime-core
docker build -t sar-runtime .
docker run -p 8000:8000 --name sar-runtime sar-runtime
```

### Option 3: Docker Compose (Recommended for local development)
```bash
cd backend/runtime-core
docker-compose up --build
```

## API Documentation

Once running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Usage Examples

### Authentication

1. Get an API key (default: `default_sar_api_key`)
2. Use in Authorization header: `Authorization: Bearer default_sar_api_key`
3. Or get a JWT token by logging in via `/auth/login`

### Making API Calls

Most protected endpoints accept both API Key and JWT Token authentication. API Key is recommended for testing as it's simpler to use.

### Deactivating the Virtual Environment

When you're done working, you can deactivate the virtual environment:
```bash
deactivate
```

## Security

The SAR implements multiple layers of security:

- **Authentication**: Multiple authentication methods with 2FA support
- **Authorization**: Role-based access control with fine-grained permissions
- **Data Isolation**: Complete tenant data separation
- **Audit Trails**: Comprehensive logging of all operations
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Input Validation**: Comprehensive input sanitization and validation
- **API Key Protection**: System-level operations protected with API keys
- **JWT Token Validation**: Secure token validation with proper secret keys

## Important Notes

- **MongoDB Atlas Integration**: The production system uses MongoDB Atlas for scalable, cloud-based storage (Reference implementation: Local MongoDB with auto-creation)
- **Database Auto-Creation**: The MongoDB database and collections will be automatically created when the application first connects to the database
- **Default API Key**: The default API key for testing is `default_sar_api_key`
- **Production Security**: For production use, make sure to use strong, unique secret keys and not the default values
- **Multi-Tenancy**: The application follows a multi-tenant architecture with complete tenant isolation
- **Dependency Management**: All dependencies are managed through the requirements.txt file

## Troubleshooting

### Common Issues

1. **Connection Issues**: Ensure MongoDB is running and accessible
2. **Authentication Failures**: Verify JWT_SECRET_KEY and API_KEY_SECRET are set correctly
3. **Tenant Isolation Errors**: Check that tenant IDs are properly set in JWT tokens
4. **Permission Denied**: Verify user roles and permissions are correctly assigned

### Logs

Check the application logs for detailed error information. The audit logging service also maintains comprehensive logs of all operations.

### MongoDB Atlas Integration

The production BHIV HR Platform uses MongoDB Atlas for scalable, cloud-based database storage:
- **Production**: MongoDB Atlas clusters with automated scaling and high availability
- **Development**: Local MongoDB instance with auto-creation capabilities (reference implementation)
- Collections and indexes are automatically created when the application first connects
- No manual database, collection, or index creation is required in either environment
- The system follows MongoDB's "lazy creation" model where database resources are provisioned on demand

## Deployment

The SAR can be deployed in various configurations:

- **Sovereign Cloud**: Deployable in KSA/UAE infrastructure
- **MongoDB Atlas**: Production-ready cloud database with auto-scaling
- **Self-Hosted**: On-premises deployment with no external dependencies
- **Containerized**: Docker-based deployment for easy scaling
- **Cloud-Native**: Kubernetes-ready for cloud deployments

## Project Structure

```
runtime-core/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Docker Compose configuration
├── README.md                    # This documentation
├── VERSION                      # Version file
├── .env.example                 # Environment variables template
├── auth/                        # Authentication service
│   ├── __init__.py
│   ├── auth_service.py          # Core auth logic
│   ├── auth_utils.py            # Authentication utilities
│   ├── middleware.py            # Authentication middleware
│   └── router.py                # Auth API endpoints
├── tenancy/                     # Tenant resolution service
│   ├── __init__.py
│   ├── router.py                # Tenant API endpoints
│   ├── middleware.py            # Tenant isolation middleware
│   ├── tenant_service.py        # Tenant resolution logic
│   ├── validators.py            # Tenant validation utilities
│   └── __init__.py              # Package initialization
├── role_enforcement/            # RBAC service
│   ├── __init__.py
│   ├── router.py                # Role API endpoints
│   ├── middleware.py            # Role enforcement middleware
│   ├── rbac_service.py          # Permission checking
│   ├── role_checker.py          # Role validation utilities
│   └── validators.py            # Role validation utilities
├── audit_logging/               # Audit logging service
│   ├── __init__.py
│   ├── router.py                # Audit API endpoints
│   ├── middleware.py            # Audit logging middleware
│   ├── audit_service.py         # Audit event management
│   └── storage.py               # Audit storage implementation
├── workflow/                    # Workflow engine
│   ├── __init__.py
│   ├── router.py                # Workflow API endpoints
│   ├── workflow_service.py      # Workflow execution
│   ├── constants.py             # Workflow constants
│   ├── exceptions.py            # Workflow exceptions
│   └── models.py                # Workflow data models
├── integration/                 # Integration layer
│   ├── __init__.py
│   ├── adapter_manager.py       # Centralized adapter management
│   ├── adapters/                # Individual integration adapters
│   │   ├── __init__.py
│   │   ├── base_adapter.py      # Base adapter class
│   │   ├── artha_adapter.py     # Payroll/finance integration
│   │   ├── karya_adapter.py     # Task/workflow integration
│   │   ├── insightflow_adapter.py # Analytics integration
│   │   └── bucket_adapter.py    # Storage/artifacts integration
│   ├── constants.py             # Integration constants
│   ├── exceptions.py            # Integration exceptions
│   └── models.py                # Integration data models
├── test/                        # Test files
│   ├── __init__.py              # Package init
│   ├── test_all_endpoints.py    # Comprehensive endpoint tests (49 tests)
│   ├── test_rbac_bootstrap.py   # RBAC bootstrap script
│   ├── comprehensive_validation.py # Asynchronous validation framework
│   ├── e2e_validation_test.py   # End-to-end validation tests
│   ├── test_2fa_validation.py   # 2FA validation tests
│   ├── test_audit_logging.py    # Audit logging tests
│   ├── test_tenant_isolation.py # Tenant isolation tests
│   └── test_workflow_engine.py  # Workflow engine tests
├── test_suite/                  # Modular test suite
│   ├── test_auth_service.py     # Auth service tests
│   ├── test_tenant_service.py   # Tenant service tests
│   ├── test_role_service.py     # Role service tests
│   ├── test_audit_service.py    # Audit service tests
│   ├── test_workflow_service.py # Workflow service tests
│   ├── test_adapters 1.py       # Adapter tests part 1
│   ├── test_adapters 2.py       # Adapter tests part 2
│   ├── test_system_integration.py # System integration tests
│   ├── test_unit_tests.py       # Unit tests
│   └── test_runner.py           # Test runner
├── handover/                    # Runtime-core handover documentation
│   ├── FRAMEWORK_HANDOVER.md    # Framework handover doc
│   └── UPDATE_SUMMARY.md        # Update summary
├── docs/                        # Runtime-core documentation
│   ├── FRONTEND_BACKEND_SYNC.md # Frontend-backend synchronization validation
│   ├── INTERNAL_TEST_CHECKLIST.md # Internal testing checklist
│   ├── KNOWN_LIMITATIONS.md     # Known system limitations
│   ├── QA_CHECKLIST.md          # Quality assurance checklist
│   ├── REAL_HIRING_LOOP.md      # Real hiring loop validation
│   ├── TRUTH_MATRIX.md          # Reality audit and truth lock documentation
│   ├── framework/               # Framework documentation
│   │   ├── BOUNDARY_DEFINITION.md # Boundary definition for HR-specific vs reusable logic
│   │   ├── GENERIC_REFACTORING_PLAN.md # Generic refactoring plan
│   │   ├── HIRING_LOOP_OVERVIEW.md # Hiring loop overview
│   │   └── REUSABILITY_GUIDE.md # Reusability guide
│   ├── security/                # Security documentation
│   │   ├── AUDIT_AND_TRACEABILITY.md # Audit and traceability documentation
│   │   └── TENANT_ISOLATION_STATUS.md # Tenant isolation status
│   ├── sovereign/               # Sovereign deployment documentation
│   │   └── DEPLOYMENT_READINESS.md # Deployment readiness
│   └── system/                  # System documentation
│       └── CURRENT_REALITY.md   # Current system reality
└── demo/                        # Demo materials
    ├── DEMO_SCOPE.md            # Demo scope definition
    └── UPDATE_SUMMARY.md        # Demo update summary
```

## Contributing

The framework is designed to be extensible. New services can be added by following the established patterns for routing, middleware, and service implementation.

## Testing

Run the comprehensive test suite:

```bash
# Run all endpoint tests
python test/test_all_endpoints.py

# Run individual service tests
python -m pytest test_suite/

# Run end-to-end validation tests
python test/e2e_validation_test.py

# Run specific test modules
python -m pytest test_suite/
```

### Test Coverage

The application includes comprehensive test coverage with:
- **42 unique endpoints** validated with **49 test scenarios**
- End-to-end validation tests for all services
- Unit tests for individual components
- Integration tests for cross-service functionality
- API endpoint validation with proper authentication testing

**Note**: This framework serves as a reference implementation. The production BHIV HR Platform has 111 operational endpoints across 6 services with MongoDB Atlas integration.

## License

This project is part of the BHIV HR Platform and is proprietary software.

## Support

For support and questions, contact the BHIV development team.