"""
One-time setup script to create the initial SUPER_ADMIN account.
This script should be run once during initial setup.

Usage:
    python scripts/setup_super_admin.py

This script:
1. Checks if a SUPER_ADMIN already exists
2. If not, creates one with the predefined credentials
3. After first successful run, subsequent runs will do nothing
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, UserRole
from app.auth import super_admin_exists, create_super_admin, get_password_hash


def setup_super_admin():
    """Create the initial super admin account if it doesn't exist."""
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if super admin already exists
        if super_admin_exists(db):
            print("Super Admin already exists. Setup is not needed.")
            print("  The system already has a SUPER_ADMIN account.")
            return
        
        # Create super admin
        print("Creating Super Admin account...")
        user = create_super_admin(
            db=db,
            name="Super Admin",
            email="blackholeinfiverse48@gmail.com",
            password="superadmin123"
        )
        
        print("Super Admin created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role.value}")
        print(f"  School ID: {user.school_id}")
        print("\nIMPORTANT:")
        print("  - Keep these credentials secure")
        print("  - Change the password after first login if possible")
        print("  - Do not run this script again")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating super admin: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    setup_super_admin()
