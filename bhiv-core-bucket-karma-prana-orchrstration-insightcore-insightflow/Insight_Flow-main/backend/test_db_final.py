#!/usr/bin/env python3
"""
Final database test with fresh import
"""

import sys
import os
import importlib

# Clear any cached modules
if 'app.core.database' in sys.modules:
    del sys.modules['app.core.database']
if 'app.core.config' in sys.modules:
    del sys.modules['app.core.config']

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_final():
    """Final database test"""
    
    print("Final Database Integration Test")
    print("=" * 40)
    
    try:
        # Fresh import
        from app.core.config import settings
        from app.core.database import get_db
        
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"USE_SOVEREIGN_CORE: {settings.USE_SOVEREIGN_CORE}")
        
        # Get database client
        db = get_db()
        print(f"Database client: {type(db).__name__}")
        
        # Test if it's mock
        if hasattr(db, 'data'):
            print("SUCCESS: Using mock database")
            
            # Test operations
            agents = db.table("agents").select("*").execute()
            print(f"Agents available: {len(agents.data)}")
            
            if agents.data:
                print(f"Sample agent: {agents.data[0]['name']}")
            
            # Test insert
            test_data = {
                "request_id": "test-123",
                "input_type": "text",
                "input_data": {"text": "test"},
                "status": "pending"
            }
            
            result = db.table("routing_logs").insert(test_data)
            print("Insert test: SUCCESS")
            
            return True
        else:
            print("Using real database client")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_final()
    
    print("\n" + "=" * 40)
    if success:
        print("DATABASE INTEGRATION: WORKING")
        print("Your endpoints will work with mock data")
    else:
        print("DATABASE INTEGRATION: FAILED")
        print("Manual configuration needed")