#!/usr/bin/env python3
"""
Fixed Communication Test - BHIV HR Platform
Tests communication endpoints with correct POST methods
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

async def test_email_endpoint():
    """Test email sending endpoint with POST method"""
    print("[INFO] Testing Email Endpoint (POST)...")
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
        print("[ERROR] Email test TIMEOUT")
        return False
    except Exception as e:
        print(f"[ERROR] Email test error: {str(e)}")
        return False

async def test_whatsapp_endpoint():
    """Test WhatsApp sending endpoint with POST method"""
    print("\n[INFO] Testing WhatsApp Endpoint (POST)...")
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
        print("[ERROR] WhatsApp test TIMEOUT")
        return False
    except Exception as e:
        print(f"[ERROR] WhatsApp test error: {str(e)}")
        return False

async def test_telegram_endpoint():
    """Test Telegram sending endpoint with POST method"""
    print("\n[INFO] Testing Telegram Endpoint (POST)...")
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
        print("[ERROR] Telegram test TIMEOUT")
        return False
    except Exception as e:
        print(f"[ERROR] Telegram test error: {str(e)}")
        return False

async def test_multi_channel_endpoint():
    """Test multi-channel notification endpoint"""
    print("\n[INFO] Testing Multi-Channel Endpoint (POST)...")
    try:
        notification_data = {
            "candidate_name": "Test Candidate",
            "candidate_email": "test@example.com",
            "candidate_phone": "+1234567890",
            "job_title": "Software Engineer",
            "message": "Your application has been updated",
            "channels": ["email"],
            "application_status": "updated"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/tools/send-notification",
                json=notification_data,
                headers=HEADERS
            )
            print(f"[SUCCESS] Multi-Channel Test Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', False)}")
                print(f"   Results: {data.get('results', [])}")
                return True
            else:
                print(f"[ERROR] Multi-channel test failed: {response.text}")
                return False
    except httpx.TimeoutException:
        print("[ERROR] Multi-channel test TIMEOUT")
        return False
    except Exception as e:
        print(f"[ERROR] Multi-channel test error: {str(e)}")
        return False

async def main():
    """Run communication tests with correct methods"""
    print("BHIV HR Platform - Fixed Communication Test")
    print("=" * 50)
    print(f"LangGraph URL: {LANGGRAPH_URL}")
    print(f"API Key: ***{API_KEY[-8:] if API_KEY else 'NOT SET'}")
    print("=" * 50)
    
    # Test communication endpoints with correct POST methods
    results = []
    results.append(("Email", await test_email_endpoint()))
    results.append(("WhatsApp", await test_whatsapp_endpoint()))
    results.append(("Telegram", await test_telegram_endpoint()))
    results.append(("Multi-Channel", await test_multi_channel_endpoint()))
    
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
    else:
        print("\n[SUCCESS] All communication tests passed!")

if __name__ == "__main__":
    asyncio.run(main())