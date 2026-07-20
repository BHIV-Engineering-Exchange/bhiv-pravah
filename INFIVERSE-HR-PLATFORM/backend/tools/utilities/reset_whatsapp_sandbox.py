#!/usr/bin/env python3
"""
Reset WhatsApp Sandbox
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def reset_whatsapp_sandbox():
    """Reset WhatsApp sandbox and get new join code"""
    print("[INFO] Resetting WhatsApp Sandbox...")
    
    try:
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        
        # Get sandbox settings
        sandbox = client.messaging.v1.services.list()
        print(f"Current sandbox status checked")
        
        print("\nTo reset WhatsApp sandbox:")
        print("1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        print("2. Click 'Reset Sandbox'")
        print("3. Get new join code")
        print("4. Send 'join <new-code>' to +14155238886")
        print("5. Add your number +919284967526")
        
        return True
    except Exception as e:
        print(f"[ERROR] Reset failed: {str(e)}")
        return False

if __name__ == "__main__":
    reset_whatsapp_sandbox()