import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from pathlib import Path

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class SecurityManager:
    """Handles authentication, authorization, and security measures"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify JWT token"""
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return username
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    @staticmethod
    def sanitize_path(file_path: str) -> Path:
        """Sanitize file path to prevent directory traversal"""
        # Remove any path traversal attempts
        clean_path = file_path.replace("../", "").replace("..\\", "")
        
        # Ensure path is within allowed directories
        base_dir = Path(__file__).parent.parent.parent
        allowed_dirs = ["data", "feedback", "logs", "uploads"]
        
        path = Path(clean_path)
        if not any(str(path).startswith(allowed_dir) for allowed_dir in allowed_dirs):
            raise ValueError(f"Access denied: Invalid path {file_path}")
        
        return base_dir / path
    
    @staticmethod
    def validate_input(data: str, max_length: int = 1000) -> str:
        """Validate and sanitize input data"""
        if not data:
            raise ValueError("Input cannot be empty")
        
        if len(data) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "&", "\"", "'", "/", "\\"]
        for char in dangerous_chars:
            data = data.replace(char, "")
        
        return data.strip()
    
    @staticmethod
    def rate_limit_check(identifier: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Simple rate limiting (in production, use Redis or similar)"""
        # This is a simplified implementation
        # In production, use proper rate limiting with Redis
        return True
    
    @staticmethod
    def audit_log(action: str, user: str, details: Dict[str, Any]):
        """Log security-relevant actions"""
        from app.utils.helpers import save_json, load_json
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": user,
            "details": details,
            "ip_address": "localhost"  # In production, get real IP
        }
        
        try:
            audit_logs = load_json("logs/audit.json", [])
            audit_logs.append(audit_entry)
            save_json("logs/audit.json", audit_logs)
        except Exception as e:
            print(f"Failed to write audit log: {e}")

# User management
class UserManager:
    """Handles user authentication and management"""
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        from app.utils.helpers import load_json
        
        users = load_json("data/users.json", [])
        user = next((u for u in users if u.get("username") == username), None)
        
        if user and SecurityManager.verify_password(password, user.get("password_hash", "")):
            return {
                "username": user["username"],
                "role": user.get("role", "user"),
                "permissions": user.get("permissions", [])
            }
        return None
    
    @staticmethod
    def create_user(username: str, password: str, role: str = "user", permissions: list = None) -> bool:
        """Create new user"""
        from app.utils.helpers import load_json, save_json
        
        if permissions is None:
            permissions = ["read"]
        
        users = load_json("data/users.json", [])
        
        # Check if user already exists
        if any(u.get("username") == username for u in users):
            return False
        
        new_user = {
            "id": len(users) + 1,
            "username": username,
            "password_hash": SecurityManager.hash_password(password),
            "role": role,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
        
        users.append(new_user)
        return save_json("data/users.json", users)

# CORS security
def get_cors_origins():
    """Get allowed CORS origins from environment"""
    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8501")
    return origins.split(",")

# Input validation decorators
def validate_json_input(max_size: int = 1024 * 1024):  # 1MB default
    """Decorator to validate JSON input size"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented with proper request size checking
            return func(*args, **kwargs)
        return wrapper
    return decorator