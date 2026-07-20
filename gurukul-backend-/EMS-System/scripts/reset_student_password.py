"""
Script to reset a student's password in EMS System.
This is useful when the password in the email doesn't match what's stored in the database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, UserRole
from app.auth import get_password_hash

def reset_student_password(email: str, new_password: str):
    """Reset a student's password"""
    db: Session = SessionLocal()
    
    try:
        # Find student by email
        student = db.query(User).filter(
            User.email == email,
            User.role == UserRole.STUDENT
        ).first()
        
        if not student:
            print(f"❌ Student with email {email} not found!")
            return False
        
        # Validate password length
        if len(new_password) < 6:
            print(f"❌ Password must be at least 6 characters long!")
            return False
        
        # Hash and set new password
        hashed_password = get_password_hash(new_password)
        student.password = hashed_password
        db.commit()
        
        print(f"✅ Password reset successfully!")
        print(f"   Student: {student.name} ({student.email})")
        print(f"   New password: {new_password}")
        print(f"   Student ID: {student.id}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting password: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_student_password.py <email> <new_password>")
        print("\nExample:")
        print('  python reset_student_password.py "vascocoder2003@gmail.com" "gLKPlixCbb2fe645"')
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    print(f"\n🔄 Resetting password for student: {email}")
    print(f"   New password: {password}")
    print()
    
    success = reset_student_password(email, password)
    
    if success:
        print("\n✅ Done! The student can now log in with the new password.")
    else:
        print("\n❌ Failed to reset password. Check the error above.")
        sys.exit(1)

