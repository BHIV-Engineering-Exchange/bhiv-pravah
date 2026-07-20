#!/usr/bin/env python3
"""
Test External Communication Services
Tests Twilio, Gmail, and Telegram credentials directly
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def test_gmail_smtp():
    """Test Gmail SMTP connection"""
    print("[INFO] Testing Gmail SMTP...")
    
    gmail_email = os.getenv("GMAIL_EMAIL")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not gmail_email or gmail_email == "your_gmail_email":
        print("[ERROR] Gmail credentials not set")
        return False
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_email, gmail_password)
        server.quit()
        print(f"[SUCCESS] Gmail SMTP connection successful for {gmail_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Gmail SMTP failed: {str(e)}")
        return False

def test_twilio_api():
    """Test Twilio API connection"""
    print("\n[INFO] Testing Twilio API...")
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or account_sid == "your_twilio_account_sid":
        print("[ERROR] Twilio credentials not set")
        return False
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        # Test by getting account info
        account = client.api.accounts(account_sid).fetch()
        print(f"[SUCCESS] Twilio API connection successful for account: {account.friendly_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Twilio API failed: {str(e)}")
        return False

def test_telegram_bot():
    """Test Telegram Bot API"""
    print("\n[INFO] Testing Telegram Bot API...")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token or bot_token == "your_telegram_bot_token":
        print("[ERROR] Telegram bot token not set")
        return False
    
    try:
        import httpx
        response = httpx.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"[SUCCESS] Telegram Bot API connection successful for: {bot_info.get('username', 'Unknown')}")
                return True
            else:
                print(f"[ERROR] Telegram Bot API error: {data}")
                return False
        else:
            print(f"[ERROR] Telegram Bot API HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Telegram Bot API failed: {str(e)}")
        return False

def main():
    """Run all external service tests"""
    print("External Communication Services Test")
    print("=" * 40)
    
    results = []
    results.append(("Gmail SMTP", test_gmail_smtp()))
    results.append(("Twilio API", test_twilio_api()))
    results.append(("Telegram Bot", test_telegram_bot()))
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    for service, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{service:15} {status}")
    
    failed_services = [name for name, success in results if not success]
    if failed_services:
        print(f"\n[ERROR] Failed Services: {', '.join(failed_services)}")
        print("\nTROUBLESHOOTING:")
        print("1. Check credentials in .env file")
        print("2. Verify network connectivity")
        print("3. Check service-specific settings")
    else:
        print("\n[SUCCESS] All external services are working!")

if __name__ == "__main__":
    main()