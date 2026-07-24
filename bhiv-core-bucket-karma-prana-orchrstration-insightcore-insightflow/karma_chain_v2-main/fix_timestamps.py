"""
Fix existing Karma users with timezone-naive timestamps
"""
from datetime import datetime, timezone
from database import users_col

def fix_user_timestamps():
    """Convert all naive timestamps to timezone-aware"""
    users = users_col.find({})
    fixed_count = 0
    
    for user in users:
        needs_update = False
        update_fields = {}
        
        # Fix cheat_history timestamps
        if "cheat_history" in user and user["cheat_history"]:
            fixed_history = []
            for ch in user["cheat_history"]:
                if "timestamp" in ch:
                    ts = ch["timestamp"]
                    if ts.tzinfo is None:
                        ch["timestamp"] = ts.replace(tzinfo=timezone.utc)
                        needs_update = True
                fixed_history.append(ch)
            if needs_update:
                update_fields["cheat_history"] = fixed_history
        
        # Fix last_decay
        if "last_decay" in user:
            ld = user["last_decay"]
            if isinstance(ld, datetime) and ld.tzinfo is None:
                update_fields["last_decay"] = ld.replace(tzinfo=timezone.utc)
                needs_update = True
        
        # Fix token_meta timestamps
        if "token_meta" in user:
            fixed_meta = {}
            for token, meta in user["token_meta"].items():
                if isinstance(meta, dict):
                    if "last_update" in meta and isinstance(meta["last_update"], datetime):
                        if meta["last_update"].tzinfo is None:
                            meta["last_update"] = meta["last_update"].replace(tzinfo=timezone.utc)
                            needs_update = True
                    if "created_at" in meta and isinstance(meta["created_at"], datetime):
                        if meta["created_at"].tzinfo is None:
                            meta["created_at"] = meta["created_at"].replace(tzinfo=timezone.utc)
                            needs_update = True
                fixed_meta[token] = meta
            if needs_update:
                update_fields["token_meta"] = fixed_meta
        
        if needs_update:
            users_col.update_one(
                {"user_id": user["user_id"]},
                {"$set": update_fields}
            )
            fixed_count += 1
            print(f"Fixed user: {user['user_id']}")
    
    print(f"\nTotal users fixed: {fixed_count}")
    return fixed_count

if __name__ == "__main__":
    print("Fixing timezone-naive timestamps in Karma database...")
    fix_user_timestamps()
    print("Done!")
