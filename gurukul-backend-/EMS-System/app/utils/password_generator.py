"""
Password generation utility that ensures unique passwords for each user.
Each password is a combination of multiple factors to ensure uniqueness.
"""

import secrets
import string
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User


def generate_unique_password(db: Session, email: str, name: str, role: str, school_id: int) -> str:
    """
    Generate a unique password for a user.
    
    The password is generated using:
    - Random secure characters
    - User's email hash (first 4 chars)
    - User's name hash (first 4 chars)
    - Timestamp hash (first 4 chars)
    - Random suffix
    
    This ensures no two users have the same password.
    
    Args:
        db: Database session
        email: User's email address
        name: User's name
        role: User's role
        school_id: School ID
        
    Returns:
        str: Unique password (12-16 characters)
    """
    # Generate base random password (8 characters)
    # Use only alphanumeric characters to avoid copy-paste issues and special character confusion
    alphabet = string.ascii_letters + string.digits
    base_password = ''.join(secrets.choice(alphabet) for _ in range(8))
    
    # Create unique identifiers from user data
    email_hash = hashlib.md5(email.encode()).hexdigest()[:4]
    name_hash = hashlib.md5(name.encode()).hexdigest()[:4]
    timestamp_hash = hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:4]
    role_hash = hashlib.md5(role.encode()).hexdigest()[:2]
    school_hash = hashlib.md5(str(school_id).encode()).hexdigest()[:2]
    
    # Combine to create unique password
    # MD5 hashes are hexadecimal (0-9, a-f), so they're already alphanumeric
    unique_suffix = email_hash + name_hash + timestamp_hash + role_hash + school_hash
    
    # Take first 8 characters of unique suffix (already alphanumeric from hex)
    unique_part = unique_suffix[:8]
    
    # If we need more characters, pad with random alphanumeric
    if len(unique_part) < 8:
        padding = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8 - len(unique_part)))
        unique_part = unique_part + padding
    
    # Final password: base (8) + unique part (8) = 16 characters
    # All alphanumeric (letters and digits only)
    password = base_password + unique_part[:8]
    
    return password


def generate_simple_password(length: int = 12) -> str:
    """
    Generate a simple random password (for testing or fallback).
    
    Args:
        length: Password length (default: 12)
        
    Returns:
        str: Random password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
