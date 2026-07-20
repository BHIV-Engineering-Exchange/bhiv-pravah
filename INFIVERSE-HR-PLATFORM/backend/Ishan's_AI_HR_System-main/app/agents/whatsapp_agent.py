# -*- coding: utf-8 -*-
from datetime import datetime
from app.utils.helpers import load_json
from typing import Optional, Dict, Any

def send_whatsapp(candidate_id: int, message_type: str = "notification", override_phone: Optional[str] = None) -> Dict[str, Any]:
    """Send WhatsApp message with proper error handling"""
    try:
        candidates = load_json("data/candidates.json")
        if not isinstance(candidates, list):
            return {"status": "failed", "reason": "invalid_candidates_data"}
        
        candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
        
        if candidate:
            name = candidate.get("name", "Candidate")
            phone = override_phone or candidate.get("phone", "")
            
            # Validate phone format
            if not phone or "+91-" not in phone:
                return {"status": "failed", "reason": "invalid_phone_number"}
            
            message = get_whatsapp_message(message_type, name)
            
            # Mock WhatsApp sending for development
            print(f"[WHATSAPP] To: {phone}")
            print(f"[WHATSAPP] Message: {message}")
            print(f"[WHATSAPP] Sent to {name} ({phone}) at {datetime.now()}")
            
            return {
                "status": "sent",
                "recipient": name,
                "phone": phone,
                "message": message,
                "type": message_type,
                "timestamp": datetime.now().isoformat()
            }
        else:
            print(f"[WHATSAPP] Failed - Candidate {candidate_id} not found")
            return {"status": "failed", "reason": "candidate_not_found"}
    except Exception as e:
        print(f"[WHATSAPP] Error: {str(e)}")
        return {"status": "failed", "reason": f"error: {str(e)}"}

def get_whatsapp_message(message_type: str, name: str) -> str:
    messages = {
        "shortlisted": f"Congratulations {name}! You've been shortlisted for the position. HR will contact you soon.",
        "interview": f"Hi {name}, your interview has been scheduled. Check your email for details.",
        "rejected": f"Hi {name}, thank you for your interest. We'll keep your profile for future opportunities.",
        "notification": f"Hi {name}! Welcome to our recruitment process. We've received your application and will be in touch soon.",
        "onboarding": f"Welcome aboard {name}! Your onboarding process will begin soon."
    }
    return messages.get(message_type, f"Hi {name}! Update from HR team.")