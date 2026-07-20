#!/usr/bin/env python3
"""
Direct WhatsApp Test via LangGraph API
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def test_direct_whatsapp():
    """Test WhatsApp directly via LangGraph API"""
    
    langgraph_url = "https://bhiv-hr-langgraph.onrender.com"
    api_key = os.getenv("API_KEY_SECRET")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test WhatsApp notification
    notification_data = {
        "candidate_name": "John Doe",
        "candidate_email": "john.doe@example.com",
        "candidate_phone": "+919284967526",  # Your verified number
        "job_title": "Software Engineer",
        "message": "Your interview has been scheduled for tomorrow at 10 AM. Please confirm your availability.",
        "channels": ["whatsapp"],
        "application_status": "interview_scheduled"
    }
    
    print("Testing WhatsApp via LangGraph API...")
    print(f"Sending to: {notification_data['candidate_phone']}")
    
    try:
        response = httpx.post(
            f"{langgraph_url}/tools/send-notification",
            json=notification_data,
            headers=headers,
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: WhatsApp message sent!")
            print("Check your WhatsApp for message from +14155238886")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_direct_whatsapp()