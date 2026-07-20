#!/usr/bin/env python3
"""
Email Automation for HR Portal
Automated email notifications for interview steps
"""

import httpx
import os
from datetime import datetime

def send_automated_email(notification_type, candidate_data, additional_data=None):
    """Send automated email notifications via LangGraph"""
    
    langgraph_url = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph.onrender.com")
    api_key = os.getenv("API_KEY_SECRET")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Email templates based on notification type
    templates = {
        "interview_scheduled": {
            "subject": f"Interview Scheduled - {candidate_data.get('job_title', 'Position')}",
            "message": f"""Dear {candidate_data.get('candidate_name', 'Candidate')},

We are pleased to inform you that your interview has been scheduled for the position of {candidate_data.get('job_title', 'Position')} at BHIV.

Interview Details:
- Date: {(additional_data or {}).get('interview_date', 'TBD')}
- Time: {(additional_data or {}).get('interview_time', 'TBD')}
- Interviewer: {(additional_data or {}).get('interviewer', 'HR Team')}
- Mode: {(additional_data or {}).get('interview_mode', 'Video Call')}

Please confirm your availability by replying to this email.

Best regards,
BHIV HR Team"""
        },
        
        "application_received": {
            "subject": f"Application Received - {candidate_data.get('job_title', 'Position')}",
            "message": f"""Dear {candidate_data.get('candidate_name', 'Candidate')},

Thank you for your interest in the {candidate_data.get('job_title', 'Position')} role at BHIV.

Your application has been successfully received and is currently under review by our HR team. We will contact you within 3-5 business days with an update on your application status.

Application Details:
- Position: {candidate_data.get('job_title', 'Position')}
- Application ID: {candidate_data.get('application_id', 'N/A')}
- Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Best regards,
BHIV HR Team"""
        },
        
        "shortlisted": {
            "subject": f"Congratulations! You've been shortlisted - {candidate_data.get('job_title', 'Position')}",
            "message": f"""Dear {candidate_data.get('candidate_name', 'Candidate')},

Congratulations! We are pleased to inform you that you have been shortlisted for the {candidate_data.get('job_title', 'Position')} role at BHIV.

Your profile has been selected based on our AI-powered matching system and values assessment. We were impressed by your qualifications and experience.

Next Steps:
- Our HR team will contact you within 24 hours to schedule an interview
- Please keep your calendar flexible for the next week
- Prepare for technical and values-based interview questions

We look forward to meeting you!

Best regards,
BHIV HR Team"""
        },
        
        "assessment_completed": {
            "subject": f"Assessment Completed - {candidate_data.get('job_title', 'Position')}",
            "message": f"""Dear {candidate_data.get('candidate_name', 'Candidate')},

Thank you for completing the assessment for the {candidate_data.get('job_title', 'Position')} role at BHIV.

Assessment Summary:
- Technical Assessment: Completed
- Values Assessment: Completed
- Overall Score: {(additional_data or {}).get('overall_score', 'Under Review')}

Our team is currently reviewing your assessment results. We will update you on the next steps within 2-3 business days.

Best regards,
BHIV HR Team"""
        }
    }
    
    template = templates.get(notification_type, templates["application_received"])
    
    notification_data = {
        "candidate_name": candidate_data.get("candidate_name", "Candidate"),
        "candidate_email": candidate_data.get("candidate_email", ""),
        "candidate_phone": candidate_data.get("candidate_phone", ""),
        "job_title": candidate_data.get("job_title", "Position"),
        "message": template["message"],
        "channels": ["email", "whatsapp"],  # Now includes WhatsApp
        "application_status": notification_type
    }
    
    try:
        response = httpx.post(
            f"{langgraph_url}/tools/send-notification",
            json=notification_data,
            headers=headers,
            timeout=10.0
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Email sent successfully"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def trigger_interview_notification(candidate_name, candidate_email, job_title, interview_date, interview_time, interviewer, candidate_phone=None):
    """Trigger automated email and WhatsApp when interview is scheduled"""
    
    candidate_data = {
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone or "",
        "job_title": job_title
    }
    
    additional_data = {
        "interview_date": interview_date,
        "interview_time": interview_time,
        "interviewer": interviewer,
        "interview_mode": "Video Call"
    }
    
    return send_automated_email("interview_scheduled", candidate_data, additional_data)

def trigger_shortlist_notification(candidate_name, candidate_email, job_title, candidate_phone=None):
    """Trigger automated email and WhatsApp when candidate is shortlisted"""
    
    candidate_data = {
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone or "",
        "job_title": job_title
    }
    
    return send_automated_email("shortlisted", candidate_data)

def trigger_application_received_notification(candidate_name, candidate_email, job_title, application_id=None, candidate_phone=None):
    """Trigger automated email and WhatsApp when application is received"""
    
    candidate_data = {
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone or "",
        "job_title": job_title,
        "application_id": application_id
    }
    
    return send_automated_email("application_received", candidate_data)