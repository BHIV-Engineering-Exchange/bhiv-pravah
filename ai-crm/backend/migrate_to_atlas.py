#!/usr/bin/env python3
"""
Migrate MongoDB data from Local to Atlas
Copies all collections from localhost to MongoDB Atlas
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
import sys

# Connection strings
LOCAL_URI = "mongodb://localhost:27017/"
ATLAS_URI = "mongodb+srv://blackholeinfiverse51:Blackhole051@cluster0.7c16heb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "ai_crm_logistics"

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "PROGRESS": "🔄"}
    print(f"[{timestamp}] {symbols.get(status, 'ℹ️')} {message}")

def migrate_data():
    """Migrate all data from local MongoDB to Atlas"""
    
    print_status("Starting MongoDB Migration to Atlas", "PROGRESS")
    print("=" * 80)
    
    try:
        # Connect to local MongoDB
        print_status("Connecting to Local MongoDB (localhost:27017)...", "PROGRESS")
        local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
        local_client.server_info()  # Test connection
        print_status("Connected to Local MongoDB", "SUCCESS")
        
        # Connect to Atlas
        print_status("Connecting to MongoDB Atlas...", "PROGRESS")
        atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
        atlas_client.server_info()  # Test connection
        print_status("Connected to MongoDB Atlas", "SUCCESS")
        
        # Get databases
        local_db = local_client[DATABASE_NAME]
        atlas_db = atlas_client[DATABASE_NAME]
        
        # Get list of collections
        collections = local_db.list_collection_names()
        
        if not collections:
            print_status(f"No collections found in local database '{DATABASE_NAME}'", "ERROR")
            return False
        
        print_status(f"Found {len(collections)} collections to migrate", "INFO")
        print()
        
        # Migrate each collection
        total_docs = 0
        for collection_name in collections:
            print_status(f"Migrating collection: {collection_name}", "PROGRESS")
            
            local_collection = local_db[collection_name]
            atlas_collection = atlas_db[collection_name]
            
            # Get all documents
            documents = list(local_collection.find())
            
            if documents:
                # Clear existing data in Atlas (optional - comment out if you want to keep existing)
                atlas_collection.delete_many({})
                
                # Insert documents
                atlas_collection.insert_many(documents)
                print_status(f"  ✓ Migrated {len(documents)} documents", "SUCCESS")
                total_docs += len(documents)
            else:
                print_status(f"  ⚠ Collection is empty, skipping", "INFO")
            
            print()
        
        print("=" * 80)
        print_status(f"Migration Complete! Total documents migrated: {total_docs}", "SUCCESS")
        print()
        
        # Verify migration
        print_status("Verifying migration...", "PROGRESS")
        atlas_collections = atlas_db.list_collection_names()
        print_status(f"Atlas now has {len(atlas_collections)} collections", "INFO")
        
        for col in atlas_collections:
            count = atlas_db[col].count_documents({})
            print(f"  • {col}: {count} documents")
        
        print()
        print_status("Migration completed successfully! 🎉", "SUCCESS")
        print_status("Your app is now using MongoDB Atlas", "INFO")
        print_status("Local MongoDB data has been copied to the cloud", "INFO")
        
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print_status(f"Connection timeout: {e}", "ERROR")
        print_status("Make sure both MongoDB local and Atlas are accessible", "ERROR")
        return False
    except Exception as e:
        print_status(f"Migration failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Close connections
        try:
            local_client.close()
            atlas_client.close()
        except:
            pass

if __name__ == "__main__":
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MongoDB Migration to Atlas" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    success = migrate_data()
    
    if success:
        print()
        print("🎯 Next Steps:")
        print("  1. Restart your backend server")
        print("  2. Open http://localhost:8000/health to verify connection")
        print("  3. Check MongoDB Atlas dashboard to see your data")
        print()
        sys.exit(0)
    else:
        print()
        print("❌ Migration failed. Please check the errors above.")
        print()
        sys.exit(1)
