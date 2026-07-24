#!/usr/bin/env python3
'''
Initialize the karma_events collection with proper indexes and schema validation.
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import karma_events_col, get_db
from pymongo import IndexModel, ASCENDING, DESCENDING
from datetime import datetime, timezone

def init_karma_events_collection():
    """Initialize karma_events collection with indexes and validation"""
    
    print("[INIT] Initializing karma_events collection...")
    
    # Create indexes for efficient querying
    indexes = [
        IndexModel([("event_id", ASCENDING)], unique=True),
        IndexModel([("event_type", ASCENDING)]),
        IndexModel([("user_id", ASCENDING)]),  # If user_id exists in data
        IndexModel([("timestamp", DESCENDING)]),
        IndexModel([("status", ASCENDING)]),
        IndexModel([("source", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)])
    ]
    
    try:
        # Create indexes
        karma_events_col.create_indexes(indexes)
        print("[OK] Indexes created successfully")
        
        # Get collection stats
        stats = karma_events_col.database.command("collStats", "karma_events")
        print(f"[STAT] Collection stats: {stats['count']} documents, {stats['size']} bytes")
        
        # Create a sample document to test
        sample_event = {
            "event_id": "test-init-001",
            "event_type": "system_init",
            "data": {
                "message": "Karma events collection initialized",
                "version": "1.0.0"
            },
            "timestamp": datetime.now(timezone.utc),
            "source": "system_initializer",
            "status": "processed",
            "response_data": {
                "status": "success",
                "message": "Collection ready for use"
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert sample document (upsert to avoid duplicates)
        result = karma_events_col.update_one(
            {"event_id": "test-init-001"},
            {"$set": sample_event},
            upsert=True
        )
        
        if result.upserted_id:
            print("[OK] Sample initialization event inserted")
        else:
            print("[INFO] Sample initialization event already exists")
        
        print("\n[SUCCESS] karma_events collection initialization complete!")
        
        # Show available indexes
        indexes_info = karma_events_col.list_indexes()
        print("\n[INDEX] Available indexes:")
        for index in indexes_info:
            print(f"  - {index['name']}: {index['key']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error initializing collection: {e}")
        return False

def verify_collection_setup():
    """Verify the collection is properly set up"""
    
    print("\n[VER] Verifying collection setup...")
    
    try:
        # Test basic operations
        test_event = {
            "event_id": "test-verify-001",
            "event_type": "test_event",
            "data": {"test": "data"},
            "timestamp": datetime.now(timezone.utc),
            "source": "verification_script",
            "status": "processed",
            "created_at": datetime.now(timezone.utc)
        }
        
        # Insert test document
        karma_events_col.insert_one(test_event)
        print("[OK] Test document inserted")
        
        # Query test document
        found = karma_events_col.find_one({"event_id": "test-verify-001"})
        if found:
            print("[OK] Test document retrieved successfully")
        else:
            print("[ERROR] Test document not found")
            return False
        
        # Clean up test document
        karma_events_col.delete_one({"event_id": "test-verify-001"})
        print("[OK] Test document cleaned up")
        
        print("[OK] Collection verification complete!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("[SETUP] Karma Events Collection Setup")
    print("=" * 40)
    
    # Initialize collection
    if init_karma_events_collection():
        # Verify setup
        if verify_collection_setup():
            print("\n[READY] All systems ready! The karma_events collection is now available.")
            print("\n[INFO] Usage:")
            print("   from database import karma_events_col")
            print("   karma_events_col.insert_one({...})")
        else:
            print("\n[WARNING] Collection initialized but verification failed.")
    else:
        print("\n[ERROR] Collection initialization failed.")
        sys.exit(1)