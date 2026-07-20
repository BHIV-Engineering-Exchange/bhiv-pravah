#!/usr/bin/env python3
"""
Fix Candidates Table - Add missing password_hash column
"""

import psycopg2

# Database connection
DATABASE_URL = "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"

def check_password_hash_column():
    """Check if password_hash column exists"""
    print("Checking password_hash column...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'candidates' AND column_name = 'password_hash'
        """)
        
        result = cursor.fetchone()
        exists = result is not None
        
        print(f"password_hash column exists: {exists}")
        
        cursor.close()
        conn.close()
        return exists
        
    except Exception as e:
        print(f"Check failed: {e}")
        return False

def add_password_hash_column():
    """Add password_hash column to candidates table"""
    print("Adding password_hash column...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Add password_hash column
        cursor.execute("""
            ALTER TABLE candidates 
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
        """)
        
        conn.commit()
        print("SUCCESS: password_hash column added")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Failed to add column: {e}")
        return False

def verify_table_structure():
    """Verify complete table structure"""
    print("\nVerifying candidates table structure...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'candidates'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"Candidates table has {len(columns)} columns:")
        
        required_columns = [
            'id', 'name', 'email', 'phone', 'location', 'experience_years',
            'technical_skills', 'education_level', 'seniority_level', 
            'password_hash', 'status', 'created_at', 'updated_at'
        ]
        
        existing_columns = [col[0] for col in columns]
        
        for col in columns:
            required = "REQUIRED" if col[0] in required_columns else "OPTIONAL"
            print(f"  - {col[0]} ({col[1]}) {required}")
        
        # Check for missing required columns
        missing = [col for col in required_columns if col not in existing_columns]
        if missing:
            print(f"\nMissing required columns: {missing}")
        else:
            print(f"\nAll required columns present!")
        
        cursor.close()
        conn.close()
        return len(missing) == 0
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

def main():
    """Fix candidates table structure"""
    print("BHIV HR Platform - Fix Candidates Table")
    print("=" * 45)
    
    # Step 1: Check current state
    has_password_hash = check_password_hash_column()
    
    # Step 2: Add column if missing
    if not has_password_hash:
        print("\npassword_hash column is missing. Adding it...")
        success = add_password_hash_column()
        if not success:
            print("Failed to add password_hash column")
            return
    else:
        print("password_hash column already exists")
    
    # Step 3: Verify final structure
    structure_ok = verify_table_structure()
    
    if structure_ok:
        print("\n" + "=" * 45)
        print("SUCCESS: Candidates table is now properly configured")
        print("- password_hash column is present")
        print("- All required columns exist")
        print("- Candidate portal should work correctly")
    else:
        print("\n" + "=" * 45)
        print("ISSUES: Some problems remain with table structure")

if __name__ == "__main__":
    main()
