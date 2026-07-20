"""
Sovereign Application Runtime (SAR) - Audit Logging Module

This module provides comprehensive audit logging with provenance tracking for the SAR.

Features:
- MongoDB Atlas integration for persistent storage
- File-based and in-memory storage backends
- Automatic request logging via middleware
- Integration with authentication and tenant services
- Support for all major audit event types
- Configurable storage backends and retention policies

Storage Backends:
- MongoDB Atlas (default) - Production ready with indexing
- File-based storage - For local development
- In-memory storage - For testing

Authentication Integration:
- Supports both API key and JWT authentication
- Automatic tenant isolation
- Comprehensive user and system event tracking
"""