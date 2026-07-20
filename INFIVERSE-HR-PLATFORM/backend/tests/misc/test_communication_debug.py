#!/usr/bin/env python3
"""
Communication Debug Test - BHIV HR Platform
Tests all communication endpoints and identifies timeout issues
"""

import httpx
import asyncio
import os
import sys
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

# Configuration
LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
API_KEY = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def test_langgraph_health():
    """Test LangGraph service health"""
    print("[INFO] Testing LangGraph Health...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LANGGRAPH_URL}/health", headers=HEADERS)
            print(f"[SUCCESS] Health Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Service: {data.get('service', 'Unknown')}")
                print(f"   Status: {data.get('status', 'Unknown')}")
                return True
            else:
                print(f"[ERROR] Health check failed: {response.text}")
                return False
    except Exception as e:
        print(f"[ERROR] Health check error: {str(e)}")
        return False

async def test_email_endpoint():
    """Test email sending endpoint"""
    print("\n[INFO] Testing Email Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/test/send-email",
                params={
                    "recipient_email": "test@example.com",
                    "subject": "BHIV HR Test Email",
                    "message": "This is a test email from BHIV HR Platform"
                },
                headers=HEADERS
            )
            print(f"[SUCCESS] Email Test Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', False)}")
                print(f"   Result: {data.get('result', {})}")
                return True
            else:
                print(f"[ERROR] Email test failed: {response.text}")
                return False
    except httpx.TimeoutException:
        print("[ERROR] Email test TIMEOUT - This is the issue!")
        return False
    except Exception as e:
        print(f"[ERROR] Email test error: {str(e)}")
        return False

async def test_whatsapp_endpoint():
    """Test WhatsApp sending endpoint"""
    print("\n[INFO] Testing WhatsApp Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/test/send-whatsapp",
                params={
                    "phone": "+1234567890",
                    "message": "Test message from BHIV HR Platform"
                },
                headers=HEADERS
            )
            print(f"[SUCCESS] WhatsApp Test Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', False)}")
                print(f"   Result: {data.get('result', {})}")
                return True
            else:
                print(f"[ERROR] WhatsApp test failed: {response.text}")
                return False
    except httpx.TimeoutException:
        print("[ERROR] WhatsApp test TIMEOUT - This is the issue!")
        return False
    except Exception as e:
        print(f"[ERROR] WhatsApp test error: {str(e)}")
        return False

async def test_telegram_endpoint():
    """Test Telegram sending endpoint"""
    print("\n[INFO] Testing Telegram Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/test/send-telegram",
                params={
                    "chat_id": "123456789",
                    "message": "Test message from BHIV HR Platform"
                },
                headers=HEADERS
            )
            print(f"[SUCCESS] Telegram Test Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', False)}")
                print(f"   Result: {data.get('result', {})}")
                return True
            else:
                print(f"[ERROR] Telegram test failed: {response.text}")
                return False
    except httpx.TimeoutException:
        print("[ERROR] Telegram test TIMEOUT - This is the issue!")
        return False
    except Exception as e:
        print(f"[ERROR] Telegram test error: {str(e)}")
        return False

async def check_credentials():
    """Check if communication credentials are properly set"""
    print("\n[INFO] Checking Communication Credentials...")
    
    credentials = {
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
        "GMAIL_EMAIL": os.getenv("GMAIL_EMAIL"),
        "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN")
    }
    
    for key, value in credentials.items():
        if value and value != f"your_{key.lower()}":
            print(f"[SUCCESS] {key}: Set (***{value[-4:]})")
        else:
            print(f"[ERROR] {key}: Not set or using placeholder")

async def main():
    """Run all communication tests"""
    print("BHIV HR Platform - Communication Debug Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print(f"LangGraph URL: {LANGGRAPH_URL}")
    print(f"API Key: ***{API_KEY[-8:] if API_KEY else 'NOT SET'}")
    print("=" * 50)
    
    # Check credentials first
    await check_credentials()
    
    # Test LangGraph health
    health_ok = await test_langgraph_health()
    
    if not health_ok:
        print("\n[ERROR] LangGraph service is not healthy. Communication tests may fail.")
        return
    
    # Test communication endpoints
    results = []
    results.append(("Email", await test_email_endpoint()))
    results.append(("WhatsApp", await test_whatsapp_endpoint()))
    results.append(("Telegram", await test_telegram_endpoint()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{test_name:15} {status}")
    
    failed_tests = [name for name, success in results if not success]
    if failed_tests:
        print(f"\n[ERROR] Failed Tests: {', '.join(failed_tests)}")
        print("\nTROUBLESHOOTING RECOMMENDATIONS:")
        print("1. Check if LangGraph service is running and accessible")
        print("2. Verify communication credentials in .env file")
        print("3. Check network connectivity to external services")
        print("4. Increase timeout values if services are slow")
        print("5. Check LangGraph service logs for detailed errors")
    else:
        print("\n[SUCCESS] All communication tests passed!")

if __name__ == "__main__":
    asyncio.run(main())