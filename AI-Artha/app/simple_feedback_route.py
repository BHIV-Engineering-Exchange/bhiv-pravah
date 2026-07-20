"""
Simplified feedback route that works
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import time
from core.mongodb import get_collection

router = APIRouter(tags=["STEP 5: AI Feedback & Tag Recommendations"])

class SimpleFeedbackRequest(BaseModel):
    content_id: str
    rating: int
    comment: str = ""

@router.post('/feedback-simple')
async def feedback_simple(f: SimpleFeedbackRequest, request: Request):
    """Simple feedback endpoint that always works"""
    try:
        # Get user from token if available
        auth_header = request.headers.get("Authorization", "")
        user_id = "anonymous"
        
        if auth_header.startswith("Bearer "):
            try:
                from app.auth import verify_token
                token = auth_header.replace("Bearer ", "")
                payload = verify_token(token)
                user_id = payload.get("user_id", "anonymous")
            except:
                pass
        
        # Validate rating
        if not (1 <= f.rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be 1-5")
        
        # Save to database
        reward = (f.rating - 3) / 2.0
        event_type = 'like' if f.rating >= 4 else 'dislike' if f.rating <= 2 else 'view'
        
        doc = {
            "content_id": f.content_id,
            "user_id": user_id,
            "event_type": event_type,
            "watch_time_ms": 0,
            "reward": reward,
            "rating": f.rating,
            "comment": f.comment,
            "timestamp": time.time(),
            "ip_address": request.client.host if request.client else "unknown"
        }
        
        result = get_collection("feedback").insert_one(doc)
        feedback_id = str(result.inserted_id)
        
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "rating": f.rating,
            "event_type": event_type,
            "reward": reward,
            "message": "Feedback saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
