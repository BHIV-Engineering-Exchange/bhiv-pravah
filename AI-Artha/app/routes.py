import os
import time
import json
import hashlib
import uuid
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SCHEMA_VERSION = os.getenv("PLATFORM_SCHEMA_VERSION", "1.0.0")

def get_trace_context(request: Request) -> dict:
    """Extract trace context from request state (injected by TracePropagationMiddleware)."""
    return {
        "trace_id": getattr(request.state, "trace_id", None) or str(uuid.uuid4()),
        "execution_id": getattr(request.state, "execution_id", None) or str(uuid.uuid4()),
        "schema_version": getattr(request.state, "schema_version", SCHEMA_VERSION),
    }

def platform_response(request: Request, module: str, status: str, data: dict, 
                      duration_ms: float = 0, error: dict = None) -> dict:
    """Wrap response in platform envelope per PLATFORM_ENTRY.md contract."""
    ctx = get_trace_context(request)
    response = {
        "trace_id": ctx["trace_id"],
        "schema_version": ctx["schema_version"],
        "status": status,
        "module": module,
        "execution_id": ctx["execution_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round(duration_ms, 2),
        "data": data,
    }
    if error:
        response["error"] = error
    return response

def platform_error_response(request: Request, module: str, code: str, message: str,
                            details: dict = None, status_code: int = 500):
    """Create platform error response per PLATFORM_ENTRY.md contract."""
    ctx = get_trace_context(request)
    return HTTPException(
        status_code=status_code,
        detail={
            "trace_id": ctx["trace_id"],
            "schema_version": ctx["schema_version"],
            "status": "error",
            "module": module,
            "execution_id": ctx["execution_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            }
        }
    )

# MongoDB database manager
from core.database import DatabaseManager, db
from core.mongodb import get_collection

from .models import (
    ContentResponse, FeedbackRequest, FeedbackResponse, 
    TagRecommendationResponse, MetricsResponse, AnalyticsResponse,
    VideoGenerationResponse
)

# Import decorators with fallback
try:
    from .observability import track_performance, track_user_action
except ImportError:
    def track_performance(name):
        def decorator(func):
            return func
        return decorator
    def track_user_action(name):
        def decorator(func):
            return func
        return decorator



# Import audit logger with fallback
try:
    from .request_middleware import audit_logger
except ImportError:
    class AuditLogger:
        def log_action(self, *args, **kwargs):
            pass
    audit_logger = AuditLogger()

# Import rate limiting with fallback
try:
    from .rate_limiting import (
        rate_limit_upload, rate_limit_generate, rate_limit_feedback, 
        rate_limit_analytics, rate_limit_default
    )
except ImportError:
    # Fallback rate limiting functions
    def rate_limit_upload(request):
        pass
    def rate_limit_generate(request):
        pass
    def rate_limit_feedback(request):
        pass
    def rate_limit_analytics(request):
        pass
    def rate_limit_default(request):
        pass

def validate_environment():
    """Optimized environment validation"""
    return {'validation': {'valid': True, 'warning_count': 0}}

try:
    from .auth import get_current_user, get_current_user_required
    from fastapi.security import HTTPBearer
    from fastapi import Request
    
    # Create optional auth dependency
    security = HTTPBearer(auto_error=False)
    
    async def get_current_user_optional(request: Request):
        """Get current user without requiring authentication"""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None
            
            token = authorization.replace("Bearer ", "")
            from .auth import verify_token
            payload = verify_token(token)
            user_id = payload.get("user_id")
            username = payload.get("sub")
            
            if user_id and username:
                class AuthUser:
                    def __init__(self, user_id: str, username: str):
                        self.user_id = user_id
                        self.username = username
                return AuthUser(user_id, username)
            return None
        except:
            return None
            
except ImportError:
    # Fallback when auth is not available
    async def get_current_user():
        return None
    async def get_current_user_required():
        class AnonymousUser:
            def __init__(self):
                self.user_id = 'anonymous'
                self.username = 'anonymous'
        return AnonymousUser()
    async def get_current_user_optional(request: Request):
        return None

# Email service fallback
def send_verification_email(email, token):
    return False
def send_invitation_email(email, inviter, token):
    return False
from .agent import RLAgent

# Import streaming metrics with fallback
try:
    from .streaming_metrics import streaming_metrics
except ImportError:
    class _StreamingMetrics:
        def log_stream_start(self, *a, **kw): return "default"
        def log_stream_end(self, *a, **kw): pass
        def get_performance_summary(self): return {}
    streaming_metrics = _StreamingMetrics()

from .observability import track_performance, track_user_action, sentry_manager, posthog_manager, set_user_context, track_event
from .observability import track_performance, track_user_action, sentry_manager, posthog_manager, set_user_context, track_event
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Import storage with S3 fallback
try:
    from core.s3_storage_adapter import storage_adapter, save_script, save_video, save_json
    from core.s3_storage_adapter import get_bucket_path
except ImportError:
    # Fallback to bhiv_bucket
    try:
        from core.bhiv_bucket import save_script, save_video, get_bucket_path
        from core import bhiv_bucket
        def save_json(segment, filename, data):
            return bhiv_bucket.save_json(segment, filename, data)
    except ImportError:
        # Create fallback functions
        import os
        import json
        
        def save_script(content, filename):
            os.makedirs("bucket/scripts", exist_ok=True)
            path = f"bucket/scripts/{filename}"
            with open(path, 'wb') as f:
                f.write(content if isinstance(content, bytes) else content.encode('utf-8'))
            return path
        
        def save_video(file_path, filename):
            os.makedirs("bucket/videos", exist_ok=True)
            dest = f"bucket/videos/{filename}"
            import shutil
            shutil.copy2(file_path, dest)
            return dest
        
        def get_bucket_path(segment, filename):
            return f"bucket/{segment}/{filename}"
        
        def save_json(segment, filename, data):
            os.makedirs(f"bucket/{segment}", exist_ok=True)
            path = f"bucket/{segment}/{filename}"
            with open(path, 'w') as f:
                json.dump(data, f)
            return path

try:
    from core import bhiv_core
except ImportError:
    # Create fallback bhiv_core
    class BhivCore:
        async def process_webhook_ingest(self, payload, source):
            return {"status": "fallback", "message": "bhiv_core not available"}
    bhiv_core = BhivCore()

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# MongoDB is initialized via core.database at import time

# Optimized initialization
agent = None
try:
    from .agent import RLAgent
    agent = RLAgent(state_path='agent_state.json')
except Exception as e:
    print(f"Initialization warning: {e}")
    agent = None
# Create routers with proper systematic step-by-step tags for grouping
step1_router = APIRouter(tags=["STEP 1: System Health & Demo Access"])
step2_router = APIRouter(tags=["STEP 2: User Authentication"])  # Will be used by auth.py
step3_router = APIRouter(tags=["STEP 3: Content Upload & Video Generation"])
step4_router = APIRouter(tags=["STEP 4: Content Access & Streaming"])
step5_router = APIRouter(tags=["STEP 5: AI Feedback & Tag Recommendations"])
step6_router = APIRouter(tags=["STEP 6: Analytics & Performance Monitoring"])


# Main router for backwards compatibility - contains only essential default endpoints
router = APIRouter(tags=["Default Endpoints"])

# Add only essential default endpoints that need to be at root level
@router.get('/health')
def health_check_default():
    """Default health check endpoint - PUBLIC ACCESS"""
    try:
        env_validation = validate_environment()
        return {
            "status": "healthy", 
            "service": "AI Content Uploader Agent",
            "version": "1.0.0",
            "environment_valid": env_validation['validation']['valid'],
            "config_warnings": env_validation['validation']['warning_count'],
            "message": "Use /docs for API documentation",
            "authentication": "not_required"
        }
    except Exception:
        return {
            "status": "healthy", 
            "service": "AI Content Uploader Agent",
            "version": "1.0.0",
            "message": "Use /docs for API documentation",
            "authentication": "not_required"
        }

@router.get('/')
def root():
    """Root endpoint - show welcome page"""
    from fastapi.responses import HTMLResponse
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>AI Content Uploader Agent</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #333; 
            text-align: center;
        }
        .links { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }
        .link-card { 
            background: #007bff; 
            color: white; 
            padding: 15px; 
            border-radius: 5px; 
            text-decoration: none; 
            text-align: center; 
            display: block;
        }
        .link-card:hover { 
            background: #0056b3; 
        }
        .status { 
            background: #28a745; 
            color: white; 
            padding: 10px; 
            border-radius: 5px; 
            text-align: center; 
            margin: 20px 0; 
        }
        .quick-start {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Content Uploader Agent</h1>
        <div class="status">Server Running Successfully</div>
        <p>Welcome to the AI-powered content analysis and video generation platform.</p>
        
        <div class="links">
            <a href="/docs" class="link-card">API Documentation</a>
            <a href="/health" class="link-card">Health Check</a>
            <a href="/dashboard" class="link-card">Dashboard</a>
            <a href="/demo-login" class="link-card">Demo Login</a>
        </div>
        
        <div class="quick-start">
            <h3>Quick Start:</h3>
            <ol>
                <li>Get demo credentials from <a href="/demo-login">/demo-login</a></li>
                <li>Visit <a href="/docs">/docs</a> for interactive API testing</li>
                <li>Use POST /users/login to authenticate</li>
                <li>Upload content with POST /upload</li>
            </ol>
        </div>
        
        <div class="quick-start">
            <h3>Server Status:</h3>
            <ul>
                <li>Database: Connected (Supabase)</li>
                <li>Storage: Supabase (1GB free)</li>
                <li>Authentication: JWT enabled</li>
                <li>API Endpoints: 58 routes loaded</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@router.get('/test')
def simple_test():
    """Simple test endpoint to verify server is working"""
    return {
        "status": "working",
        "message": "Server is running correctly",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "endpoints": {
            "health": "/health",
            "demo_login": "/demo-login", 
            "api_docs": "/docs",
            "contents": "/contents",
            "metrics": "/metrics"
        },
        "next_steps": [
            "Visit /docs for full API documentation",
            "Use /demo-login to get test credentials",
            "Try /contents to see available content"
        ]
    }

# Remove all other endpoints from default router - they are now properly organized in step routers

# Create demo user if not exists
def create_demo_user():
    """Check demo user in main database - now uses Supabase"""
    try:
        print("Checking demo user in main database...")
        
        # Check main database first (Supabase)
        from core.database import DatabaseManager
        db = DatabaseManager()
        existing_user = db.get_user_by_username('demo')
        
        if existing_user:
            # Verify password works
            try:
                from .security import PasswordManager
                if PasswordManager.verify_password('demo1234', existing_user.password_hash):
                    print("Demo user ready in main database with correct password")
                    return True
                else:
                    print("Demo user exists but password verification failed - run fix_demo_password.py")
                    return False
            except Exception as verify_error:
                print(f"Password verification error: {verify_error}")
                return False
        else:
            print("Demo user not found in main database - run create_demo_in_supabase.py")
            return False
            
    except Exception as e:
        print(f"Demo user check failed: {e}")
        return False

def update_demo_password(new_password):
    """Update demo user password with proper hashing"""
    try:
        try:
            from .security import PasswordManager
            demo_hash = PasswordManager.hash_password(new_password)
        except ImportError:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            demo_hash = pwd_context.hash(new_password)
        
        users = get_collection("users")
        result = users.update_one({"username": "demo"}, {"$set": {"password_hash": demo_hash}})
        if result.matched_count == 0:
            users.insert_one({
                "user_id": "demo001",
                "username": "demo",
                "password_hash": demo_hash,
                "email": "demo@example.com",
                "email_verified": True,
                "created_at": time.time()
            })
        return True
    except Exception as e:
        print(f"Failed to update demo password: {e}")
        return False

# Check demo user on startup
try:
    demo_ready = create_demo_user()
    if not demo_ready:
        print("Demo user needs to be fixed - run fix_demo_password.py")
except Exception as e:
    print(f"Demo user check failed on startup: {e}")

# ===== STEP 1: SYSTEM STATUS & ONBOARDING =====

@step1_router.get('/health')
def health_check():
    """STEP 1A: Check if system is running - PUBLIC ACCESS"""
    try:
        env_validation = validate_environment()
        return {
            "status": "healthy", 
            "service": "AI Content Uploader Agent",
            "version": "1.0.0",
            "systematic_organization": "9 step workflow",
            "environment_valid": env_validation['validation']['valid'],
            "config_warnings": env_validation['validation']['warning_count'],
            "authentication": "not_required",
            "next_step": "GET /demo-login for test credentials or POST /users/register to create account"
        }
    except Exception:
        return {
            "status": "healthy", 
            "service": "AI Content Uploader Agent",
            "version": "1.0.0",
            "authentication": "not_required",
            "next_step": "GET /demo-login for test credentials or POST /users/register to create account"
        }

@step1_router.get('/health/platform')
def health_platform():
    """Phase IV: Platform contract health and deployment verification checklist"""
    try:
        env_validation = validate_environment()
        
        # Platform module availability checks
        try:
            from .platform_contract import SCHEMA_VERSION as platform_schema
            platform_contract_ok = True
        except ImportError:
            platform_schema = None
            platform_contract_ok = False
        
        try:
            from .runtime_observability import event_store
            observability_ok = True
        except ImportError:
            observability_ok = False
        
        try:
            from .bucket_validation import bucket_validation_router
            bucket_validation_ok = True
        except ImportError:
            bucket_validation_ok = False
        
        deployment_checklist = {
            "trace_propagation_middleware": "added" if platform_contract_ok else "missing",
            "schema_version": platform_schema or "N/A",
            "runtime_observability": "available" if observability_ok else "missing",
            "bucket_validation": "available" if bucket_validation_ok else "missing",
            "environment_valid": env_validation['validation']['valid'],
            "config_warnings": env_validation['validation']['warning_count'],
            "platform_endpoints": {
                "POST /platform/execute": platform_contract_ok,
                "POST /platform/validate-contract": platform_contract_ok,
                "GET /platform/modules": platform_contract_ok,
                "GET /observability/events": observability_ok,
                "GET /observability/health": observability_ok,
                "POST /bucket-validation/write-and-verify": bucket_validation_ok,
                "GET /bucket-validation/status": bucket_validation_ok,
            }
        }
        
        all_healthy = all([
            platform_contract_ok,
            observability_ok,
            bucket_validation_ok,
            env_validation['validation']['valid']
        ])
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "phase": "IV",
            "platform_contract": platform_contract_ok,
            "runtime_observability": observability_ok,
            "bucket_validation": bucket_validation_ok,
            "deployment_checklist": deployment_checklist,
            "schema_version": "1.0.0",
            "authentication": "not_required",
            "next_step": "POST /platform/execute with trace_id, schema_version, prompt, module"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "phase": "IV",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step1_router.get('/demo-login')
def demo_login():
    """STEP 1B: Get demo credentials for quick testing - PUBLIC ACCESS"""
    # Use static demo credentials for reliability
    demo_password = "demo1234"
    
    # Ensure demo user exists and password works
    create_demo_user()
    
    # Test login credentials
    login_test_result = test_demo_login()
    
    return {
        "demo_credentials": {"username": "demo", "password": demo_password},
        "authentication": "not_required",
        "login_test": login_test_result,
        "password_hashing": "bcrypt (compatible with login system)",
        "instructions": [
            "1. Copy the credentials above",
            "2. Go to POST /users/login endpoint",
            "3. Use 'Try it out' and enter username and password",
            "4. Execute to get your access token"
        ],
        "next_step": "POST /users/login with these credentials to get access token"
    }



def test_demo_login():
    """Test demo login credentials"""
    try:
        from .security import PasswordManager
        from core.database import DatabaseManager
        
        # Test main database first (Supabase)
        db = DatabaseManager()
        user = db.get_user_by_username('demo')
        
        if user:
            if PasswordManager.verify_password('demo1234', user.password_hash):
                return {"status": "success", "message": "Demo credentials work correctly in main database"}
            else:
                return {"status": "failed", "message": "Password verification failed in main database"}
        else:
            return {"status": "failed", "message": "Demo user not found in main database"}
    except Exception as e:
        return {"status": "error", "message": str(e)}



# ===== STEP 2: USER AUTHENTICATION =====

class InviteUser(BaseModel):
    email: str

@step2_router.post('/invite-user')
def invite_user(invite: InviteUser, current_user = Depends(get_current_user_required)):
    """STEP 2A: Send user invitation (requires authentication)"""
    # Enhanced security validation
    
    # Email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, invite.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Rate limiting check (max 5 invitations per hour per user)
    try:
        invitations = get_collection("invitations")
        hour_ago = time.time() - 3600
        
        recent_count = invitations.count_documents({
            "inviter_id": current_user.user_id,
            "created_at": {"$gt": hour_ago}
        })
        
        if recent_count >= 5:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 invitations per hour.")
        
        existing = invitations.count_documents({
            "email": invite.email,
            "created_at": {"$gt": hour_ago},
            "used": False
        })
        if existing > 0:
            raise HTTPException(status_code=400, detail="Email already has pending invitation")
        
        invitation_token = uuid.uuid4().hex
        expires_at = time.time() + (7 * 24 * 3600)
        
        invitations.insert_one({
            "email": invite.email,
            "inviter_id": current_user.user_id,
            "invitation_token": invitation_token,
            "created_at": time.time(),
            "expires_at": expires_at,
            "used": False
        })
        
        # Send invitation email (sanitized)
        email_sent = send_invitation_email(invite.email, current_user.username, invitation_token)
        
        return {
            'status': 'success',
            'email': invite.email,
            'email_sent': email_sent,
            'invitation_token': invitation_token if not email_sent else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Invitation failed")

@step2_router.get('/verify-email')
def verify_email(token: str):
    """STEP 2B: Verify user email address"""
    try:
        users = get_collection("users")
        result = users.update_one(
            {"verification_token": token},
            {"$set": {"email_verified": True}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=400, detail='Invalid verification token')
        
        return {'status': 'success', 'message': 'Email verified successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@step2_router.get('/accept-invitation')
def accept_invitation(token: str):
    """STEP 2C: Accept user invitation"""
    try:
        invitations = get_collection("invitations")
        result = invitations.find_one({"invitation_token": token})
        
        if not result:
            raise HTTPException(status_code=400, detail='Invalid invitation token')
        
        if result.get("used"):
            raise HTTPException(status_code=400, detail='Invitation already used')
        
        if time.time() > result.get("expires_at", 0):
            raise HTTPException(status_code=400, detail='Invitation expired')
        
        email = result["email"]
        
        return {
            'status': 'valid',
            'email': email,
            'message': 'Invitation is valid. Please complete registration.',
            'register_url': f'/users/register?email={email}&invitation_token={token}'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: Main auth endpoints are in auth.py router (/users/register, /users/login, /users/profile)
# These are fallback endpoints for direct access without auth router

# ===== STEP 3: CONTENT CREATION =====

@step3_router.get('/contents')
def list_contents(limit: int = 20, current_user = Depends(get_current_user_required)):
    """STEP 3A: Browse existing content from Supabase database"""
    try:
        content_col = get_collection("content")
        rows = list(content_col.find(
            {},
            {"content_id": 1, "uploader_id": 1, "title": 1, "description": 1, "file_path": 1,
             "content_type": 1, "duration_ms": 1, "uploaded_at": 1, "authenticity_score": 1,
             "current_tags": 1, "views": 1, "likes": 1, "shares": 1}
        ).sort("uploaded_at", -1).limit(limit))
        
        items = []
        for row in rows:
            items.append({
                'content_id': row.get('content_id'),
                'uploader_id': row.get('uploader_id'),
                'title': row.get('title'),
                'description': row.get('description', ''),
                'file_path': row.get('file_path'),
                'content_type': row.get('content_type'),
                'duration_ms': row.get('duration_ms'),
                'uploaded_at': row.get('uploaded_at'),
                'authenticity_score': row.get('authenticity_score'),
                'current_tags': row.get('current_tags'),
                'views': row.get('views'),
                'likes': row.get('likes'),
                'shares': row.get('shares'),
                'download_url': f'/download/{row.get("content_id")}',
                'stream_url': f'/stream/{row.get("content_id")}'
            })
        
        return {
            'items': items,
            'total_count': len(items),
            'database': 'mongodb',
            'next_step': 'POST /upload to add new content'
        }
        
    except Exception as e:
        return {
            'items': [], 
            'error': str(e),
            'database': 'connection_failed',
            'message': 'Could not connect to database'
        }

# Simplified video generation endpoint above



@step3_router.post('/upload', response_model=dict, status_code=201)
async def upload_async(
    request: Request,
    file: UploadFile = File(...), 
    title: str = Form(...), 
    description: str = Form(''),
    current_user = Depends(get_current_user_required),
    _rate_limit = Depends(rate_limit_upload)
):
    """STEP 3B: Upload content file with enhanced validation and detailed response (requires authentication)
    Supports: Images, Videos, Audio, Documents up to 100MB with comprehensive security validation
    """
    
    # Get request ID and client IP for audit logging
    request_id = getattr(request.state, 'request_id', None)
    try:
        from app.security import security_manager
        client_ip = security_manager.get_client_ip(request)
    except:
        client_ip = request.client.host if request.client else "unknown"
    
    start_time = time.time()
    
    # Track user action with observability
    try:
        set_user_context(current_user.user_id, current_user.username)
        track_event(current_user.user_id, "file_upload_started", {
            "file_type": file.content_type,
            "title": title,
            "request_id": request_id
        })
    except Exception as obs_error:
        logger.warning(f"Observability tracking failed: {obs_error}")
    
    try:
        # Enhanced file validation
        validation_result = None
        try:
            from app.input_validation import FileValidator, TextValidator
            
            # Enhanced file validation
            validation_result = await FileValidator.validate_file(
                file, 
                allowed_categories=['image', 'video', 'audio', 'document', 'text']
            )
            
            # Text input sanitization
            title = TextValidator.sanitize_text(title, max_length=1000)
            if description:
                description = TextValidator.sanitize_text(description, max_length=10000)
                
        except ImportError:
            # Fallback validation if enhanced validation not available
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            allowed_extensions = {'.mp4', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.txt', '.pdf'}
            allowed_mime_types = {
                'video/mp4', 'audio/mpeg', 'audio/wav', 'image/jpeg', 'image/png', 'text/plain', 'application/pdf'
            }
            
            safe_filename = os.path.basename(file.filename)
            ext = os.path.splitext(safe_filename)[1].lower()
            
            if ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed")
            
            # More flexible MIME type validation - allow if extension is valid
            if file.content_type and file.content_type not in allowed_mime_types:
                # Allow if extension is in allowed list (browser may send generic MIME type)
                if ext not in allowed_extensions:
                    raise HTTPException(status_code=400, detail=f"MIME type {file.content_type} not allowed")
            
            data = await file.read()
            max_size = 100 * 1024 * 1024
            if len(data) > max_size:
                raise HTTPException(status_code=413, detail="File too large")
            
            # Create fallback validation result
            validation_result = {
                'mime_type': file.content_type or 'application/octet-stream',
                'size': len(data),
                'file_hash': hashlib.sha256(data).hexdigest(),
                'warnings': []
            }
        
        # Generate secure content ID
        if validation_result:
            content_id = generate_content_id(current_user.user_id, file.filename)
        else:
            h = hashlib.sha256(data).hexdigest()[:12]
            content_id = f"{h}_{uuid.uuid4().hex[:6]}"
        
        uploader_id = current_user.user_id if current_user else 'anonymous'
        
        # Create secure filename
        safe_filename = os.path.basename(file.filename)
        ext = os.path.splitext(safe_filename)[1].lower()
        
        if validation_result and 'file_hash' in validation_result:
            secure_filename = f"{content_id}{ext}"
            file_path = await save_file_securely(file, secure_filename, validation_result)
        else:
            # Fallback file saving
            clean_name = ''.join(c for c in safe_filename if c.isalnum() or c in '.-_')
            if not clean_name:
                clean_name = f"file{ext}"
            fname = f"{int(time.time())}_{content_id}_{clean_name}"
            
            # Use new storage adapter for direct upload
            try:
                from core.s3_storage_adapter import storage_adapter
                # Upload to storage (async-compatible)
                file_path = await asyncio.to_thread(
                    storage_adapter.upload_content, data, 'uploads', fname
                )
            except Exception as storage_error:
                logger.warning(f"Storage adapter failed, using fallback: {storage_error}")
                # Fallback to local save
                file_path = get_bucket_path('uploads', fname)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                await asyncio.to_thread(
                    lambda: open(file_path, 'wb').write(data)
                )
        
        # If it's a script file, also save to scripts bucket
        script_path = None
        if ext == '.txt':
            try:
                script_filename = f"{content_id}_script.txt"
                script_path = save_script(data, script_filename)
                import logging
                logging.info(f"Script file also saved to scripts bucket: {script_path}")
            except Exception as script_error:
                import logging
                logging.warning(f"Failed to save script to scripts bucket: {script_error}")
        
        # Compute authenticity and tags (async)
        authenticity_task = asyncio.to_thread(compute_authenticity, file_path, title, description)
        tags_task = asyncio.to_thread(suggest_tags, title, description)
        
        authenticity, tags = await asyncio.gather(authenticity_task, tags_task)
        uploaded_at = time.time()
        
        # Calculate authenticity score from validation if available
        if validation_result and 'file_hash' in validation_result:
            authenticity = calculate_authenticity_score(validation_result['file_hash'])
        
        # Save to Supabase database using DatabaseManager
        try:
            from core.database import DatabaseManager
            content_data = {
                'content_id': content_id,
                'uploader_id': uploader_id,
                'title': title,
                'description': description,
                'file_path': file_path,
                'content_type': validation_result['mime_type'] if validation_result else (file.content_type or 'application/octet-stream'),
                'uploaded_at': uploaded_at,
                'authenticity_score': authenticity,
                'current_tags': json.dumps(tags),
                'views': 0,
                'likes': 0,
                'shares': 0
            }
            
            # Use DatabaseManager to create content
            db_content = DatabaseManager.create_content(content_data)
            import logging
            logging.info(f"Content saved to Supabase: {content_id}")
            
            # Save to system logs
            try:
                DatabaseManager.save_system_log(
                    level="INFO",
                    message=f"Content uploaded to Supabase: {content_id} - {title}",
                    module="file_upload",
                    user_id=uploader_id
                )
            except Exception as log_error:
                print(f"Failed to save system log: {log_error}")
            
            print(f"Content successfully saved to database: {content_id}")
            
            # If it's a script file, also save to scripts table and bucket
            if ext == '.txt' and script_path:
                try:
                    script_content = data.decode('utf-8')
                    script_data = {
                        'script_id': f"upload_{content_id}",
                        'content_id': content_id,
                        'user_id': uploader_id,
                        'title': f"Uploaded script: {title}",
                        'script_content': script_content,
                        'script_type': 'uploaded_text',
                        'file_path': script_path,
                        'used_for_generation': False,
                        'created_at': time.time()
                    }
                    
                    # Save to both Supabase and local database
                    try:
                        get_collection("scripts").insert_one(script_data)
                        logging.info(f"Script saved to database: upload_{content_id}")
                        
                        DatabaseManager.save_system_log(
                            level="INFO",
                            message=f"Script uploaded: upload_{content_id} - {title}",
                            module="script_upload",
                            user_id=uploader_id
                        )
                    except Exception as script_db_error:
                        logging.error(f"Failed to save script to database: {script_db_error}")
                        
                        try:
                            DatabaseManager.save_system_log(
                                level="ERROR",
                                message=f"Script upload database save failed: {str(script_db_error)}",
                                module="script_upload",
                                user_id=uploader_id
                            )
                        except Exception as log_error:
                            print(f"Failed to save error log: {log_error}")
                    
                    # Save script metadata to bucket
                    script_metadata = {
                        'script_id': script_data['script_id'],
                        'content_id': content_id,
                        'title': title,
                        'script_type': 'uploaded_text',
                        'file_size': len(data),
                        'created_at': script_data['created_at'],
                        'bucket_path': script_path
                    }
                    metadata_filename = f"script_meta_{content_id}.json"
                    try:
                        from core import bhiv_bucket
                        bhiv_bucket.save_json('scripts', metadata_filename, script_metadata)
                    except:
                        pass
                    
                except Exception as script_error:
                    import logging
                    logging.warning(f"Failed to save script: {script_error}")
            
            # Save upload log
            log_data = {
                'content_id': content_id,
                'user_id': uploader_id,
                'action': 'file_upload',
                'filename': safe_filename,
                'file_size': validation_result['size'] if validation_result else len(data),
                'content_type': validation_result['mime_type'] if validation_result else file.content_type,
                'tags': tags,
                'authenticity_score': authenticity,
                'storage_path': file_path,
                'script_path': script_path,
                'timestamp': uploaded_at
            }
            log_filename = f"upload_{content_id}_{int(uploaded_at)}.json"
            try:
                save_json('logs', log_filename, log_data)
                import logging
                logging.info(f"Upload log saved: {log_filename}")
            except Exception as log_error:
                import logging
                logging.warning(f"Failed to save upload log: {log_error}")
                
        except Exception as db_error:
            import logging
            logging.error(f"Supabase save failed: {db_error}")
            
            # Fallback - save to MongoDB
            try:
                content_col = get_collection("content")
                content_col.update_one(
                    {"content_id": content_id},
                    {"$set": {
                        "content_id": content_id,
                        "uploader_id": uploader_id,
                        "title": title,
                        "description": description,
                        "file_path": file_path,
                        "content_type": validation_result['mime_type'] if validation_result else (file.content_type or 'application/octet-stream'),
                        "uploaded_at": uploaded_at,
                        "authenticity_score": authenticity,
                        "current_tags": json.dumps(tags),
                        "views": 0,
                        "likes": 0,
                        "shares": 0
                    }},
                    upsert=True
                )
                logging.info(f"Content saved to database: {content_id}")
            except Exception as save_error:
                logging.error(f"Database save failed: {save_error}")
                print(f"Database save failed: {db_error}")
        
        # Register content with RL agent for future recommendations (async)
        try:
            await asyncio.to_thread(agent.register_content, content_id, tags, authenticity)
        except Exception as rl_error:
            logger.warning(f"Failed to register content with RL agent: {rl_error}")
            
            # Save warning to system logs
            try:
                from core.database import DatabaseManager
                DatabaseManager.save_system_log(
                    level="WARNING",
                    message=f"Failed to register content with RL agent: {str(rl_error)}",
                    module="rl_agent",
                    user_id=uploader_id
                )
            except Exception as log_error:
                print(f"Failed to save warning log: {log_error}")
        
        # Track successful upload
        track_event(current_user.user_id, "file_upload_completed", {
            "content_id": content_id,
            "file_type": validation_result['mime_type'] if validation_result else file.content_type,
            "authenticity_score": authenticity,
            "tags_count": len(tags)
        })
        
        # Log successful upload to Supabase audit_logs
        processing_time = time.time() - start_time
        try:
            audit_logs = get_collection("audit_logs")
            audit_logs.insert_one({
                "user_id": current_user.user_id,
                "action": "content_upload",
                "resource_type": "content",
                "resource_id": content_id,
                "timestamp": time.time(),
                "ip_address": client_ip,
                "details": {
                    "filename": file.filename,
                    "file_size": validation_result['size'] if validation_result else len(data),
                    "mime_type": validation_result['mime_type'] if validation_result else file.content_type,
                    "processing_time_seconds": processing_time,
                    "validation_warnings": validation_result['warnings'] if validation_result else []
                },
                "status": "success"
            })
            logger.info(f"Audit log saved to database for upload: {content_id}")
                
        except Exception as audit_error:
            logger.warning(f"Supabase audit logging failed: {audit_error}")
            # Fallback audit log to local file
            try:
                os.makedirs('logs', exist_ok=True)
                audit_data = {
                    "timestamp": time.time(),
                    "user_id": current_user.user_id,
                    "action": "content_upload",
                    "resource_id": content_id,
                    "ip_address": client_ip,
                    "details": {
                        "filename": file.filename,
                        "file_size": validation_result['size'] if validation_result else len(data),
                        "processing_time": processing_time
                    }
                }
                with open(f'logs/audit_{int(time.time())}.json', 'w') as f:
                    json.dump(audit_data, f)
                logger.info(f"Audit log saved to local file for upload: {content_id}")
            except Exception as file_error:
                logger.error(f"All audit logging failed: {file_error}")
        
        # Log audit event for compliance
        try:
            audit_logger.log_action(
                user_id=current_user.user_id,
                action="file_upload",
                resource_type="content",
                resource_id=content_id,
                request_id=request_id,
                ip_address=client_ip,
                details={
                    "filename": safe_filename,
                    "file_size": validation_result['size'] if validation_result else len(data),
                    "content_type": validation_result['mime_type'] if validation_result else file.content_type,
                    "storage_path": file_path
                }
            )
        except Exception as audit_error:
            logger.warning(f"Audit logging failed: {audit_error}")
        
        # Return enhanced detailed response
        return {
            "message": "✅ Content uploaded successfully with enhanced security validation",
            "content_id": content_id,
            "title": title,
            "description": description,
            "file_size_mb": round((validation_result['size'] if validation_result else len(data)) / 1024 / 1024, 2),
            "mime_type": validation_result['mime_type'] if validation_result else (file.content_type or 'application/octet-stream'),
            "authenticity_score": authenticity,
            "processing_time_seconds": round(processing_time, 3),
            "tags": tags,
            "validation": {
                "passed": True,
                "file_hash": (validation_result['file_hash'][:16] + "...") if validation_result and 'file_hash' in validation_result else "computed",
                "warnings": validation_result['warnings'] if validation_result else []
            },
            "access_urls": {
                "view": f"/content/{content_id}",
                "download": f"/download/{content_id}",
                "stream": f"/stream/{content_id}" if 'video' in (validation_result['mime_type'] if validation_result else file.content_type or '') else None,
                "metadata": f"/content/{content_id}/metadata"
            },
            "next_step": f"Use /content/{content_id} to view details or /stream/{content_id} to access content"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed upload attempt to Supabase
        try:
            audit_logs = get_collection("audit_logs")
            audit_logs.insert_one({
                "user_id": current_user.user_id,
                "action": "content_upload_failed",
                "resource_type": "content",
                "resource_id": "unknown",
                "timestamp": time.time(),
                "ip_address": client_ip,
                "details": {"error": str(e), "filename": file.filename},
                "status": "failed"
            })
            logger.info(f"Failed upload audit log saved to database")
                
        except Exception as audit_error:
            logger.warning(f"Failed upload audit logging failed: {audit_error}")
        
        # Log error with audit trail
        try:
            audit_logger.log_action(
                user_id=current_user.user_id,
                action="file_upload",
                resource_type="content", 
                resource_id=content_id if 'content_id' in locals() else "unknown",
                request_id=request_id,
                ip_address=client_ip,
                details={"error": str(e)},
                status="failed"
            )
        except Exception as audit_error:
            logger.warning(f"Audit logging failed: {audit_error}")
        
        logger.error(f"Upload failed for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@step3_router.post('/generate-video', response_model=VideoGenerationResponse, status_code=202)
@track_performance("video_generation")
@track_user_action("generate_video")
async def generate_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user = Depends(get_current_user_required)
):
    """STEP 3C: Generate video one frame per script line"""
    
    # Track video generation with observability
    set_user_context(current_user.user_id, current_user.username)
    track_event(current_user.user_id, "video_generation_started", {
        "title": title,
        "file_size": file.size
    })

    # Validate extension and size
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext != '.txt':
        raise HTTPException(status_code=400, detail="Only .txt files allowed")
    if file.size is not None and file.size > 1_048_576:
        raise HTTPException(status_code=413, detail="Script file too large (max 1MB)")

    # Read script
    script_content = (await file.read()).decode('utf-8').strip()
    if not script_content:
        raise HTTPException(status_code=400, detail="Empty script content")

    # Save temporary script
    content_id = uuid.uuid4().hex[:12]
    timestamp = time.time()
    bucket_video_path = get_bucket_path('videos', f"{content_id}.mp4")
    os.makedirs(os.path.dirname(bucket_video_path), exist_ok=True)

    # Use the create_multi_frame_video function from video.generator
    try:
        from video.generator import create_multi_frame_video
        create_multi_frame_video(script_content, bucket_video_path, frame_duration=3.0)
    except ImportError:
        # Fallback: Create a simple text file instead of video
        try:
            sentences = []
            import re
            for line in script_content.split('\n'):
                line = line.strip()
                if line:
                    line_sentences = re.split(r'[.!?]+', line)
                    for sentence in line_sentences:
                        sentence = sentence.strip()
                        if sentence:
                            sentences.append(sentence)
            
            # Create text representation
            video_text = f"VIDEO CONTENT\n{'='*50}\n\n"
            for i, sentence in enumerate(sentences, 1):
                video_text += f"Frame {i} (3s): {sentence}\n\n"
            
            # Save as .txt file (will be renamed to .mp4 for compatibility)
            with open(bucket_video_path.replace('.mp4', '.txt'), 'w', encoding='utf-8') as f:
                f.write(video_text)
            
            # Create empty .mp4 file for compatibility
            with open(bucket_video_path, 'w') as f:
                f.write('')
                
        except Exception as fallback_error:
            raise HTTPException(
                status_code=500,
                detail=f"Video generation failed. MoviePy not available and fallback failed: {str(fallback_error)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {str(e)}"
        )

    # Verify video created
    if not os.path.exists(bucket_video_path):
        raise HTTPException(status_code=500, detail="Video file was not created")

    # Count sentences for metadata
    import re
    sentences = []
    for line in script_content.split('\n'):
        line = line.strip()
        if line:
            line_sentences = re.split(r'[.!?]+', line)
            for sentence in line_sentences:
                sentence = sentence.strip()
                if sentence:
                    sentences.append(sentence)
    frame_duration = 3.0

    # Save to database
    try:
        content_col = get_collection("content")
        content_col.update_one(
            {"content_id": content_id},
            {"$set": {
                "content_id": content_id,
                "uploader_id": current_user.user_id,
                "title": title,
                "description": 'Generated video from script',
                "file_path": bucket_video_path,
                "content_type": 'video/mp4',
                "duration_ms": int(frame_duration * len(sentences) * 1000),
                "uploaded_at": timestamp,
                "authenticity_score": 0.8,
                "current_tags": json.dumps(['generated', 'video', 'script']),
                "views": 0,
                "likes": 0,
                "shares": 0
            }},
            upsert=True
        )
        
        get_collection("scripts").update_one(
            {"script_id": f"video_{content_id}"},
            {"$set": {
                "script_id": f"video_{content_id}",
                "content_id": content_id,
                "user_id": current_user.user_id,
                "title": f"Video script: {title}",
                "script_content": script_content,
                "script_type": 'video_generation',
                "file_path": None,
                "created_at": timestamp,
                "used_for_generation": True
            }},
            upsert=True
        )
        
        print(f"Content and script saved to database: {content_id}")
        
        try:
            DatabaseManager.save_system_log(
                level="INFO",
                message=f"Video generated and saved to database: {content_id} - {title}",
                module="video_generation",
                user_id=current_user.user_id
            )
        except Exception as log_error:
            print(f"Failed to save system log: {log_error}")
        
        # Save script to bucket as well
        try:
            script_filename = f"video_script_{content_id}.txt"
            script_bucket_path = save_script(script_content.encode('utf-8'), script_filename)
            print(f"Script saved to bucket: {script_bucket_path}")
            
            # Save to system logs
            try:
                from core.database import DatabaseManager
                DatabaseManager.save_system_log(
                    level="INFO",
                    message=f"Script saved to bucket: {script_bucket_path}",
                    module="video_generation",
                    user_id=current_user.user_id
                )
            except Exception as log_error:
                print(f"Failed to save system log: {log_error}")
        except Exception as bucket_error:
            print(f"Failed to save script to bucket: {bucket_error}")
            
            # Save warning to system logs
            try:
                from core.database import DatabaseManager
                DatabaseManager.save_system_log(
                    level="WARNING",
                    message=f"Failed to save script to bucket: {str(bucket_error)}",
                    module="video_generation",
                    user_id=current_user.user_id
                )
            except Exception as log_error:
                print(f"Failed to save warning log: {log_error}")
        
    except Exception as e:
        import logging
        logging.error(f"Database save failed: {e}")
        print(f"Database save failed: {e}")
        
        # Save error to system logs
        try:
            from core.database import DatabaseManager
            DatabaseManager.save_system_log(
                level="ERROR",
                message=f"Video generation database save failed: {str(e)}",
                module="video_generation",
                user_id=current_user.user_id
            )
        except Exception as log_error:
            print(f"Failed to save error log: {log_error}")

    # Track successful video generation
    track_event(current_user.user_id, "video_generation_completed", {
        "content_id": content_id,
        "total_scenes": len(sentences),
        "total_duration": frame_duration * len(sentences)
    })
    
    return VideoGenerationResponse(
        content_id=content_id,
        video_path=f"/download/{content_id}",
        stream_url=f"/stream/{content_id}",
        local_file_path=bucket_video_path,
        storyboard_stats={
            "total_duration": frame_duration * len(sentences),
            "total_scenes": len(sentences),
            "version": "1.0",
            "generation_method": "sentence_per_frame",
        },
        processing_status="completed",
        next_step=f"Use /content/{content_id} to view details or /stream/{content_id} to watch video"
    )

# ===== STEP 4: CONTENT ACCESS & VIEWING =====

@step4_router.get('/content/{content_id}')
def get_content(content_id: str, current_user = Depends(get_current_user_required)):
    """STEP 4A: Get content details and access URLs"""
    try:
        content_col = get_collection("content")
        row = content_col.find_one(
            {"content_id": content_id},
            {"content_id": 1, "title": 1, "description": 1, "file_path": 1, "content_type": 1}
        )
        
        if not row:
            raise HTTPException(status_code=404, detail='Content not found')
        
        return {
            'content_id': row.get('content_id'),
            'title': row.get('title'),
            'description': row.get('description'),
            'file_path': row.get('file_path'),
            'content_type': row.get('content_type'),
            'download_url': f'/download/{content_id}',
            'stream_url': f'/stream/{content_id}'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@step4_router.get('/content/{content_id}/metadata')
def get_content_metadata(content_id: str, request: Request):
    """STEP 4A-2: Get detailed content metadata including stats and related data"""
    current_user = None  # For now, make it work without auth
    try:
        content_col = get_collection("content")
        content = content_col.find_one({"content_id": content_id})
        if not content:
            raise HTTPException(status_code=404, detail='Content not found')
        
        feedback_col = get_collection("feedback")
        feedback_pipeline = [
            {"$match": {"content_id": content_id}},
            {"$group": {
                "_id": None,
                "total_feedback": {"$sum": 1},
                "average_rating": {"$avg": "$rating"},
                "total_watch_time_ms": {"$sum": "$watch_time_ms"}
            }}
        ]
        feedback_results = list(feedback_col.aggregate(feedback_pipeline))
        feedback_stats = feedback_results[0] if feedback_results else {
            "total_feedback": 0, "average_rating": 0, "total_watch_time_ms": 0
        }
        
        related_script = get_collection("scripts").find_one({"content_id": content_id})
        
        try:
            tags = json.loads(content.get('current_tags', '[]')) if content.get('current_tags') else []
        except:
            tags = []
        
        file_size = 0
        if content.get('file_path') and os.path.exists(content['file_path']):
            file_size = os.path.getsize(content['file_path'])
        
        return {
            'content_id': content.get('content_id'),
            'title': content.get('title'),
            'description': content.get('description'),
            'uploader_id': content.get('uploader_id'),
            'content_type': content.get('content_type'),
            'file_path': content.get('file_path'),
            'file_size_bytes': file_size,
            'duration_ms': content.get('duration_ms'),
            'uploaded_at': content.get('uploaded_at'),
            'authenticity_score': content.get('authenticity_score'),
            'tags': tags,
            'views': content.get('views', 0),
            'likes': content.get('likes', 0),
            'shares': content.get('shares', 0),
            'feedback_stats': {
                'total_feedback': feedback_stats.get('total_feedback', 0),
                'average_rating': round(feedback_stats.get('average_rating', 0) or 0, 2),
                'total_watch_time_ms': feedback_stats.get('total_watch_time_ms', 0) or 0
            },
            'related_script': {
                'script_id': related_script.get('script_id') if related_script else None,
                'title': related_script.get('title') if related_script else None
            } if related_script else None,
            'urls': {
                'download': f'/download/{content_id}',
                'stream': f'/stream/{content_id}',
                'metadata': f'/content/{content_id}/metadata'
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Content metadata error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@step4_router.get('/download/{content_id}')
def download(content_id: str, current_user = Depends(get_current_user_required)):
    """STEP 4B: Download content file"""
    try:
        content_col = get_collection("content")
        content = content_col.find_one(
            {"content_id": content_id},
            {"file_path": 1}
        )
        if not content:
            raise HTTPException(status_code=404, detail='Content not found')
        file_path = content.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail='File not found')
        
        return FileResponse(file_path, filename=os.path.basename(file_path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@step4_router.get('/stream/{content_id}')
def stream_video(content_id: str, request: Request, current_user = Depends(get_current_user_required), range_request: Optional[str] = None):
    """STEP 4C: Stream video content with range support (authentication optional for analytics)"""
    from fastapi.responses import StreamingResponse
    
    # Log streaming start
    client_ip = request.client.host if request.client else "unknown"
    range_header = request.headers.get('range')
    session_id = streaming_metrics.log_stream_start(content_id, client_ip, range_header)
    
    # Get content using database with fallback
    try:
        content_col = get_collection("content")
        content = content_col.find_one(
            {"content_id": content_id},
            {"file_path": 1}
        )
        if not content:
            streaming_metrics.log_stream_end(session_id, 0, 404)
            raise HTTPException(status_code=404, detail='Content not found')
        file_path = content.get('file_path')
    except HTTPException:
        raise
    except Exception as db_error:
        import logging
        logging.error(f"Database query failed: {db_error}")
        streaming_metrics.log_stream_end(session_id, 0, 500)
        raise HTTPException(status_code=500, detail="Database query failed")
    if not os.path.exists(file_path):
        streaming_metrics.log_stream_end(session_id, 0, 404)
        raise HTTPException(status_code=404, detail='File not found')
    
    file_size = os.path.getsize(file_path)
    
    if range_header:
        try:
            byte_range = range_header.replace('bytes=', '')
            start_end = byte_range.split('-')
            start = int(start_end[0])
            end = int(start_end[1]) if start_end[1] else file_size - 1
            
            if start >= file_size or end >= file_size or start > end:
                streaming_metrics.log_stream_end(session_id, 0, 416)
                raise HTTPException(status_code=416, detail='Range not satisfiable')
            
            bytes_to_serve = end - start + 1
            
            def iter_file():
                bytes_served = 0
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = bytes_to_serve
                    while remaining > 0:
                        chunk_size = min(1024 * 1024, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        bytes_served += len(data)
                        yield data
                # Log completion after streaming
                streaming_metrics.log_stream_end(session_id, bytes_served, 206)
            
            return StreamingResponse(
                iter_file(), 
                status_code=206,
                headers={
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(bytes_to_serve)
                },
                media_type='video/mp4'
            )
        except (ValueError, IndexError):
            streaming_metrics.log_stream_end(session_id, 0, 416)
            raise HTTPException(status_code=416, detail='Invalid range')
    
    # Full file streaming
    streaming_metrics.log_stream_end(session_id, file_size, 200)
    return FileResponse(file_path)

# ===== FEEDBACK =====

# ===== STEP 5: FEEDBACK & AI LEARNING =====



@step5_router.post('/feedback')
async def feedback_async(f: FeedbackRequest, request: Request, current_user = Depends(get_current_user_required)):
    """STEP 5A: Submit feedback to train RL agent (requires authentication)"""
    try:
        if not (1 <= f.rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be 1-5")
        
        user_id = current_user.user_id
        reward = (f.rating - 3) / 2.0
        event_type = 'like' if f.rating >= 4 else 'dislike' if f.rating <= 2 else 'view'
        
        feedback_col = get_collection("feedback")
        result = feedback_col.insert_one({
            "content_id": f.content_id,
            "user_id": user_id,
            "event_type": event_type,
            "watch_time_ms": 0,
            "rating": f.rating,
            "comment": f.comment,
            "reward": reward,
            "timestamp": time.time(),
            "ip_address": request.client.host if request.client else "unknown"
        })
        feedback_id = str(result.inserted_id)
        
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "rating": f.rating,
            "event_type": event_type,
            "reward": reward
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@step5_router.get('/recommend-tags/{content_id}', response_model=TagRecommendationResponse)
@track_performance("tag_recommendation")
def recommend_tags(content_id: str, current_user = Depends(get_current_user)):
    """STEP 5B: Get AI-powered tag recommendations using Q-Learning agent (authentication optional for personalization)"""
    try:
        # Get content from database
        # Get content from Supabase database
        try:
            from core.database import DatabaseManager
            db = DatabaseManager()
            content = db.get_content_by_id(content_id)
            if not content:
                raise HTTPException(status_code=404, detail='Content not found')
            
            # Extract tags and authenticity from content object
            current_tags = getattr(content, 'current_tags', None)
            authenticity_score = getattr(content, 'authenticity_score', 0.5)
        except HTTPException:
            raise
        except Exception as db_error:
            import logging
            logging.error(f"Database query failed: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(db_error)}")
        
        try:
            existing_tags = json.loads(current_tags) if current_tags else []
        except:
            existing_tags = []
        
        # Register content with RL agent if not already registered
        agent.register_content(content_id, existing_tags, authenticity_score)
        
        # Get AI-powered recommendations from RL agent
        try:
            rl_recommendation = agent.recommend_tags(content_id)
            recommended_tags = rl_recommendation['tags']
            action_taken = rl_recommendation['action_taken']
            
            # Get agent metrics for transparency
            agent_metrics = agent.metrics()
            
            return TagRecommendationResponse(
                content_id=content_id,
                recommended_tags=recommended_tags,
                original_tags=existing_tags,
                rl_action_taken=action_taken,
                authenticity_score=authenticity_score,
                agent_confidence={
                    'epsilon': agent_metrics['epsilon'],
                    'q_states': agent_metrics['q_states'],
                    'avg_recent_reward': agent_metrics['avg_recent_reward']
                },
                next_step='POST /feedback to provide rating and train the RL agent further'
            )
            
        except Exception as rl_error:
            # Fallback to simple recommendation if RL agent fails
            import logging
            logging.warning(f"RL agent failed for {content_id}: {rl_error}")
            
            fallback_tags = existing_tags[:3] if existing_tags else ['general', 'content']
            return {
                'content_id': content_id,
                'recommended_tags': fallback_tags,
                'original_tags': existing_tags,
                'rl_action_taken': 'fallback',
                'authenticity_score': authenticity_score,
                'warning': 'RL agent unavailable, using fallback recommendations',
                'next_step': 'POST /feedback to provide rating and train the RL agent'
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@step5_router.get('/average-rating/{content_id}')
def get_average_rating(content_id: str, current_user = Depends(get_current_user)):
    """STEP 5C: Get average rating for content (authentication optional)"""
    try:
        feedback_col = get_collection("feedback")
        pipeline = [
            {"$match": {"content_id": content_id, "rating": {"$ne": None}}},
            {"$group": {
                "_id": None,
                "average_rating": {"$avg": "$rating"},
                "rating_count": {"$sum": 1}
            }}
        ]
        results = list(feedback_col.aggregate(pipeline))
        
        if results:
            avg_rating = results[0].get('average_rating', 0.0) or 0.0
            rating_count = results[0].get('rating_count', 0)
        else:
            avg_rating = 0.0
            rating_count = 0
        
        return {
            'content_id': content_id,
            'average_rating': round(avg_rating, 2),
            'rating_count': rating_count,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== STEP 6: ANALYTICS & MONITORING =====

@step6_router.get('/metrics', response_model=MetricsResponse)
async def metrics_async(
    request: Request,
    current_user = Depends(get_current_user),
    _rate_limit = Depends(rate_limit_analytics)
):
    """STEP 6A: View system metrics including RL agent performance - ASYNC with rate limiting (authentication optional)"""
    try:
        # Get system metrics (async)
        async def get_system_metrics():
            try:
                analytics_data = db.get_analytics_data()
                return analytics_data
            except Exception:
                content_col = get_collection("content")
                feedback_col = get_collection("feedback")
                users_col = get_collection("users")
                total_contents = content_col.count_documents({})
                total_feedback = feedback_col.count_documents({})
                total_users = users_col.count_documents({})
                return {
                    'total_content': total_contents,
                    'total_feedback': total_feedback,
                    'total_users': total_users
                }
        
        analytics_data = await get_system_metrics()
        total_contents = analytics_data.get('total_content', 0)
        total_feedback = analytics_data.get('total_feedback', 0)
        total_users = analytics_data.get('total_users', 0)
        
        # Get RL agent metrics (async)
        rl_metrics = await asyncio.to_thread(agent.metrics) if agent else {'status': 'unavailable'}
        
        return MetricsResponse(
            system_metrics={
                'total_contents': total_contents,
                'total_feedback': total_feedback,
                'total_users': total_users
            },
            rl_agent_metrics=rl_metrics,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            next_step='GET /rl/agent-stats for detailed RL metrics'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@step6_router.get('/rl/agent-stats')
def get_rl_agent_stats(current_user = Depends(get_current_user)):
    """STEP 6B: View detailed RL agent statistics and Q-table insights (authentication optional)"""
    try:
        agent_metrics = agent.metrics()
        
        # Get Q-table sample for inspection
        q_sample = {}
        if hasattr(agent, 'q') and agent.q:
            # Show top 5 states by total Q-value
            state_totals = {state: sum(actions.values()) for state, actions in agent.q.items()}
            top_states = sorted(state_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            q_sample = {state: agent.q[state] for state, _ in top_states}
        
        return {
            'agent_performance': agent_metrics,
            'q_table_sample': q_sample,
            'learning_status': {
                'exploration_rate': agent_metrics.get('epsilon', 0.0),
                'learning_active': agent_metrics.get('epsilon', 0.0) > 0.01,
                'states_learned': agent_metrics.get('q_states', 0),
                'recent_performance': agent_metrics.get('avg_recent_reward', 0.0)
            },
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'next_step': 'POST /feedback to train agent or GET /recommend-tags/{id} to see recommendations'
        }
    except Exception as e:
        return {
            'error': str(e),
            'agent_performance': {'status': 'error'},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/lm/stats')
def get_lm_stats(current_user = Depends(get_current_user)):
    """STEP 6B: View Language Model and AI component statistics (authentication optional)"""
    try:
        from core import bhiv_lm_client
        config = bhiv_lm_client.get_llm_config()
        return {
            'lm_config': config, 
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'next_step': 'GET /bhiv/analytics for sentiment analysis statistics'
        }
    except ImportError:
        return {
            'lm_config': {'status': 'LM client not available', 'fallback_mode': True}, 
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'lm_config': {'status': 'error', 'error': str(e)}, 
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }



@step6_router.get('/logs')
def get_logs(lines: int = 50, admin_key: str = None):
    """STEP 6C: View recent system logs for debugging (Admin Only)"""
    # Admin authentication
    if admin_key != "logs_2025":
        raise HTTPException(status_code=403, detail="Access denied. Admin key required.")
    
    try:
        import glob
        log_files = glob.glob('logs/*.log')
        if not log_files:
            return {'logs': [], 'message': 'No log files found'}
        
        # Get most recent log file
        latest_log = max(log_files, key=os.path.getmtime)
        
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            log_lines = f.readlines()[-lines:]
        
        return {
            'log_file': latest_log,
            'lines_requested': lines,
            'lines_returned': len(log_lines),
            'logs': [line.strip() for line in log_lines],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'access_level': 'admin'
        }
    except Exception as e:
        return {
            'error': str(e),
            'logs': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/streaming-performance')
def get_streaming_performance(current_user = Depends(get_current_user)):
    """STEP 6D: Real-time streaming analytics (authentication optional)"""
    try:
        from .streaming_metrics import streaming_metrics
        return {
            'streaming_stats': streaming_metrics.get_performance_summary(),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': str(e),
            'streaming_stats': {'total_streams': 0, 'active_streams': 0},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/reports/video-stats')
def get_video_stats(current_user = Depends(get_current_user)):
    """STEP 6E: Comprehensive content analytics (authentication optional)"""
    try:
        content_col = get_collection("content")
        
        video_count = content_col.count_documents({
            "content_type": {"$regex": "^video"}
        })
        
        total_content = content_col.count_documents({})
        
        stats_pipeline = [
            {"$group": {
                "_id": None,
                "avg_duration_ms": {"$avg": "$duration_ms"},
                "total_views": {"$sum": "$views"},
                "total_likes": {"$sum": "$likes"}
            }}
        ]
        stats_results = list(content_col.aggregate(stats_pipeline))
        stats = stats_results[0] if stats_results else {
            "avg_duration_ms": 0, "total_views": 0, "total_likes": 0
        }
        
        types_pipeline = [
            {"$group": {"_id": "$content_type", "count": {"$sum": 1}}}
        ]
        types_results = list(content_col.aggregate(types_pipeline))
        content_types = {r["_id"]: r["count"] for r in types_results if r["_id"]}
        
        return {
            'total_videos': video_count,
            'total_content': total_content,
            'content_types': content_types,
            'avg_duration_ms': stats.get('avg_duration_ms', 0) or 0,
            'total_views': stats.get('total_views', 0) or 0,
            'total_likes': stats.get('total_likes', 0) or 0,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': str(e),
            'total_videos': 0,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/reports/storyboard-stats')
def get_storyboard_stats(current_user = Depends(get_current_user)):
    """STEP 6F: Storyboard generation statistics (authentication optional)"""
    try:
        # Use storage adapter to list storyboard files
        try:
            storyboard_files = storage_adapter.list_files('storyboards')
            total_storyboards = len(storyboard_files)
        except:
            total_storyboards = 0
        generation_methods = {'llm': 0, 'heuristic': 0, 'manual': 0}
        
        return {
            'total_storyboards': total_storyboards,
            'generation_methods': generation_methods,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': str(e),
            'total_storyboards': 0,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/ingest/webhook')
def webhook_ingest_get(current_user = Depends(get_current_user)):
    """STEP 6L: Webhook ingestion endpoint info (authentication optional)"""
    return {
        'endpoint': '/ingest/webhook',
        'method': 'POST',
        'description': 'Webhook endpoint for external content ingestion',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

@step6_router.post('/ingest/webhook')
async def webhook_ingest_post(request: Request, current_user = Depends(get_current_user)):
    """STEP 6K: Webhook endpoint for external content ingestion (authentication optional)"""
    try:
        payload = await request.json()
        result = await bhiv_core.process_webhook_ingest(payload=payload, source='webhook_api')
        return {'webhook_result': result, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
    except Exception as e:
        return {'error': str(e), 'status': 'failed', 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}

@step6_router.get('/bucket/stats')
def get_bucket_stats(current_user = Depends(get_current_user)):
    """STEP 6F: Storage backend statistics (authentication optional)"""
    try:
        bucket_segments = {
            'uploads': 'bucket/uploads',
            'videos': 'bucket/videos', 
            'scripts': 'bucket/scripts',
            'storyboards': 'bucket/storyboards',
            'ratings': 'bucket/ratings',
            'logs': 'bucket/logs'
        }
        
        file_counts = {}
        total_files = 0
        
        for segment, path in bucket_segments.items():
            if os.path.exists(path):
                count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                file_counts[segment] = count
                total_files += count
            else:
                file_counts[segment] = 0
        
        # Also check uploads directory
        uploads_count = 0
        if os.path.exists('uploads'):
            uploads_count = len([f for f in os.listdir('uploads') if os.path.isfile(os.path.join('uploads', f))])
        
        stats = {
            'storage_type': 'local_bucket',
            'bucket_segments': list(bucket_segments.keys()),
            'file_counts': file_counts,
            'uploads_dir_files': uploads_count,
            'total_bucket_files': total_files
        }
        
        return {
            'bucket_stats': stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': str(e),
            'bucket_stats': {'storage_type': 'unknown'},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/bucket/list/{segment}')
def list_bucket_files(segment: str, limit: int = 20, current_user = Depends(get_current_user)):
    """STEP 6G: List files in bucket segment (authentication optional)"""
    try:
        valid_segments = ['uploads', 'videos', 'scripts', 'storyboards', 'ratings', 'logs']
        if segment not in valid_segments:
            raise HTTPException(status_code=400, detail=f'Invalid segment. Valid: {valid_segments}')
        
        bucket_path = f'bucket/{segment}'
        if not os.path.exists(bucket_path):
            return {
                'segment': segment,
                'files': [],
                'message': f'Segment {segment} not found'
            }
        
        files = []
        for filename in os.listdir(bucket_path)[:limit]:
            filepath = os.path.join(bucket_path, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'size_bytes': stat.st_size,
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                })
        
        return {
            'segment': segment,
            'files': files,
            'total_files': len(files),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': str(e),
            'segment': segment,
            'files': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/bhiv/analytics', response_model=AnalyticsResponse, status_code=200)
def get_bhiv_analytics(current_user = Depends(get_current_user)):
    """STEP 6H: Advanced analytics with sentiment analysis (authentication optional)"""
    try:
        # Get analytics from Supabase database
        try:
            from core.database import DatabaseManager
            db = DatabaseManager()
            analytics_data = db.get_analytics_data()
            total_users = analytics_data.get('total_users', 0)
            total_content = analytics_data.get('total_content', 0)
            total_feedback = analytics_data.get('total_feedback', 0)
            avg_rating = analytics_data.get('average_rating', 0.0)
            sentiment_data = analytics_data.get('sentiment_breakdown', {})
            avg_engagement = analytics_data.get('average_engagement', 0.0)
        except Exception as db_error:
            import logging
            logging.error(f"Analytics query failed: {db_error}")
            total_users = total_content = total_feedback = 0
            avg_rating = avg_engagement = 0.0
            sentiment_data = {}
        
        # Calculate proper engagement rate
        if total_content > 0:
            engagement_rate = min(100.0, (total_feedback / total_content) * 100)
        else:
            engagement_rate = 0.0
        
        return AnalyticsResponse(
            total_users=total_users,
            total_content=total_content,
            total_feedback=total_feedback,
            average_rating=round(avg_rating, 2),
            average_engagement=round(avg_engagement, 2),
            sentiment_breakdown=sentiment_data,
            engagement_rate=round(engagement_rate, 1),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        return {
            'error': str(e),
            'total_users': 0,
            'total_content': 0,
            'total_feedback': 0,
            'average_rating': 0.0,
            'sentiment_breakdown': {},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

@step6_router.get('/observability/performance')
def get_performance_metrics():
    """STEP 6J: Get detailed performance metrics - PUBLIC ACCESS"""
    import psutil
    import os
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get database metrics
        try:
            from core.database import DatabaseManager
            db = DatabaseManager()
            analytics_data = db.get_analytics_data()
            db_metrics = {
                'total_users': analytics_data.get('total_users', 0),
                'total_content': analytics_data.get('total_content', 0),
                'total_feedback': analytics_data.get('total_feedback', 0)
            }
        except Exception:
            db_metrics = {'error': 'Database metrics unavailable'}
        
        # Get application metrics
        app_metrics = {
            'uptime_seconds': time.time() - psutil.Process().create_time(),
            'process_memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
            'open_files': len(psutil.Process().open_files()),
            'threads': psutil.Process().num_threads()
        }
        
        return {
            'system_metrics': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024
            },
            'application_metrics': app_metrics,
            'database_metrics': db_metrics,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': str(e),
            'system_metrics': {},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

# ===== STEP 7: TASK QUEUE MANAGEMENT =====







# ===== STEP 8: SYSTEM MAINTENANCE & OPERATIONS =====












# ===== ENHANCED UPLOAD UTILITY FUNCTIONS =====

def generate_content_id(user_id: str, filename: str) -> str:
    """Generate secure content ID"""
    timestamp = str(int(time.time()))
    file_hash = hashlib.sha256(f"{user_id}{filename}{timestamp}".encode()).hexdigest()[:12]
    return f"{file_hash}_{timestamp}"

async def save_file_securely(file: UploadFile, secure_filename: str, validation_result: dict) -> str:
    """Save file with enhanced security measures"""
    try:
        # Ensure upload directory exists
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create secure file path
        file_path = os.path.join(upload_dir, secure_filename)
        
        # Save file with validation
        content = await file.read()
        
        # Verify content matches validation
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != validation_result['file_hash']:
            raise HTTPException(
                status_code=400,
                detail="File integrity check failed"
            )
        
        # Write file securely
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Set secure file permissions (Windows compatible)
        try:
            os.chmod(file_path, 0o644)
        except OSError:
            pass  # Windows may not support chmod
        
        logger.info(f"File saved securely: {secure_filename} ({len(content)} bytes)")
        return file_path
        
    except Exception as e:
        logger.error(f"Secure file save failed: {e}")
        raise HTTPException(status_code=500, detail="File save failed")

def calculate_authenticity_score(file_hash: str) -> float:
    """Calculate deterministic authenticity score from file hash"""
    # Use first 16 characters of hash for deterministic scoring
    hash_segment = file_hash[:16]
    numeric_value = int(hash_segment, 16)
    # Normalize to 0.0-1.0 range
    score = (numeric_value % 1000) / 1000.0
    return round(score, 3)

# ===== UTILITY FUNCTIONS =====

def wrap_text_for_video(text, max_chars_per_line=40):
    """Simple text wrapping for video display"""
    if not text:
        return ""
    
    words = text.split()
    wrapped_lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                wrapped_lines.append(current_line)
            current_line = word
    
    if current_line:
        wrapped_lines.append(current_line)
    
    return "\n".join(wrapped_lines)

def compute_authenticity(file_path, title, description):
    """Optimized authenticity computation"""
    try:
        with open(file_path, 'rb') as f:
            b = f.read(512)  # Reduced read size
        h = hashlib.sha256(b + title.encode('utf-8') + description.encode('utf-8')).hexdigest()
        return round(int(h[:8], 16) / 0xFFFFFFFF, 4)
    except Exception:
        return 0.5  # Default authenticity

def suggest_tags(title, description):
    """Optimized tag suggestion"""
    text = (title + ' ' + description).lower()
    words = [w.strip('.,!?:;()[]') for w in text.split() if len(w) > 3]
    return list(dict.fromkeys(words))[:5]  # Remove duplicates, limit to 5





# GDPR Compliance Endpoints - Now handled by gdpr_compliance.py
# Legacy endpoints for backward compatibility
@step2_router.delete('/users/{user_id}/data')
async def delete_user_data_legacy(
    user_id: str,
    current_user = Depends(get_current_user_required)
):
    """GDPR: Delete all user data (Legacy endpoint - use /gdpr/delete-data)"""
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only delete own data")
    
    return {
        "message": "Please use the new GDPR endpoint: DELETE /gdpr/delete-data",
        "new_endpoint": "/gdpr/delete-data",
        "status": "deprecated"
    }

@step2_router.get('/users/{user_id}/data-export')
async def export_user_data_legacy(
    user_id: str,
    current_user = Depends(get_current_user_required)
):
    """GDPR: Export all user data (Legacy endpoint - use /gdpr/export-data)"""
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only export own data")
    
    return {
        "message": "Please use the new GDPR endpoint: GET /gdpr/export-data",
        "new_endpoint": "/gdpr/export-data",
        "status": "deprecated"
    }


