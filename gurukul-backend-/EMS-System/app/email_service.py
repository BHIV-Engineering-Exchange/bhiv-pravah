"""
Email service for sending password setup emails.
Supports Brevo API, SendGrid API (for Render), and SMTP (for local development).
"""
import secrets
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi import HTTPException, status
from app.config import settings
from app.models import User, PasswordToken
import requests

# Try to import SendGrid (optional dependency)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("[EMAIL] SendGrid library not installed. Install with: pip install sendgrid")


# Email configuration
# For SendGrid API: Only MAIL_FROM matters (must be verified in SendGrid)
# For SMTP: MAIL_USERNAME and MAIL_FROM should match for Gmail compatibility
mail_from = settings.MAIL_FROM

# Auto-fix for SMTP: If MAIL_FROM doesn't match MAIL_USERNAME, use MAIL_USERNAME (required for Gmail)
# This only applies when using SMTP, not SendGrid API
if not settings.SENDGRID_API_KEY and settings.MAIL_USERNAME and settings.MAIL_FROM != settings.MAIL_USERNAME:
    print(f"[EMAIL WARNING] MAIL_FROM ({settings.MAIL_FROM}) doesn't match MAIL_USERNAME ({settings.MAIL_USERNAME})")
    print(f"[EMAIL WARNING] Using MAIL_USERNAME as MAIL_FROM for Gmail SMTP compatibility")
    mail_from = settings.MAIL_USERNAME

# SMTP configuration (for local development or services that allow SMTP)
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

# Determine email sending method (priority: Brevo API > SendGrid API > SMTP)
USE_BREVO_API = settings.BREVO_API_KEY is not None
USE_SENDGRID_API = settings.SENDGRID_API_KEY is not None and SENDGRID_AVAILABLE

if USE_BREVO_API:
    print(f"[EMAIL] Using Brevo API (works on Render)")
elif USE_SENDGRID_API:
    print(f"[EMAIL] Using SendGrid API (works on Render)")
elif settings.SENDGRID_API_KEY and not SENDGRID_AVAILABLE:
    print(f"[EMAIL WARNING] SENDGRID_API_KEY is set but sendgrid library is not installed")
    print(f"[EMAIL WARNING] Falling back to SMTP. Install sendgrid: pip install sendgrid")
else:
    print(f"[EMAIL] Using SMTP (MAIL_SERVER: {settings.MAIL_SERVER})")


