"""
Sovereign Application Runtime (SAR) - Tenant Resolution Service

This module provides tenant resolution and isolation functionality for the SAR.
It ensures proper tenant context throughout the application lifecycle and prevents
cross-tenant data leakage.
"""

from fastapi import HTTPException, Request, Depends
from typing import Optional, Dict, Any, Union
from enum import Enum
import os
import jwt
from datetime import datetime, timezone
import re
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)


class TenantType(Enum):
    """Enumeration of tenant types supported by the SAR"""
    CLIENT = "client"
    ORGANIZATION = "organization"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class TenantResolutionError(Exception):
    """Custom exception for tenant resolution errors"""
    pass


class TenantConfig:
    """Configuration class for SAR tenant resolution service"""
    
    def __init__(self):
        # Use the same environment variables as the services
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.tenant_isolation_enabled = os.getenv("SAR_TENANT_ISOLATION_ENABLED", "true").lower() == "true"
        self.require_tenant_header = os.getenv("SAR_REQUIRE_TENANT_HEADER", "false").lower() == "true"
        self.default_tenant_id = os.getenv("SAR_DEFAULT_TENANT_ID", "default")
        self.tenant_header_name = os.getenv("SAR_TENANT_HEADER_NAME", "X-Tenant-ID")
        self.tenant_context_key = os.getenv("SAR_TENANT_CONTEXT_KEY", "tenant_id")
        # MongoDB Atlas configuration
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")


