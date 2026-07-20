#!/usr/bin/env python3
"""
Send Test Messages to Specified Contacts
"""

import os
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def send_whatsapp_message():
    """Send WhatsApp message to +919284967526"""
    print("[INFO] Sending WhatsApp message...")
    
    try:
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        
        message = client.messages.create(
            from_='whatsapp:+14155238886',
            to='whatsapp:+919284967526',
            body='🎯 BHIV HR Platform Test Message\n\nHi! This is a test message from the BHIV HR communication system. The WhatsApp integration is working perfectly!\n\n✅ Status: Operational\n📧 Contact: shashankmishra0411@gmail.com'
        )
        
        print(f"[SUCCESS] WhatsApp message sent! SID: {message.sid}")
        return True
    except Exception as e:
        print(f"[ERROR] WhatsApp failed: {str(e)}")
        return False

def send_email_message():
    """Send email to blackholeinfiverse56@gmail.com"""
    print("\n[INFO] Sending email...")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'BHIV HR Platform - Communication Test'
        msg['From'] = os.getenv("GMAIL_EMAIL")
        msg['To'] = 'blackholeinfiverse56@gmail.com'
        
        text_body = """
BHIV HR Platform - Communication System Test

Hi!

This is a test email from the BHIV HR Platform communication system.

✅ Email Integration: Working
🎯 Platform Status: Operational
📊 Services: 6/6 Live
🔗 Platform URL: https://bhiv-hr-gateway-ltg0.onrender.com

The communication system has been successfully tested and is ready for production use.

Best regards,
BHIV HR Platform Team
        """
        
        html_body = """
        <html>
        <body>
        <h2>🎯 BHIV HR Platform - Communication System Test</h2>
        <p>Hi!</p>
        <p>This is a test email from the <strong>BHIV HR Platform</strong> communication system.</p>
        <ul>
        <li>✅ <strong>Email Integration:</strong> Working</li>
        <li>🎯 <strong>Platform Status:</strong> Operational</li>
        <li>📊 <strong>Services:</strong> 6/6 Live</li>
        <li>🔗 <strong>Platform URL:</strong> <a href="https://bhiv-hr-gateway-ltg0.onrender.com">BHIV HR Gateway</a></li>
        </ul>
        <p>The communication system has been successfully tested and is ready for production use.</p>
        <p><strong>Best regards,</strong><br>BHIV HR Platform Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.getenv("GMAIL_EMAIL"), os.getenv("GMAIL_APP_PASSWORD"))
            server.send_message(msg)
        
        print("[SUCCESS] Email sent successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Email failed: {str(e)}")
        return False

def send_telegram_message():
    """Send Telegram message to chat ID 5326747205"""
    print("\n[INFO] Sending Telegram message...")
    
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = "5326747205"
        
        message_text = """🎯 *BHIV HR Platform Test*

Hi Shashank!

This is a test message from the BHIV HR Platform communication system.

✅ *Status:* All systems operational
📊 *Services:* 6/6 Live  
🔗 *Platform:* [BHIV HR Gateway](https://bhiv-hr-gateway-ltg0.onrender.com)

The Telegram integration is working perfectly!

_Best regards,_
_BHIV HR Platform Team_"""
        
        response = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message_text,
                "parse_mode": "Markdown"
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print(f"[SUCCESS] Telegram message sent! Message ID: {data['result']['message_id']}")
                return True
            else:
                print(f"[ERROR] Telegram API error: {data}")
                return False
        else:
            print(f"[ERROR] Telegram HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Telegram failed: {str(e)}")
        return False

def main():
    """Send test messages to all specified contacts"""
    print("BHIV HR Platform - Sending Test Messages")
    print("=" * 45)
    print("WhatsApp: +919284967526")
    print("Email: blackholeinfiverse56@gmail.com") 
    print("Telegram: Chat ID 5326747205")
    print("=" * 45)
    
    results = []
    results.append(("WhatsApp", send_whatsapp_message()))
    results.append(("Email", send_email_message()))
    results.append(("Telegram", send_telegram_message()))
    
    print("\n" + "=" * 45)
    print("MESSAGE DELIVERY SUMMARY")
    print("=" * 45)
    
    for service, success in results:
        status = "[SENT]" if success else "[FAILED]"
        print(f"{service:10} {status}")
    
    successful = sum(1 for _, success in results if success)
    print(f"\n[SUCCESS] {successful}/3 messages sent successfully!")

if __name__ == "__main__":
    main()