"""
MongoDB Checkpointer for LangGraph
Custom implementation to replace PostgresSaver
"""
from typing import Any, Dict, Iterator, Optional, Tuple
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class MongoDBSaver(BaseCheckpointSaver):
    """MongoDB-based checkpoint saver for LangGraph workflows"""
    
    def __init__(self, mongodb_uri: str = None, db_name: str = None):
        super().__init__()
        self._client: Optional[MongoClient] = None
        self._db = None
        self._mongodb_uri = mongodb_uri or os.getenv("DATABASE_URL") or os.getenv("MONGODB_URI")
        self._db_name = db_name or os.getenv("MONGODB_DB_NAME", "bhiv_hr")
        self._collection_name = "langgraph_checkpoints"
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        try:
            if not self._mongodb_uri:
                raise ValueError("MongoDB URI is required")
            
            self._client = MongoClient(self._mongodb_uri, serverSelectionTimeoutMS=5000)
            self._client.admin.command('ping')  # Test connection
            self._db = self._client[self._db_name]
            
            # Create indexes for efficient querying
            self._db[self._collection_name].create_index([("thread_id", 1), ("thread_ts", -1)])
            
            logger.info(f"✅ MongoDB checkpointer connected to {self._db_name}")
        except Exception as e:
            logger.error(f"❌ MongoDB checkpointer connection failed: {e}")
            raise
    
    @classmethod
    def from_conn_string(cls, conn_string: str, db_name: str = None) -> "MongoDBSaver":
        """Create saver from connection string (compatible with PostgresSaver API)"""
        return cls(mongodb_uri=conn_string, db_name=db_name)
    
    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """Serialize checkpoint for MongoDB storage"""
        return {
            "v": checkpoint.get("v", 1),
            "ts": checkpoint.get("ts", datetime.utcnow().isoformat()),
            "id": checkpoint.get("id"),
            "channel_values": json.dumps(checkpoint.get("channel_values", {})),
            "channel_versions": json.dumps(checkpoint.get("channel_versions", {})),
            "versions_seen": json.dumps(checkpoint.get("versions_seen", {})),
        }
    
    def _deserialize_checkpoint(self, doc: Dict[str, Any]) -> Checkpoint:
        """Deserialize checkpoint from MongoDB document"""
        return {
            "v": doc.get("v", 1),
            "ts": doc.get("ts"),
            "id": doc.get("id"),
            "channel_values": json.loads(doc.get("channel_values", "{}")),
            "channel_versions": json.loads(doc.get("channel_versions", "{}")),
            "versions_seen": json.loads(doc.get("versions_seen", "{}")),
        }
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get checkpoint tuple for a thread"""
        thread_id = config.get("configurable", {}).get("thread_id")
        thread_ts = config.get("configurable", {}).get("thread_ts")
        
        if not thread_id:
            return None
        
        try:
            query = {"thread_id": thread_id}
            if thread_ts:
                query["thread_ts"] = thread_ts
            
            doc = self._db[self._collection_name].find_one(
                query,
                sort=[("thread_ts", -1)]
            )
            
            if not doc:
                return None
            
            checkpoint = self._deserialize_checkpoint(doc.get("checkpoint", {}))
            metadata = doc.get("metadata", {})
            parent_config = doc.get("parent_config")
            
            return CheckpointTuple(
                config={"configurable": {"thread_id": thread_id, "thread_ts": doc.get("thread_ts")}},
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config
            )
        except Exception as e:
            logger.error(f"Error getting checkpoint: {e}")
            return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints for a thread"""
        query = {}
        
        if config:
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                query["thread_id"] = thread_id
        
        if before:
            before_ts = before.get("configurable", {}).get("thread_ts")
            if before_ts:
                query["thread_ts"] = {"$lt": before_ts}
        
        if filter:
            for key, value in filter.items():
                query[f"metadata.{key}"] = value
        
        try:
            cursor = self._db[self._collection_name].find(query).sort("thread_ts", -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            for doc in cursor:
                checkpoint = self._deserialize_checkpoint(doc.get("checkpoint", {}))
                metadata = doc.get("metadata", {})
                parent_config = doc.get("parent_config")
                
                yield CheckpointTuple(
                    config={"configurable": {"thread_id": doc.get("thread_id"), "thread_ts": doc.get("thread_ts")}},
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=parent_config
                )
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> Dict[str, Any]:
        """Save a checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        thread_ts = checkpoint.get("ts", datetime.utcnow().isoformat())
        
        if not thread_id:
            raise ValueError("thread_id is required in config")
        
        try:
            doc = {
                "thread_id": thread_id,
                "thread_ts": thread_ts,
                "checkpoint": self._serialize_checkpoint(checkpoint),
                "metadata": metadata or {},
                "parent_config": config.get("configurable", {}).get("parent_config"),
                "created_at": datetime.utcnow()
            }
            
            self._db[self._collection_name].update_one(
                {"thread_id": thread_id, "thread_ts": thread_ts},
                {"$set": doc},
                upsert=True
            )
            
            return {"configurable": {"thread_id": thread_id, "thread_ts": thread_ts}}
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            logger.info("MongoDB checkpointer connection closed")
