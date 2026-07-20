"""
Sovereign Application Runtime (SAR) - Role Enforcement Module

This module provides comprehensive role-based access control (RBAC) functionality for the SAR.

Features:
- Multi-role support (system_admin, client_admin, client_user, candidate, api_key_user)
- Fine-grained permission control with resource-action pairs
- Tenant-isolated role assignments
- MongoDB Atlas integration for role data storage
- Integration with authentication and tenant services
- Role-based access enforcement middleware
- Dynamic permission checking with caching

Role Types:
- SYSTEM_ADMIN: Full system access
- CLIENT_ADMIN: Tenant-level administrative access
- CLIENT_USER: Limited tenant access
- CANDIDATE: Self-service access
- API_KEY_USER: System-level access for service-to-service communication

Permissions:
- Resource-based with action-level granularity
- Scope support (tenant, system, global, own, public)
- Wildcard permissions for broad access

Dependencies:
- Requires MongoDB Atlas connection
- Integrates with authentication and tenant services
- Uses the same authentication patterns as the services

Usage:
from role_enforcement.rbac_service import sar_rbac, require_permission
from role_enforcement.middleware import RoleEnforcementMiddleware
"""