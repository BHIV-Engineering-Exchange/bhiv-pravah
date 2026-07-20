from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import asyncio
from app.database import get_db
from app.dependencies import get_current_super_admin
from app.auth import super_admin_exists, create_super_admin
from app.schemas import SuperAdminSetupResponse, InviteAdminRequest, InviteAdminResponse
from app.models import User, UserRole, School
from app.email_service import generate_password_token, send_password_setup_email
from app.config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

router = APIRouter(prefix="/super", tags=["super-admin"])


@router.post("/setup", response_model=SuperAdminSetupResponse)
def setup_super_admin(db: Session = Depends(get_db)):
    """
    One-time setup endpoint to create the initial SUPER_ADMIN account.
    This endpoint can only be used once. After the first successful call,
    it will return a message indicating that super admin already exists.
    
    IMPORTANT: This endpoint should be protected or removed in production
    after initial setup. Consider using environment variables or removing
    this endpoint entirely and using the setup script instead.
    """
    # Check if super admin already exists
    if super_admin_exists(db):
        return SuperAdminSetupResponse(
            success=False,
            message="Super Admin already exists. Setup is disabled.",
            already_exists=True
        )
    
    # Create super admin with predefined credentials
    try:
        create_super_admin(
            db=db,
            name="Super Admin",
            email="blackholeinfiverse48@gmail.com",
            password="superadmin123"
        )
        return SuperAdminSetupResponse(
            success=True,
            message="Super Admin created successfully.",
            already_exists=False
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating super admin: {str(e)}"
        )


@router.post("/invite-admin", response_model=InviteAdminResponse, status_code=status.HTTP_201_CREATED)
async def invite_admin(
    invite_data: InviteAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Invite a new admin by email.
    Only SUPER_ADMIN can invite admins.
    
    This endpoint:
    1. Creates an ADMIN user with password = NULL
    2. Generates a secure, time-limited token
    3. Sends an email with password setup link
    4. Returns admin details
    """
    # Verify school exists
    school = db.query(School).filter(School.id == invite_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {invite_data.school_id} not found"
        )
    
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create admin user with NULL password
    admin_user = User(
        name=invite_data.name,
        email=invite_data.email,
        password=None,  # Password will be set by user via email link
        role=UserRole.ADMIN,
        school_id=invite_data.school_id,
        is_active=True
    )
    
    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Generate password setup token
        password_token = generate_password_token(db, admin_user.id)
        
        # Send password setup email
        email_sent = await send_password_setup_email(db, admin_user, password_token)
        
        if not email_sent:
            # Email failed, but user was created
            # Log the error for debugging
            print(f"[ADMIN INVITE ERROR] Failed to send invitation email to {admin_user.email}")
            print(f"[ADMIN INVITE ERROR] Admin user was created (ID: {admin_user.id}), but email could not be sent")
            print(f"[ADMIN INVITE ERROR] Check SMTP configuration and verify sender email is authorized in email service")
            
            return InviteAdminResponse(
                success=False,
                message=f"Admin account created, but failed to send invitation email to {admin_user.email}. Please check email configuration and verify the sender email is authorized in your email service (Brevo/SendGrid/etc).",
                admin_id=admin_user.id,
                email=admin_user.email
            )
        
        return InviteAdminResponse(
            success=True,
            message=f"Admin invitation sent successfully to {admin_user.email}. Please check your email to set your password.",
            admin_id=admin_user.id,
            email=admin_user.email
        )
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create admin user. Email might already be in use."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating admin: {str(e)}"
        )


@router.get("/test-email-config")
async def test_email_config(current_user: User = Depends(get_current_super_admin)):
    """
    Test email configuration and show current settings.
    This helps diagnose email sending issues.
    Only SUPER_ADMIN can access this endpoint.
    """
    try:
        # Check configuration
        config_status = {
            "MAIL_USERNAME": settings.MAIL_USERNAME if settings.MAIL_USERNAME else "❌ NOT SET",
            "MAIL_PASSWORD": "✅ SET" if settings.MAIL_PASSWORD else "❌ NOT SET",
            "MAIL_FROM": settings.MAIL_FROM,
            "MAIL_SERVER": settings.MAIL_SERVER,
            "MAIL_PORT": settings.MAIL_PORT,
            "MAIL_STARTTLS": settings.MAIL_STARTTLS,
            "MAIL_SSL_TLS": settings.MAIL_SSL_TLS,
            "USE_CREDENTIALS": settings.USE_CREDENTIALS,
            "FRONTEND_URL": settings.FRONTEND_URL,
        }
        
        # Try to create email connection config
        # Auto-fix: If MAIL_FROM doesn't match MAIL_USERNAME, use MAIL_USERNAME (required for Gmail)
        mail_from = settings.MAIL_FROM
        if settings.MAIL_USERNAME and settings.MAIL_FROM != settings.MAIL_USERNAME:
            mail_from = settings.MAIL_USERNAME
        
        try:
            conf = ConnectionConfig(
                MAIL_USERNAME=settings.MAIL_USERNAME,
                MAIL_PASSWORD=settings.MAIL_PASSWORD,
                MAIL_FROM=mail_from,
                MAIL_PORT=settings.MAIL_PORT,
                MAIL_SERVER=settings.MAIL_SERVER,
                MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=settings.USE_CREDENTIALS,
                VALIDATE_CERTS=settings.VALIDATE_CERTS,
                TEMPLATE_FOLDER=None,
            )
            config_valid = True
            config_error = None
        except Exception as e:
            config_valid = False
            config_error = str(e)
        
        # Try to send a test email
        test_email_sent = False
        test_email_error = None
        if config_valid and settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            try:
                test_message = MessageSchema(
                    subject="Test Email - School Management System",
                    recipients=[settings.MAIL_USERNAME],  # Send to yourself
                    body="This is a test email to verify SMTP configuration.",
                    subtype=MessageType.plain,
                )
                fm = FastMail(conf)
                await asyncio.wait_for(fm.send_message(test_message), timeout=30.0)
                test_email_sent = True
            except asyncio.TimeoutError:
                test_email_error = {
                    "error_type": "TimeoutError",
                    "error_message": f"SMTP connection to {settings.MAIL_SERVER} timed out after 30 seconds. This usually means the SMTP server is unreachable or blocking the connection.",
                    "full_error": "TimeoutError: SMTP connection timeout",
                    "recommendation": "Gmail SMTP often blocks connections from cloud providers like Render. Consider using SendGrid, Mailgun, or AWS SES instead."
                }
            except Exception as e:
                test_email_error = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "full_error": repr(e)
                }
        
        return {
            "status": "ok",
            "configuration": config_status,
            "config_valid": config_valid,
            "config_error": config_error,
            "test_email_sent": test_email_sent,
            "test_email_error": test_email_error,
            "recommendations": []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
