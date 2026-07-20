"""
MongoDB Schema Migration Script
Fixes issues found during verification:
1. Adds 'role' field to existing candidates (defaults to 'candidate')
2. Identifies candidates missing 'password_hash' (legacy data)
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

async def migrate_schema():
    """Migrate MongoDB schema to fix identified issues"""
    
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
        
        migrations_applied = []
        migrations_skipped = []
        migrations_failed = []
        
        # ===== MIGRATION 1: Add 'role' field to candidates =====
        print("="*60)
        print("[MIGRATION 1] Adding 'role' field to existing candidates...")
        print("="*60)
        
        try:
            # Count candidates without role field
            candidates_without_role = await db.candidates.count_documents({"role": {"$exists": False}})
            
            if candidates_without_role > 0:
                print(f"[INFO] Found {candidates_without_role} candidates without 'role' field")
                
                # Update all candidates without role to have role='candidate'
                result = await db.candidates.update_many(
                    {"role": {"$exists": False}},
                    {"$set": {"role": "candidate"}}
                )
                
                print(f"[OK] Updated {result.modified_count} candidates with role='candidate'")
                migrations_applied.append(f"Added 'role' field to {result.modified_count} candidates")
            else:
                print("[INFO] All candidates already have 'role' field")
                migrations_skipped.append("All candidates already have 'role' field")
        except Exception as e:
            error_msg = f"Failed to add 'role' field: {str(e)}"
            migrations_failed.append(error_msg)
            print(f"[ERROR] {error_msg}")
        
        # ===== MIGRATION 2: Identify candidates without password_hash =====
        print("\n" + "="*60)
        print("[MIGRATION 2] Identifying candidates without 'password_hash'...")
        print("="*60)
        
        try:
            # Count candidates without password_hash
            candidates_without_password = await db.candidates.count_documents({"password_hash": {"$exists": False}})
            
            if candidates_without_password > 0:
                print(f"[WARN] Found {candidates_without_password} candidates without 'password_hash' field")
                print("[INFO] These are likely legacy/test data and cannot login")
                print("[INFO] They will need to register again or reset password")
                
                # Get sample emails for reference
                sample_docs = await db.candidates.find(
                    {"password_hash": {"$exists": False}},
                    {"email": 1, "name": 1, "_id": 0}
                ).limit(5).to_list(length=5)
                
                if sample_docs:
                    print("\n[INFO] Sample candidates without passwords:")
                    for doc in sample_docs:
                        print(f"   - {doc.get('email', 'N/A')} ({doc.get('name', 'N/A')})")
                
                migrations_applied.append(f"Identified {candidates_without_password} candidates without passwords (legacy data)")
            else:
                print("[OK] All candidates have 'password_hash' field")
                migrations_skipped.append("All candidates have 'password_hash' field")
        except Exception as e:
            error_msg = f"Failed to check password_hash: {str(e)}"
            migrations_failed.append(error_msg)
            print(f"[ERROR] {error_msg}")
        
        # ===== MIGRATION 3: Verify clients have email field =====
        print("\n" + "="*60)
        print("[MIGRATION 3] Verifying clients have 'email' field...")
        print("="*60)
        
        try:
            # Count clients without email
            clients_without_email = await db.clients.count_documents({"email": {"$exists": False}})
            
            if clients_without_email > 0:
                print(f"[WARN] Found {clients_without_email} clients without 'email' field")
                print("[INFO] These clients cannot use email-based login")
                
                # Check if they have contact_email that can be migrated
                clients_with_contact_email = await db.clients.count_documents({
                    "email": {"$exists": False},
                    "contact_email": {"$exists": True}
                })
                
                if clients_with_contact_email > 0:
                    print(f"[INFO] Found {clients_with_contact_email} clients with 'contact_email' that can be migrated")
                    
                    # Migrate contact_email to email
                    result = await db.clients.update_many(
                        {"email": {"$exists": False}, "contact_email": {"$exists": True}},
                        [{"$set": {"email": "$contact_email"}}]
                    )
                    
                    print(f"[OK] Migrated 'contact_email' to 'email' for {result.modified_count} clients")
                    migrations_applied.append(f"Migrated email field for {result.modified_count} clients")
                else:
                    print("[WARN] No clients with 'contact_email' found for migration")
                    migrations_failed.append(f"{clients_without_email} clients missing email field")
            else:
                print("[OK] All clients have 'email' field")
                migrations_skipped.append("All clients have 'email' field")
        except Exception as e:
            error_msg = f"Failed to verify/migrate client email: {str(e)}"
            migrations_failed.append(error_msg)
            print(f"[ERROR] {error_msg}")
        
        # ===== SUMMARY =====
        print("\n" + "="*60)
        print("[SUMMARY] MIGRATION SUMMARY")
        print("="*60)
        
        if migrations_applied:
            print(f"\n[OK] Applied {len(migrations_applied)} migration(s):")
            for migration in migrations_applied:
                print(f"   - {migration}")
        
        if migrations_skipped:
            print(f"\n[INFO] Skipped {len(migrations_skipped)} migration(s) (not needed):")
            for migration in migrations_skipped:
                print(f"   - {migration}")
        
        if migrations_failed:
            print(f"\n[ERROR] Failed {len(migrations_failed)} migration(s):")
            for migration in migrations_failed:
                print(f"   - {migration}")
        
        if not migrations_failed:
            print("\n[SUCCESS] All migrations completed successfully!")
        else:
            print("\n[WARN] Some migrations failed. Please review errors above.")
        
        # ===== FINAL VERIFICATION =====
        print("\n" + "="*60)
        print("[VERIFY] Final Verification")
        print("="*60)
        
        # Check candidates with role
        candidates_with_role = await db.candidates.count_documents({"role": {"$exists": True}})
        total_candidates = await db.candidates.count_documents({})
        print(f"[INFO] Candidates with 'role' field: {candidates_with_role}/{total_candidates}")
        
        # Check candidates with password
        candidates_with_password = await db.candidates.count_documents({"password_hash": {"$exists": True}})
        print(f"[INFO] Candidates with 'password_hash' field: {candidates_with_password}/{total_candidates}")
        
        # Check clients with email
        clients_with_email = await db.clients.count_documents({"email": {"$exists": True}})
        total_clients = await db.clients.count_documents({})
        print(f"[INFO] Clients with 'email' field: {clients_with_email}/{total_clients}")
        
        client.close()
        return len(migrations_failed) == 0
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("MongoDB Schema Migration")
    print("="*60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    print("[WARN] This script will modify your database.")
    print("[INFO] Make sure you have a backup before proceeding.\n")
    
    success = asyncio.run(migrate_schema())
    
    sys.exit(0 if success else 1)

