from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from creator_core_engine import CreatorCoreService, create_creator_core_router
from core.models import CoreRequest, CoreResponse
from core.gateway import Gateway
from db.memory import ContextMemory
from app_config import DB_PATH

app = FastAPI(
    title="Unified Backend Bridge",
    description="Central orchestration layer for Finance, Education, and Creator agents",
    version="1.0.0"
)

# Initialize gateway and memory
gateway = Gateway()
memory = ContextMemory(DB_PATH)
creator_core_service = CreatorCoreService()

app.include_router(create_creator_core_router(creator_core_service))

@app.post("/core", response_model=CoreResponse)
async def core_endpoint(request: CoreRequest) -> CoreResponse:
    """Main gateway endpoint for processing agent requests"""
    try:
        response = gateway.process_request(
            module=request.module,
            intent=request.intent, 
            user_id=request.user_id,
            data=request.data
        )
        # Validate response structure before creating CoreResponse
        if not isinstance(response, dict) or 'status' not in response:
            raise HTTPException(status_code=500, detail="Invalid agent response format")
        
        # Ensure required fields exist
        response.setdefault('message', 'No message provided')
        response.setdefault('result', {})
        
        return CoreResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Response validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-history")
async def get_history(user_id: str) -> List[Dict[str, Any]]:
    """Get full interaction history for a user"""
    try:
        history = memory.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-context") 
async def get_context(user_id: str) -> List[Dict[str, Any]]:
    """Get recent context (last 3 interactions) for a user"""
    try:
        context = memory.get_context(user_id)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Unified Backend Bridge API",
        "version": "1.0.0",
        "docs": "/docs",
        "creator_core_endpoint": "/creator-core/generate-blueprint",
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)