"""
Test helper endpoints for Karma integration testing
"""
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from database import users_col
from utils.utils_user import create_user_if_missing

router = APIRouter()

class TestUserRequest(BaseModel):
    user_id: str
    role: str = "learner"

@router.post("/test/create-user")
def create_test_user(request: TestUserRequest):
    """Create a test user with proper timezone handling"""
    user = create_user_if_missing(request.user_id, request.role)
    return {
        "success": True,
        "user_id": user["user_id"],
        "role": user["role"],
        "message": "Test user created successfully"
    }

@router.delete("/test/delete-user/{user_id}")
def delete_test_user(user_id: str):
    """Delete a test user"""
    result = users_col.delete_one({"user_id": user_id})
    return {
        "success": result.deleted_count > 0,
        "deleted_count": result.deleted_count
    }

@router.post("/test/fix-timestamps")
def fix_all_timestamps():
    """Fix all naive timestamps in database"""
    users = list(users_col.find({}))
    fixed_count = 0
    
    for user in users:
        needs_update = False
        update_fields = {}
        
        # Fix cheat_history
        if "cheat_history" in user and user["cheat_history"]:
            fixed_history = []
            for ch in user["cheat_history"]:
                if "timestamp" in ch and isinstance(ch["timestamp"], datetime):
                    if ch["timestamp"].tzinfo is None:
                        ch["timestamp"] = ch["timestamp"].replace(tzinfo=timezone.utc)
                        needs_update = True
                fixed_history.append(ch)
            if needs_update:
                update_fields["cheat_history"] = fixed_history
        
        # Fix last_decay
        if "last_decay" in user and isinstance(user["last_decay"], datetime):
            if user["last_decay"].tzinfo is None:
                update_fields["last_decay"] = user["last_decay"].replace(tzinfo=timezone.utc)
                needs_update = True
        
        if needs_update:
            users_col.update_one(
                {"user_id": user["user_id"]},
                {"$set": update_fields}
            )
            fixed_count += 1
    
    return {
        "success": True,
        "fixed_count": fixed_count,
        "message": f"Fixed {fixed_count} users"
    }
