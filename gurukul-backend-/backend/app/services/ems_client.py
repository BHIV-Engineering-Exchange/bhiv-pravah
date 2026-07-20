"""
EMS API Client Service
Handles all API calls to the EMS System backend.
"""

import httpx
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EMSClient:
    """Client for interacting with EMS System API"""
    
    def __init__(self):
        self.base_url = settings.EMS_API_BASE_URL
        self.api_key = settings.EMS_API_KEY
        self.timeout = 30.0  # 30 seconds timeout
    
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add API key if available
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        # Add JWT token if provided
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Any:
        """Make HTTP request to EMS API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(token)
        
        # Log request details (without sensitive data)
        if json_data and "password" in json_data:
            log_data = {**json_data, "password": "***"}
        else:
            log_data = json_data
        logger.debug(f"EMS API Request: {method} {url} | Data: {log_data}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params
                )
                
                logger.debug(f"EMS API Response: {response.status_code} for {url}")
                
                # Handle errors
                if response.status_code >= 400:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", str(response.text))
                    except:
                        error_detail = response.text or f"HTTP {response.status_code}"
                    
                    logger.error(f"EMS API error [{response.status_code}]: {error_detail}")
                    
                    if response.status_code == 401:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"EMS authentication failed: {error_detail}"
                        )
                    elif response.status_code == 403:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"EMS access forbidden: {error_detail}"
                        )
                    elif response.status_code == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"EMS resource not found: {error_detail}"
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"EMS API error: {error_detail}"
                        )
                
                # Return JSON response
                if response.content:
                    return response.json()
                return None
                
        except httpx.TimeoutException:
            logger.error(f"EMS API timeout: {url}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="EMS API request timed out"
            )
        except httpx.ConnectError:
            logger.error(f"EMS API connection error: {url}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to EMS System. Please check if EMS backend is running."
            )
        except Exception as e:
            logger.error(f"EMS API unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"EMS API communication error: {str(e)}"
            )
    
    # Authentication methods
    
    async def login(self, email: str, password: str) -> Dict[str, str]:
        """Login to EMS and get JWT token"""
        logger.info(f"Attempting EMS login for email: {email} to {self.base_url}/v1/auth/login-json")
        try:
            result = await self._request(
                method="POST",
                endpoint="/v1/auth/login-json",  # Updated to match new EMS router prefix
                json_data={"email": email, "password": password}
            )
            logger.info(f"EMS login successful for email: {email}")
            return result
        except Exception as e:
            logger.error(f"EMS login failed for email {email}: {str(e)}")
            raise
    
    # Student endpoints
    
    async def get_student_dashboard_stats(self, token: str) -> Dict:
        """Get student dashboard statistics"""
        return await self._request(
            method="GET",
            endpoint="/student/dashboard/stats",
            token=token
        )
    
    async def get_student_classes(self, token: str) -> List[Dict]:
        """Get student's enrolled classes"""
        return await self._request(
            method="GET",
            endpoint="/student/classes",
            token=token
        )
    
    async def get_student_lessons(self, token: str, class_id: Optional[int] = None) -> List[Dict]:
        """Get student's lessons"""
        params = {}
        if class_id:
            params["class_id"] = class_id
        
        return await self._request(
            method="GET",
            endpoint="/student/lessons",
            token=token,
            params=params
        )
    
    async def get_student_timetable(self, token: str) -> List[Dict]:
        """Get student's timetable/schedule"""
        return await self._request(
            method="GET",
            endpoint="/student/timetable",
            token=token
        )
    
    async def get_student_announcements(self, token: str) -> List[Dict]:
        """Get student announcements"""
        return await self._request(
            method="GET",
            endpoint="/student/announcements",
            token=token
        )
    
    async def get_student_attendance(
        self,
        token: str,
        class_id: Optional[int] = None,
        attendance_date: Optional[str] = None
    ) -> List[Dict]:
        """Get student's attendance records"""
        params = {}
        if class_id:
            params["class_id"] = class_id
        if attendance_date:
            params["attendance_date"] = attendance_date
        
        return await self._request(
            method="GET",
            endpoint="/student/attendance",
            token=token,
            params=params
        )
    
    async def get_student_teachers(self, token: str) -> List[Dict]:
        """Get student's teachers"""
        return await self._request(
            method="GET",
            endpoint="/student/teachers",
            token=token
        )
    
    async def get_student_grades(self, token: str, class_id: Optional[int] = None) -> List[Dict]:
        """Get student's grades"""
        params = {}
        if class_id:
            params["class_id"] = class_id
        
        return await self._request(
            method="GET",
            endpoint="/student/grades",
            token=token,
            params=params
        )
    
    # Admin endpoints (for auto-creating students)
    
    async def create_student(
        self,
        admin_token: str,
        name: str,
        email: str,
        grade: str = "N/A",
        parent_email: Optional[str] = None,
        parent_name: Optional[str] = None
    ) -> Dict:
        """Create a new student in EMS (requires admin token)"""
        student_data = {
            "name": name,
            "email": email,
            "grade": grade
        }
        if parent_email:
            student_data["parent_email"] = parent_email
        if parent_name:
            student_data["parent_name"] = parent_name
        
        # EMS admin router has prefix="/admin", endpoint is "/students"
        # So full path is "/admin/students"
        return await self._request(
            method="POST",
            endpoint="/admin/students",
            token=admin_token,
            json_data=student_data
        )
    
    # Health check
    async def health_check(self) -> Dict:
        """Check if EMS API is reachable"""
        try:
            return await self._request(method="GET", endpoint="/health")
        except Exception as e:
            logger.error(f"EMS health check failed: {str(e)}")
            raise

# Singleton instance
ems_client = EMSClient()

