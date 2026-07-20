"""Database-backed workflow tracker using MongoDB with fallback support"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

logger = logging.getLogger(__name__)


class DatabaseWorkflowTracker:
    def __init__(self):
        self._client = None
        self._db = None
        self.fallback_storage = {}  # In-memory fallback
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB database with fallback to in-memory"""
        try:
            mongodb_uri = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL') or os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("No MongoDB URI configured")
            
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.admin.command('ping')
            
            db_name = os.getenv('MONGODB_DB_NAME', 'bhiv_hr')
            self._db = self._client[db_name]
            logger.info("✅ MongoDB connection established for workflow tracking")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection failed, using in-memory fallback: {str(e)}")
            self._client = None
            self._db = None
    
    def _get_collection(self):
        """Get workflows collection"""
        if self._db is None:
            return None
        return self._db.workflows
    
    def _serialize_id(self, doc: dict) -> dict:
        """Convert ObjectId to string for JSON serialization"""
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc
    
    def create_workflow(self, workflow_id: str, workflow_type: str = "candidate_application", 
                       candidate_id: int = None, job_id: int = None, client_id: str = None,
                       input_data: Dict = None):
        """Create new workflow with database + fallback"""
        workflow_data = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "status": "running",
            "candidate_id": candidate_id,
            "job_id": job_id,
            "client_id": client_id,
            "progress_percentage": 0,
            "current_step": "initializing",
            "total_steps": 5,
            "input_data": input_data or {},
            "output_data": {},
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        collection = self._get_collection()
        if collection is not None:
            try:
                collection.insert_one(workflow_data)
                logger.info(f"✅ Workflow {workflow_id} created in database")
                return
            except Exception as e:
                logger.error(f"❌ Failed to create workflow in database: {e}")
        
        # Fallback to in-memory
        workflow_data['started_at'] = workflow_data['started_at'].isoformat()
        workflow_data['updated_at'] = workflow_data['updated_at'].isoformat()
        self.fallback_storage[workflow_id] = workflow_data
        logger.info(f"⚠️ Workflow {workflow_id} created in fallback storage")
    
    def update_workflow(self, workflow_id: str, **kwargs):
        """Update workflow with detailed progress tracking"""
        update_data = {}
        
        for key, value in kwargs.items():
            if key in ['status', 'progress_percentage', 'current_step', 'total_steps', 
                      'error_message', 'completed_at', 'output_data', 'input_data']:
                update_data[key] = value
        
        if not update_data:
            return
        
        # Always update updated_at
        update_data['updated_at'] = datetime.utcnow()
        
        collection = self._get_collection()
        if collection is not None:
            try:
                collection.update_one(
                    {'workflow_id': workflow_id},
                    {'$set': update_data}
                )
                logger.debug(f"✅ Workflow {workflow_id} updated in database")
                return
            except Exception as e:
                logger.error(f"❌ Failed to update workflow in database: {e}")
        
        # Fallback to in-memory
        if workflow_id in self.fallback_storage:
            for key, value in update_data.items():
                if isinstance(value, datetime):
                    self.fallback_storage[workflow_id][key] = value.isoformat()
                else:
                    self.fallback_storage[workflow_id][key] = value
            logger.debug(f"⚠️ Workflow {workflow_id} updated in fallback storage")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow status from database or fallback"""
        collection = self._get_collection()
        if collection is not None:
            try:
                result = collection.find_one({'workflow_id': workflow_id})
                if result:
                    result = self._serialize_id(result)
                    # Convert datetime to ISO format strings
                    for key in ['started_at', 'updated_at', 'completed_at']:
                        if key in result and isinstance(result[key], datetime):
                            result[key] = result[key].isoformat()
                    return result
            except Exception as e:
                logger.error(f"❌ Failed to get workflow status: {e}")
        
        # Fallback to in-memory
        return self.fallback_storage.get(workflow_id)
    
    def list_workflows(self, limit: int = 50) -> List[Dict]:
        """List workflows from database or fallback"""
        collection = self._get_collection()
        if collection is not None:
            try:
                cursor = collection.find({}).sort('started_at', -1).limit(limit)
                workflows = []
                for doc in cursor:
                    doc = self._serialize_id(doc)
                    # Convert datetime to ISO format strings
                    for key in ['started_at', 'updated_at', 'completed_at']:
                        if key in doc and isinstance(doc[key], datetime):
                            doc[key] = doc[key].isoformat()
                    workflows.append(doc)
                return workflows
            except Exception as e:
                logger.error(f"❌ Failed to list workflows: {e}")
        
        # Fallback to in-memory
        workflows = list(self.fallback_storage.values())
        return sorted(workflows, key=lambda x: x.get('started_at', ''), reverse=True)[:limit]
    
    def get_active_workflows(self) -> List[Dict]:
        """Get all running workflows"""
        collection = self._get_collection()
        if collection is not None:
            try:
                cursor = collection.find(
                    {'status': {'$in': ['running', 'processing']}}
                ).sort('started_at', -1)
                
                workflows = []
                for doc in cursor:
                    doc = self._serialize_id(doc)
                    if isinstance(doc.get('started_at'), datetime):
                        doc['started_at'] = doc['started_at'].isoformat()
                    workflows.append(doc)
                return workflows
            except Exception as e:
                logger.error(f"❌ Failed to get active workflows: {e}")
        
        # Fallback to in-memory
        return [w for w in self.fallback_storage.values() 
                if w.get('status') in ['running', 'processing']]
    
    def complete_workflow(self, workflow_id: str, final_status: str = "completed", 
                         output_data: Dict = None, error_message: str = None):
        """Mark workflow as completed with final data"""
        update_data = {
            "status": final_status,
            "progress_percentage": 100 if final_status == "completed" else 0,
            "current_step": "finished" if final_status == "completed" else "failed",
            "completed_at": datetime.utcnow()
        }
        
        if output_data:
            update_data["output_data"] = output_data
        if error_message:
            update_data["error_message"] = error_message
        
        self.update_workflow(workflow_id, **update_data)
        logger.info(f"✅ Workflow {workflow_id} completed with status: {final_status}")
    
    def cleanup_old_workflows(self, days: int = 30):
        """Clean up old completed workflows"""
        collection = self._get_collection()
        if collection is not None:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                result = collection.delete_many({
                    'status': {'$in': ['completed', 'failed', 'cancelled']},
                    'started_at': {'$lt': cutoff_date}
                })
                logger.info(f"✅ Cleaned up {result.deleted_count} workflows older than {days} days")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup old workflows: {e}")


# Global tracker instance
tracker = DatabaseWorkflowTracker()
