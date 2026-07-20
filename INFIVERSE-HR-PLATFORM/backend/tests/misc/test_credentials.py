#!/usr/bin/env python3
"""
BHIV HR Platform - Credential Validation Script
Tests all communication services after deployment
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_twilio():
    """Test Twilio WhatsApp service"""
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            return {"status": "FAIL", "service": "Twilio", "error": "Missing credentials"}
        
        client = Client(account_sid, auth_token)
        account = client.api.accounts(account_sid).fetch()
        
        return {
            "status": "OK", 
            "service": "Twilio WhatsApp", 
            "account": account_sid,
            "account_status": account.status
        }
    except Exception as e:
        return {"status": "FAIL", "service": "Twilio", "error": str(e)}

async def test_gmail():
    """Test Gmail SMTP connection"""
    try:
        import smtplib
        
        email = os.getenv('GMAIL_EMAIL')
        password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not email or not password:
            return {"status": "FAIL", "service": "Gmail", "error": "Missing credentials"}
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email, password)
        
        return {
            "status": "OK", 
            "service": "Gmail SMTP", 
            "email": email,
            "connection": "Success"
        }
    except Exception as e:
        return {"status": "FAIL", "service": "Gmail", "error": str(e)}

async def test_telegram():
    """Test Telegram Bot"""
    try:
        from telegram import Bot
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not token:
            return {"status": "FAIL", "service": "Telegram", "error": "Missing token"}
        
        bot = Bot(token=token)
        bot_info = await bot.get_me()
        
        return {
            "status": "OK", 
            "service": "Telegram Bot", 
            "username": f"@{bot_info.username}",
            "bot_id": bot_info.id
        }
    except Exception as e:
        return {"status": "FAIL", "service": "Telegram", "error": str(e)}

async def test_gemini():
    """Test Gemini AI"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            return {"status": "FAIL", "service": "Gemini", "error": "Missing API key"}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, respond with 'OK' if you're working")
        
        return {
            "status": "OK", 
            "service": "Gemini AI", 
            "model": "gemini-pro",
            "response": response.text[:50]
        }
    except Exception as e:
        return {"status": "FAIL", "service": "Gemini", "error": str(e)}

async def test_live_services():
    """Test live deployed services"""
    try:
        import httpx
        
        services = [
            ("Gateway", "https://bhiv-hr-gateway-ltg0.onrender.com/health"),
            ("LangGraph", "https://bhiv-hr-langgraph.onrender.com/health"),
            ("Agent", "https://bhiv-hr-agent-nhgg.onrender.com/health")
        ]
        
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for name, url in services:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        results.append({"status": "OK", "service": f"{name} Service", "url": url, "response_code": 200})
                    else:
                        results.append({"status": "FAIL", "service": f"{name} Service", "error": f"HTTP {response.status_code}"})
                except Exception as e:
                    results.append({"status": "FAIL", "service": f"{name} Service", "error": str(e)})
        
        return results
    except Exception as e:
        return [{"status": "FAIL", "service": "Live Services", "error": str(e)}]

async def main():
    """Run all credential and service tests"""
    print("BHIV HR Platform - Post-Deployment Validation")
    print("=" * 60)
    
    # Test credentials
    credential_tests = [
        ("Twilio WhatsApp", test_twilio()),
        ("Gmail SMTP", test_gmail()),
        ("Telegram Bot", test_telegram()),
        ("Gemini AI", test_gemini())
    ]
    
    print("\n1. CREDENTIAL VALIDATION:")
    print("-" * 30)
    
    credential_results = []
    for name, test_coro in credential_tests:
        print(f"Testing {name}...")
        result = await test_coro
        credential_results.append(result)
        
        if result["status"] == "OK":
            print(f"   [OK] {result['service']}: SUCCESS")
            for key, value in result.items():
                if key not in ["status", "service"]:
                    print(f"      {key}: {value}")
        else:
            print(f"   [FAIL] {result['service']}: FAILED")
            print(f"      Error: {result['error']}")
    
    # Test live services
    print("\n2. LIVE SERVICE VALIDATION:")
    print("-" * 30)
    
    service_results = await test_live_services()
    
    for result in service_results:
        if result["status"] == "OK":
            print(f"   [OK] {result['service']}: ONLINE")
            if "url" in result:
                print(f"      URL: {result['url']}")
        else:
            print(f"   [FAIL] {result['service']}: OFFLINE")
            print(f"      Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY:")
    
    credential_success = sum(1 for r in credential_results if r["status"] == "OK")
    service_success = sum(1 for r in service_results if r["status"] == "OK")
    
    print(f"\nCredentials: {credential_success}/{len(credential_results)} working")
    for result in credential_results:
        status_text = '[OK]' if result['status'] == 'OK' else '[FAIL]'
        print(f"   {status_text} {result['service']}")
    
    print(f"\nServices: {service_success}/{len(service_results)} online")
    for result in service_results:
        status_text = '[OK]' if result['status'] == 'OK' else '[FAIL]'
        print(f"   {status_text} {result['service']}")
    
    total_success = credential_success + service_success
    total_tests = len(credential_results) + len(service_results)
    
    print(f"\nOverall: {total_success}/{total_tests} tests passed")
    
    if total_success == total_tests:
        print("\n[SUCCESS] ALL SYSTEMS READY - Proceed to Step 3 (Docker Startup)")
        return True
    else:
        print(f"\n[WARNING] {total_tests - total_success} issues need attention")
        return False

if __name__ == "__main__":
    asyncio.run(main())