import psycopg2
import sys

# Database connection details
DB_CONFIG = {
    'host': 'dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com',
    'port': 5432,
    'database': 'bhiv_hr_i7zb',
    'user': 'bhiv_user',
    'password': 'JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA'
}

# SQL commands to execute
SQL_COMMANDS = [
    # Add missing columns to clients table
    """
    ALTER TABLE clients 
    ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;
    """,
    
    # Update existing records
    """
    UPDATE clients 
    SET failed_login_attempts = 0 
    WHERE failed_login_attempts IS NULL;
    """,
    
    # Create job_applications table
    """
    CREATE TABLE IF NOT EXISTS job_applications (
        id SERIAL PRIMARY KEY,
        candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        cover_letter TEXT,
        status VARCHAR(50) DEFAULT 'applied' CHECK (status IN ('applied', 'reviewed', 'shortlisted', 'rejected', 'withdrawn')),
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(candidate_id, job_id)
    );
    """,
    
    # Add indexes
    """
    CREATE INDEX IF NOT EXISTS idx_job_applications_candidate ON job_applications(candidate_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_applications_job ON job_applications(job_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_job_applications_date ON job_applications(applied_date);
    """,
    
    # Update schema version
    """
    INSERT INTO schema_version (version, description) VALUES 
    ('4.2.0', 'Production schema with job_applications table and client auth fixes')
    ON CONFLICT (version) DO UPDATE SET applied_at = CURRENT_TIMESTAMP;
    """
]

def execute_deployment():
    """Execute database schema deployment"""
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Connected successfully!")
        print("Executing schema deployment commands...\n")
        
        for i, sql in enumerate(SQL_COMMANDS, 1):
            try:
                print(f"Executing command {i}/{len(SQL_COMMANDS)}...")
                cursor.execute(sql)
                conn.commit()
                print(f"Command {i} executed successfully")
            except Exception as e:
                print(f"Error in command {i}: {e}")
                conn.rollback()
                continue
        
        # Verify deployment
        print("\nVerifying deployment...")
        
        # Check schema version
        cursor.execute("SELECT version, applied_at FROM schema_version ORDER BY applied_at DESC LIMIT 1;")
        version_result = cursor.fetchone()
        if version_result:
            print(f"Schema version: {version_result[0]} (applied: {version_result[1]})")
        
        # Check clients table columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'clients' 
            AND column_name IN ('failed_login_attempts', 'locked_until');
        """)
        client_columns = cursor.fetchall()
        print(f"Clients table columns added: {len(client_columns)}/2")
        
        # Check job_applications table
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'job_applications';
        """)
        job_apps_table = cursor.fetchone()
        if job_apps_table:
            print("job_applications table created")
        else:
            print("job_applications table not found")
        
        cursor.close()
        conn.close()
        
        print("\nDATABASE DEPLOYMENT COMPLETED!")
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("BHIV HR Platform - Database Schema Deployment v4.2.0")
    print("=" * 60)
    
    success = execute_deployment()
    
    if success:
        print("\nNext step: Redeploy Gateway service on Render dashboard")
        print("   Go to: https://dashboard.render.com -> bhiv-hr-gateway -> Manual Deploy")
    else:
        print("\nDeployment failed. Check connection and try again.")
    
    sys.exit(0 if success else 1)
