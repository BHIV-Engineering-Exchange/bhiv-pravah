from fastapi import APIRouter, HTTPException, Request
from app.models import CandidateCreate
from app.utils.helpers import load_json, save_json
from app.utils.database import db_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidate", tags=["candidates"])

@router.post("/add")
def add_candidate(candidate: CandidateCreate, request: Request):
    """Add new candidate with database backend"""
    try:
        candidate_dict = candidate.dict()
        candidate_dict["match_score"] = 0.0
        
        # Add to database
        candidate_id = db_manager.add_candidate(candidate_dict)
        
        # Log the action
        db_manager.log_system_event(
            "INFO", 
            "candidate_added", 
            f"New candidate added: {candidate.name}",
            {"candidate_id": candidate_id, "email": candidate.email}
        )
        
        # Maintain JSON compatibility
        candidates = load_json("data/candidates.json")
        if not isinstance(candidates, list):
            candidates = []
        
        candidate_dict["id"] = candidate_id
        candidates.append(candidate_dict)
        save_json("data/candidates.json", candidates)
        
        return {
            "status": "success", 
            "candidate_id": candidate_id, 
            "message": "Candidate added successfully",
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to add candidate: {e}")
        db_manager.log_system_event("ERROR", "candidate_add_failed", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list")
def list_candidates():
    """List all candidates"""
    candidates = load_json("data/candidates.json")
    return candidates if isinstance(candidates, list) else []

@router.get("/{candidate_id}")
def get_candidate(candidate_id: int):
    """Get specific candidate by ID"""
    candidates = load_json("data/candidates.json")
    if not isinstance(candidates, list):
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/list/enhanced")
def list_candidates_enhanced(active_only: bool = True, limit: int = 100):
    """Enhanced candidate listing with database backend"""
    try:
        candidates = db_manager.get_all_candidates(active_only)
        return {
            "candidates": candidates[:limit],
            "total_count": len(candidates),
            "active_only": active_only
        }
    except Exception as e:
        logger.error(f"Failed to list candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{candidate_id}/history")
def get_candidate_history(candidate_id: int):
    """Get complete candidate history"""
    try:
        candidate = db_manager.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        feedback_history = db_manager.get_feedback_by_candidate(candidate_id)
        communication_history = db_manager.get_communication_history(candidate_id)
        
        return {
            "candidate": candidate,
            "feedback_history": feedback_history,
            "communication_history": communication_history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get candidate history: {e}")
        raise HTTPException(status_code=500, detail=str(e))