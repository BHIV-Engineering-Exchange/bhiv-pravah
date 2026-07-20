#!/usr/bin/env python3
"""
Reset client lock status to fix authentication
"""

import psycopg2
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"

def reset_client_lock():
    """Reset client lock status"""
    print("Resetting Client Lock Status")
    print("=" * 30)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Reset failed attempts and unlock account
        cursor.execute("""
            UPDATE clients 
            SET failed_login_attempts = 0, locked_until = NULL
            WHERE client_id = %s
        """, ("<DEMO_USERNAME>",))
        
        conn.commit()
        
        # Verify the reset
        cursor.execute("""
            SELECT client_id, failed_login_attempts, locked_until, status
            FROM clients WHERE client_id = %s
        """, ("<DEMO_USERNAME>",))
        
        client = cursor.fetchone()
        
        if client:
            print(f"Client: {client[0]}")
            print(f"Failed attempts: {client[1]}")
            print(f"Locked until: {client[2]}")
            print(f"Status: {client[3]}")
            print("\nSUCCESS: Client lock reset")
        else:
            print("FAIL: Client not found")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"FAIL: Reset error: {e}")
        return False

if __name__ == "__main__":
    reset_client_lock()
