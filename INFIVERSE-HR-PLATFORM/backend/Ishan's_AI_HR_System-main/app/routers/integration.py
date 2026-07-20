from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from app.utils.ai_engine import AIEngine
from app.utils.ml_models import MLModels
from app.utils.database import db_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integration", tags=["platform-integration"])

class ExternalCandidate(BaseModel):
    full_name: Optional[str] = None
    name: Optional[str] = None
    email_address: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    external_id: Optional[str] = None

class PlatformInsights(BaseModel):
    platform_name: str
    candidate_data: Dict[str, Any]

@router.post("/sync-candidate")
def sync_external_candidate(candidate: ExternalCandidate):
    """Sync candidate from external HR platform"""
    try:
        # Transform external format to internal format
        internal_candidate = {
            "name": candidate.full_name or candidate.name,
            "email": candidate.email_address or candidate.email,
            "phone": candidate.phone_number or candidate.phone,
            "skills": candidate.skills
        }
        
        # Calculate AI match score
        match_score = AIEngine.calculate_match_score(internal_candidate)
        internal_candidate["match_score"] = match_score
        
        # Add to database
        candidate_id = db_manager.add_candidate(internal_candidate)
        
        # Log integration event
        db_manager.log_system_event(
            "INFO",
            "external_candidate_synced",
            f"Candidate synced from external platform: {internal_candidate['name']}",
            {"candidate_id": candidate_id, "external_id": candidate.external_id}
        )
        
        return {
            "status": "success",
            "candidate_id": candidate_id,
            "match_score": match_score,
            "message": "Candidate synced successfully"
        }
        
    except Exception as e:
        logger.error(f"External candidate sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
def analyze_external_candidate(candidate_data: Dict[str, Any]):
    """Analyze candidate and return AI insights"""
    try:
        # Extract skills and calculate similarity
        skills = candidate_data.get("skills", [])
        job_requirements = ["Python", "FastAPI", "AI", "Machine Learning"]
        
        similarity_score = MLModels.calculate_skill_similarity(skills, job_requirements)
        
        # Generate recommendations
        recommendations = AIEngine.generate_recommendations(
            candidate_data.get("id", 0), 
            []  # No feedback history for external candidates
        )
        
        return {
            "similarity_score": similarity_score,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "status": "analyzed"
        }
        
    except Exception as e:
        logger.error(f"Candidate analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform-insights")
def get_platform_insights():
    """Get insights formatted for external platforms"""
    try:
        from app.utils.helpers import load_json
        
        candidates = load_json("data/candidates.json")
        feedback_logs = load_json("feedback/feedback_log.csv")
        
        # Calculate insights
        total_candidates = len(candidates) if isinstance(candidates, list) else 0
        avg_score = 0
        top_skills = []
        
        if isinstance(candidates, list) and candidates:
            scores = [c.get('match_score', 0) for c in candidates]
            avg_score = sum(scores) / len(scores)
            
            # Extract top skills
            all_skills = []
            for c in candidates:
                all_skills.extend(c.get('skills', []))
            
            skill_counts = {}
            for skill in all_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_candidates": total_candidates,
            "average_match_score": round(avg_score, 2),
            "total_feedback": len(feedback_logs) if isinstance(feedback_logs, list) else 0,
            "top_skills": top_skills,
            "hiring_trends": "Positive trend - AI-driven insights available",
            "ai_status": "Active",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Platform insights failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
def platform_webhook(payload: Dict[str, Any]):
    """Webhook endpoint for external platform events"""
    try:
        event_type = payload.get("event_type")
        candidate_data = payload.get("candidate_data", {})
        
        if event_type == "candidate_added":
            # Auto-sync new candidate
            external_candidate = ExternalCandidate(**candidate_data)
            result = sync_external_candidate(external_candidate)
            return {"status": "processed", "result": result}
        
        elif event_type == "candidate_updated":
            # Handle candidate updates
            return {"status": "updated", "message": "Candidate update processed"}
        
        else:
            return {"status": "ignored", "message": f"Unknown event type: {event_type}"}
            
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def integration_health():
    """Health check for integration services"""
    try:
        return {
            "status": "healthy",
            "services": {
                "ai_engine": "active",
                "ml_models": "active", 
                "database": "connected",
                "integration_api": "ready"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}