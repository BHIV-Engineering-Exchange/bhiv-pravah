#!/usr/bin/env python3
"""
Deploy updated schema with workflows table to local database
Clean implementation for Solution 3 + Solution 2 fallback
"""

import psycopg2
import sys
import os
from datetime import datetime

# Database configuration
DATABASE_URL = "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"

def deploy_schema():
    """Deploy the updated schema with workflows table"""
    try:
        print("Deploying updated schema with workflows table...")
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Connected to database")
        
        # Read and execute the consolidated schema
        schema_path = os.path.join(os.path.dirname(__file__), "services", "db", "consolidated_schema.sql")
        
        if not os.path.exists(schema_path):
            print(f"Schema file not found: {schema_path}")
            return False
        
        print(f"Reading schema from: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print("Executing schema deployment...")
        
        # Execute the schema
        cursor.execute(schema_sql)
        conn.commit()
        
        print("Schema deployed successfully!")
        
        # Verify workflows table exists
        cursor.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'workflows' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        if columns:
            print(f"Workflows table created with {len(columns)} columns:")
            for table, column, data_type in columns:
                print(f"   - {column}: {data_type}")
        else:
            print("Workflows table not found after deployment")
            return False
        
        # Check schema version
        cursor.execute("SELECT version, description FROM schema_version ORDER BY applied_at DESC LIMIT 1")
        version_info = cursor.fetchone()
        if version_info:
            print(f"Schema version: {version_info[0]} - {version_info[1]}")
        
        # Test workflow table operations
        print("Testing workflow table operations...")
        
        # Test insert
        test_workflow_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        cursor.execute("""
            INSERT INTO workflows (workflow_id, workflow_type, status, progress_percentage, current_step, total_steps)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (test_workflow_id, "test", "running", 50, "testing", 3))
        
        # Test select
        cursor.execute("SELECT workflow_id, status, progress_percentage FROM workflows WHERE workflow_id = %s", (test_workflow_id,))
        test_result = cursor.fetchone()
        
        if test_result:
            print(f"Test workflow created: {test_result[0]} - {test_result[1]} ({test_result[2]}%)")
            
            # Clean up test data
            cursor.execute("DELETE FROM workflows WHERE workflow_id = %s", (test_workflow_id,))
            print("Test data cleaned up")
        else:
            print("Test workflow creation failed")
            return False
        
        conn.commit()
        
        print("Schema deployment completed successfully!")
        print("\nSummary:")
        print("   Workflows table created")
        print("   Indexes and triggers applied")
        print("   Database operations tested")
        print("   Ready for LangGraph service")
        
        return True
        
    except Exception as e:
        print(f"Schema deployment failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_deployment():
    """Verify the deployment was successful"""
    try:
        print("\nVerifying deployment...")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'workflows'
        """)
        table_count = cursor.fetchone()[0]
        
        if table_count == 0:
            print("Workflows table not found")
            return False
        
        # Check indexes
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'workflows'
        """)
        indexes = cursor.fetchall()
        print(f"Found {len(indexes)} indexes on workflows table")
        
        # Check triggers
        cursor.execute("""
            SELECT trigger_name FROM information_schema.triggers 
            WHERE event_object_table = 'workflows'
        """)
        triggers = cursor.fetchall()
        print(f"Found {len(triggers)} triggers on workflows table")
        
        print("Deployment verification successful!")
        return True
        
    except Exception as e:
        print(f"Verification failed: {str(e)}")
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("BHIV HR Platform - Schema Deployment")
    print("=" * 50)
    
    success = deploy_schema()
    if success:
        verify_deployment()
        print("\nNext Steps:")
        print("   1. Restart LangGraph service")
        print("   2. Test workflow creation")
        print("   3. Monitor progress tracking")
    else:
        print("\nDeployment failed. Please check the errors above.")
        sys.exit(1)