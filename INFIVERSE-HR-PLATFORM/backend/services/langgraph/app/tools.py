from langchain_core.tools import tool
import httpx
import logging
from datetime import datetime
import sys
import os

# Import config from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import settings
except ImportError:
    # Fallback for Docker environment
    import os
    class Settings:
        gateway_url = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
        api_key_secret = os.getenv("API_KEY_SECRET", "")
    settings = Settings()
from .communication import comm_manager

logger = logging.getLogger(__name__)
HTTPX_TIMEOUT = 120.0

@tool
async def get_candidate_profile(candidate_id: int) -> dict:
    """Fetch candidate profile from API Gateway"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.gateway_url}/v1/candidates/{candidate_id}",
                headers={"Authorization": f"Bearer {settings.api_key_secret}"},
                timeout=HTTPX_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"✅ Retrieved candidate {candidate_id}")
            return response.json()
    except Exception as e:
        logger.error(f"❌ Error fetching candidate {candidate_id}: {str(e)}")
        return {"error": str(e), "candidate_id": candidate_id}

@tool
async def get_job_details(job_id: int) -> dict:
    """Fetch job details from API Gateway"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.gateway_url}/v1/jobs/{job_id}",
                headers={"Authorization": f"Bearer {settings.api_key_secret}"},
                timeout=HTTPX_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"✅ Retrieved job {job_id}")
            return response.json()
    except Exception as e:
        logger.error(f"❌ Error fetching job {job_id}: {str(e)}")
        return {"error": str(e), "job_id": job_id}

@tool
async def update_application_status(application_id: int, status: str, notes: str = "") -> dict:
    """Update application status in database"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{settings.gateway_url}/v1/applications/{application_id}",
                json={"status": status, "notes": notes},
                headers={"Authorization": f"Bearer {settings.api_key_secret}"},
                timeout=HTTPX_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"✅ Updated application {application_id} to {status}")
            return response.json()
    except Exception as e:
        logger.error(f"❌ Error updating application {application_id}: {str(e)}")
        return {"error": str(e), "application_id": application_id}

@tool
async def get_ai_matching_score(candidate_id: int, job_id: int) -> dict:
    """Get AI matching score from matching engine"""
    try:
        # Mock response for local testing
        if settings.environment == "development":
            mock_score = 78  # Good score for testing
            logger.info(f"🧪 MOCK AI matching score for candidate {candidate_id}: {mock_score}/100")
            return {"candidate_id": candidate_id, "job_id": job_id, "score": mock_score}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.gateway_url}/v1/match",
                json={"candidate_id": candidate_id, "job_id": job_id},
                headers={"Authorization": f"Bearer {settings.api_key_secret}"},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Got matching score for candidate {candidate_id}: {result.get('score', 0)}/100")
            return result
    except Exception as e:
        logger.error(f"❌ Error getting match score: {str(e)}")
        return {"error": str(e), "candidate_id": candidate_id, "job_id": job_id, "score": 65}

@tool
async def send_multi_channel_notification(
    candidate_id: int,
    candidate_email: str,
    candidate_phone: str,
    candidate_name: str,
    job_title: str,
    application_status: str,
    message: str,
    channels: list
) -> dict:
    """Send notification across multiple channels"""
    payload = {
        "candidate_id": candidate_id,
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone,
        "candidate_name": candidate_name,
        "job_title": job_title,
        "application_status": application_status,
        "message": message
    }
    
    results = await comm_manager.send_multi_channel(payload, channels)
    
    return {
        "status": "completed",
        "candidate_id": candidate_id,
        "notifications": results,
        "success_count": len([r for r in results if r["status"] == "success"]),
        "failed_count": len([r for r in results if r["status"] == "failed"]),
        "timestamp": datetime.now().isoformat()
    }

@tool
async def log_audit_event(event_type: str, details: dict) -> dict:
    """Log audit event to database"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.gateway_url}/v1/audit-logs",
                json={"event_type": event_type, "details": details},
                headers={"Authorization": f"Bearer {settings.api_key_secret}"},
                timeout=HTTPX_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"✅ Audit event logged: {event_type}")
            return response.json()
    except Exception as e:
        logger.error(f"❌ Error logging audit event: {str(e)}")
        return {"error": str(e), "event_type": event_type}

@tool
async def update_hr_dashboard(application_id: int, update_data: dict) -> dict:
    """Trigger real-time HR dashboard update"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.gateway_url}/v1/dashboard/refresh",
                json={"application_id": application_id, "data": update_data},
                headers={"Authorization": f"Bearer {settings.api_key_secret}"},
                timeout=HTTPX_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"✅ Dashboard updated for application {application_id}")
            return {"status": "dashboard_updated", "application_id": application_id}
    except Exception as e:
        logger.error(f"❌ Error updating dashboard: {str(e)}")
        return {"error": str(e), "application_id": application_id}