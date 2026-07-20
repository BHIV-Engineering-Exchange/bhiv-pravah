"""
Diagnostic script to check why a user cannot login.
Run this to see the user's status in the database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User

def check_user(email: str):
    """Check user status for login issues."""
    db: Session = SessionLocal()
    
    try:
        print(f"\nChecking user: {email}\n")
        print("=" * 50)
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"[X] USER NOT FOUND")
            print(f"   No user exists with email: {email}")
            print(f"\n   Possible reasons:")
            print(f"   - Email is incorrect")
            print(f"   - User was never created")
            return
        
        print(f"[OK] USER FOUND")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role.value}")
        print(f"   School ID: {user.school_id}")
        print(f"\n   Login Status Checks:")
        print(f"   {'[OK]' if user.is_active else '[X]'} Active: {user.is_active}")
        print(f"   {'[OK]' if user.password is not None else '[X]'} Password Set: {user.password is not None}")
        
        if not user.is_active:
            print(f"\n   [!] ISSUE: User is INACTIVE (is_active = False)")
            print(f"   Solution: User was soft-deleted. Contact admin to reactivate.")
        
        if user.password is None:
            print(f"\n   [!] ISSUE: Password is NULL")
            if user.role.value == "ADMIN":
                print(f"   Solution: This is a School Admin. They need to:")
                print(f"   1. Check their email for password setup link")
                print(f"   2. Use /auth/set-password endpoint with the token from email")
            else:
                print(f"   Solution: Password was never set. Contact admin.")
        
        if user.password is not None and user.is_active:
            print(f"\n   [OK] User should be able to login")
            print(f"   If login still fails, check:")
            print(f"   - Password is correct")
            print(f"   - Email is typed correctly")
            print(f"   - No extra spaces in email/password")
        
        print(f"\n" + "=" * 50)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_user_login.py <email>")
        print("Example: python scripts/check_user_login.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    check_user(email)
