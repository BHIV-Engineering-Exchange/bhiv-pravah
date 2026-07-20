from datetime import timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session  # type: ignore[reportMissingImports]
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_password_hash
from app.config import settings
from app.schemas import (
    LoginRequest, Token, SetPasswordRequest, SetPasswordResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ChangePasswordRequest, ChangePasswordResponse
)
from app.models import User, UserRole
from app.email_service import (
    validate_password_token, mark_token_as_used,
    generate_password_token, send_password_reset_email
)
from app.dependencies import get_current_user
from app.auth import verify_password
from app.schemas import UserResponse

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    Supports OAuth2 form data (username/password).
    Token contains: user_id, role, school_id
    
    Note: In Swagger UI, 'username' field should contain the email address.
    For JSON requests, use /v1/auth/login-json instead.
    """
    # OAuth2PasswordRequestForm uses 'username' field, but we use email
    # So we treat 'username' as email
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate session_id for this login session
    session_id = str(uuid4())
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),  # JWT standard requires sub to be string
            "role": user.role.value,
            "school_id": user.school_id,
            "jti": session_id,  # JWT ID claim (standard)
            "session_id": session_id  # Custom claim for easy access
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-json", response_model=Token)
def login_json(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Alternative login endpoint using JSON body (email/password).
    Use this for programmatic API access or frontend integrations.
    """
    # First check if user exists
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check specific issues for better error messages
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Please contact administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.password is None:
        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password not set. Please check your email for password setup link.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password not set. Please contact administrator.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Now authenticate
    # Log authentication attempt (without password)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Login attempt for email: {credentials.email}")
    
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        # Provide more detailed error information
        db_user = db.query(User).filter(User.email == credentials.email).first()
        if not db_user:
            logger.warning(f"Login failed: User with email {credentials.email} not found")
        elif not db_user.is_active:
            logger.warning(f"Login failed: User {credentials.email} is inactive")
        elif db_user.password is None:
            logger.warning(f"Login failed: User {credentials.email} has no password set")
        else:
            logger.warning(f"Login failed: Password mismatch for {credentials.email}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate session_id for this login session
    session_id = str(uuid4())
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "school_id": user.school_id,
            "jti": session_id,  # JWT ID claim (standard)
            "session_id": session_id  # Custom claim for easy access
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/set-password", response_model=SetPasswordResponse)
def set_password(
    request: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Set password for a user using a password setup token.
    This endpoint is used when a user receives an invitation email
    and needs to set their password for the first time.
    """
    # Validate token
    password_token = validate_password_token(db, request.token)
    
    # Get user
    user = db.query(User).filter(User.id == password_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate password (basic validation - you can add more rules)
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash and set password
    hashed_password = get_password_hash(request.password)
    user.password = hashed_password
    
    # Mark token as used
    mark_token_as_used(db, password_token)
    
    # Commit changes
    db.commit()
    
    return SetPasswordResponse(
        success=True,
        message="Password set successfully. You can now log in."
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset. Sends an email with a reset link.
    Works for all user roles (TEACHER, STUDENT, PARENT, ADMIN).
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success message (security: don't reveal if email exists)
    if not user:
        return ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    
    # Check if user is active
    if not user.is_active:
        return ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    
    # Generate password reset token
    password_token = generate_password_token(db, user.id)
    
    # Send password reset email
    email_sent = await send_password_reset_email(db, user, password_token)
    
    if email_sent:
        return ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    else:
        return ForgotPasswordResponse(
            success=False,
            message="Failed to send password reset email. Please try again later."
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a password reset token.
    Requires both old password and new password for security.
    This endpoint is used when a user clicks the reset link from their email.
    """
    # Validate token
    password_token = validate_password_token(db, request.token)
    
    # Get user
    user = db.query(User).filter(User.id == password_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password matches current password
    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no password set. Please use set-password endpoint instead."
        )
    
    if not verify_password(request.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old password is incorrect"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Check that new password is different from old password
    if verify_password(request.new_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from your current password"
        )
    
    # Hash and set new password
    hashed_password = get_password_hash(request.new_password)
    user.password = hashed_password
    
    # Mark token as used
    mark_token_as_used(db, password_token)
    
    # Commit changes
    db.commit()
    
    return ResetPasswordResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password."
    )


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change password for logged-in users.
    Requires the current password to be provided.
    """
    # Verify current password
    if not current_user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password set. Please use password reset instead."
        )
    
    if not verify_password(request.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )
    
    # Check if new password is different from current
    if verify_password(request.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Hash and set new password
    hashed_password = get_password_hash(request.new_password)
    current_user.password = hashed_password
    
    # Commit changes
    db.commit()
    
    return ChangePasswordResponse(
        success=True,
        message="Password changed successfully."
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        school_id=current_user.school_id
    )


from app.schemas import UserCreate
from app.models import School

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Public registration endpoint. Allows creating users of any role.
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    school_id = user_data.school_id
    
    # If not SUPER_ADMIN, require a school_id or auto-assign to the first school
    if user_data.role != UserRole.SUPER_ADMIN:
        if not school_id:
            # Check if any school exists
            school = db.query(School).first()
            if not school:
                # Create a default school
                school = School(
                    name="Gurukul Demo Academy",
                    address="123 Demo Street, Blackhole Infiverse",
                    phone="555-DEMO",
                    email="demo@gurukul.com"
                )
                db.add(school)
                db.commit()
                db.refresh(school)
            school_id = school.id
        else:
            # Verify school exists
            school = db.query(School).filter(School.id == school_id).first()
            if not school:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"School with ID {school_id} does not exist"
                )
    else:
        # SUPER_ADMIN does not belong to a school
        school_id = None

    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        role=user_data.role,
        password=hashed_password,
        school_id=school_id,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

