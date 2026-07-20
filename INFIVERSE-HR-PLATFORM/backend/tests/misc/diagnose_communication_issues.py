#!/usr/bin/env python3
"""
Diagnose Communication Issues
"""

import os
import httpx
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def diagnose_whatsapp():
    """Diagnose WhatsApp issues"""
    print("[INFO] Diagnosing WhatsApp...")
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    print(f"Account SID: {account_sid}")
    print(f"WhatsApp Number: {whatsapp_number}")
    
    try:
        client = Client(account_sid, auth_token)
        
        # Check account status
        account = client.api.accounts(account_sid).fetch()
        print(f"Account Status: {account.status}")
        
        # Check WhatsApp sender status
        senders = client.messaging.v1.services.list()
        print(f"Messaging Services: {len(senders)}")
        
        # Try to get recent messages
        messages = client.messages.list(limit=5)
        print(f"Recent messages: {len(messages)}")
        for msg in messages:
            print(f"  - {msg.sid}: {msg.status} to {msg.to}")
        
        return True
    except Exception as e:
        print(f"[ERROR] WhatsApp diagnosis failed: {str(e)}")
        return False

def diagnose_telegram():
    """Diagnose Telegram bot issues"""
    print("\n[INFO] Diagnosing Telegram Bot...")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    print(f"Bot Token: {bot_token[:10]}...{bot_token[-10:] if len(bot_token) > 20 else bot_token}")
    
    try:
        # Test bot info
        response = httpx.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10.0)
        print(f"getMe Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data["result"]
                print(f"Bot Username: @{bot_info.get('username')}")
                print(f"Bot Name: {bot_info.get('first_name')}")
                print(f"Bot ID: {bot_info.get('id')}")
                
                # Test getting updates
                updates_response = httpx.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", timeout=10.0)
                print(f"getUpdates Status: {updates_response.status_code}")
                
                if updates_response.status_code == 200:
                    updates_data = updates_response.json()
                    updates = updates_data.get("result", [])
                    print(f"Recent Updates: {len(updates)}")
                    
                    if updates:
                        latest = updates[-1]
                        chat_id = latest.get("message", {}).get("chat", {}).get("id")
                        print(f"Latest Chat ID: {chat_id}")
                
                return True
            else:
                print(f"Bot API Error: {data}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Telegram diagnosis failed: {str(e)}")
        return False

def test_whatsapp_sandbox():
    """Test WhatsApp sandbox requirements"""
    print("\n[INFO] Testing WhatsApp Sandbox...")
    
    try:
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        
        # Check if number is verified in sandbox
        incoming_phone_numbers = client.incoming_phone_numbers.list()
        print(f"Verified Numbers: {len(incoming_phone_numbers)}")
        
        # Check WhatsApp sandbox status
        try:
            sandbox = client.messaging.v1.services("MG9752274e9e519418a7406176694466fa").fetch()
            print(f"Sandbox Status: Active")
        except:
            print("Sandbox Status: Not configured")
        
        return True
    except Exception as e:
        print(f"[ERROR] Sandbox test failed: {str(e)}")
        return False

def main():
    """Run communication diagnostics"""
    print("BHIV HR Platform - Communication Diagnostics")
    print("=" * 50)
    
    # Diagnose WhatsApp
    whatsapp_ok = diagnose_whatsapp()
    
    # Test WhatsApp sandbox
    sandbox_ok = test_whatsapp_sandbox()
    
    # Diagnose Telegram
    telegram_ok = diagnose_telegram()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    print(f"WhatsApp API:     {'[OK]' if whatsapp_ok else '[ISSUE]'}")
    print(f"WhatsApp Sandbox: {'[OK]' if sandbox_ok else '[ISSUE]'}")
    print(f"Telegram Bot:     {'[OK]' if telegram_ok else '[ISSUE]'}")
    
    if not whatsapp_ok:
        print("\nWhatsApp Issues:")
        print("1. Check if +919284967526 is verified in Twilio sandbox")
        print("2. Send 'join <sandbox-keyword>' to +14155238886 first")
        print("3. Verify account has WhatsApp enabled")
    
    if not telegram_ok:
        print("\nTelegram Issues:")
        print("1. Verify bot token is correct")
        print("2. Start conversation with bot first")
        print("3. Send /start command to bot")

if __name__ == "__main__":
    main()