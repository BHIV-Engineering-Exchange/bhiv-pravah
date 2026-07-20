"""
Base Integration Adapter for the BHIV Application Framework
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import os
import jwt
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseIntegrationAdapter(ABC):
    """
    Base class for all integration adapters in the BHIV Application Framework.
    
    Adapters are designed to be:
    - Optional: System works without any adapters
    - Pluggable: Can be enabled/disabled via configuration
    - Fail-safe: If an adapter fails, it doesn't break the main system
    - Secure: Supports API key and JWT token authentication
    - Auditable: Logs integration events to MongoDB
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adapter with configuration.
        
        Args:
            config: Dictionary containing adapter configuration
                   Must include 'enabled' key to control activation
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.name = config.get('name', self.__class__.__name__)
        
        # Initialize MongoDB connection
        self._mongo_client = None
        self._db = None
        self._integration_logs_collection = None
        self._connect_to_mongodb()
        
        # Initialize authentication settings
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.candidate_jwt_secret_key = os.getenv("CANDIDATE_JWT_SECRET_KEY", "")
        self.api_key_secret = os.getenv("API_KEY_SECRET", "")
        
    def _connect_to_mongodb(self):
        """Establish MongoDB connection for integration logging"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI", os.getenv("DATABASE_URL"))
            if not mongodb_uri:
                logger.warning("MONGODB_URI/DATABASE_URL not configured, skipping MongoDB integration")
                return
            
            self._mongo_client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=2,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
            )
            
            # Test connection
            self._mongo_client.admin.command('ping')
            
            db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")
            self._db = self._mongo_client[db_name]
            self._integration_logs_collection = self._db.integration_logs
            
            # Create indexes for efficient queries
            self._integration_logs_collection.create_index([("adapter_name", 1)])
            self._integration_logs_collection.create_index([("event_id", 1)])
            self._integration_logs_collection.create_index([("timestamp", -1)])
            self._integration_logs_collection.create_index([("tenant_id", 1)])
            
            logger.info(f"✅ Connected to MongoDB for integration logging: {db_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB for integration logging: {e}")
            self._mongo_client = None
            self._db = None
            self._integration_logs_collection = None
    
    def _log_integration_event(self, event: Dict[str, Any], result: Optional[Dict[str, Any]], error: Optional[str] = None):
        """Log integration event to MongoDB for auditing purposes"""
        if not self._integration_logs_collection:
            return
        
        try:
            log_entry = {
                "adapter_name": self.name,
                "event_id": event.get("event_id"),
                "action": event.get("action"),
                "tenant_id": event.get("tenant_id"),
                "user_id": event.get("user_id"),
                "event_data": event,
                "result": result,
                "error": error,
                "timestamp": event.get("timestamp"),
                "created_at": datetime.utcnow()
            }
            
            self._integration_logs_collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log integration event: {e}")
    
    def _validate_auth(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate authentication token (API key or JWT)
        Follows the same pattern as services for consistency
        """
        # Try API key first
        if self.api_key_secret and token == self.api_key_secret:
            return {
                "type": "api_key",
                "credentials": token,
                "user_id": "service",
                "role": "admin"
            }
        
        # Try JWT token with fallbacks
        # First try candidate JWT
        if self.candidate_jwt_secret_key:
            try:
                payload = jwt.decode(
                    token, 
                    self.candidate_jwt_secret_key, 
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                user_info = self._extract_user_from_payload(payload)
                return {
                    "type": "jwt_token",
                    "user_id": user_info["user_id"],
                    "email": user_info["email"],
                    "role": user_info["role"],
                    "name": user_info["name"],
                }
            except jwt.ExpiredSignatureError:
                pass  # Continue to try other methods
            except jwt.InvalidTokenError:
                pass  # Continue to try other methods
        
        # Then try client JWT
        if self.jwt_secret_key:
            try:
                payload = jwt.decode(
                    token, 
                    self.jwt_secret_key, 
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                user_info = self._extract_user_from_payload(payload)
                return {
                    "type": "jwt_token",
                    "user_id": user_info["user_id"],
                    "email": user_info["email"],
                    "role": user_info["role"],
                    "name": user_info["name"],
                }
            except jwt.ExpiredSignatureError:
                pass  # Continue to try other methods
            except jwt.InvalidTokenError:
                pass  # Continue to try other methods
        
        return None
    
    def _extract_user_from_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from JWT token payload"""
        user_id = payload.get("sub") or payload.get("candidate_id") or payload.get("client_id") or payload.get("user_id")
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("user_metadata", {}).get("role") or payload.get("role", "candidate"),
            "name": payload.get("user_metadata", {}).get("name") or payload.get("name", ""),
            "aud": payload.get("aud"),
            "exp": payload.get("exp"),
        }
    
    def execute(self, event: Dict[str, Any]) -> Optional[Any]:
        """
        Execute the adapter logic. This method wraps the internal implementation
        to ensure that adapter failures don't break the main application flow.
        
        Args:
            event: Event data to process
            
        Returns:
            Result of the adapter execution, or None if disabled/failure
        """
        if not self.enabled:
            logger.debug(f"Adapter {self.name} is disabled, skipping execution")
            # Log disabled execution
            self._log_integration_event(event, {"status": "skipped", "reason": "adapter_disabled"})
            return None
        
        try:
            logger.info(f"Executing adapter {self.name} for event: {event.get('action', 'unknown')}")
            result = self._execute_internal(event)
            logger.info(f"Adapter {self.name} executed successfully")
            
            # Log successful execution
            self._log_integration_event(event, result)
            return result
        except Exception as e:
            logger.error(f"Adapter {self.name} failed: {str(e)}", exc_info=True)
            # Log failed execution
            self._log_integration_event(event, None, str(e))
            # Don't let adapter failure break the main application flow
            return None
    
    @abstractmethod
    def _execute_internal(self, event: Dict[str, Any]) -> Any:
        """
        Internal method to be implemented by subclasses.
        This is where the actual adapter logic goes.
        
        Args:
            event: Event data to process
            
        Returns:
            Result of the processing
        """
        raise NotImplementedError("Subclasses must implement _execute_internal method")


# Example usage:
# 
# class ArthaAdapter(BaseIntegrationAdapter):
#     def _execute_internal(self, event):
#         # Implementation for Artha integration
#         pass
#
# class KaryaAdapter(BaseIntegrationAdapter):
#     def _execute_internal(self, event):
#         # Implementation for Karya integration
#         pass
#
# class InsightFlowAdapter(BaseIntegrationAdapter):
#     def _execute_internal(self, event):
#         # Implementation for InsightFlow integration
#         pass
#
# class BucketAdapter(BaseIntegrationAdapter):
#     def _execute_internal(self, event):
#         # Implementation for Bucket integration
#         pass