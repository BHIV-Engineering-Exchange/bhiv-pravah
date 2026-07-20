import sys
import os
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.config import settings

def migrate():
    # Load .env if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
    except ImportError:
        pass

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Try fallbacks from settings
        db_url = settings.DATABASE_URL
        
    if not db_url:
        print("DATABASE_URL not set. Skipping migration.")
        return

    print(f"Connecting to database...")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        print("Checking for missing columns in prana_packets...")
        
        # Check previous_hash
        try:
            conn.execute(text("SELECT previous_hash FROM prana_packets LIMIT 1"))
            print("Column 'previous_hash' already exists.")
        except Exception:
            print("Adding column 'previous_hash'...")
            # We use a new transaction/connection if the old one aborted
            with engine.connect() as conn2:
                conn2.execute(text("ALTER TABLE prana_packets ADD COLUMN previous_hash VARCHAR(64)"))
                conn2.commit()

        # Check current_hash
        try:
            with engine.connect() as conn3:
                conn3.execute(text("SELECT current_hash FROM prana_packets LIMIT 1"))
                print("Column 'current_hash' already exists.")
        except Exception:
            print("Adding column 'current_hash'...")
            with engine.connect() as conn4:
                conn4.execute(text("ALTER TABLE prana_packets ADD COLUMN current_hash VARCHAR(64)"))
                conn4.commit()
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
