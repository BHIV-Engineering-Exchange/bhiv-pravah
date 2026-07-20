"""
Test script to check if email configuration works.
This will try to send a test email.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType


async def test_email():
    """Test email sending."""
    print("=" * 60)
    print("Email Configuration Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking Configuration:")
    print(f"   MAIL_USERNAME: {settings.MAIL_USERNAME or '(NOT SET)'}")
    print(f"   MAIL_PASSWORD: {'SET' if settings.MAIL_PASSWORD else '(NOT SET)'}")
    print(f"   MAIL_FROM: {settings.MAIL_FROM}")
    print(f"   MAIL_SERVER: {settings.MAIL_SERVER}")
    print(f"   MAIL_PORT: {settings.MAIL_PORT}")
    print(f"   MAIL_STARTTLS: {settings.MAIL_STARTTLS}")
    print(f"   USE_CREDENTIALS: {settings.USE_CREDENTIALS}")
    
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("\n[ERROR] MAIL_USERNAME or MAIL_PASSWORD is not set!")
        print("   Please configure these in your .env file.")
        return False
    
    if settings.MAIL_FROM != settings.MAIL_USERNAME:
        print(f"\nWARNING: MAIL_FROM ({settings.MAIL_FROM}) doesn't match MAIL_USERNAME ({settings.MAIL_USERNAME})")
        print("   For Gmail, they should match!")
    
    # Try to send test email
    print("\n2. Testing Email Connection...")
    
    try:
        # Create email configuration
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=settings.USE_CREDENTIALS,
            VALIDATE_CERTS=settings.VALIDATE_CERTS,
            TEMPLATE_FOLDER=None,
        )
        
        # Check if MAIL_USERNAME is a real email or Brevo SMTP identifier
        test_recipient = settings.MAIL_USERNAME
        if "@smtp-brevo.com" in test_recipient or "@smtp.brevo.com" in test_recipient:
            print(f"   WARNING: MAIL_USERNAME ({test_recipient}) appears to be a Brevo SMTP identifier, not a real email!")
            print(f"   Test emails sent to this address will NOT be received.")
            print(f"   Please enter a real email address to test:")
            test_recipient = input("   Enter test email address: ").strip()
            if not test_recipient:
                print("   Skipping test email (no recipient provided)")
                return False
        
        # Create test message
        message = MessageSchema(
            subject="Test Email - School Management System",
            recipients=[test_recipient],
            body="""
            This is a test email from the School Management System.
            
            If you received this email, your email configuration is working correctly!
            
            Best regards,
            School Management System
            """,
            subtype=MessageType.plain,
        )
        
        # Try to send
        print(f"   Attempting to send test email to: {test_recipient}")
        fm = FastMail(conf)
        await fm.send_message(message)
        print("   [OK] Email sent successfully!")
        print(f"   Please check your inbox: {test_recipient}")
        print(f"   Also check spam/junk folder!")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Failed to send email")
        print(f"   Error: {str(e)}")
        print("\n   Common Issues:")
        print("   1. Wrong App Password (use Gmail App Password, not regular password)")
        print("   2. MAIL_FROM doesn't match MAIL_USERNAME")
        print("   3. Firewall blocking SMTP connection")
        print("   4. Gmail security settings blocking the connection")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_email())
    sys.exit(0 if success else 1)
