#!/usr/bin/env python3
"""
Simple LangGraph Endpoint Test
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def test_endpoints():
    """Test key endpoints with proper authentication"""
    
    base_url = "http://localhost:9001"
    api_key = os.getenv("API_KEY_SECRET")
    
    print(f"Testing with API key: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Health (no auth needed)
    try:
        response = httpx.get(f"{base_url}/health", timeout=10.0)
        print(f"Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test 2: Send notification (needs auth)
    try:
        data = {
            "candidate_name": "Test User",
            "candidate_email": "test@example.com",
            "candidate_phone": "+919284967526",
            "job_title": "Test Position",
            "message": "Test notification",
            "channels": ["email"],
            "application_status": "test"
        }
        
        response = httpx.post(f"{base_url}/tools/send-notification", json=data, headers=headers, timeout=30.0)
        print(f"Notification: {response.status_code}")
        if response.status_code == 200:
            print(f"  SUCCESS: {response.json()}")
        else:
            print(f"  ERROR: {response.text}")
            
    except Exception as e:
        print(f"Notification error: {e}")
    
    # Test 3: Workflow stats (needs auth)
    try:
        response = httpx.get(f"{base_url}/workflows/stats", headers=headers, timeout=10.0)
        print(f"Stats: {response.status_code}")
        if response.status_code == 200:
            print(f"  SUCCESS: {response.json()}")
        else:
            print(f"  ERROR: {response.text}")
            
    except Exception as e:
        print(f"Stats error: {e}")

if __name__ == "__main__":
    test_endpoints()