from fastapi import APIRouter, HTTPException
from app.utils.notifications import NotificationManager
from app.utils.ai_engine import AIEngine
from app.utils.helpers import load_json
from app.utils.database import db_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/smart", tags=["smart-features"])

@router.post("/schedule-followup/{candidate_id}")
def schedule_smart_followup(candidate_id: int, days: int = 3):
    """Schedule AI-optimized follow-up"""
    try:
        success = NotificationManager.schedule_follow_up(candidate_id, days)
        if success:
            return {"status": "success", "message": f"Follow-up scheduled for {days} days"}
        else:
            raise HTTPException(status_code=500, detail="Failed to schedule follow-up")
    except Exception as e:
        logger.error(f"Follow-up scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{candidate_id}")
def get_ai_recommendations(candidate_id: int):
    """Get AI-powered candidate recommendations"""
    try:
        feedback_history = db_manager.get_feedback_by_candidate(candidate_id)
        recommendations = AIEngine.generate_recommendations(candidate_id, feedback_history)
        
        return {
            "candidate_id": candidate_id,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    except Exception as e:
        logger.error(f"AI recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smart-reminder/{candidate_id}")
def send_smart_reminder(candidate_id: int, message_type: str = "interview_reminder"):
    """Send personalized smart reminder"""
    try:
        result = NotificationManager.send_smart_reminder(candidate_id, message_type)
        return result
    except Exception as e:
        logger.error(f"Smart reminder failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-notifications")
def get_pending_notifications():
    """Get all pending smart notifications"""
    try:
        notifications = NotificationManager.get_pending_notifications()
        return {
            "pending_notifications": notifications,
            "total_pending": len(notifications)
        }
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-score-update")
def update_all_match_scores():
    """Update AI match scores for all candidates"""
    try:
        candidates = load_json("data/candidates.json")
        if not isinstance(candidates, list):
            return {"updated": 0, "message": "No candidates found"}
        
        updated_count = 0
        for candidate in candidates:
            new_score = AIEngine.calculate_match_score(candidate)
            candidate['match_score'] = new_score
            updated_count += 1
        
        from app.utils.helpers import save_json
        save_json("data/candidates.json", candidates)
        
        return {
            "status": "success",
            "updated": updated_count,
            "message": f"Updated match scores for {updated_count} candidates"
        }
    except Exception as e:
        logger.error(f"Bulk score update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))