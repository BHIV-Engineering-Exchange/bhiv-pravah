#!/usr/bin/env python3
"""
WhatsApp/Twilio Diagnostic Tool
Diagnoses WhatsApp messaging issues and provides troubleshooting steps
"""

import os
import sys
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def load_config():
    """Load Twilio configuration from environment"""
    return {
        'account_sid': os.getenv('TWILIO_ACCOUNT_SID', '<YOUR_TWILIO_ACCOUNT_SID>'),
        'auth_token': os.getenv('TWILIO_AUTH_TOKEN', '<YOUR_TWILIO_AUTH_TOKEN>'),
        'whatsapp_number': os.getenv('TWILIO_WHATSAPP_NUMBER', '+14155238886')
    }

def check_twilio_account(config):
    """Check Twilio account status and sandbox configuration"""
    print("🔍 Checking Twilio Account Status...")
    
    try:
        client = Client(config['account_sid'], config['auth_token'])
        
        # Get account info
        account = client.api.accounts(config['account_sid']).fetch()
        print(f"✅ Account SID: {account.sid}")
        print(f"✅ Account Status: {account.status}")
        print(f"✅ Account Type: {account.type}")
        
        # Check WhatsApp sandbox status
        print(f"\n📱 WhatsApp Sandbox Configuration:")
        print(f"✅ Sandbox Number: {config['whatsapp_number']}")
        
        return True, client
        
    except TwilioRestException as e:
        print(f"❌ Twilio API Error: {e.msg}")
        return False, None
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        return False, None

def check_sandbox_participants(client):
    """Check WhatsApp sandbox participants (verified numbers)"""
    print("\n👥 Checking WhatsApp Sandbox Participants...")
    
    try:
        # Get sandbox participants
        participants = client.messaging.v1.services.list()
        
        if participants:
            print("✅ Sandbox participants found:")
            for participant in participants:
                print(f"   - Service: {participant.friendly_name}")
        else:
            print("⚠️ No sandbox participants found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking participants: {str(e)}")
        return False

def test_whatsapp_message(client, config, phone_number):
    """Test sending WhatsApp message"""
    print(f"\n📤 Testing WhatsApp Message to {phone_number}...")
    
    try:
        message = client.messages.create(
            from_=f"whatsapp:{config['whatsapp_number']}",
            to=f"whatsapp:{phone_number}",
            body="🧪 Test message from BHIV HR Platform diagnostic tool"
        )
        
        print(f"✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print(f"   Direction: {message.direction}")
        
        return True, message.sid
        
    except TwilioRestException as e:
        print(f"❌ WhatsApp Message Failed: {e.msg}")
        print(f"   Error Code: {e.code}")
        
        # Provide specific troubleshooting based on error code
        if e.code == 63016:
            print("\n🔧 SOLUTION: Phone number not verified in sandbox")
            print("   1. Go to Twilio Console > Messaging > Try it out > Send a WhatsApp message")
            print("   2. Add your phone number to the sandbox")
            print("   3. Send 'join <sandbox-keyword>' to +14155238886 from your WhatsApp")
        elif e.code == 21211:
            print("\n🔧 SOLUTION: Invalid phone number format")
            print("   1. Ensure phone number includes country code (e.g., +919876543210)")
            print("   2. Remove any spaces or special characters")
        
        return False, None
        
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False, None

def get_message_status(client, message_sid):
    """Check message delivery status"""
    print(f"\n📊 Checking Message Status for {message_sid}...")
    
    try:
        message = client.messages(message_sid).fetch()
        
        print(f"✅ Message Status: {message.status}")
        print(f"   Price: {message.price} {message.price_unit}")
        print(f"   Error Code: {message.error_code or 'None'}")
        print(f"   Error Message: {message.error_message or 'None'}")
        
        # Explain status
        status_explanations = {
            'queued': '📋 Message is queued for delivery',
            'sent': '📤 Message sent to WhatsApp',
            'delivered': '✅ Message delivered to recipient',
            'read': '👀 Message read by recipient',
            'failed': '❌ Message delivery failed',
            'undelivered': '⚠️ Message could not be delivered'
        }
        
        explanation = status_explanations.get(message.status, 'Unknown status')
        print(f"   Explanation: {explanation}")
        
        return message.status
        
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")
        return None

def provide_troubleshooting_guide():
    """Provide comprehensive troubleshooting guide"""
    print("\n" + "="*60)
    print("🔧 WHATSAPP TROUBLESHOOTING GUIDE")
    print("="*60)
    
    print("\n1. 📱 VERIFY PHONE NUMBER IN SANDBOX:")
    print("   • Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    print("   • Click 'Send a WhatsApp message'")
    print("   • Add your phone number to sandbox")
    print("   • Send 'join <keyword>' to +14155238886 from WhatsApp")
    
    print("\n2. 📞 PHONE NUMBER FORMAT:")
    print("   • Must include country code: +919876543210")
    print("   • No spaces or special characters")
    print("   • India: +91xxxxxxxxxx")
    print("   • US: +1xxxxxxxxxx")
    
    print("\n3. 🔑 SANDBOX LIMITATIONS:")
    print("   • Only verified numbers can receive messages")
    print("   • Sandbox keyword expires after 72 hours")
    print("   • Re-verify if messages stop working")
    
    print("\n4. 🚀 UPGRADE TO PRODUCTION:")
    print("   • Request WhatsApp Business API approval")
    print("   • Complete Twilio verification process")
    print("   • Get dedicated WhatsApp Business number")
    
    print("\n5. 🧪 TESTING STEPS:")
    print("   • Verify your number in sandbox first")
    print("   • Test with your own verified number")
    print("   • Check message status in Twilio Console")
    print("   • Monitor logs for error codes")

def main():
    """Main diagnostic function"""
    print("🚀 BHIV HR Platform - WhatsApp Diagnostic Tool")
    print("="*50)
    
    # Load configuration
    config = load_config()
    print(f"📋 Configuration loaded:")
    print(f"   Account SID: {config['account_sid'][:8]}...")
    print(f"   WhatsApp Number: {config['whatsapp_number']}")
    
    # Check Twilio account
    account_ok, client = check_twilio_account(config)
    if not account_ok:
        print("\n❌ Cannot proceed - Twilio account check failed")
        provide_troubleshooting_guide()
        return
    
    # Check sandbox participants
    check_sandbox_participants(client)
    
    # Test phone number (the one from your test)
    test_phone = "+9284967526"
    print(f"\n🎯 Testing with phone number: {test_phone}")
    
    # Send test message
    success, message_sid = test_whatsapp_message(client, config, test_phone)
    
    if success and message_sid:
        # Check message status
        import time
        print("\n⏳ Waiting 5 seconds before checking status...")
        time.sleep(5)
        get_message_status(client, message_sid)
    
    # Always provide troubleshooting guide
    provide_troubleshooting_guide()
    
    print("\n" + "="*60)
    print("✅ Diagnostic Complete!")
    print("💡 If messages show 'sent' but don't arrive, verify the phone number in Twilio sandbox")
    print("="*60)

if __name__ == "__main__":
    main()