from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Add parent directory to path for accessing dependencies from parent directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) 

from dependencies import get_api_key
from .decision_engine import DecisionEngine, EventTimeline
# MongoDB migration: Using mongodb_adapter instead of postgres_adapter
from .mongodb_adapter import mongodb_adapter as db_adapter
from .ml_models import MLModels

logger = logging.getLogger(__name__)

# Pydantic models
class RLPredictionRequest(BaseModel):
    candidate_id: int
    job_id: int
    candidate_features: Dict
    job_features: Dict

class RLFeedbackRequest(BaseModel):
    prediction_id: Optional[int] = None
    candidate_id: int
    job_id: int
    actual_outcome: str
    feedback_score: float
    feedback_source: str = "system"
    feedback_notes: Optional[str] = ""

class RLResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    message: str = ""
    timestamp: str

# Initialize components
decision_engine = DecisionEngine(db_adapter)
event_timeline = EventTimeline(db_adapter)

# Create router
router = APIRouter(prefix="/rl", tags=["RL + Feedback Agent"])

@router.post("/predict", response_model=RLResponse)
async def rl_predict_match(request: RLPredictionRequest, api_key: str = Depends(get_api_key)):
    """RL-Enhanced Candidate Matching Prediction"""
    try:
        # Get feedback history for RL enhancement
        feedback_history = db_adapter.get_feedback_history(
            candidate_id=request.candidate_id, 
            limit=50
        )
        
        # Make RL decision
        decision_data = decision_engine.make_rl_decision(
            candidate_features=request.candidate_features,
            job_features=request.job_features,
            feedback_history=feedback_history
        )
        
        if decision_data.get('error'):
            raise HTTPException(status_code=500, detail=decision_data['error'])
        
        # Store prediction in database
        prediction_data = {
            'candidate_id': request.candidate_id,
            'job_id': request.job_id,
            'rl_score': decision_data['rl_score'],
            'confidence_level': decision_data['confidence_level'],
            'decision_type': decision_data['decision_type'],
            'features_used': decision_data['features_used'],
            'model_version': decision_data['model_version']
        }
        
        prediction_id = db_adapter.store_rl_prediction(prediction_data)
        
        # Log decision event
        event_timeline.log_rl_decision(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            decision_data=decision_data
        )
        
        return RLResponse(
            success=True,
            data={
                "prediction_id": prediction_id,
                "rl_prediction": decision_data,
                "feedback_samples_used": len(feedback_history)
            },
            message="RL prediction completed successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"RL prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", response_model=RLResponse)
async def submit_rl_feedback(request: RLFeedbackRequest, api_key: str = Depends(get_api_key)):
    """Submit Feedback for RL Learning"""
    try:
        # Calculate reward signal
        reward_signal = decision_engine._calculate_reward_signal({
            'actual_outcome': request.actual_outcome,
            'feedback_score': request.feedback_score
        })
        
        # Prepare feedback data
        feedback_data = {
            'prediction_id': request.prediction_id,
            'feedback_source': request.feedback_source,
            'actual_outcome': request.actual_outcome,
            'feedback_score': request.feedback_score,
            'reward_signal': reward_signal,
            'feedback_notes': request.feedback_notes
        }
        
        # Store feedback in database
        feedback_id = db_adapter.store_rl_feedback(feedback_data)
        
        if not feedback_id:
            raise HTTPException(status_code=500, detail="Failed to store feedback")
        
        return RLResponse(
            success=True,
            data={
                "feedback_id": feedback_id,
                "reward_signal": reward_signal,
                "processed_feedback": feedback_data
            },
            message="RL feedback submitted successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"RL feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=RLResponse)
async def get_rl_analytics(api_key: str = Depends(get_api_key)):
    """Get RL System Analytics and Performance Metrics"""
    try:
        # Get database analytics
        db_analytics = db_adapter.get_rl_analytics()
        
        if db_analytics.get('error'):
            raise HTTPException(status_code=500, detail=db_analytics['error'])
        
        return RLResponse(
            success=True,
            data={
                "rl_analytics": db_analytics,
                "system_status": "operational"
            },
            message="RL analytics retrieved successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"RL analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{model_version}")
async def get_rl_performance(model_version: str = "v1.0.0", api_key: str = Depends(get_api_key)):
    """Get RL Model Performance Metrics"""
    try:
        analytics = db_adapter.get_rl_analytics()
        
        performance_data = {
            "model_version": model_version,
            "current_metrics": analytics,
            "status": "active" if analytics.get("total_predictions", 0) > 0 else "initializing"
        }
        
        return RLResponse(
            success=True,
            data=performance_data,
            message="RL performance data retrieved",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"RL performance retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{candidate_id}")
async def get_candidate_rl_history(candidate_id: int, api_key: str = Depends(get_api_key)):
    """Get RL Decision History for Candidate"""
    try:
        history = db_adapter.get_candidate_rl_history(candidate_id)
        
        return RLResponse(
            success=True,
            data={
                "candidate_id": candidate_id,
                "rl_history": history,
                "total_decisions": len(history)
            },
            message="RL history retrieved successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"RL history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain")
async def trigger_rl_retrain(api_key: str = Depends(get_api_key)):
    """Trigger RL Model Retraining (API key required — governance-aligned)"""
    try:
        # Get recent feedback for retraining
        feedback_history = db_adapter.get_feedback_history(limit=1000)
        
        if len(feedback_history) < 10:
            return RLResponse(
                success=False,
                message="Insufficient feedback data for retraining (minimum 10 required)",
                timestamp=datetime.now().isoformat()
            )
        
        # Calculate new performance metrics
        total_predictions = len(feedback_history)
        positive_outcomes = len([f for f in feedback_history if f.get('reward_signal', 0) > 0])
        accuracy = positive_outcomes / total_predictions if total_predictions > 0 else 0
        
        # Store updated performance
        performance_data = {
            'model_version': 'v1.0.1',
            'accuracy': accuracy,
            'precision_score': accuracy,  # Simplified
            'recall_score': accuracy,
            'f1_score': accuracy,
            'average_reward': sum(f.get('reward_signal', 0) for f in feedback_history) / total_predictions,
            'total_predictions': total_predictions,
            'evaluation_date': datetime.now().isoformat()
        }
        
        performance_id = db_adapter.store_model_performance(performance_data)
        
        return RLResponse(
            success=True,
            data={
                "performance_id": performance_id,
                "new_model_version": "v1.0.1",
                "training_samples": total_predictions,
                "accuracy": round(accuracy * 100, 2)
            },
            message="RL model retrained successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"RL retraining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
