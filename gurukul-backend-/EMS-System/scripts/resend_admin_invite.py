"""
Script to resend admin invitation email.
Use this if the email wasn't received or the token expired.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, PasswordToken, UserRole
from app.email_service import generate_password_token, send_password_setup_email
from datetime import datetime


async def resend_invite(admin_email: str):
    """Resend invitation email to an admin."""
    db: Session = SessionLocal()
    try:
        # Find the admin user
        admin = db.query(User).filter(
            User.email == admin_email,
            User.role == UserRole.ADMIN
        ).first()
        
        if not admin:
            print(f"ERROR: Admin with email {admin_email} not found!")
            return False
        
        print(f"Found admin: {admin.name} ({admin.email})")
        print(f"Admin ID: {admin.id}")
        print(f"Password set: {'Yes' if admin.password else 'No'}")
        
        # Check if password is already set
        if admin.password:
            print(f"\nWARNING: Admin already has a password set!")
            print("If you want to reset it, you'll need to use password reset functionality.")
            return False
        
        # Generate new password token
        print("\nGenerating new password token...")
        password_token = generate_password_token(db, admin.id)
        print(f"Token created: {password_token.token[:20]}...")
        print(f"Expires at: {password_token.expires_at}")
        
        # Send email
        print(f"\nSending email to {admin.email}...")
        email_sent = await send_password_setup_email(db, admin, password_token)
        
        if email_sent:
            print(f"\n[SUCCESS] Email sent successfully!")
            print(f"Recipient: {admin.email}")
            print(f"Setup link: http://localhost:5173/set-password?token={password_token.token}")
            print("\nPlease check:")
            print("1. Email inbox (and spam folder)")
            print("2. Brevo dashboard for delivery status")
            return True
        else:
            print(f"\n[ERROR] Failed to send email!")
            print("Check server logs for error details.")
            return False
        
    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/resend_admin_invite.py <admin-email>")
        print("\nExample:")
        print("  python scripts/resend_admin_invite.py yashikatirkey518@gmail.com")
        sys.exit(1)
    
    admin_email = sys.argv[1]
    success = asyncio.run(resend_invite(admin_email))
    sys.exit(0 if success else 1)
