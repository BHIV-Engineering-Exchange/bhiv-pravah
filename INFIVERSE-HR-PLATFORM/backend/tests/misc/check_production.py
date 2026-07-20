#!/usr/bin/env python3
"""
Check Production LangGraph Service Configuration
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def check_production_config():
    """Check if production service has real credentials"""
    
    langgraph_url = "https://bhiv-hr-langgraph.onrender.com"
    api_key = os.getenv("API_KEY_SECRET")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Check service health and config
    try:
        print("Checking production LangGraph service...")
        
        # Test health endpoint
        health_response = httpx.get(f"{langgraph_url}/health", timeout=10.0)
        print(f"Health Status: {health_response.status_code}")
        print(f"Health Response: {health_response.text}")
        
        # Test direct WhatsApp endpoint (if exists)
        test_data = {
            "phone": "+919284967526",
            "message": "Production test message"
        }
        
        whatsapp_response = httpx.post(
            f"{langgraph_url}/test/send-whatsapp",
            json=test_data,
            headers=headers,
            timeout=10.0
        )
        print(f"WhatsApp Test Status: {whatsapp_response.status_code}")
        print(f"WhatsApp Response: {whatsapp_response.text}")
        
    except Exception as e:
        print(f"Error checking production: {str(e)}")

if __name__ == "__main__":
    check_production_config()