#!/usr/bin/env python3
"""
Test WhatsApp Webhook Setup
"""

import requests

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    webhook_url = "https://bhiv-hr-langgraph.onrender.com/webhook/whatsapp"
    
    # Test payload (simulates Twilio webhook)
    test_payload = {
        "From": "whatsapp:+919284967526",
        "To": "whatsapp:+14155238886", 
        "Body": "1"
    }
    
    try:
        response = requests.post(webhook_url, json=test_payload, timeout=10)
        print(f"✅ Webhook Response: {response.status_code}")
        print(f"📄 Response Body: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Webhook Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing WhatsApp Webhook Setup...")
    test_webhook_endpoint()