async def _send_email_via_brevo_api(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send email using Brevo HTTP API (works on Render).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        from_email: Sender email (defaults to settings.MAIL_FROM)
        from_name: Sender name (defaults to settings.MAIL_FROM_NAME)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not settings.BREVO_API_KEY:
        print(f"[EMAIL ERROR] BREVO_API_KEY not set")
        return False
    
    try:
        from_email = from_email or mail_from
        from_name = from_name or settings.MAIL_FROM_NAME
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "sender": {
                "email": from_email,
                "name": from_name
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": body
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            print(f"[EMAIL] Successfully sent email via Brevo API to {to_email}")
            print(f"[EMAIL] Brevo response status: {response.status_code}")
            return True
        else:
            # Log detailed error information
            print(f"[EMAIL ERROR] Brevo API returned status {response.status_code}")
            print(f"[EMAIL ERROR] From email: {from_email}")
            print(f"[EMAIL ERROR] To email: {to_email}")
            
            try:
                error_body = response.text
                print(f"[EMAIL ERROR] Response body: {error_body}")
                
                # Check for common errors
                if response.status_code == 401:
                    print(f"[EMAIL ERROR] AUTHENTICATION FAILED: Check your BREVO_API_KEY")
                elif response.status_code == 400:
                    if "sender" in error_body.lower() or "from" in error_body.lower():
                        print(f"[EMAIL ERROR] SENDER NOT VERIFIED: The email '{from_email}' must be verified in Brevo")
                        print(f"[EMAIL ERROR] Action: Go to Brevo Dashboard → Settings → Sender Authentication → Verify a Single Sender")
                elif response.status_code == 403:
                    print(f"[EMAIL ERROR] PERMISSION DENIED: Your API key may not have 'Send Email' permissions")
            except:
                print(f"[EMAIL ERROR] Could not parse error response")
            
            return False
            
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email via Brevo API to {to_email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def _send_email_via_sendgrid_api(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send email using SendGrid API (works on Render).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        from_email: Sender email (defaults to settings.MAIL_FROM)
        from_name: Sender name (defaults to settings.MAIL_FROM_NAME)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not SENDGRID_AVAILABLE:
        print(f"[EMAIL ERROR] SendGrid library not available")
        return False
    
    if not settings.SENDGRID_API_KEY:
        print(f"[EMAIL ERROR] SENDGRID_API_KEY not set")
        return False
    
    try:
        from_email = from_email or mail_from
        from_name = from_name or settings.MAIL_FROM_NAME
        
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"[EMAIL] Successfully sent email via SendGrid API to {to_email}")
            print(f"[EMAIL] SendGrid response status: {response.status_code}")
            return True
        else:
            # Log detailed error information
            print(f"[EMAIL ERROR] SendGrid API returned status {response.status_code}")
            print(f"[EMAIL ERROR] From email: {from_email}")
            print(f"[EMAIL ERROR] To email: {to_email}")
            
            # Try to decode response body
            try:
                error_body = response.body.decode('utf-8') if response.body else "No error body"
                print(f"[EMAIL ERROR] Response body: {error_body}")
                
                # Check for common errors
                if "403" in str(response.status_code) or "unauthorized" in error_body.lower():
                    print(f"[EMAIL ERROR] AUTHENTICATION FAILED: Check your SENDGRID_API_KEY")
                elif "sender" in error_body.lower() or "from" in error_body.lower():
                    print(f"[EMAIL ERROR] SENDER NOT VERIFIED: The email '{from_email}' must be verified in SendGrid")
                    print(f"[EMAIL ERROR] Action: Go to SendGrid Dashboard → Settings → Sender Authentication → Verify a Single Sender")
                elif "403" in str(response.status_code):
                    print(f"[EMAIL ERROR] PERMISSION DENIED: Your API key may not have 'Mail Send' permissions")
            except:
                print(f"[EMAIL ERROR] Response body (raw): {response.body}")
            
            return False
            
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email via SendGrid API to {to_email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def _send_email_via_smtp(
    to_email: str,
    subject: str,
    body: str
) -> bool:
    """
    Send email using SMTP (for local development).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=body,
            subtype=MessageType.plain,
        )
        
        fm = FastMail(conf)
        await asyncio.wait_for(fm.send_message(message), timeout=30.0)
        print(f"[EMAIL] Successfully sent email via SMTP to {to_email}")
        return True
    except asyncio.TimeoutError:
        print(f"[EMAIL ERROR] Timeout: SMTP connection to {settings.MAIL_SERVER} timed out after 30 seconds")
        print(f"[EMAIL ERROR] This usually means the SMTP server is unreachable or blocking the connection")
        print(f"[EMAIL ERROR] Render blocks SMTP ports. Use SendGrid API instead (set SENDGRID_API_KEY)")
        return False
    except Exception as smtp_error:
        print(f"[EMAIL ERROR] SMTP error when sending to {to_email}")
        print(f"[EMAIL ERROR] Error type: {type(smtp_error).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(smtp_error)}")
        error_str = str(smtp_error).lower()
        if "sender" in error_str and ("not verified" in error_str or "unauthorized" in error_str):
            print(f"[EMAIL ERROR] SENDER EMAIL NOT VERIFIED: The sender email ({mail_from}) must be verified in your email service")
        import traceback
        traceback.print_exc()
        return False


async def _send_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send email using the configured method (Brevo API > SendGrid API > SMTP).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        from_email: Sender email (optional)
        from_name: Sender name (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if USE_BREVO_API:
        return await _send_email_via_brevo_api(to_email, subject, body, from_email, from_name)
    elif USE_SENDGRID_API:
        return await _send_email_via_sendgrid_api(to_email, subject, body, from_email, from_name)
    else:
        return await _send_email_via_smtp(to_email, subject, body)


async def send_password_setup_email(
    db: Session,
    user: User,
    password_token: PasswordToken
) -> bool:
    """
    Send password setup email to the user.
    
    Args:
        db: Database session
        user: User object
        password_token: PasswordToken object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create password setup link (HashRouter format: #/set-password)
        setup_link = f"{settings.FRONTEND_URL}#/set-password?token={password_token.token}"
        
        # Email content
        subject = "Set Your Password - School Management System"
        body = f"""
        Hello {user.name},
        
        You have been invited to join the School Management System as an Administrator.
        
        Please set your password by clicking on the following link:
        {setup_link}
        
        This link will expire in {settings.PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.
        
        If you did not request this invitation, please ignore this email.
        
        Best regards,
        School Management System
        """
        
        # Send email using configured method (SendGrid API or SMTP)
        email_sent = await _send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
        
        if email_sent:
            print(f"[EMAIL] Setup link: {setup_link}")
        
        return email_sent
        
    except Exception as e:
        # Log error with full details
        print(f"[EMAIL ERROR] Failed to send email to {user.email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        print(f"[EMAIL ERROR] Traceback:")
        traceback.print_exc()
        return False


async def send_login_credentials_email(
    db: Session,
    user: User,
    password: str,
    role: str
) -> bool:
    """
    Send login credentials email to newly created users (Teachers, Students, Parents).
    Includes generated password and reset password link.
    
    Args:
        db: Database session
        user: User object
        password: Plain text password (will be sent in email)
        role: User role (TEACHER, STUDENT, PARENT)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Generate password reset token
        password_token = generate_password_token(db, user.id)
        
        role_display = {
            "TEACHER": "Teacher",
            "STUDENT": "Student",
            "PARENT": "Parent"
        }.get(role, role)
        
        login_url = f"{settings.FRONTEND_URL}#/login"
        reset_link = f"{settings.FRONTEND_URL}#/reset-password?token={password_token.token}"
        
        # Email content
        subject = f"Your {role_display} Account Credentials - School Management System"
        body = f"""
Hello {user.name},

Your {role_display} account has been created in the School Management System.

═══════════════════════════════════════════════════════════
YOUR LOGIN CREDENTIALS:
═══════════════════════════════════════════════════════════

Email Address: {user.email}
Password: {password}

═══════════════════════════════════════════════════════════

Please login at: {login_url}

IMPORTANT SECURITY INFORMATION:
- You can use the generated password above to log in immediately
- The password contains only letters and numbers (no special characters)
- We strongly recommend changing your password to something more memorable
- Click the link below to reset your password to a new one of your choice

RESET PASSWORD LINK:
{reset_link}

This reset link will expire in {settings.PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.

IMPORTANT: When resetting your password, you will need to provide:
- Your CURRENT password (the generated password above)
- Your NEW password (choose a new one)

TROUBLESHOOTING:
- Make sure you copy the password exactly as shown (case-sensitive)
- Check for any extra spaces before or after the password
- If login fails, use the reset password link above

SECURITY NOTES:
- Do not share your password with anyone
- Keep your credentials secure
- Change your password regularly

If you did not expect this account, please contact your school administrator immediately.

Best regards,
School Management System
        """
        
        # Send email using configured method (SendGrid API or SMTP)
        email_sent = await _send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
        
        if email_sent:
            print(f"[EMAIL] Reset link: {reset_link}")
        
        return email_sent
        
    except Exception as e:
        # Log error with full details
        print(f"[EMAIL ERROR] Failed to send login credentials to {user.email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        print(f"[EMAIL ERROR] Traceback:")
        traceback.print_exc()
        return False


def generate_password_token(db: Session, user_id: int) -> PasswordToken:
    """
    Generate a secure, unique token for password setup.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        PasswordToken: Created password token
    """
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_TOKEN_EXPIRE_MINUTES)
    
    # Create password token
    password_token = PasswordToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(password_token)
    db.commit()
    db.refresh(password_token)
    
    return password_token


def validate_password_token(db: Session, token: str) -> PasswordToken:
    """
    Validate a password setup token.
    
    Args:
        db: Database session
        token: Token string
        
    Returns:
        PasswordToken: Valid password token
        
    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    password_token = db.query(PasswordToken).filter(PasswordToken.token == token).first()
    
    if not password_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    if password_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has already been used"
        )
    
    if password_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    
    return password_token


def mark_token_as_used(db: Session, password_token: PasswordToken) -> None:
    """
    Mark a password token as used.
    
    Args:
        db: Database session
        password_token: PasswordToken object
    """
    password_token.is_used = True
    db.commit()


async def send_password_reset_email(
    db: Session,
    user: User,
    password_token: PasswordToken
) -> bool:
    """
    Send password reset email to the user.
    
    Args:
        db: Database session
        user: User object
        password_token: PasswordToken object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create password reset link
        reset_link = f"{settings.FRONTEND_URL}#/reset-password?token={password_token.token}"
        
        # Email content
        subject = "Reset Your Password - School Management System"
        body = f"""
Hello {user.name},

You have requested to reset your password for your {user.role.value} account.

Please reset your password by clicking on the following link:
{reset_link}

IMPORTANT: You will need to provide:
- Your CURRENT password (old password)
- Your NEW password

This link will expire in {settings.PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
School Management System
        """
        
        # Send email using configured method (SendGrid API or SMTP)
        email_sent = await _send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
        
        if email_sent:
            print(f"[EMAIL] Reset link: {reset_link}")
        
        return email_sent
        
    except Exception as e:
        # Log error with full details
        print(f"[EMAIL ERROR] Failed to send password reset email to {user.email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        print(f"[EMAIL ERROR] Traceback:")
        traceback.print_exc()
        return False


async def send_school_admin_credentials_email(
    db: Session,
    user: User,
    password: str,
    password_token: PasswordToken,
    school_name: str
) -> bool:
    """
    Send school admin credentials email with generated password and reset link.
    
    Args:
        db: Database session
        user: User object (school admin)
        password: Plain text generated password
        password_token: PasswordToken object for reset link
        school_name: Name of the school
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create password reset link
        reset_link = f"{settings.FRONTEND_URL}#/reset-password?token={password_token.token}"
        login_url = f"{settings.FRONTEND_URL}#/login"
        
        # Email content
        subject = f"Your School Admin Account Credentials - {school_name}"
        body = f"""
Hello {user.name},

Your school "{school_name}" has been created in the School Management System, and you have been set up as the School Administrator.

═══════════════════════════════════════════════════════════
YOUR LOGIN CREDENTIALS:
═══════════════════════════════════════════════════════════

Email Address: {user.email}
Password: {password}

═══════════════════════════════════════════════════════════

Please login at: {login_url}

IMPORTANT SECURITY INFORMATION:
- You can use the generated password above to log in immediately
- The password contains only letters and numbers (no special characters)
- We strongly recommend changing your password to something more memorable
- Click the link below to reset your password to a new one of your choice

RESET PASSWORD LINK:
{reset_link}

This reset link will expire in {settings.PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.

IMPORTANT: When resetting your password, you will need to provide:
- Your CURRENT password (the generated password above)
- Your NEW password (choose a new one)

TROUBLESHOOTING:
- Make sure you copy the password exactly as shown (case-sensitive)
- Check for any extra spaces before or after the password
- If login fails, use the reset password link above

SECURITY NOTES:
- Do not share your password with anyone
- Keep your credentials secure
- Change your password regularly

If you did not expect this account, please contact the system administrator immediately.

Best regards,
School Management System
        """
        
        # Send email using configured method (SendGrid API or SMTP)
        email_sent = await _send_email(
            to_email=user.email,
            subject=subject,
            body=body
        )
        
        if email_sent:
            print(f"[EMAIL] Reset link: {reset_link}")
        
        return email_sent
        
    except Exception as e:
        # Log error with full details
        print(f"[EMAIL ERROR] Failed to send school admin credentials to {user.email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        print(f"[EMAIL ERROR] Traceback:")
        traceback.print_exc()
        return False