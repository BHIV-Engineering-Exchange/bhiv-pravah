#!/usr/bin/env python3
"""
MongoDB Connection Configuration
"""

import os
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class MongoDBConnection:
    """MongoDB connection handler"""
    
    _client: Optional[MongoClient] = None
    _async_client: Optional[AsyncIOMotorClient] = None
    _db = None
    _async_db = None
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Get MongoDB connection string from environment"""
        mongodb_url = os.getenv('MONGODB_URL')
        
        if not mongodb_url:
            # Default to local MongoDB
            host = os.getenv('MONGODB_HOST', 'localhost')
            port = os.getenv('MONGODB_PORT', '27017')
            database = os.getenv('MONGODB_DATABASE', 'ai_crm_logistics')
            username = os.getenv('MONGODB_USERNAME', '')
            password = os.getenv('MONGODB_PASSWORD', '')
            
            if username and password:
                mongodb_url = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
            else:
                mongodb_url = f"mongodb://{host}:{port}/{database}"
        
        return mongodb_url
    
    @classmethod
    def get_database_name(cls) -> str:
        """Get database name"""
        return os.getenv('MONGODB_DATABASE', 'ai_crm_logistics')
    
    @classmethod
    def connect(cls):
        """Create MongoDB connection"""
        if cls._client is None:
            connection_string = cls.get_connection_string()
            cls._client = MongoClient(connection_string)
            cls._db = cls._client[cls.get_database_name()]
            print(f"[OK] Connected to MongoDB: {cls.get_database_name()}")
        return cls._db
    
    @classmethod
    def connect_async(cls):
        """Create async MongoDB connection"""
        if cls._async_client is None:
            connection_string = cls.get_connection_string()
            cls._async_client = AsyncIOMotorClient(connection_string)
            cls._async_db = cls._async_client[cls.get_database_name()]
            print(f"[OK] Connected to MongoDB (async): {cls.get_database_name()}")
        return cls._async_db
    
    @classmethod
    def get_database(cls):
        """Get database instance"""
        if cls._db is None:
            cls.connect()
        return cls._db
    
    @classmethod
    def get_async_database(cls):
        """Get async database instance"""
        if cls._async_db is None:
            cls.connect_async()
        return cls._async_db
    
    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            print("[OK] MongoDB connection closed")
        
        if cls._async_client:
            cls._async_client.close()
            cls._async_client = None
            cls._async_db = None
    
    @classmethod
    def test_connection(cls) -> bool:
        """Test MongoDB connection"""
        try:
            db = cls.get_database()
            db.command('ping')
            print("[OK] MongoDB connection test successful")
            return True
        except Exception as e:
            print(f"[ERROR] MongoDB connection test failed: {e}")
            return False


# Initialize database connection
def get_db():
    """Get MongoDB database instance"""
    return MongoDBConnection.get_database()


def get_async_db():
    """Get async MongoDB database instance"""
    return MongoDBConnection.get_async_database()


# Collection names
COLLECTIONS = {
    # Logistics collections
    'orders': 'orders',
    'returns': 'returns',
    'restock_requests': 'restock_requests',
    'agent_logs': 'agent_logs',
    'human_reviews': 'human_reviews',
    'inventory': 'inventory',
    'purchase_orders': 'purchase_orders',
    'suppliers': 'suppliers',
    'shipments': 'shipments',
    'couriers': 'couriers',
    'products': 'products',
    'delivery_events': 'delivery_events',
    'alerts': 'alerts',
    'kpi_metrics': 'kpi_metrics',
    'notification_logs': 'notification_logs',
    
    # CRM collections
    'accounts': 'accounts',
    'contacts': 'contacts',
    'leads': 'leads',
    'opportunities': 'opportunities',
    'activities': 'activities',
    'communication_logs': 'communication_logs',
    'tasks': 'tasks',
    'notes': 'notes',
    
    # Auth collections
    'users': 'users',

    # SETU collections
    'setu_trace_lineage': 'setu_trace_lineage',
    'setu_trace_logs': 'setu_trace_logs',
    'setu_lineage_events': 'setu_lineage_events',
    'setu_telemetry_events': 'setu_telemetry_events',
}