class TenantInfo:
    """Class to hold tenant information"""
    
    def __init__(self, tenant_id: str, tenant_type: TenantType, name: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.tenant_id = tenant_id
        self.tenant_type = tenant_type
        self.name = name
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tenant_type": self.tenant_type.value,
            "name": self.name,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class TenantResolver:
    """Main tenant resolution service class for the Sovereign Application Runtime"""
    
    def __init__(self):
        self.config = TenantConfig()
        self.tenant_cache = {}  # In production, use a distributed cache
        self._client = None
        self._db = None
        self._connect_to_mongodb()
    
    def _connect_to_mongodb(self):
        """Establish MongoDB connection for tenant data storage"""
        try:
            self._client = MongoClient(self.config.mongodb_uri)
            self._db = self._client[self.config.mongodb_db_name]
            # Create indexes for efficient queries
            if self._db is not None:
                self._db.clients.create_index([("tenant_id", 1)])
                self._db.users.create_index([("tenant_id", 1)])
                self._db.candidates.create_index([("tenant_id", 1)])
            logger.info("✅ Connected to MongoDB for tenant data")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB for tenant data: {e}")
            self._client = None
            self._db = None
    
    def get_tenant_from_jwt(self, token: str) -> Optional[TenantInfo]:
        """Extract tenant information from JWT token"""
        try:
            # Use the same JWT verification logic as the auth service
            from auth.auth_service import sar_auth
            payload = sar_auth.verify_jwt_token(token, secret=self.config.jwt_secret_key)
            if not payload:
                return None
            
            # Extract tenant information from JWT claims
            tenant_id = payload.get("tenant_id") or payload.get("client_id") or payload.get("user_id")
            if not tenant_id:
                return None
            
            tenant_type_str = payload.get("tenant_type", "client")
            try:
                tenant_type = TenantType(tenant_type_str.lower())
            except ValueError:
                tenant_type = TenantType.CLIENT  # Default fallback
            
            # Get additional tenant information from MongoDB if available
            tenant_name = payload.get("tenant_name") or payload.get("company_name") or payload.get("name", "")
            if self._db is not None:
                try:
                    # Try to get tenant name from clients collection
                    client_doc = self._db.clients.find_one({"client_id": tenant_id})
                    if client_doc and client_doc.get("company_name"):
                        tenant_name = client_doc["company_name"]
                    else:
                        # Try to get tenant name from users collection
                        user_doc = self._db.users.find_one({"user_id": tenant_id})
                        if user_doc and user_doc.get("name"):
                            tenant_name = user_doc["name"]
                except Exception as e:
                    logger.warning(f"Failed to get tenant name from MongoDB: {e}")
            
            return TenantInfo(
                tenant_id=tenant_id,
                tenant_type=tenant_type,
                name=tenant_name,
                metadata={
                    "exp": payload.get("exp"),
                    "iat": payload.get("iat"),
                    "permissions": payload.get("permissions", []),
                    "source": "jwt",
                    "email": payload.get("email"),
                    "role": payload.get("role", "candidate")
                }
            )
        except Exception as e:
            logger.error(f"Error extracting tenant from JWT: {e}")
            return None
    
    def get_tenant_from_header(self, request: Request) -> Optional[TenantInfo]:
        """Extract tenant information from request headers"""
        tenant_id = request.headers.get(self.config.tenant_header_name)
        if not tenant_id:
            return None
        
        return TenantInfo(
            tenant_id=tenant_id,
            tenant_type=TenantType.CLIENT,  # Default type for header-based tenants
            metadata={"source": "header"}
        )
    
    def get_tenant_from_request(self, request: Request) -> Optional[TenantInfo]:
        """Get tenant information from the incoming request using multiple strategies"""
        # Try to get tenant from Authorization header (JWT)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            tenant_info = self.get_tenant_from_jwt(token)
            if tenant_info:
                return tenant_info
        
        # Try to get tenant from custom header
        tenant_info = self.get_tenant_from_header(request)
        if tenant_info:
            return tenant_info
        
        # If no tenant found and required, raise an error
        if self.config.require_tenant_header:
            raise TenantResolutionError("Tenant ID is required but not found in request")
        
        # Return default tenant if available
        if self.config.default_tenant_id:
            return TenantInfo(
                tenant_id=self.config.default_tenant_id,
                tenant_type=TenantType.CLIENT,
                metadata={"source": "default"}
            )
        
        return None
    
    def validate_tenant_access(self, tenant_info: TenantInfo, resource_tenant_id: str) -> bool:
        """Validate that a tenant has access to a specific resource"""
        if not self.config.tenant_isolation_enabled:
            return True  # Bypass validation if isolation is disabled
        
        # Check if tenant has direct access to the resource
        if tenant_info.tenant_id == resource_tenant_id:
            return True
        
        # Check if tenant has cross-tenant access permissions (e.g., admin users)
        if self._db is not None:
            try:
                # Check if the tenant is an admin or has cross-tenant permissions
                user_doc = self._db.users.find_one({"user_id": tenant_info.tenant_id})
                if user_doc and user_doc.get("role") == "admin":
                    logger.info(f"Admin user {tenant_info.tenant_id} granted cross-tenant access to {resource_tenant_id}")
                    return True
                
                # Check if there are explicit cross-tenant permissions
                permission_doc = self._db.tenant_permissions.find_one({
                    "tenant_id": tenant_info.tenant_id,
                    "target_tenant_id": resource_tenant_id,
                    "permission": "read"  # or "write"
                })
                if permission_doc:
                    logger.info(f"Cross-tenant permission granted for {tenant_info.tenant_id} to access {resource_tenant_id}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to check cross-tenant permissions: {e}")
        
        return False
    
    def get_tenant_isolation_query_filter(self, tenant_info: TenantInfo, collection_name: str = "jobs") -> Dict[str, Any]:
        """Get the MongoDB query filter for tenant isolation"""
        if not self.config.tenant_isolation_enabled:
            return {}  # No filter needed if isolation is disabled
        
        # Determine the appropriate field name based on collection
        if collection_name in ["jobs", "offers", "feedback", "interviews"]:
            field = "client_id"
        elif collection_name in ["candidates", "users"]:
            field = "tenant_id"  # For tenant-scoped collections
        else:
            field = "tenant_id"  # Default
        
        return {field: tenant_info.tenant_id}
    
    def get_tenant_isolation_aggregation_pipeline(self, tenant_info: TenantInfo, collection_name: str = "jobs") -> List[Dict[str, Any]]:
        """Get the MongoDB aggregation pipeline for tenant isolation"""
        if not self.config.tenant_isolation_enabled:
            return []  # No pipeline needed if isolation is disabled
        
        # Determine the appropriate field name based on collection
        if collection_name in ["jobs", "offers", "feedback", "interviews"]:
            field = "client_id"
        elif collection_name in ["candidates", "users"]:
            field = "tenant_id"  # For tenant-scoped collections
        else:
            field = "tenant_id"  # Default
        
        return [{"$match": {field: tenant_info.tenant_id}}]
    
    def create_tenant_context(self, tenant_info: TenantInfo) -> Dict[str, Any]:
        """Create a tenant context dictionary for use in request handlers"""
        return {
            self.config.tenant_context_key: tenant_info.tenant_id,
            "tenant_info": tenant_info.to_dict(),
            "tenant_isolation_enabled": self.config.tenant_isolation_enabled
        }
    
    def validate_cross_tenant_request(self, requesting_tenant: TenantInfo, target_tenant_id: str) -> bool:
        """Validate if a cross-tenant request is allowed"""
        if not self.config.tenant_isolation_enabled:
            return True
        
        # For now, only allow requests within the same tenant
        # In the future, this could be extended with cross-tenant permissions
        return requesting_tenant.tenant_id == target_tenant_id
    
    def get_shared_resource_access(self, tenant_info: TenantInfo, resource_type: str) -> bool:
        """Check if a tenant has access to shared resources of a specific type"""
        # Define which resources are shared across tenants
        shared_resources = {
            "candidates": True,  # Candidates are shared across tenants
            "users": False,      # Users are tenant-specific
            "jobs": False,       # Jobs are tenant-specific
            "feedback": False,   # Feedback is tenant-specific
        }
        
        return shared_resources.get(resource_type, False)


# Global instance of the tenant resolver
sar_tenant_resolver = TenantResolver()


# FastAPI dependency for tenant resolution
async def get_tenant_info(request: Request):
    """FastAPI dependency to get tenant information from the request"""
    try:
        tenant_info = sar_tenant_resolver.get_tenant_from_request(request)
        if not tenant_info and sar_tenant_resolver.config.require_tenant_header:
            raise HTTPException(status_code=400, detail="Tenant ID is required")
        return tenant_info
    except TenantResolutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tenant resolution error: {str(e)}")


# Convenience function to validate tenant access to resources
def validate_tenant_access_to_resource(tenant_info: TenantInfo, resource_tenant_id: str):
    """Validate that a tenant has access to a specific resource, raising HTTPException if not"""
    if not sar_tenant_resolver.validate_tenant_access(tenant_info, resource_tenant_id):
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied: Tenant {tenant_info.tenant_id} cannot access resource belonging to tenant {resource_tenant_id}"
        )