#!/usr/bin/env python3
"""
Additional API endpoints for chatbot and notifications
Add these to your main API
"""

from fastapi import HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from auth_system import get_current_user, require_role, User

class ChatQuery(BaseModel):
    query: str

def add_chatbot_endpoints(app):
    """Add chatbot endpoints to FastAPI app"""
    
    @app.post("/chatbot/query")
    def chatbot_query(chat_query: ChatQuery, current_user: User = Depends(get_current_user)):
        """Query the smart chatbot with live data"""
        try:
            from smart_chatbot import get_chatbot_response
            response = get_chatbot_response(chat_query.query)
            
            return {
                "query": chat_query.query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "user": current_user.username
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

    @app.get("/chatbot/health")
    def chatbot_health():
        """Check chatbot health"""
        try:
            from smart_chatbot import SmartChatbot
            chatbot = SmartChatbot()
            test_response = chatbot.quick_query("System status check")
            
            return {
                "status": "healthy",
                "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/notifications/test")
    def test_notifications(current_user: User = Depends(require_role("admin"))):
        """Test notification system (admin only)"""
        try:
            from email_notifications import demo_notifications
            demo_notifications()
            return {
                "success": True,
                "message": "Test notifications sent successfully",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Notification test failed: {str(e)}")

    print("✅ Chatbot and notification endpoints added to API")

if __name__ == "__main__":
    print("This file contains additional API endpoints.")
    print("Import and use add_chatbot_endpoints(app) in your main API file.")