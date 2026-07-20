from datetime import datetime
from app.utils.helpers import load_json
from typing import Dict, Any
import re

def trigger_voice_call(candidate_id: int, call_type: str = "onboarding") -> Dict[str, Any]:
    """Trigger voice call with proper validation and error handling"""
    try:
        if candidate_id <= 0:
            return {"status": "failed", "reason": "invalid_candidate_id"}
        
        if not _is_valid_call_type(call_type):
            return {"status": "failed", "reason": "invalid_call_type"}
        
        candidates = load_json("data/candidates.json")
        if not isinstance(candidates, list):
            return {"status": "failed", "reason": "invalid_candidates_data"}
        
        candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
        
        if candidate:
            name = candidate.get("name", "Candidate")
            phone = candidate.get("phone", "No phone")
            
            if not phone or not re.match(r'^\+91-\d{10}$', phone):
                return {"status": "failed", "reason": "invalid_phone_format"}
            
            message = get_voice_message(call_type, name)
            
            # Mock voice call for development
            print(f"[VOICE] Calling: {phone}")
            print(f"[VOICE] Message: {message}")
            print(f"[VOICE] {call_type} call triggered for {name} (ID: {candidate_id})")
            
            return {
                "status": "triggered", 
                "recipient": name, 
                "phone": phone,
                "call_type": call_type,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        else:
            print(f"[VOICE] Failed - Candidate {candidate_id} not found")
            return {"status": "failed", "reason": "candidate_not_found"}
    except Exception as e:
        print(f"[VOICE] Error: {str(e)}")
        return {"status": "failed", "reason": f"error: {str(e)}"}

def get_voice_message(call_type: str, name: str) -> str:
    """Get voice message for call type"""
    messages = {
        "onboarding": f"Hello {name}, welcome to our company! We're excited to have you join our team.",
        "interview_reminder": f"Hello {name}, this is a reminder about your upcoming interview. Please check your email for details.",
        "follow_up": f"Hello {name}, we wanted to follow up on your application status.",
        "welcome": f"Hello {name}, welcome! We look forward to working with you."
    }
    return messages.get(call_type, f"Hello {name}, this is a message from HR.")

def _is_valid_call_type(call_type: str) -> bool:
    """Validate call type"""
    valid_types = ["onboarding", "interview_reminder", "follow_up", "welcome"]
    return call_type in valid_types

def schedule_interview_call(candidate_id: int) -> Dict[str, Any]:
    """Schedule interview reminder call"""
    return trigger_voice_call(candidate_id, "interview_reminder")