"""
RL Database Manager for LangGraph Service
Provides rl_db_manager interface for RL data operations using MongoDB
Migrated from PostgreSQL to MongoDB
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)


class RLDatabaseManager:
    """Database manager for RL operations using MongoDB"""
    
    def __init__(self):
        self._client = None
        self._db = None
    
    def _get_connection(self):
        """Get MongoDB connection with lazy initialization"""
        if self._client is None:
            mongo_uri = os.getenv('MONGODB_URI') or os.getenv('DATABASE_URL')
            if not mongo_uri:
                logger.warning("MONGODB_URI not set - using mock mode for testing")
                return None
            
            try:
                self._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
                db_name = os.getenv('MONGODB_DB_NAME', 'bhiv_hr')
                self._db = self._client[db_name]
                # Test connection
                self._client.admin.command('ping')
                logger.info(f"✅ RL Database Manager connected to MongoDB: {db_name}")
            except Exception as e:
                logger.error(f"❌ MongoDB connection failed: {e}")
                self._client = None
                self._db = None
        
        return self._db
    
    def _serialize_id(self, doc: dict) -> dict:
        """Convert ObjectId to string for JSON serialization"""
        if doc and '_id' in doc:
            doc['id'] = str(doc['_id'])
            del doc['_id']
        return doc
    
    def get_feedback_history(self, candidate_id: int = None, limit: int = 100) -> List[Dict]:
        """Get feedback history for RL learning"""
        try:
            db = self._get_connection()
            if db is None:
                logger.warning("Database not available - returning empty feedback history")
                return []
            
            # Use aggregation to join rl_feedback with rl_predictions
            pipeline = [
                {
                    '$lookup': {
                        'from': 'rl_predictions',
                        'localField': 'prediction_id',
                        'foreignField': '_id',
                        'as': 'prediction'
                    }
                },
                {'$unwind': {'path': '$prediction', 'preserveNullAndEmptyArrays': True}},
                {'$sort': {'created_at': -1}},
                {'$limit': limit}
            ]
            
            if candidate_id:
                pipeline.insert(0, {
                    '$match': {'prediction.candidate_id': candidate_id}
                })
            
            feedback_history = []
            cursor = db.rl_feedback.aggregate(pipeline)
            
            for doc in cursor:
                feedback_dict = self._serialize_id(doc)
                
                # Extract prediction data
                if 'prediction' in feedback_dict:
                    prediction = feedback_dict.pop('prediction')
                    feedback_dict['candidate_features'] = prediction.get('features', {})
                    feedback_dict['rl_score'] = prediction.get('rl_score')
                
                feedback_history.append(feedback_dict)
            
            logger.debug(f"Retrieved {len(feedback_history)} feedback records")
            return feedback_history
            
        except Exception as e:
            logger.error(f"Failed to get feedback history: {e}")
            return []
    
    def store_rl_prediction(self, prediction_data: Dict) -> Optional[str]:
        """Store RL prediction in database"""
        try:
            db = self._get_connection()
            if db is None:
                logger.warning("Database not available - prediction not stored")
                return None
            
            doc = {
                'candidate_id': prediction_data.get('candidate_id'),
                'job_id': prediction_data.get('job_id'),
                'rl_score': prediction_data.get('rl_score', 0),
                'confidence_level': prediction_data.get('confidence_level', 50),
                'decision_type': prediction_data.get('decision_type', 'review'),
                'features': prediction_data.get('features_used', {}),
                'model_version': prediction_data.get('model_version', 'v1.0.0'),
                'created_at': datetime.utcnow()
            }
            
            result = db.rl_predictions.insert_one(doc)
            prediction_id = str(result.inserted_id)
            
            logger.info(f"✅ RL prediction stored: ID {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store RL prediction: {e}")
            return None
    
    def store_rl_feedback(self, feedback_data: Dict) -> Optional[str]:
        """Store RL feedback in database"""
        try:
            db = self._get_connection()
            if db is None:
                logger.warning("Database not available - feedback not stored")
                return None
            
            # Convert prediction_id string to ObjectId if needed
            prediction_id = feedback_data.get('prediction_id')
            if prediction_id and isinstance(prediction_id, str):
                try:
                    prediction_id = ObjectId(prediction_id)
                except:
                    pass
            
            doc = {
                'prediction_id': prediction_id,
                'feedback_source': feedback_data.get('feedback_source', 'system'),
                'actual_outcome': feedback_data.get('actual_outcome', 'unknown'),
                'feedback_score': feedback_data.get('feedback_score', 0),
                'reward_signal': feedback_data.get('reward_signal', 0),
                'feedback_notes': feedback_data.get('feedback_notes', ''),
                'created_at': datetime.utcnow()
            }
            
            result = db.rl_feedback.insert_one(doc)
            feedback_id = str(result.inserted_id)
            
            logger.info(f"✅ RL feedback stored: ID {feedback_id}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store RL feedback: {e}")
            return None
    
    def store_training_data(self, training_data: Dict) -> Optional[str]:
        """Store training data for RL model improvement"""
        try:
            db = self._get_connection()
            if db is None:
                logger.warning("Database not available - training data not stored")
                return None
            
            doc = {
                'candidate_features': training_data.get('candidate_features', {}),
                'job_features': training_data.get('job_features', {}),
                'matching_score': training_data.get('matching_score', 0),
                'actual_outcome': training_data.get('actual_outcome', 'unknown'),
                'reward': training_data.get('reward', 0),
                'feature_vector': training_data.get('feature_vector', []),
                'metadata': training_data.get('metadata', {}),
                'created_at': datetime.utcnow()
            }
            
            result = db.rl_training_data.insert_one(doc)
            training_id = str(result.inserted_id)
            
            logger.info(f"✅ RL training data stored: ID {training_id}")
            return training_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store training data: {e}")
            return None
    
    def store_model_performance(self, performance_data: Dict) -> Optional[str]:
        """Store model performance metrics"""
        try:
            db = self._get_connection()
            if db is None:
                logger.warning("Database not available - performance data not stored")
                return None
            
            doc = {
                'model_version': performance_data.get('model_version', 'v1.0.0'),
                'accuracy': performance_data.get('accuracy', 0),
                'precision_score': performance_data.get('precision_score', 0),
                'recall_score': performance_data.get('recall_score', 0),
                'f1_score': performance_data.get('f1_score', 0),
                'average_reward': performance_data.get('average_reward', 0),
                'total_predictions': performance_data.get('total_predictions', 0),
                'evaluation_date': performance_data.get('evaluation_date', datetime.utcnow()),
                'created_at': datetime.utcnow()
            }
            
            result = db.rl_model_performance.insert_one(doc)
            performance_id = str(result.inserted_id)
            
            logger.info(f"✅ Model performance stored: ID {performance_id}")
            return performance_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store model performance: {e}")
            return None
    
    def get_rl_analytics(self) -> Dict[str, Any]:
        """Get RL system analytics"""
        try:
            db = self._get_connection()
            if db is None:
                return {"error": "Database not available", "total_predictions": 0, "total_feedback": 0}
            
            # Get prediction counts
            total_predictions = db.rl_predictions.count_documents({})
            
            # Get feedback counts
            total_feedback = db.rl_feedback.count_documents({})
            
            # Get latest model performance
            latest_performance = db.rl_model_performance.find_one(
                {},
                sort=[('evaluation_date', -1)]
            )
            if latest_performance:
                latest_performance = self._serialize_id(latest_performance)
            
            # Get decision type distribution
            decision_pipeline = [
                {'$group': {'_id': '$decision_type', 'count': {'$sum': 1}}}
            ]
            decision_cursor = db.rl_predictions.aggregate(decision_pipeline)
            decision_distribution = {doc['_id']: doc['count'] for doc in decision_cursor if doc['_id']}
            
            analytics = {
                "total_predictions": total_predictions,
                "total_feedback": total_feedback,
                "feedback_rate": (total_feedback / max(total_predictions, 1)) * 100,
                "decision_distribution": decision_distribution,
                "latest_performance": latest_performance,
                "generated_at": datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get RL analytics: {e}")
            return {"error": str(e)}
    
    def get_candidate_rl_history(self, candidate_id: int) -> List[Dict]:
        """Get RL decision history for candidate"""
        try:
            db = self._get_connection()
            if db is None:
                return []
            
            # Use aggregation to join predictions with feedback
            pipeline = [
                {'$match': {'candidate_id': candidate_id}},
                {
                    '$lookup': {
                        'from': 'rl_feedback',
                        'localField': '_id',
                        'foreignField': 'prediction_id',
                        'as': 'feedback'
                    }
                },
                {'$unwind': {'path': '$feedback', 'preserveNullAndEmptyArrays': True}},
                {'$sort': {'created_at': -1}}
            ]
            
            history = []
            cursor = db.rl_predictions.aggregate(pipeline)
            
            for doc in cursor:
                history_dict = self._serialize_id(doc)
                
                # Extract feedback data if present
                if 'feedback' in history_dict and history_dict['feedback']:
                    feedback = history_dict.pop('feedback')
                    history_dict['actual_outcome'] = feedback.get('actual_outcome')
                    history_dict['feedback_score'] = feedback.get('feedback_score')
                    history_dict['reward_signal'] = feedback.get('reward_signal')
                else:
                    history_dict.pop('feedback', None)
                    history_dict['actual_outcome'] = None
                    history_dict['feedback_score'] = None
                    history_dict['reward_signal'] = None
                
                history.append(history_dict)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get candidate RL history: {e}")
            return []
    
    def log_rl_decision(self, event_data: Dict) -> Optional[str]:
        """Log RL decision event to audit log"""
        try:
            db = self._get_connection()
            if db is None:
                return None
            
            doc = {
                'action': 'rl_decision',
                'resource': 'rl_predictions',
                'resource_id': event_data.get('candidate_id'),
                'details': event_data,
                'timestamp': datetime.utcnow()
            }
            
            result = db.audit_logs.insert_one(doc)
            log_id = str(result.inserted_id)
            
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to log RL decision: {e}")
            return None


# Global instance - provides rl_db_manager interface
rl_db_manager = RLDatabaseManager()
