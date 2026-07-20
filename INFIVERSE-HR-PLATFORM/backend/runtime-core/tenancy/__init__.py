"""
Sovereign Application Runtime (SAR) - Tenant Resolution Module

This module provides comprehensive tenant resolution and isolation functionality for the SAR.

Features:
- Multi-tenant support with tenant isolation
- Tenant resolution from JWT tokens and headers
- Cross-tenant access validation
- MongoDB Atlas integration for tenant data storage
- Tenant-scoped query filtering
- Support for different tenant types (client, organization, enterprise, government)

Tenant Resolution:
- Extracts tenant information from JWT tokens
- Supports tenant resolution from custom headers
- Fallback to default tenant if configured
- Integration with authentication service for tenant extraction

Tenant Isolation:
- MongoDB query filters for tenant isolation
- Cross-tenant access validation with admin override
- Shared resource access control
- Tenant-scoped aggregation pipelines

Dependencies:
- Requires MongoDB Atlas connection
- Uses the same authentication patterns as the auth module
- Integrates with the audit logging module

Usage:
from tenancy.tenant_service import get_tenant_info, sar_tenant_resolver
from tenancy.middleware import TenantIsolationMiddleware
"""