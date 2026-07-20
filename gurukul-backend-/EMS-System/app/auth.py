from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User, UserRole


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Checks:
    - User exists
    - User has a password set (password is not None)
    - User is active (is_active is True)
    - Password matches
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"[AUTH] User not found: {email}")
        return None
    
    # Check if user is active
    if not user.is_active:
        print(f"[AUTH] User is inactive: {email}")
        return None
    
    # Check if password is set
    if user.password is None:
        print(f"[AUTH] User has no password set: {email}")
        return None
    
    # Verify password
    password_match = verify_password(password, user.password)
    if not password_match:
        print(f"[AUTH] Password mismatch for: {email}")
        print(f"[AUTH] Password length provided: {len(password)}")
        print(f"[AUTH] Stored hash length: {len(user.password) if user.password else 0}")
        return None
    
    print(f"[AUTH] Successful login for: {email} (Role: {user.role.value})")
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def create_super_admin(db: Session, name: str, email: str, password: str) -> User:
    """Create a super admin user. Should only be called once."""
    hashed_password = get_password_hash(password)
    user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=UserRole.SUPER_ADMIN,
        school_id=None,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def super_admin_exists(db: Session) -> bool:
    """Check if a super admin already exists."""
    return db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first() is not None
