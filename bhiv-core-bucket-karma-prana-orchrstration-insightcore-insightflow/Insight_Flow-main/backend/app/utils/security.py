# app/utils/security.py
"""
Security utilities for InsightFlow project.

Provides functions for generating cryptographically secure secrets,
tokens, and keys for production deployment.
"""

import secrets
import string
import hashlib
import base64
from typing import Optional


def generate_jwt_secret(length: int = 64) -> str:
    """
    Generate cryptographically secure JWT secret.
    
    Args:
        length: Length of the secret (minimum 32)
    
    Returns:
        Base64-encoded secure random string
    """
    if length < 32:
        raise ValueError("JWT secret must be at least 32 characters long")
    
    # Generate random bytes and encode as base64
    random_bytes = secrets.token_bytes(length)
    return base64.b64encode(random_bytes).decode('utf-8')


def generate_service_key(prefix: str = "svc", length: int = 32) -> str:
    """
    Generate cryptographically secure service key.
    
    Args:
        prefix: Prefix for the key (e.g., "svc", "api")
        length: Length of the random part (minimum 16)
    
    Returns:
        Service key with format: {prefix}_{secure_random_string}
    """
    if length < 16:
        raise ValueError("Service key must be at least 16 characters long")
    
    # Generate secure random string with alphanumeric characters
    alphabet = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return f"{prefix}_{random_string}"


def generate_database_password(length: int = 24) -> str:
    """
    Generate cryptographically secure database password.
    
    Args:
        length: Length of the password (minimum 16)
    
    Returns:
        Secure random password with mixed characters
    """
    if length < 16:
        raise ValueError("Database password must be at least 16 characters long")
    
    # Use alphanumeric + safe special characters
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return password


def generate_api_key(length: int = 40) -> str:
    """
    Generate cryptographically secure API key.
    
    Args:
        length: Length of the key (minimum 20)
    
    Returns:
        Hex-encoded secure random string
    """
    if length < 20:
        raise ValueError("API key must be at least 20 characters long")
    
    # Generate random bytes and convert to hex
    random_bytes = secrets.token_bytes(length // 2)
    return random_bytes.hex()


def validate_secret_strength(secret: str, min_length: int = 16) -> tuple[bool, list[str]]:
    """
    Validate the strength of a secret/password.
    
    Args:
        secret: Secret to validate
        min_length: Minimum required length
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check length
    if len(secret) < min_length:
        issues.append(f"Secret is too short (minimum {min_length} characters)")
    
    # Check for placeholder patterns
    placeholder_patterns = ['placeholder', 'change-me', 'your-secret', 'default', 'example']
    if any(pattern in secret.lower() for pattern in placeholder_patterns):
        issues.append("Secret contains placeholder text")
    
    # Check for common weak patterns
    weak_patterns = ['password', '123456', 'admin', 'secret']
    if any(pattern in secret.lower() for pattern in weak_patterns):
        issues.append("Secret contains common weak patterns")
    
    # Check character diversity (for longer secrets)
    if len(secret) >= 16:
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        
        if not (has_upper and has_lower and has_digit):
            issues.append("Secret should contain uppercase, lowercase, and numeric characters")
    
    return len(issues) == 0, issues


def hash_secret(secret: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a secret with salt for secure storage.
    
    Args:
        secret: Secret to hash
        salt: Optional salt (generated if not provided)
    
    Returns:
        Tuple of (hashed_secret, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 with SHA-256
    hashed = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt.encode(), 100000)
    return base64.b64encode(hashed).decode('utf-8'), salt


def verify_secret(secret: str, hashed_secret: str, salt: str) -> bool:
    """
    Verify a secret against its hash.
    
    Args:
        secret: Plain secret to verify
        hashed_secret: Base64-encoded hashed secret
        salt: Salt used for hashing
    
    Returns:
        True if secret matches, False otherwise
    """
    try:
        expected_hash, _ = hash_secret(secret, salt)
        return secrets.compare_digest(expected_hash, hashed_secret)
    except Exception:
        return False


def generate_production_secrets() -> dict:
    """
    Generate a complete set of production secrets.
    
    Returns:
        Dictionary with all required secrets for production deployment
    """
    return {
        'JWT_SECRET_KEY': generate_jwt_secret(64),
        'SOVEREIGN_SERVICE_KEY': generate_service_key('sovereign', 32),
        'SOVEREIGN_JWT_SECRET': generate_jwt_secret(64),
        'SOVEREIGN_DB_PASSWORD': generate_database_password(24),
        'API_KEY': generate_api_key(40)
    }


if __name__ == "__main__":
    # CLI tool for generating secrets
    import sys
    
    if len(sys.argv) > 1:
        secret_type = sys.argv[1].lower()
        
        if secret_type == 'jwt':
            print(generate_jwt_secret())
        elif secret_type == 'service':
            print(generate_service_key())
        elif secret_type == 'password':
            print(generate_database_password())
        elif secret_type == 'api':
            print(generate_api_key())
        elif secret_type == 'all':
            secrets_dict = generate_production_secrets()
            for key, value in secrets_dict.items():
                print(f"{key}={value}")
        else:
            print("Usage: python security.py [jwt|service|password|api|all]")
    else:
        # Generate all secrets by default
        secrets_dict = generate_production_secrets()
        print("# Production Secrets - Add these to your .env file")
        for key, value in secrets_dict.items():
            print(f"{key}={value}")