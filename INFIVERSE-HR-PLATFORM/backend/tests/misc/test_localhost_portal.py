#!/usr/bin/env python3
"""
Test WhatsApp via Localhost Portal Integration
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def test_localhost_portal():
    """Test WhatsApp via localhost LangGraph service"""
    
    localhost_url = "http://localhost:9001"
    api_key = os.getenv("API_KEY_SECRET")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test WhatsApp notification via localhost
    notification_data = {
        "candidate_name": "John Doe",
        "candidate_email": "john.doe@example.com",
        "candidate_phone": "+919284967526",
        "job_title": "Software Engineer", 
        "message": "LOCALHOST TEST: Your interview has been scheduled for tomorrow at 10 AM.",
        "channels": ["whatsapp"],
        "application_status": "interview_scheduled"
    }
    
    print("Testing WhatsApp via localhost LangGraph...")
    print(f"URL: {localhost_url}/tools/send-notification")
    print(f"Phone: {notification_data['candidate_phone']}")
    
    try:
        response = httpx.post(
            f"{localhost_url}/tools/send-notification",
            json=notification_data,
            headers=headers,
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: WhatsApp sent via localhost!")
            print("Check your WhatsApp for message")
        else:
            print(f"ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Make sure localhost LangGraph service is running on port 9001")

if __name__ == "__main__":
    test_localhost_portal()