"""
MongoDB Index Creation Script
Creates recommended indexes for optimal query performance.
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[INFO] Loaded environment variables from: {env_path}")
    else:
        # Try loading from backend/.env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"[INFO] Loaded environment variables from: {env_path}")
except ImportError:
    print("[WARN] python-dotenv not installed, using system environment variables only")
except Exception as e:
    print(f"[WARN] Could not load .env file: {e}")

async def create_indexes():
    """Create recommended indexes for MongoDB collections"""
    
    # Get MongoDB connection
    mongodb_uri = os.getenv("DATABASE_URL") or os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("[ERROR] DATABASE_URL or MONGODB_URI environment variable is required")
        return False
    
    db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")
    
    try:
        client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        await client.admin.command('ping')
        print(f"[OK] Connected to MongoDB database: {db_name}\n")
        
        db = client[db_name]
        
        indexes_created = []
        indexes_existing = []
        indexes_failed = []
        
        # ===== CANDIDATES COLLECTION INDEXES =====
        print("="*60)
        print("[INFO] Creating indexes for 'candidates' collection...")
        print("="*60)
        
        if "candidates" in await db.list_collection_names():
            # Email index (unique, for login lookups)
            try:
                result = await db.candidates.create_index("email", unique=True, name="email_unique")
                indexes_created.append("candidates.email (unique)")
                print("[OK] Created unique index on 'email' field")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    indexes_existing.append("candidates.email")
                    print("[INFO] Index on 'email' field already exists")
                else:
                    indexes_failed.append(f"candidates.email: {str(e)}")
                    print(f"[ERROR] Failed to create index on 'email': {str(e)}")
            
            # Role index (for filtering by role)
            try:
                result = await db.candidates.create_index("role", name="role_index")
                indexes_created.append("candidates.role")
                print("[OK] Created index on 'role' field")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    indexes_existing.append("candidates.role")
                    print("[INFO] Index on 'role' field already exists")
                else:
                    indexes_failed.append(f"candidates.role: {str(e)}")
                    print(f"[ERROR] Failed to create index on 'role': {str(e)}")
            
            # Created_at index (for sorting)
            try:
                result = await db.candidates.create_index("created_at", name="created_at_index")
                indexes_created.append("candidates.created_at")
                print("[OK] Created index on 'created_at' field")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    indexes_existing.append("candidates.created_at")
                    print("[INFO] Index on 'created_at' field already exists")
                else:
                    indexes_failed.append(f"candidates.created_at: {str(e)}")
                    print(f"[ERROR] Failed to create index on 'created_at': {str(e)}")
        else:
                print("[WARN] 'candidates' collection does not exist (will be created on first insert)")
        
        # ===== CLIENTS COLLECTION INDEXES =====
        print("\n" + "="*60)
        print("[INFO] Creating indexes for 'clients' collection...")
        print("="*60)
        
        if "clients" in await db.list_collection_names():
            # Email index (unique, for email-based login)
            try:
                result = await db.clients.create_index("email", unique=True, name="email_unique")
                indexes_created.append("clients.email (unique)")
                print("[OK] Created unique index on 'email' field")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    indexes_existing.append("clients.email")
                    print("[INFO] Index on 'email' field already exists")
                else:
                    indexes_failed.append(f"clients.email: {str(e)}")
                    print(f"[ERROR] Failed to create index on 'email': {str(e)}")
            
            # Client_id index (unique, for client_id-based login)
            try:
                result = await db.clients.create_index("client_id", unique=True, name="client_id_unique")
                indexes_created.append("clients.client_id (unique)")
                print("[OK] Created unique index on 'client_id' field")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    indexes_existing.append("clients.client_id")
                    print("[INFO] Index on 'client_id' field already exists")
                else:
                    indexes_failed.append(f"clients.client_id: {str(e)}")
                    print(f"[ERROR] Failed to create index on 'client_id': {str(e)}")
            
            # Status index (for filtering active clients)
            try:
                result = await db.clients.create_index("status", name="status_index")
                indexes_created.append("clients.status")
                print("[OK] Created index on 'status' field")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    indexes_existing.append("clients.status")
                    print("[INFO] Index on 'status' field already exists")
                else:
                    indexes_failed.append(f"clients.status: {str(e)}")
                    print(f"[ERROR] Failed to create index on 'status': {str(e)}")
        else:
            print("[WARN] 'clients' collection does not exist (will be created on first insert)")
        
        # ===== SUMMARY =====
        print("\n" + "="*60)
        print("[SUMMARY] INDEX CREATION SUMMARY")
        print("="*60)
        
        if indexes_created:
            print(f"\n[OK] Created {len(indexes_created)} new index(es):")
            for idx in indexes_created:
                print(f"   - {idx}")
        
        if indexes_existing:
            print(f"\n[INFO] {len(indexes_existing)} index(es) already exist:")
            for idx in indexes_existing:
                print(f"   - {idx}")
        
        if indexes_failed:
            print(f"\n[ERROR] Failed to create {len(indexes_failed)} index(es):")
            for idx in indexes_failed:
                print(f"   - {idx}")
        
        if not indexes_failed:
            print("\n[SUCCESS] All indexes created successfully!")
        
        client.close()
        return len(indexes_failed) == 0
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("MongoDB Index Creation")
    print("="*60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    success = asyncio.run(create_indexes())
    
    sys.exit(0 if success else 1)

