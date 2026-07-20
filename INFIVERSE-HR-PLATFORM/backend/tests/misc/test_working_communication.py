#!/usr/bin/env python3
"""
Test Working Communication - Multi-Channel Endpoint
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
API_KEY = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def test_email_notification():
    """Test email notification via multi-channel endpoint"""
    print("[INFO] Testing Email via Multi-Channel Endpoint...")
    
    notification_data = {
        "candidate_name": "Test Candidate",
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "job_title": "Software Engineer",
        "message": "This is a test notification from BHIV HR Platform",
        "channels": ["email"],
        "application_status": "updated"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/tools/send-notification",
                json=notification_data,
                headers=HEADERS
            )
            
            print(f"[SUCCESS] Response Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', False)}")
                print(f"   Results: {data.get('results', [])}")
                return True, data
            else:
                print(f"[ERROR] Failed: {response.text}")
                return False, response.text
                
    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        return False, str(e)

async def test_whatsapp_notification():
    """Test WhatsApp notification via multi-channel endpoint"""
    print("\n[INFO] Testing WhatsApp via Multi-Channel Endpoint...")
    
    notification_data = {
        "candidate_name": "Test Candidate",
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "job_title": "Software Engineer", 
        "message": "This is a test WhatsApp notification from BHIV HR Platform",
        "channels": ["whatsapp"],
        "application_status": "updated"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/tools/send-notification",
                json=notification_data,
                headers=HEADERS
            )
            
            print(f"[SUCCESS] Response Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', False)}")
                print(f"   Results: {data.get('results', [])}")
                return True, data
            else:
                print(f"[ERROR] Failed: {response.text}")
                return False, response.text
                
    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        return False, str(e)

async def main():
    """Test working communication channels"""
    print("Testing Working Communication Channels")
    print("=" * 40)
    
    # Test email
    email_success, email_result = await test_email_notification()
    
    # Test WhatsApp
    whatsapp_success, whatsapp_result = await test_whatsapp_notification()
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    print(f"Email Notification:    {'[PASS]' if email_success else '[FAIL]'}")
    print(f"WhatsApp Notification: {'[PASS]' if whatsapp_success else '[FAIL]'}")
    
    if email_success and whatsapp_success:
        print("\n[SUCCESS] Multi-channel communication is working!")
    else:
        print("\n[INFO] Some channels may be in mock mode (check results above)")

if __name__ == "__main__":
    asyncio.run(main())