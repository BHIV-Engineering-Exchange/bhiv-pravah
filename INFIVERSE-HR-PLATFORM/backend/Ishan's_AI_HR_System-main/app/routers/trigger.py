from fastapi import APIRouter, HTTPException
from app.models import AutomationTrigger
from app.agents.email_agent import send_email
from app.agents.whatsapp_agent import send_whatsapp
from app.agents.voice_agent import trigger_voice_call
from app.utils.helpers import load_json
from app.utils.database import db_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trigger", tags=["automation"])

@router.post("/")
def trigger_automation(trigger: AutomationTrigger):
    """Event orchestrator - triggers multi-channel communication"""
    candidates = load_json("data/candidates.json")
    if not isinstance(candidates, list):
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate = next((c for c in candidates if c.get("id") == trigger.candidate_id), None)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    results = []
    
    try:
        # Log event start
        db_manager.log_system_event(
            "INFO", 
            f"automation_triggered_{trigger.event_type}",
            f"Automation triggered for candidate {trigger.candidate_id}",
            {"event_type": trigger.event_type, "metadata": trigger.metadata}
        )
        
        if trigger.event_type == "shortlisted":
            email_result = send_email(trigger.candidate_id, "shortlisted", 
                                    trigger.metadata.get("override_email"))
            whatsapp_result = send_whatsapp(trigger.candidate_id, "shortlisted", 
                                          trigger.metadata.get("override_phone"))
            results.extend([email_result, whatsapp_result])
            
        elif trigger.event_type == "rejected":
            email_result = send_email(trigger.candidate_id, "rejected", 
                                    trigger.metadata.get("override_email"))
            whatsapp_result = send_whatsapp(trigger.candidate_id, "rejected", 
                                          trigger.metadata.get("override_phone"))
            results.extend([email_result, whatsapp_result])
            
        elif trigger.event_type == "interview_scheduled":
            email_result = send_email(trigger.candidate_id, "interview", 
                                    trigger.metadata.get("override_email"))
            whatsapp_result = send_whatsapp(trigger.candidate_id, "interview", 
                                          trigger.metadata.get("override_phone"))
            voice_result = trigger_voice_call(trigger.candidate_id, "interview_reminder")
            results.extend([email_result, whatsapp_result, voice_result])
            
        elif trigger.event_type == "onboarding_completed":
            whatsapp_result = send_whatsapp(trigger.candidate_id, "onboarding", 
                                          trigger.metadata.get("override_phone"))
            voice_result = trigger_voice_call(trigger.candidate_id, "onboarding")
            results.extend([whatsapp_result, voice_result])
        
        # Log successful completion
        db_manager.log_system_event(
            "INFO", 
            f"automation_completed_{trigger.event_type}",
            f"Automation completed for candidate {trigger.candidate_id}",
            {"results": results, "total_communications": len(results)}
        )
        
        return {
            "status": "success", 
            "event_type": trigger.event_type, 
            "results": results,
            "total_communications": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        db_manager.log_system_event("ERROR", "automation_failed", str(e))
        raise HTTPException(status_code=500, detail=f"Automation failed: {str(e)}")

@router.get("/history/{candidate_id}")
def get_automation_history(candidate_id: int):
    """Get automation history for a candidate"""
    try:
        # Get from database logs
        logs = db_manager.get_system_logs(
            level=None, 
            limit=100, 
            event_filter=f"automation_%_{candidate_id}"
        )
        
        return {
            "candidate_id": candidate_id, 
            "automation_history": logs,
            "total_events": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get automation history: {e}")
        return {"candidate_id": candidate_id, "automation_history": [], "error": str(e)}