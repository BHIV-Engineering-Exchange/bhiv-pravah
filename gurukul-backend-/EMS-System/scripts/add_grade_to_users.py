"""
Migration script to add 'grade' column to 'users' table.
This allows storing grade information for students.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine

def run_migration():
    print("Starting migration: Adding 'grade' column to 'users' table...")
    db: Session = SessionLocal()
    try:
        with engine.connect() as connection:
            # Check if 'grade' column already exists
            result = connection.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='users' AND column_name='grade';"
            )).fetchone()

            if result:
                print("[OK] Column 'grade' already exists in 'users' table. Skipping.")
            else:
                # Add the 'grade' column
                connection.execute(text("ALTER TABLE users ADD COLUMN grade VARCHAR(50) NULL;"))
                print("[OK] Column 'grade' added to 'users' table.")
            
            connection.commit()
        print("Migration for 'grade' column completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"[X] Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
