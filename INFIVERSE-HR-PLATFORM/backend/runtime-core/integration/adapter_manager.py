"""
Adapter Manager for the BHIV Application Framework

This module provides a centralized way to manage and execute all integration adapters.
"""

import logging
from typing import Dict, List, Any
from .adapters import get_all_adapters
from .adapters.base_adapter import BaseIntegrationAdapter
import os
import jwt
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime

logger = logging.getLogger(__name__)

class AdapterManager:
    """
    Manages all integration adapters for the BHIV Application Framework.
    
    The AdapterManager allows for:
    - Dynamic loading of adapters
    - Centralized execution of adapters
    - Configuration management
    - Error handling across all adapters
    - Secure authentication with API keys and JWT tokens
    - MongoDB-based audit logging
    """
    
    def __init__(self, adapter_configs: Dict[str, Dict[str, Any]] = None):
        """
        Initialize the AdapterManager with adapter configurations.
        
        Args:
            adapter_configs: Dictionary mapping adapter names to their configurations
                           If None, all adapters will be initialized as disabled
        """
        self.adapters: Dict[str, BaseIntegrationAdapter] = {}
        self.adapter_configs = adapter_configs or {}
        
        # Initialize authentication settings
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.candidate_jwt_secret_key = os.getenv("CANDIDATE_JWT_SECRET_KEY", "")
        self.api_key_secret = os.getenv("API_KEY_SECRET", "")
        
        # Initialize MongoDB connection for manager-level logging
        self._mongo_client = None
        self._db = None
        self._adapter_events_collection = None
        self._connect_to_mongodb()
        
        # Load all available adapters
        available_adapters = get_all_adapters()
        
        for adapter_name, adapter_class in available_adapters.items():
            # Get configuration for this adapter, default to disabled if not specified
            config = self.adapter_configs.get(adapter_name, {
                "name": f"{adapter_name.title()} Adapter",
                "enabled": False
            })
            config['name'] = config.get('name', f"{adapter_name.title()} Adapter")
            
            # Initialize the adapter
            adapter_instance = adapter_class(config)
            self.adapters[adapter_name] = adapter_instance
            
            logger.info(f"Initialized adapter: {adapter_name} (enabled: {adapter_instance.enabled})")
    
    def _connect_to_mongodb(self):
        """Establish MongoDB connection for adapter event logging"""
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
            self._adapter_events_collection = self._db.adapter_events
            
            # Create indexes for efficient queries
            self._adapter_events_collection.create_index([("event_type", 1)])
            self._adapter_events_collection.create_index([("timestamp", -1)])
            self._adapter_events_collection.create_index([("tenant_id", 1)])
            
            logger.info(f"✅ Connected to MongoDB for adapter event logging: {db_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB for adapter event logging: {e}")
            self._mongo_client = None
            self._db = None
            self._adapter_events_collection = None
    
    def _log_adapter_event(self, event_type: str, details: Dict[str, Any]):
        """Log adapter manager events to MongoDB for auditing purposes"""
        if not self._adapter_events_collection:
            return
        
        try:
            log_entry = {
                "event_type": event_type,
                "details": details,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            self._adapter_events_collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log adapter event: {e}")
    
    def execute_all_adapters(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all registered adapters with the given event.
        
        Args:
            event: Event data to process by all adapters
            
        Returns:
            Dictionary containing results from all adapters
        """
        results = {}
        
        # Log the execution event
        self._log_adapter_event("execute_all_adapters", {
            "event_id": event.get("event_id"),
            "action": event.get("action"),
            "tenant_id": event.get("tenant_id"),
            "user_id": event.get("user_id"),
            "adapter_count": len(self.adapters)
        })
        
        for adapter_name, adapter in self.adapters.items():
            try:
                result = adapter.execute(event)
                results[adapter_name] = result
            except Exception as e:
                logger.error(f"Error executing {adapter_name}: {str(e)}", exc_info=True)
                results[adapter_name] = {"error": str(e), "success": False}
        
        return results
    
    def execute_adapter(self, adapter_name: str, event: Dict[str, Any]) -> Any:
        """
        Execute a specific adapter with the given event.
        
        Args:
            adapter_name: Name of the adapter to execute
            event: Event data to process
            
        Returns:
            Result from the adapter execution
        """
        if adapter_name not in self.adapters:
            logger.warning(f"Adapter {adapter_name} not found")
            # Log the error event
            self._log_adapter_event("adapter_not_found", {
                "adapter_name": adapter_name,
                "event_id": event.get("event_id"),
                "action": event.get("action")
            })
            return None
        
        adapter = self.adapters[adapter_name]
        result = adapter.execute(event)
        
        # Log the execution event
        self._log_adapter_event("execute_adapter", {
            "adapter_name": adapter_name,
            "event_id": event.get("event_id"),
            "action": event.get("action"),
            "tenant_id": event.get("tenant_id"),
            "user_id": event.get("user_id"),
            "result": result
        })
        
        return result
    
    def get_active_adapters(self) -> List[str]:
        """
        Get a list of all currently active (enabled) adapters.
        
        Returns:
            List of adapter names that are currently enabled
        """
        return [name for name, adapter in self.adapters.items() if adapter.enabled]
    
    def toggle_adapter(self, adapter_name: str, enabled: bool) -> bool:
        """
        Enable or disable an adapter at runtime.
        
        Args:
            adapter_name: Name of the adapter to toggle
            enabled: Whether to enable or disable the adapter
            
        Returns:
            True if the adapter was found and toggled, False otherwise
        """
        if adapter_name not in self.adapters:
            logger.warning(f"Cannot toggle {adapter_name}: adapter not found")
            # Log the error event
            self._log_adapter_event("toggle_adapter_failed", {
                "adapter_name": adapter_name,
                "enabled": enabled,
                "reason": "adapter_not_found"
            })
            return False
        
        self.adapters[adapter_name].enabled = enabled
        logger.info(f"Toggled {adapter_name} to {'enabled' if enabled else 'disabled'}")
        
        # Log the toggle event
        self._log_adapter_event("toggle_adapter", {
            "adapter_name": adapter_name,
            "enabled": enabled
        })
        
        return True


# Example usage:
# 
# if __name__ == "__main__":
#     # Example configuration
#     configs = {
#         'artha': {
#             "name": "Artha Adapter",
#             "enabled": True,
#             "artha_api_url": "https://artha-api.example.com",
#             "artha_api_key": "your-key"
#         },
#         'karya': {
#             "name": "Karya Adapter", 
#             "enabled": True,
#             "karya_api_url": "https://karya-api.example.com",
#             "karya_api_key": "your-key"
#         }
#     }
#     
#     # Initialize manager
#     manager = AdapterManager(configs)
#     
#     # Example event
#     event = {
#         "event_id": "evt_123",
#         "action": "payroll_processed",
#         "tenant_id": "tenant_abc", 
#         "user_id": "user_123",
#         "timestamp": "2026-01-10T17:00:00Z"
#     }
#     
#     # Execute all adapters
#     results = manager.execute_all_adapters(event)
#     print(results)


# Initialize default instance for SAR framework
if __name__ != "__main__":
    # This creates a default adapter manager instance when the module is imported
    # This is used by the SAR integration framework
    default_configs = {
        'artha': {
            "name": "Artha Payroll Adapter",
            "enabled": False,  # Disabled by default for security
        },
        'karya': {
            "name": "Karya Task Adapter",
            "enabled": False,  # Disabled by default for security
        },
        'insightflow': {
            "name": "InsightFlow Analytics Adapter",
            "enabled": False,  # Disabled by default for security
        },
        'bucket': {
            "name": "Bucket Storage Adapter",
            "enabled": False,  # Disabled by default for security
        }
    }
    
    # Create default instance with default configurations
    default_adapter_manager = AdapterManager(default_configs)