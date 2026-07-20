from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import httpx
import sys
import os

# Add parent directory to path for accessing dependencies from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Now dependencies can be imported safely (using local jwt_auth from dependencies)
from dependencies import get_api_key

router = APIRouter(prefix="/rl", tags=["RL + Feedback Agent"])

@router.post("/predict")
async def rl_predict_match(
    request_data: Dict[str, Any],
    api_key: str = Depends(get_api_key)
):
    """Proxy RL prediction to LangGraph service"""
    try:
        langgraph_service_url = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{langgraph_service_url}/rl/predict",
                json=request_data,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_rl_feedback(
    feedback_data: Dict[str, Any],
    api_key: str = Depends(get_api_key)
):
    """Proxy RL feedback to LangGraph service"""
    try:
        langgraph_service_url = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{langgraph_service_url}/rl/feedback",
                json=feedback_data,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_rl_analytics(api_key: str = Depends(get_api_key)):
    """Proxy RL analytics to LangGraph service"""
    try:
        langgraph_service_url = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(
                f"{langgraph_service_url}/rl/analytics",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_rl_performance(api_key: str = Depends(get_api_key)):
    """Proxy RL performance to LangGraph service"""
    try:
        langgraph_service_url = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(
                f"{langgraph_service_url}/rl/performance",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))