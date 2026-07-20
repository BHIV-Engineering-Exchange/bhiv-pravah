"""
Test email configuration and SMTP connection.
Run this to verify your email setup is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings


async def test_email_config():
    """Test email configuration and send a test email."""
    print("=" * 60)
    print("Email Configuration Test".center(60))
    print("=" * 60)

    # Check configuration
    print("\n1. Checking Configuration:")
    print(f"   MAIL_SERVER: {settings.MAIL_SERVER}")
    print(f"   MAIL_USERNAME: {settings.MAIL_USERNAME}")
    print(f"   MAIL_FROM: {settings.MAIL_FROM}")
    print(f"   MAIL_PORT: {settings.MAIL_PORT}")
    print(f"   MAIL_STARTTLS: {settings.MAIL_STARTTLS}")
    print(f"   USE_CREDENTIALS: {settings.USE_CREDENTIALS}")
    print(f"   Password set: {'Yes' if settings.MAIL_PASSWORD else 'No'}")

    # Validate configuration
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("\n[ERROR] MAIL_USERNAME or MAIL_PASSWORD is not set!")
        print("Please configure your .env file with email credentials.")
        return False

    if settings.MAIL_SERVER != "smtp-relay.brevo.com":
        print(f"\n[WARNING] MAIL_SERVER is set to {settings.MAIL_SERVER}")
        print("Expected: smtp-relay.brevo.com for Brevo")

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

    # Test email sending
    print("\n2. Testing Email Connection...")
    test_recipient = settings.MAIL_USERNAME  # Send to yourself for testing
    
    try:
        message = MessageSchema(
            subject="Test Email - School Management System",
            recipients=[test_recipient],
            body=f"""
This is a test email from the School Management System.

If you received this email, your email configuration is working correctly!

Configuration Details:
- Server: {settings.MAIL_SERVER}
- Port: {settings.MAIL_PORT}
- From: {settings.MAIL_FROM}

Best regards,
School Management System
            """,
            subtype=MessageType.plain,
        )

        print(f"   Attempting to send test email to: {test_recipient}")
        fm = FastMail(conf)
        await fm.send_message(message)
        
        print("   [SUCCESS] Email sent successfully!")
        print(f"   Please check your inbox: {test_recipient}")
        print("   Also check spam/junk folder!")
        return True

    except Exception as e:
        print("   [ERROR] Failed to send email")
        print(f"   Error: {str(e)}")
        print("\n   Common Issues:")
        print("   1. Wrong SMTP credentials")
        print("   2. MAIL_USERNAME doesn't match Brevo account email")
        print("   3. MAIL_PASSWORD is not the SMTP key")
        print("   4. Firewall blocking SMTP connection")
        print("   5. Brevo account is suspended")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_email_config())
    sys.exit(0 if success else 1)
