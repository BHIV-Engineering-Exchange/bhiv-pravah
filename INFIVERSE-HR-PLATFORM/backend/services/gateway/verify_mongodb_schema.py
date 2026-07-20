"""
MongoDB Schema Verification Script
Verifies that all required collections and fields exist for authentication and role management.
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

async def verify_mongodb_schema():
    """Verify MongoDB collections and required fields"""
    
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
        print(f"[OK] Connected to MongoDB database: {db_name}")
        
        db = client[db_name]
        
        # Check collections exist
        collections = await db.list_collection_names()
        print(f"\n[INFO] Found {len(collections)} collections: {', '.join(sorted(collections))}")
        
        issues = []
        warnings = []
        
        # ===== CANDIDATES COLLECTION =====
        print("\n" + "="*60)
        print("[CHECK] Checking 'candidates' collection...")
        print("="*60)
        
        if "candidates" not in collections:
            issues.append("[ERROR] 'candidates' collection does not exist")
            print("[ERROR] 'candidates' collection does not exist")
        else:
            print("[OK] 'candidates' collection exists")
            
            # Check required fields by sampling documents
            sample_docs = await db.candidates.find({}).limit(5).to_list(length=5)
            total_candidates = await db.candidates.count_documents({})
            print(f"[INFO] Total candidates: {total_candidates}")
            
            if total_candidates > 0:
                # Check fields in sample documents
                required_fields = ["email", "password_hash", "name"]
                optional_fields = ["role", "phone", "location", "status", "created_at"]
                
                sample_fields = set()
                for doc in sample_docs:
                    sample_fields.update(doc.keys())
                
                print(f"\n📝 Fields found in sample documents: {', '.join(sorted(sample_fields))}")
                
                # Check required fields
                missing_required = []
                for field in required_fields:
                    if field not in sample_fields:
                        missing_required.append(field)
                
                if missing_required:
                    issues.append(f"❌ Missing required fields in candidates: {', '.join(missing_required)}")
                    print(f"❌ Missing required fields: {', '.join(missing_required)}")
                else:
                    print(f"✅ All required fields present: {', '.join(required_fields)}")
                
                # Check role field
                if "role" not in sample_fields:
                    warnings.append("⚠️ 'role' field not found in candidates collection (needed for recruiter support)")
                    print("[WARN] 'role' field not found - existing documents may need migration")
                else:
                    # Check role values
                    role_counts = {}
                    async for doc in db.candidates.find({"role": {"$exists": True}}):
                        role = doc.get("role", "candidate")
                        role_counts[role] = role_counts.get(role, 0) + 1
                    
                    print(f"[OK] 'role' field exists")
                    if role_counts:
                        print(f"   Role distribution: {role_counts}")
                    
                    # Check for documents without role field
                    no_role_count = await db.candidates.count_documents({"role": {"$exists": False}})
                    if no_role_count > 0:
                        warnings.append(f"[WARN] {no_role_count} candidate documents missing 'role' field (will default to 'candidate')")
                        print(f"[WARN] {no_role_count} documents missing 'role' field")
                
                # Check email index
                indexes = await db.candidates.index_information()
                has_email_index = False
                for idx_name, idx_info in indexes.items():
                    if idx_name == "_id_":
                        continue
                    keys = idx_info.get("key", [])
                    if isinstance(keys, list):
                        for key_item in keys:
                            if isinstance(key_item, (list, tuple)) and len(key_item) > 0:
                                if key_item[0] == "email":
                                    has_email_index = True
                                    break
                    if has_email_index:
                        break
                if not has_email_index:
                    warnings.append("[WARN] No index on 'email' field in candidates collection (recommended for performance)")
                    print("[WARN] No index on 'email' field (recommended)")
                else:
                    print("✅ Index on 'email' field exists")
            else:
                print("[INFO] No candidates found (collection is empty)")
        
        # ===== CLIENTS COLLECTION =====
        print("\n" + "="*60)
        print("[CHECK] Checking 'clients' collection...")
        print("="*60)
        
        if "clients" not in collections:
            issues.append("[ERROR] 'clients' collection does not exist")
            print("[ERROR] 'clients' collection does not exist")
        else:
            print("[OK] 'clients' collection exists")
            
            # Check required fields by sampling documents
            sample_docs = await db.clients.find({}).limit(5).to_list(length=5)
            total_clients = await db.clients.count_documents({})
            print(f"[INFO] Total clients: {total_clients}")
            
            if total_clients > 0:
                # Check fields in sample documents
                required_fields = ["client_id", "email", "password_hash", "company_name"]
                optional_fields = ["client_code", "status", "failed_login_attempts", "locked_until", "created_at"]
                
                sample_fields = set()
                for doc in sample_docs:
                    sample_fields.update(doc.keys())
                
                print(f"\n[INFO] Fields found in sample documents: {', '.join(sorted(sample_fields))}")
                
                # Check required fields
                missing_required = []
                for field in required_fields:
                    if field not in sample_fields:
                        missing_required.append(field)
                
                if missing_required:
                    issues.append(f"[ERROR] Missing required fields in clients: {', '.join(missing_required)}")
                    print(f"[ERROR] Missing required fields: {', '.join(missing_required)}")
                else:
                    print(f"[OK] All required fields present: {', '.join(required_fields)}")
                
                # Check email field (critical for email-based login)
                if "email" not in sample_fields:
                    issues.append("[ERROR] 'email' field missing in clients collection (required for email-based login)")
                    print("[ERROR] 'email' field missing (required for email-based login)")
                else:
                    print("[OK] 'email' field exists (required for email-based login)")
                
                # Check email and client_id indexes
                indexes = await db.clients.index_information()
                has_email_index = False
                has_client_id_index = False
                for idx_name, idx_info in indexes.items():
                    if idx_name == "_id_":
                        continue
                    keys = idx_info.get("key", [])
                    if isinstance(keys, list):
                        for key_item in keys:
                            if isinstance(key_item, (list, tuple)) and len(key_item) > 0:
                                field_name = key_item[0]
                                if field_name == "email":
                                    has_email_index = True
                                elif field_name == "client_id":
                                    has_client_id_index = True
                    # Also check index name (some indexes are named after the field)
                    if "email" in idx_name.lower():
                        has_email_index = True
                    if "client_id" in idx_name.lower() or "clientid" in idx_name.lower():
                        has_client_id_index = True
                
                if not has_email_index:
                    warnings.append("⚠️ No index on 'email' field in clients collection (recommended for performance)")
                    print("⚠️ No index on 'email' field (recommended)")
                else:
                    print("[OK] Index on 'email' field exists")
                
                if not has_client_id_index:
                    warnings.append("[WARN] No index on 'client_id' field in clients collection (recommended for performance)")
                    print("[WARN] No index on 'client_id' field (recommended)")
                else:
                    print("[OK] Index on 'client_id' field exists")
            else:
                print("[INFO] No clients found (collection is empty)")
        
        # ===== SUMMARY =====
        print("\n" + "="*60)
        print("[SUMMARY] VERIFICATION SUMMARY")
        print("="*60)
        
        if issues:
            print("\n[ERROR] ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
            print("\n[WARN] These issues must be fixed for the application to work correctly.")
        else:
            print("\n[OK] No critical issues found!")
        
        if warnings:
            print("\n[WARN] WARNINGS:")
            for warning in warnings:
                print(f"   {warning}")
            print("\n[INFO] These warnings are recommendations for optimal performance.")
        
        if not issues and not warnings:
            print("\n[SUCCESS] All checks passed! MongoDB schema is ready.")
        
        # ===== RECOMMENDATIONS =====
        print("\n" + "="*60)
        print("[INFO] RECOMMENDATIONS")
        print("="*60)
        print("1. Create indexes for better query performance:")
        print("   - db.candidates.createIndex({ email: 1 }, { unique: true })")
        print("   - db.clients.createIndex({ email: 1 }, { unique: true })")
        print("   - db.clients.createIndex({ client_id: 1 }, { unique: true })")
        print("\n2. If existing candidates are missing 'role' field:")
        print("   - They will default to 'candidate' role")
        print("   - To set recruiter role: db.candidates.updateMany({ role: { $exists: false } }, { $set: { role: 'candidate' } })")
        print("\n3. Verify email-based login works for clients")
        print("   - Test with: POST /v1/client/login with { email, password }")
        
        client.close()
        return len(issues) == 0
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("MongoDB Schema Verification")
    print("="*60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    success = asyncio.run(verify_mongodb_schema())
    
    sys.exit(0 if success else 1)

