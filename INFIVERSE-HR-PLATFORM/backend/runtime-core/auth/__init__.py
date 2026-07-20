"""
Sovereign Application Runtime (SAR) - Authentication Module

This module provides comprehensive authentication services for the SAR.

Features:
- Dual authentication (API key and JWT tokens)
- Multi-tenant support with tenant isolation
- 2FA/TOTP support
- Password management and validation
- Candidate and client authentication
- Role-based access control
- Support for candidate, recruiter, and client roles

Authentication Patterns:
- Unified authentication: API key OR JWT token
- Role-specific authentication (candidate, recruiter, client, admin)
- Optional authentication for public endpoints
- Support for both standard and custom JWT tokens

Dependencies:
- Requires environment variables: JWT_SECRET_KEY, API_KEY_SECRET, CANDIDATE_JWT_SECRET_KEY
- Uses the same authentication patterns as the services folder

Usage:
from auth.auth_service import get_auth, get_api_key, get_candidate_auth, get_recruiter_auth, get_client_auth, get_admin_auth
"""