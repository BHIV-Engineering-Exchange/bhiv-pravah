#!/usr/bin/env python3
"""
Test Supabase connection with provided credentials
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_supabase_connection():
    """Test direct Supabase connection"""
    
    print("Testing Supabase Connection")
    print("=" * 40)
    
    try:
        from supabase import create_client
        
        # Your credentials
        url = "https://roranqhhhnrdidjdrzvk.supabase.co"
        service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJvcmFucWhoaG5yZGlkamRyenZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTEyODQxOCwiZXhwIjoyMDc2NzA0NDE4fQ._WmsYDEFCBAH4l2mO0egKIVZBGB8Yl8Wic41ta89QWI"
        
        print(f"URL: {url}")
        print(f"Service Key: {service_key[:50]}...")
        
        # Create client
        client = create_client(url, service_key)
        print("Client created successfully")
        
        # Test connection with a simple query
        result = client.table("agents").select("*").limit(1).execute()
        print(f"Connection test: SUCCESS")
        print(f"Agents table exists: {len(result.data)} records found")
        
        # Check if tables exist
        tables = ["agents", "routing_logs", "feedback_events"]
        for table in tables:
            try:
                result = client.table(table).select("*", count="exact").limit(1).execute()
                print(f"Table '{table}': EXISTS ({result.count} records)")
            except Exception as e:
                print(f"Table '{table}': MISSING or ERROR - {e}")
        
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def test_app_database():
    """Test app database integration"""
    
    print("\nTesting App Database Integration")
    print("-" * 40)
    
    try:
        from app.core.database import get_db
        
        db = get_db()
        print(f"Database client: {type(db).__name__}")
        
        # Test agents query
        agents = db.table("agents").select("*").execute()
        print(f"App database test: SUCCESS")
        print(f"Agents available: {len(agents.data)}")
        
        return True
        
    except Exception as e:
        print(f"App database test failed: {e}")
        return False

if __name__ == "__main__":
    print("Supabase Integration Test")
    print("=" * 50)
    
    # Test direct connection
    direct_ok = test_supabase_connection()
    
    # Test app integration
    app_ok = test_app_database()
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"Direct Supabase: {'PASS' if direct_ok else 'FAIL'}")
    print(f"App Integration: {'PASS' if app_ok else 'FAIL'}")
    
    if direct_ok and app_ok:
        print("\nSUPABASE FULLY CONNECTED!")
        print("Your database is properly integrated")
    elif direct_ok:
        print("\nSupabase works but app needs restart")
        print("Restart your FastAPI server")
    else:
        print("\nConnection issues detected")
        print("Check network and credentials")