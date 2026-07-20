from fastapi import APIRouter, HTTPException, Request
from app.models import FeedbackCreate
from app.utils.helpers import load_json, save_json
from app.utils.database import db_manager
from app.utils.decision_engine import DecisionEngine, EventTimeline
from datetime import datetime
import csv
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/hr_feedback")
def submit_feedback(feedback: FeedbackCreate, request: Request):
    """Submit HR feedback with decision logging"""
    try:
        # Validate candidate exists
        candidate = db_manager.get_candidate(feedback.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Add feedback to database
        feedback_dict = feedback.dict()
        feedback_dict["hr_name"] = "System"  # In production, get from authenticated user
        feedback_id = db_manager.add_feedback(feedback_dict)
        
        # Decision logging logic using DecisionEngine
        decision_id = DecisionEngine.log_decision(
            candidate_id=feedback.candidate_id,
            decision=feedback.actual_outcome,
            score=feedback.feedback_score,
            reasoning=feedback.comment,
            hr_name=feedback_dict["hr_name"]
        )
        
        # Event timeline logging
        EventTimeline.log_event(
            candidate_id=feedback.candidate_id,
            event_type="feedback_submitted",
            details={
                "feedback_id": feedback_id,
                "decision_id": decision_id,
                "score": feedback.feedback_score,
                "outcome": feedback.actual_outcome
            }
        )
        
        timestamp = datetime.now().isoformat()
        
        # Maintain CSV compatibility
        csv_file = "feedback/feedback_log.csv"
        file_exists = os.path.exists(csv_file)
        
        try:
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "candidate_id", "score", "comment", "outcome", "event"])
                writer.writerow([timestamp, feedback.candidate_id, feedback.feedback_score, 
                               feedback.comment, feedback.actual_outcome, "feedback_processed"])
        except Exception as csv_error:
            logger.error(f"CSV logging failed: {csv_error}")
        
        # Event timeline logging
        timeline_entry = {
            "timestamp": timestamp,
            "event_type": "feedback_submitted",
            "candidate_id": feedback.candidate_id,
            "details": {
                "score": feedback.feedback_score,
                "outcome": feedback.actual_outcome,
                "comment": feedback.comment[:100] + "..." if len(feedback.comment) > 100 else feedback.comment
            }
        }
        
        # Maintain JSON compatibility
        system_logs = load_json("feedback/system_log.json")
        if not isinstance(system_logs, list):
            system_logs = []
        
        system_logs.append({
            "timestamp": timestamp,
            "event": "feedback_processed",
            "details": timeline_entry
        })
        save_json("feedback/system_log.json", system_logs)
        
        return {
            "status": "success", 
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id,
            "decision_id": decision_id,
            "decision_logged": True,
            "timeline_logged": True,
            "timestamp": timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        db_manager.log_system_event("ERROR", "feedback_submission_failed", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/logs")
def get_feedback_logs():
    """Get feedback logs"""
    try:
        logs = []
        
        # Try CSV first
        csv_file = "feedback/feedback_log.csv"
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                logs = list(reader)
        
        # Fallback to JSON
        if not logs:
            json_logs = load_json("feedback/system_log.json")
            if isinstance(json_logs, list):
                logs = [log.get("details", {}) for log in json_logs if log.get("event") == "feedback_processed"]
        
        return logs
    except Exception as e:
        logger.error(f"Failed to load feedback logs: {e}")
        return []

@router.get("/timeline/{candidate_id}")
def get_candidate_timeline(candidate_id: int):
    """Get event timeline for candidate"""
    try:
        # Get timeline from EventTimeline
        timeline = EventTimeline.get_candidate_timeline(candidate_id)
        
        return {
            "candidate_id": candidate_id,
            "timeline": timeline,
            "total_events": len(timeline)
        }
    except Exception as e:
        logger.error(f"Failed to get candidate timeline: {e}")
        return {"candidate_id": candidate_id, "timeline": [], "error": str(e)}

@router.get("/decisions/analytics")
def get_decision_analytics():
    """Get decision analytics and patterns"""
    try:
        analytics = DecisionEngine.get_decision_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Failed to get decision analytics: {e}")
        return {"error": str(e)}

@router.get("/decisions/history/{candidate_id}")
def get_candidate_decisions(candidate_id: int):
    """Get decision history for specific candidate"""
    try:
        decisions = DecisionEngine.get_decision_history(candidate_id)
        return {
            "candidate_id": candidate_id,
            "decisions": decisions,
            "total_decisions": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to get candidate decisions: {e}")
        return {"candidate_id": candidate_id, "decisions": [], "error": str(e)}