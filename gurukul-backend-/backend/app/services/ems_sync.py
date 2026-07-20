"""
EMS Sync Service
Handles syncing student-generated content from Gurukul to EMS System
"""

import httpx
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EMSSyncService:
    """Service for syncing student content to EMS System"""
    
    def __init__(self):
        self.base_url = settings.EMS_API_BASE_URL
        self.api_key = settings.EMS_API_KEY
        self.timeout = 30.0
        self.admin_email = settings.EMS_ADMIN_EMAIL
        self.admin_password = settings.EMS_ADMIN_PASSWORD
    
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def _get_admin_token(self) -> Optional[str]:
        """Get admin token for EMS authentication"""
        if not self.admin_email or not self.admin_password:
            logger.error("EMS admin credentials not configured. Cannot sync content.")
            logger.error(f"EMS_ADMIN_EMAIL: {'SET' if self.admin_email else 'NOT SET'}")
            logger.error(f"EMS_ADMIN_PASSWORD: {'SET' if self.admin_password else 'NOT SET'}")
            return None
        
        try:
            logger.info(f"Attempting to get EMS admin token for email: {self.admin_email}")
            from app.services.ems_client import ems_client
            token_response = await ems_client.login(self.admin_email, self.admin_password)
            token = token_response.get("access_token")
            if token:
                logger.info("Successfully obtained EMS admin token")
            else:
                logger.error("EMS admin login succeeded but no access_token in response")
            return token
        except Exception as e:
            logger.error(f"Failed to get EMS admin token: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        token: str,
        json_data: Optional[Dict] = None
    ) -> Any:
        """Make HTTP request to EMS API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(token)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data
                )
                
                if response.status_code >= 400:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", str(response.text))
                    except:
                        error_detail = response.text or f"HTTP {response.status_code}"
                    
                    logger.error(f"EMS sync error [{response.status_code}]: {error_detail} | URL: {url}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"EMS sync failed [{response.status_code}]: {error_detail}"
                    )
                
                # Log successful response
                if response.status_code == 200 or response.status_code == 201:
                    if response.content:
                        try:
                            return response.json()
                        except:
                            logger.warning(f"EMS sync returned {response.status_code} but response is not JSON: {response.text[:200]}")
                            return {"status": "success", "message": "Synced successfully"}
                    else:
                        logger.warning(f"EMS sync returned {response.status_code} but response has no content")
                        return {"status": "success", "message": "Synced successfully (no response body)"}
                
                return None
                
        except httpx.TimeoutException:
            logger.error(f"EMS sync timeout: {url}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="EMS sync request timed out"
            )
        except httpx.ConnectError:
            logger.error(f"EMS sync connection error: {url}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to EMS System for syncing"
            )
        except Exception as e:
            logger.error(f"EMS sync unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"EMS sync communication error: {str(e)}"
            )
    
    async def sync_summary(
        self,
        gurukul_id: str,
        student_email: str,
        school_id: Optional[int],
        title: str,
        content: str,
        source: Optional[str] = None,
        source_type: Optional[str] = None,
        extra_metadata: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Sync a summary from Gurukul to EMS using EMS admin credentials"""
        admin_token = await self._get_admin_token()
        if not admin_token:
            logger.warning(
                f"Cannot sync summary {gurukul_id}: EMS admin credentials not configured. "
                "Set EMS_ADMIN_EMAIL and EMS_ADMIN_PASSWORD to enable syncing."
            )
            return None  # Gracefully fail without raising exception
        
        sync_data = {
            "student_email": student_email,
            "school_id": school_id,
            "gurukul_id": gurukul_id,
            "title": title,
            "content": content,
            "source": source,
            "source_type": source_type or "text",
            "extra_metadata": extra_metadata or {}
        }
        
        try:
            result = await self._request(
                method="POST",
                endpoint="/admin/student-content/summaries",
                token=admin_token,
                json_data=sync_data
            )
            if result is None:
                logger.warning(f"Sync summary {gurukul_id} returned None - check if student exists in EMS with email: {student_email}")
            return result
        except HTTPException as e:
            logger.error(f"HTTPException syncing summary {gurukul_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to sync summary {gurukul_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def sync_flashcard(
        self,
        gurukul_id: str,
        student_email: str,
        school_id: Optional[int],
        question: str,
        answer: str,
        question_type: str = "conceptual",
        days_until_review: int = 0,
        confidence: float = 0.0,
    ) -> Optional[Dict]:
        """Sync a flashcard from Gurukul to EMS using EMS admin credentials"""
        admin_token = await self._get_admin_token()
        if not admin_token:
            logger.warning(
                f"Cannot sync flashcard {gurukul_id}: EMS admin credentials not configured. "
                "Set EMS_ADMIN_EMAIL and EMS_ADMIN_PASSWORD to enable syncing."
            )
            return None  # Gracefully fail without raising exception
        
        sync_data = {
            "student_email": student_email,
            "school_id": school_id,
            "gurukul_id": gurukul_id,
            "question": question,
            "answer": answer,
            "question_type": question_type,
            "days_until_review": days_until_review,
            "confidence": confidence
        }
        
        try:
            result = await self._request(
                method="POST",
                endpoint="/admin/student-content/flashcards",
                token=admin_token,
                json_data=sync_data
            )
            if result is None:
                logger.warning(f"Sync flashcard {gurukul_id} returned None - check if student exists in EMS with email: {student_email}")
            return result
        except HTTPException as e:
            logger.error(f"HTTPException syncing flashcard {gurukul_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to sync flashcard {gurukul_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def sync_test_result(
        self,
        gurukul_id: str,
        student_email: str,
        school_id: Optional[int],
        subject: str,
        topic: str,
        difficulty: str,
        num_questions: int,
        questions: List,
        user_answers: Dict,
        score: int,
        total_questions: int,
        percentage: float,
        time_taken: Optional[int] = None,
    ) -> Optional[Dict]:
        """Sync a test result from Gurukul to EMS using EMS admin credentials"""
        admin_token = await self._get_admin_token()
        if not admin_token:
            logger.warning(
                f"Cannot sync test result {gurukul_id}: EMS admin credentials not configured. "
                "Set EMS_ADMIN_EMAIL and EMS_ADMIN_PASSWORD to enable syncing."
            )
            return None  # Gracefully fail without raising exception
        
        sync_data = {
            "student_email": student_email,
            "school_id": school_id,
            "gurukul_id": gurukul_id,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "questions": questions,
            "user_answers": user_answers,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "time_taken": time_taken
        }
        
        try:
            result = await self._request(
                method="POST",
                endpoint="/admin/student-content/test-results",
                token=admin_token,
                json_data=sync_data
            )
            if result is None:
                logger.warning(f"Sync test result {gurukul_id} returned None - check if student exists in EMS with email: {student_email}")
            return result
        except HTTPException as e:
            logger.error(f"HTTPException syncing test result {gurukul_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to sync test result {gurukul_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def sync_subject_data(
        self,
        gurukul_id: str,
        student_email: str,
        school_id: Optional[int],
        subject: str,
        topic: str,
        notes: str,
        provider: str = "groq",
        youtube_recommendations: Optional[list] = None,
    ) -> Optional[Dict]:
        """Sync subject explorer data from Gurukul to EMS using EMS admin credentials"""
        admin_token = await self._get_admin_token()
        if not admin_token:
            logger.warning(
                f"Cannot sync subject data {gurukul_id}: EMS admin credentials not configured. "
                "Set EMS_ADMIN_EMAIL and EMS_ADMIN_PASSWORD to enable syncing."
            )
            return None  # Gracefully fail without raising exception
        
        sync_data = {
            "student_email": student_email,
            "school_id": school_id,
            "gurukul_id": gurukul_id,
            "subject": subject,
            "topic": topic,
            "notes": notes,
            "provider": provider,
            "youtube_recommendations": youtube_recommendations or []
        }
        
        try:
            result = await self._request(
                method="POST",
                endpoint="/admin/student-content/subject-data",
                token=admin_token,
                json_data=sync_data
            )
            if result is None:
                logger.warning(f"Sync subject data {gurukul_id} returned None - check if student exists in EMS with email: {student_email}")
            return result
        except HTTPException as e:
            logger.error(f"HTTPException syncing subject data {gurukul_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to sync subject data {gurukul_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

# Singleton instance
ems_sync = EMSSyncService()

