"""
Script to migrate the database schema:
1. Add is_active column to users table (default True)
2. Make password column nullable in users table
3. Create password_tokens table
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table."""
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None


def table_exists(conn, table_name):
    """Check if a table exists."""
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = :table_name
    """), {"table_name": table_name})
    return result.fetchone() is not None


def migrate_database():
    """Migrate database schema to add new fields and tables."""
    print("Starting database migration...")
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # 1. Add is_active column to users table (if it doesn't exist)
            print("Checking/adding is_active column to users table...")
            if not column_exists(conn, "users", "is_active"):
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE
                """))
                print("  [OK] is_active column added")
            else:
                print("  [INFO] is_active column already exists")
            
            # 2. Make password column nullable (if it's not already)
            print("Making password column nullable...")
            # First check if it's already nullable
            result = conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password'
            """))
            row = result.fetchone()
            if row and row[0] == 'NO':
                conn.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN password DROP NOT NULL
                """))
                print("  [OK] password column is now nullable")
            else:
                print("  [INFO] password column is already nullable")
            
            # 3. Create password_tokens table (if it doesn't exist)
            print("Creating password_tokens table...")
            if not table_exists(conn, "password_tokens"):
                conn.execute(text("""
                    CREATE TABLE password_tokens (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        token VARCHAR(255) UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        is_used BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX idx_password_tokens_user_id ON password_tokens(user_id)"))
                conn.execute(text("CREATE INDEX idx_password_tokens_token ON password_tokens(token)"))
                conn.execute(text("CREATE INDEX idx_password_tokens_expires_at ON password_tokens(expires_at)"))
                
                print("  [OK] password_tokens table created")
            else:
                print("  [INFO] password_tokens table already exists")
            
            # 4. Update existing users to set is_active=True (in case of NULL values)
            print("Updating existing users...")
            result = conn.execute(text("""
                UPDATE users 
                SET is_active = TRUE 
                WHERE is_active IS NULL OR is_active = FALSE
            """))
            print(f"  [OK] Updated {result.rowcount} user(s) to is_active=TRUE")
            
            # Commit the transaction
            trans.commit()
            print("\n[SUCCESS] Database migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\n[ERROR] Database migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    migrate_database()
