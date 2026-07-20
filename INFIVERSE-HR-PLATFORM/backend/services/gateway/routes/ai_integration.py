from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import httpx
import os
import sys

# Add parent directory to path for accessing dependencies from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dependencies import get_api_key

from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["AI Integration"])

class TestCommunicationRequest(BaseModel):
    channel: str = "email"
    recipient_email: Optional[str] = None
    phone: Optional[str] = None
    chat_id: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None

@router.post("/test-communication")
async def test_communication_system(
    test_data: TestCommunicationRequest,
    api_key: str = Depends(get_api_key)
) -> Dict:
    """Test communication system via LangGraph"""
    try:
        langgraph_service_url = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")
        
        # Route to appropriate test endpoint based on channel
        channel = test_data.channel
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if channel == "email":
                recipient = test_data.recipient_email or "shashankmishra0411@gmail.com"
                subject = test_data.subject or "BHIV HR Test Email"
                message = test_data.message or "This is a test email from BHIV HR Platform"
                
                response = await client.post(f"{langgraph_service_url}/test/send-email",
                                          params={
                                              "recipient_email": recipient,
                                              "subject": subject,
                                              "message": message
                                          },
                                          headers={"Authorization": f"Bearer {api_key}"})
            elif channel == "whatsapp":
                phone = test_data.phone or "+919284967526"
                message = test_data.message or "Test message from BHIV HR Platform"
                
                response = await client.post(f"{langgraph_service_url}/test/send-whatsapp", 
                                          params={
                                              "phone": phone,
                                              "message": message
                                          },
                                          headers={"Authorization": f"Bearer {api_key}"})
            elif channel == "telegram":
                chat_id = test_data.chat_id or "test_chat_id"
                message = test_data.message or "Test message from BHIV HR Platform"
                
                response = await client.post(f"{langgraph_service_url}/test/send-telegram",
                                          params={
                                              "chat_id": chat_id,
                                              "message": message
                                          },
                                          headers={"Authorization": f"Bearer {api_key}"})
            else:
                raise HTTPException(status_code=400, detail="Invalid channel. Use 'email', 'whatsapp', or 'telegram'")
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {"success": False, "error": f"LangGraph service returned {response.status_code}: {response.text}"}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Communication service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GeminiAnalyzeRequest(BaseModel):
    text: str
    analysis_type: str = "resume"

@router.post("/gemini/analyze")
async def analyze_with_gemini(
    request: GeminiAnalyzeRequest,
    api_key: str = Depends(get_api_key)
) -> Dict:
    """Analyze text using Gemini AI"""
    try:
        import google.generativeai as genai
        
        # Get Gemini API key from environment
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key or gemini_api_key.startswith("<"):
            return {
                "success": False,
                "error": "Gemini API key not configured",
                "analysis": None,
                "note": "Set GEMINI_API_KEY environment variable to enable Gemini analysis"
            }
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Create prompt based on analysis type
        if request.analysis_type == "resume":
            prompt = f"Analyze this resume text and provide: 1) Key skills, 2) Experience level, 3) Education, 4) Strengths, 5) Areas for improvement:\n\n{request.text}"
        elif request.analysis_type == "job_description":
            prompt = f"Analyze this job description and extract: 1) Required skills, 2) Experience requirements, 3) Education requirements, 4) Key responsibilities:\n\n{request.text}"
        elif request.analysis_type == "match":
            prompt = f"Analyze the match between candidate and job. Provide: 1) Skill match percentage, 2) Experience alignment, 3) Overall fit score (0-100), 4) Recommendations:\n\n{request.text}"
        else:
            prompt = f"Analyze the following text:\n\n{request.text}"
        
        # Generate analysis
        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "analysis": response.text,
            "analysis_type": request.analysis_type,
            "model": "gemini-pro"
        }
    except ImportError:
        return {
            "success": False,
            "error": "Gemini library not installed",
            "analysis": None,
            "note": "Install google-generativeai package to enable Gemini analysis"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": None
        }