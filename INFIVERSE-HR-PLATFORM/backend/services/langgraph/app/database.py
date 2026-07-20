"""
MongoDB Connection Module for LangGraph Service
Uses pymongo (sync MongoDB driver)
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import os
import logging
import sys

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """
    Get or create MongoDB client (sync)
    Uses singleton pattern for connection reuse
    """
    global _mongo_client
    
    if _mongo_client is None:
        # Try to get from config first, then environment variables
        try:
            from config import settings
            mongodb_uri = settings.database_url
        except (ImportError, AttributeError):
            mongodb_uri = os.getenv("DATABASE_URL") or os.getenv("MONGODB_URI")
        
        if not mongodb_uri:
            raise ValueError(
                "DATABASE_URL or MONGODB_URI environment variable is required"
            )
        
        try:
            _mongo_client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=2,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
            )
            # Test connection
            _mongo_client.admin.command('ping')
            logger.info("MongoDB client (sync) initialized and connected")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB client: {e}")
            raise
    
    return _mongo_client


def get_mongo_db() -> Database:
    """
    Get or create MongoDB database instance (sync)
    """
    global _mongo_db
    
    if _mongo_db is None:
        client = get_mongo_client()
        db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")
        _mongo_db = client[db_name]
        logger.info(f"Using MongoDB database: {db_name}")
    
    return _mongo_db


def get_collection(collection_name: str) -> Collection:
    """
    Get a MongoDB collection (sync)
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection object
    """
    db = get_mongo_db()
    return db[collection_name]


def close_mongo_connections():
    """
    Close MongoDB connections (useful for cleanup/g testing)
    """
    global _mongo_client, _mongo_db
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        logger.info("MongoDB client closed")
    
    _mongo_db = None
