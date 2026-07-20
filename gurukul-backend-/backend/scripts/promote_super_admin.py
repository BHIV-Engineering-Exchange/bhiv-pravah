
import asyncio
import argparse
import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.all_models import User
from app.routers.auth import get_password_hash

async def promote_user(email: str, password: str = None, full_name: str = "Super Admin"):
    """
    Promotes an existing user to Super Admin, or creates one if they don't exist.
    A Super Admin is defined as ADMIN role with tenant_id = NULL.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"[Core] User {email} found. Promoting to Super Admin...")
            user.role = "ADMIN"
            user.tenant_id = None
            if password:
                user.hashed_password = get_password_hash(password)
            db.commit()
            print(f"[Core] SUCCESS: {email} is now a Super Admin.")
        else:
            if not password:
                print(f"[Core] ERROR: User {email} not found and no password provided for creation.")
                return

            print(f"[Core] User {email} not found. Creating new Super Admin...")
            new_user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                role="ADMIN",
                tenant_id=None,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print(f"[Core] SUCCESS: New Super Admin {email} created.")

    except Exception as e:
        print(f"[Core] FAILED: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote or create a Super Admin user.")
    parser.add_argument("--email", required=True, help="Email of the user")
    parser.add_argument("--password", help="Password for the user (required if creating new)")
    parser.add_argument("--name", default="Super Admin", help="Full name of the user")
    
    args = parser.parse_args()
    
    # Run the async promotion
    asyncio.run(promote_user(args.email, args.password, args.name))
