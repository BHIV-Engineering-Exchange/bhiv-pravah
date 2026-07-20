"""
Test admin invitation email flow.
This simulates the complete invitation process.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, UserRole, PasswordToken
from app.email_service import generate_password_token, send_password_setup_email
from app.config import settings
from datetime import datetime


async def test_admin_invitation(test_email: str):
    """Test the complete admin invitation flow."""
    print("=" * 60)
    print("Admin Invitation Email Test".center(60))
    print("=" * 60)

    db: Session = SessionLocal()
    
    try:
        # Check if test user exists
        print(f"\n1. Checking for test user: {test_email}")
        test_user = db.query(User).filter(User.email == test_email).first()
        
        if test_user:
            print(f"   Found existing user: {test_user.name} (ID: {test_user.id})")
            print(f"   Role: {test_user.role.value}")
            print(f"   Password set: {'Yes' if test_user.password else 'No'}")
        else:
            print("   [INFO] Test user not found. This is OK for testing.")
            print("   In real scenario, user would be created by Super Admin.")
            return False

        # Generate password token
        print(f"\n2. Generating password token...")
        password_token = generate_password_token(db, test_user.id)
        print(f"   Token created: {password_token.token[:20]}...")
        print(f"   Expires at: {password_token.expires_at}")

        # Create setup link
        setup_link = f"{settings.FRONTEND_URL}/set-password?token={password_token.token}"
        print(f"\n3. Password setup link:")
        print(f"   {setup_link}")

        # Send email
        print(f"\n4. Sending invitation email...")
        email_sent = await send_password_setup_email(db, test_user, password_token)

        if email_sent:
            print("   [SUCCESS] Email sent successfully!")
            print(f"   Recipient: {test_user.email}")
            print(f"\n5. Next Steps:")
            print(f"   - Check inbox: {test_user.email}")
            print(f"   - Check spam folder")
            print(f"   - Click the setup link in email")
            print(f"   - Or use this link: {setup_link}")
            return True
        else:
            print("   [ERROR] Failed to send email!")
            print("   Check email configuration and logs.")
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
        print("Usage: python tests/email/test_admin_invitation.py <admin-email>")
        print("\nExample:")
        print("  python tests/email/test_admin_invitation.py admin@example.com")
        sys.exit(1)
    
    test_email = sys.argv[1]
    success = asyncio.run(test_admin_invitation(test_email))
    sys.exit(0 if success else 1)
