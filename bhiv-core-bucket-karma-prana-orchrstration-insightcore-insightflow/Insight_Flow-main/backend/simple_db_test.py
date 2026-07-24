#!/usr/bin/env python3
"""
Simple database connection test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database connection"""
    
    print("Database Connection Test")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        print(f"USE_SOVEREIGN_CORE: {settings.USE_SOVEREIGN_CORE}")
        print(f"SUPABASE_URL: {bool(settings.SUPABASE_URL)}")
        
        from app.core.database import get_db
        db = get_db()
        
        print(f"Database client type: {type(db).__name__}")
        
        # Test basic query
        if hasattr(db, 'table'):
            agents = db.table("agents").select("*").limit(1).execute()
            print(f"Agents query successful: {len(agents.data)} records")
            
            # Check if we have sample agents
            if agents.data:
                agent = agents.data[0]
                print(f"Sample agent: {agent.get('name', 'Unknown')}")
            
            return True
        else:
            print("Database client missing table method")
            return False
            
    except Exception as e:
        print(f"Database test failed: {e}")
        return False

def test_supabase_direct():
    """Test Supabase connection directly"""
    
    print("\nDirect Supabase Test")
    print("-" * 30)
    
    try:
        from supabase import create_client
        from app.core.config import settings
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            print("Supabase credentials missing")
            return False
        
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        
        # Test connection
        result = client.table("agents").select("*").limit(1).execute()
        print(f"Direct Supabase connection: SUCCESS")
        print(f"Agents found: {len(result.data)}")
        
        return True
        
    except Exception as e:
        print(f"Direct Supabase test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Database Integration...")
    
    # Test 1: Application database
    app_db_ok = test_database()
    
    # Test 2: Direct Supabase
    supabase_ok = test_supabase_direct()
    
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"App Database: {'PASS' if app_db_ok else 'FAIL'}")
    print(f"Supabase Direct: {'PASS' if supabase_ok else 'FAIL'}")
    
    if app_db_ok and supabase_ok:
        print("\nDatabase is properly connected!")
    elif supabase_ok:
        print("\nSupabase works but app integration needs fixing")
    else:
        print("\nDatabase connection issues detected")
        print("Check your .env file and Supabase credentials")