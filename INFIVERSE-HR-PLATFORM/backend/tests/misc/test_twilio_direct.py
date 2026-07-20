#!/usr/bin/env python3
"""
Test Twilio WhatsApp Sandbox Status
"""

from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

def check_whatsapp_sandbox():
    """Check WhatsApp sandbox configuration"""
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    print(f"Account SID: {account_sid}")
    print(f"WhatsApp Number: {whatsapp_number}")
    
    try:
        client = Client(account_sid, auth_token)
        
        # Test sending WhatsApp message directly
        message = client.messages.create(
            from_=f'whatsapp:{whatsapp_number}',
            to='whatsapp:+919284967526',
            body='🧪 BHIV HR Test: WhatsApp sandbox is working! Reply to confirm.'
        )
        
        print(f"SUCCESS: Message sent successfully!")
        print(f"Message SID: {message.sid}")
        print(f"Status: {message.status}")
        print(f"To: {message.to}")
        print(f"From: {message.from_}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        
        if "not a valid WhatsApp number" in str(e):
            print("\nSOLUTION: Your number is not verified in WhatsApp sandbox")
            print("1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
            print("2. Send 'join <keyword>' to +14155238886")
            print("3. Wait for confirmation message")
            
        return False

if __name__ == "__main__":
    check_whatsapp_sandbox()