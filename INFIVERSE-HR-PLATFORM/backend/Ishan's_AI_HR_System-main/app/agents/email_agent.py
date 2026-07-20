from datetime import datetime
from app.utils.helpers import load_json
from typing import Optional, Dict, Any

def send_email(candidate_id: int, template: str = "default", override_email: Optional[str] = None) -> Dict[str, Any]:
    """Send email with proper error handling"""
    try:
        candidates = load_json("data/candidates.json")
        if not isinstance(candidates, list):
            return {"status": "failed", "reason": "invalid_candidates_data"}
        
        candidate = next((c for c in candidates if c.get("id") == candidate_id), None)
    
        if candidate:
            name = candidate.get("name", "Candidate")
            email = override_email or candidate.get("email", "no-email@example.com")
            
            # Validate email format
            if not email or "@" not in email:
                return {"status": "failed", "reason": "invalid_email_address"}
            
            # Get email content
            subject, body = get_email_content(template, name)
            
            # Mock email sending for development
            print(f"[EMAIL] To: {email}")
            print(f"[EMAIL] Subject: {subject}")
            print(f"[EMAIL] Sent to {name} ({email}) at {datetime.now()}")
            
            return {
                "status": "sent", 
                "recipient": name, 
                "email": email,
                "subject": subject,
                "template": template,
                "timestamp": datetime.now().isoformat()
            }
        else:
            print(f"[EMAIL] Failed - Candidate {candidate_id} not found")
            return {"status": "failed", "reason": "candidate_not_found"}
    except Exception as e:
        print(f"[EMAIL] Error: {str(e)}")
        return {"status": "failed", "reason": f"error: {str(e)}"}

def send_rejection_email(candidate_id, override_email=None):
    return send_email(candidate_id, "rejection", override_email)

def send_interview_email(candidate_id, override_email=None):
    return send_email(candidate_id, "interview", override_email)

def get_email_content(template, name):
    templates = {
        "default": (
            "Update from HR Team",
            f"Dear {name},\n\nWe have an update regarding your application. Please check your candidate portal for more details.\n\nBest regards,\nHR Team"
        ),
        "rejection": (
            "Application Status Update",
            f"Dear {name},\n\nThank you for your interest in our company. After careful consideration, we have decided to move forward with other candidates for this position. We will keep your profile on file for future opportunities.\n\nBest regards,\nHR Team"
        ),
        "interview": (
            "Interview Invitation",
            f"Dear {name},\n\nCongratulations! We would like to invite you for an interview. Our team will contact you shortly with the details.\n\nBest regards,\nHR Team"
        ),
        "shortlisted": (
            "Congratulations - You're Shortlisted!",
            f"Dear {name},\n\nGreat news! You have been shortlisted for the position. We will be in touch with next steps soon.\n\nBest regards,\nHR Team"
        )
    }
    return templates.get(template, templates["default"])