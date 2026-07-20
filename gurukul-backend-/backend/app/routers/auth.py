
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # type: ignore[reportMissingModuleSource]
from sqlalchemy.orm import Session  # type: ignore[reportMissingImports]
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.config import settings
from app.models.all_models import User, Tenant, Profile, Summary, Flashcard, Reflection, StudentProgress
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse, UpdateProfile
from typing import Optional
import logging
from fastapi import BackgroundTasks
from app.services.vaani_manager import vaani_manager


logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Password hashing
# Using bcrypt directly to avoid passlib compatibility issues
import bcrypt  # type: ignore[reportMissingImports]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Encode password to bytes if it's a string
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        print(f"[Auth] Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    # Bcrypt has a 72-byte limit, so we need to handle long passwords
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password
    
    # Truncate to 72 bytes if necessary (bcrypt limit)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with session_id"""
    import uuid
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Generate session_id (JWT ID) for this token
    session_id = str(uuid.uuid4())
    to_encode.update({
        "exp": expire, 
        "iat": datetime.utcnow(),
        "jti": session_id,  # JWT ID claim (standard)
        "session_id": session_id  # Also include as session_id for easy access
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# For Supabase, we might verify using the JWT secret.
# Or if we just trust the frontend sent a valid token validated by Supabase client...
# Ideally we verify signature.
# For this "Yellow Mandate", let's implement a robust check if we had the key.
# If SUPABASE_KEY is missing, we might use a mock logic for dev (Warning: NOT PRODUCTION SAFE but enables progress)

async def _create_ems_student_account(user: User):
    """
    Helper function to auto-create EMS student account when student registers in Gurukul
    This is called asynchronously and failures are logged but don't block registration
    Uses a shorter timeout to prevent blocking the signup request
    """
    if not settings.EMS_ADMIN_EMAIL or not settings.EMS_ADMIN_PASSWORD:
        logger.warning("EMS admin credentials not configured. Skipping EMS student account creation.")
        return
    
    try:
        import asyncio
        from app.services.ems_client import ems_client
        
        # Use a shorter timeout (10 seconds) to prevent blocking signup too long
        # If EMS is slow or down, we'll fail fast and continue with registration
        async def _create_with_timeout():
            # Authenticate as admin with EMS
            admin_token_response = await ems_client.login(
                settings.EMS_ADMIN_EMAIL,
                settings.EMS_ADMIN_PASSWORD
            )
            admin_token = admin_token_response.get("access_token")
            
            if not admin_token:
                logger.warning("Failed to get EMS admin token. Skipping EMS student account creation.")
                return
            
            # Create student in EMS
            student_name = user.full_name or user.email.split("@")[0]
            await ems_client.create_student(
                admin_token=admin_token,
                name=student_name,
                email=user.email,
                grade="N/A"  # Default grade, can be updated later by admin
            )
            
            logger.info(f"Successfully created EMS student account for {user.email}")
        
        # Run with 10 second timeout - if EMS is slow, fail fast
        await asyncio.wait_for(_create_with_timeout(), timeout=10.0)
        
    except asyncio.TimeoutError:
        logger.warning(f"EMS account creation timed out for {user.email} - registration continues without EMS account")
    except Exception as e:
        # Log the error but don't fail registration
        logger.error(f"Failed to create EMS student account for {user.email}: {str(e)}")
        # Registration still succeeds even if EMS account creation fails


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Verify JWT token and return current user from SQLite database"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and verify JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        email: str = payload.get("sub")  # 'sub' is standard JWT claim for subject (user identifier)
        if email is None:
            raise credentials_exception

        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
            
        return user
        
    except JWTError:
        raise credentials_exception
    except Exception as e:
        print(f"[Auth] Error: {e}")
        raise credentials_exception

def require_role(role: str):
    def role_checker(user: User = Depends(get_current_user)):
        if user.role != role and user.role != "ADMIN": # Admin can do anything
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required Role: {role}"
            )
        return user
    return role_checker

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user. Support STUDENT, TEACHER, INSTITUTION_ADMIN, REGIONAL_ADMIN, and ADMIN roles."""
    if user_data.role.upper() not in {"STUDENT", "TEACHER", "INSTITUTION_ADMIN", "REGIONAL_ADMIN", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not permitted to register."
        )
    # Validate password length (bcrypt has 72-byte limit, but we'll enforce reasonable limits)
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    if len(user_data.password) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be less than 100 characters long"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Find or create default tenant
    default_tenant = db.query(Tenant).filter(Tenant.name == "Gurukul Main").first()
    if not default_tenant:
        default_tenant = Tenant(name="Gurukul Main", type="INSTITUTION")
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name or user_data.email.split("@")[0],
        role=user_data.role.upper(),
        tenant_id=default_tenant.id,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-create EMS student account if enabled and user is a student
    # Run in background task to not block the response
    if settings.EMS_AUTO_CREATE_STUDENTS and new_user.role.upper() == "STUDENT":
        import asyncio
        # Create background task - don't await it, let it run in background
        # This prevents EMS slowness from blocking the signup response
        asyncio.create_task(_create_ems_student_account(new_user))
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "assessment_completed": new_user.assessment_completed
        }
    }

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Login and get access token"""
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not user.hashed_password or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Allow login for all dashboard roles
    if user.role.upper() not in {"STUDENT", "TEACHER", "INSTITUTION_ADMIN", "REGIONAL_ADMIN", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not permitted to log in."
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Trigger background XTTS provisioning
    background_tasks.add_task(vaani_manager.trigger_download)

    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "assessment_completed": user.assessment_completed
        }
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/update-profile", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    try:
        # Update full_name if provided
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        
        db.commit()
        db.refresh(current_user)
        
        return current_user
    except Exception as e:
        db.rollback()
        print(f"[Auth] Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile. Please try again."
        )

@router.get("/profile-data")
async def get_profile_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's profile data JSON"""
    try:
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
        if not profile:
            return {"data": {}}
        return {"data": profile.data or {}}
    except Exception as e:
        logger.error(f"[Auth] Error retrieving profile data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile data."
        )

@router.put("/profile-data")
async def update_profile_data(
    profile_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's profile data JSON"""
    try:
        from sqlalchemy.orm.attributes import flag_modified
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
        if not profile:
            profile = Profile(user_id=current_user.id, data=profile_update)
            db.add(profile)
        else:
            profile.data = profile_update
            flag_modified(profile, "data")
        db.commit()
        db.refresh(profile)
        return {"success": True, "data": profile.data}
    except Exception as e:
        db.rollback()
        logger.error(f"[Auth] Error updating profile data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile data."
        )

@router.post("/complete-assessment", response_model=UserResponse)
async def complete_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark the assessment as completed for the current user"""
    try:
        current_user.assessment_completed = True
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        logger.error(f"[Auth] Error completing assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assessment status."
        )

@router.delete("/delete-account")
async def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete the current user's account and all associated data"""
    try:
        user_id = current_user.id
        
        # Delete all related records
        # 1. Delete Profile
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if profile:
            db.delete(profile)
        
        # 2. Delete Summaries
        summaries = db.query(Summary).filter(Summary.user_id == user_id).all()
        for summary in summaries:
            db.delete(summary)
        
        # 3. Delete Flashcards
        flashcards = db.query(Flashcard).filter(Flashcard.user_id == user_id).all()
        for flashcard in flashcards:
            db.delete(flashcard)
        
        # 4. Delete Reflections
        reflections = db.query(Reflection).filter(Reflection.user_id == user_id).all()
        for reflection in reflections:
            db.delete(reflection)
        
        # 5. Delete StudentProgress
        student_progress = db.query(StudentProgress).filter(StudentProgress.user_id == user_id).all()
        for progress in student_progress:
            db.delete(progress)
        
        # 6. Finally, delete the user
        db.delete(current_user)
        db.commit()
        
        return {
            "message": "Account and all associated data have been permanently deleted",
            "success": True
        }
    except Exception as e:
        db.rollback()
        print(f"[Auth] Error deleting account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please try again or contact support."
        )
