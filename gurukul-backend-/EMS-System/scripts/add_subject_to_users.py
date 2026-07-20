"""
Migration script to add 'subject' column to users table.
This allows storing the subject for teachers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, SessionLocal

def migrate():
    """Add subject column to users table."""
    print("Adding 'subject' column to users table...")
    
    db = SessionLocal()
    try:
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='subject'
            """))
            
            if result.fetchone():
                print("[OK] Column 'subject' already exists in users table.")
            else:
                # Add the column
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN subject VARCHAR(255) NULL
                """))
                connection.commit()
                print("[OK] Column 'subject' added to users table successfully!")
        
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
