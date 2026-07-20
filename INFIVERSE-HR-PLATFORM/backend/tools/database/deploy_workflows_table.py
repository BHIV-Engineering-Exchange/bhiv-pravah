#!/usr/bin/env python3
"""
Deploy only the workflows table to existing database
"""

import psycopg2
import psycopg2.errors
import sys
from datetime import datetime

DATABASE_URL = "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"

def deploy_workflows_table():
    """Deploy only the workflows table"""
    try:
        print("Deploying workflows table...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Connected to database")
        
        # Create workflows table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id SERIAL PRIMARY KEY,
            workflow_id VARCHAR(100) UNIQUE NOT NULL,
            workflow_type VARCHAR(100) NOT NULL CHECK (workflow_type IN ('candidate_application', 'candidate_shortlisted', 'interview_scheduled', 'custom')),
            status VARCHAR(50) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled', 'completed_with_warnings')),
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL,
            job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
            client_id VARCHAR(100) REFERENCES clients(client_id) ON DELETE SET NULL,
            progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
            current_step VARCHAR(255),
            total_steps INTEGER DEFAULT 1,
            input_data JSONB,
            output_data JSONB,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("Workflows table created")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_workflows_workflow_id ON workflows(workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(workflow_type)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_candidate ON workflows(candidate_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_job ON workflows(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_client ON workflows(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_started_at ON workflows(started_at)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_completed_at ON workflows(completed_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print(f"Created {len(indexes)} indexes")
        
        # Create update trigger (PostgreSQL doesn't support IF NOT EXISTS for triggers)
        try:
            cursor.execute("""
            CREATE TRIGGER update_workflows_updated_at 
            BEFORE UPDATE ON workflows 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """)
            print("Created update trigger")
        except psycopg2.errors.DuplicateObject:
            print("Update trigger already exists")
        
        # Create audit trigger
        try:
            cursor.execute("""
            CREATE TRIGGER audit_workflows_changes 
            AFTER INSERT OR UPDATE OR DELETE ON workflows 
            FOR EACH ROW EXECUTE FUNCTION audit_table_changes()
            """)
            print("Created audit trigger")
        except psycopg2.errors.DuplicateObject:
            print("Audit trigger already exists")
        
        print("Created audit trigger")
        
        # Update schema version
        cursor.execute("""
        INSERT INTO schema_version (version, description) VALUES 
        ('4.2.2', 'Added workflows table for LangGraph workflow tracking - November 15, 2025')
        ON CONFLICT (version) DO UPDATE SET applied_at = CURRENT_TIMESTAMP
        """)
        
        print("Updated schema version")
        
        # Test the table
        test_workflow_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        cursor.execute("""
            INSERT INTO workflows (workflow_id, workflow_type, status, progress_percentage, current_step, total_steps)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (test_workflow_id, "candidate_application", "running", 50, "testing", 3))
        
        cursor.execute("SELECT workflow_id, status, progress_percentage FROM workflows WHERE workflow_id = %s", (test_workflow_id,))
        test_result = cursor.fetchone()
        
        if test_result:
            print(f"Test workflow created: {test_result[0]} - {test_result[1]} ({test_result[2]}%)")
            cursor.execute("DELETE FROM workflows WHERE workflow_id = %s", (test_workflow_id,))
            print("Test data cleaned up")
        
        conn.commit()
        
        # Verify table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'workflows' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"\nWorkflows table structure ({len(columns)} columns):")
        for column, data_type in columns:
            print(f"   - {column}: {data_type}")
        
        print("\nWorkflows table deployment completed successfully!")
        return True
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("BHIV HR Platform - Workflows Table Deployment")
    print("=" * 50)
    
    success = deploy_workflows_table()
    if success:
        print("\nNext Steps:")
        print("   1. Restart LangGraph service")
        print("   2. Test workflow tracking")
    else:
        print("\nDeployment failed.")
        sys.exit(1)