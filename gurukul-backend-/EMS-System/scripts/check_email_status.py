"""
Script to check email status and configuration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, PasswordToken
from app.config import settings
from datetime import datetime


def check_email_status():
    """Check email configuration and recent password tokens."""
    print("=" * 60)
    print("Email Status Check")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Email Configuration:")
    print(f"   MAIL_SERVER: {settings.MAIL_SERVER}")
    print(f"   MAIL_USERNAME: {settings.MAIL_USERNAME}")
    print(f"   MAIL_FROM: {settings.MAIL_FROM}")
    print(f"   MAIL_PORT: {settings.MAIL_PORT}")
    print(f"   Password set: {'Yes' if settings.MAIL_PASSWORD else 'No'}")
    
    # Check recent password tokens
    db: Session = SessionLocal()
    try:
        print("\n2. Recent Password Tokens (Last 10):")
        tokens = db.query(PasswordToken).order_by(PasswordToken.created_at.desc()).limit(10).all()
        
        if not tokens:
            print("   No password tokens found.")
        else:
            for token in tokens:
                user = db.query(User).filter(User.id == token.user_id).first()
                status = "USED" if token.is_used else "ACTIVE"
                expired = "EXPIRED" if token.expires_at < datetime.utcnow() else "VALID"
                
                print(f"\n   Token ID: {token.id}")
                print(f"   User: {user.name if user else 'Unknown'} ({user.email if user else 'Unknown'})")
                print(f"   Status: {status} | {expired}")
                print(f"   Created: {token.created_at}")
                print(f"   Expires: {token.expires_at}")
                print(f"   Token: {token.token[:20]}...")
        
        # Check users without passwords
        print("\n3. Users Without Passwords (Need Email Setup):")
        users_no_password = db.query(User).filter(User.password == None).all()
        if not users_no_password:
            print("   No users without passwords.")
        else:
            for user in users_no_password:
                print(f"   - {user.name} ({user.email}) - Role: {user.role.value}")
                # Check if they have active tokens
                active_tokens = db.query(PasswordToken).filter(
                    PasswordToken.user_id == user.id,
                    PasswordToken.is_used == False,
                    PasswordToken.expires_at > datetime.utcnow()
                ).all()
                print(f"     Active tokens: {len(active_tokens)}")
                if active_tokens:
                    for token in active_tokens:
                        setup_link = f"{settings.FRONTEND_URL}/set-password?token={token.token}"
                        print(f"     Setup link: {setup_link}")
        
    except Exception as e:
        print(f"\nError checking database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_email_status()
