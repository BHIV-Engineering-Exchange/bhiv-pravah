from datetime import datetime
from typing import List, Dict, Any
import json

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    MongoClient = None
    ConnectionFailure = Exception
    ServerSelectionTimeoutError = Exception
    PYMONGO_AVAILABLE = False

class MongoDBAdapter:
    """MongoDB adapter for storing user interactions in MongoDB Atlas"""
    
    def __init__(self, connection_string: str = None, database_name: str = "core_integrator"):
        if not PYMONGO_AVAILABLE:
            raise RuntimeError("pymongo not installed; cannot use MongoDB adapter")
        
        if not connection_string:
            raise ValueError("MongoDB connection string is required")
        
        self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        self.db = self.client[database_name]
        self.collection = self.db.interactions
        
        # Create index for efficient queries
        self.collection.create_index([("user_id", 1), ("module", 1), ("timestamp", -1)])
        
        # Test connection
        try:
            self.client.admin.command('ping')
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def store_interaction(self, user_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        """Store a request-response interaction"""
        timestamp = datetime.now().isoformat()
        module = request_data.get("module", "unknown")
        
        document = {
            "user_id": user_id,
            "module": module,
            "timestamp": timestamp,
            "request_data": request_data,
            "response_data": response_data
        }
        
        self.collection.insert_one(document)
        
        # Retention: keep only latest 5 interactions per user per module
        pipeline = [
            {"$match": {"user_id": user_id, "module": module}},
            {"$sort": {"timestamp": -1, "_id": -1}},
            {"$skip": 5}
        ]
        
        old_docs = list(self.collection.aggregate(pipeline))
        if old_docs:
            old_ids = [doc["_id"] for doc in old_docs]
            self.collection.delete_many({"_id": {"$in": old_ids}})
    
    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get full interaction history for a user"""
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort([("timestamp", -1), ("_id", -1)])
        
        return [
            {
                "module": doc["module"],
                "timestamp": doc["timestamp"],
                "request": doc["request_data"],
                "response": doc["response_data"]
            }
            for doc in cursor
        ]
    
    def get_context(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent context (last N interactions) for a user"""
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort([("timestamp", -1), ("_id", -1)]).limit(limit)
        
        return [
            {
                "module": doc["module"],
                "timestamp": doc["timestamp"],
                "request": doc["request_data"],
                "response": doc["response_data"]
            }
            for doc in cursor
        ]