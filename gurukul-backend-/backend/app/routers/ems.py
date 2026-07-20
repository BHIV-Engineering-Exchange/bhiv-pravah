from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.all_models import User, Tenant, Cohort, Flashcard, Summary, Reflection, StudentProgress
from app.schemas.ems import (
    TenantCreate, TenantResponse, UserCreateAdmin, UserUpdateAdmin, UserResponse,
    CohortCreate, CohortResponse, ProvisionTenantRequest, ProvisionTenantResponse,
)
import uuid
import re

router = APIRouter()


def _verify_ems_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verify API key for server-to-server calls from EMS. If EMS_API_KEY is set, key is required."""
    if getattr(settings, "EMS_API_KEY", None):
        if x_api_key != settings.EMS_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


# --- EMS → Gurukul: Provision tenant when EMS creates a school (multi-tenant wiring) ---

@router.post("/provision-tenant", response_model=ProvisionTenantResponse, status_code=status.HTTP_201_CREATED)
async def provision_tenant_from_ems(
    body: ProvisionTenantRequest,
    _: bool = Depends(_verify_ems_api_key),
):
    """
    Called by EMS when super admin creates a new school. Creates a row in Gurukul central
    tenant_registry so this school gets its own tenant (and DB) in Gurukul. Same concept:
    one school in EMS = one tenant in Gurukul.
    """
    from app.core.central_registry import get_central_db, TenantRegistry, create_central_tables

    from app.core.tenant_db_provisioner import create_tenant_database_and_schema

    create_central_tables()
    tenant_id = str(uuid.uuid4())
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", body.subdomain_slug).strip("_") or "school"
    database_url = body.database_url
    if not database_url:
        base_url = getattr(settings, "CENTRAL_DATABASE_URL", None) or settings.DATABASE_URL
        if base_url and "/" in base_url:
            parts = base_url.rstrip("/").rsplit("/", 1)
            if len(parts) == 2:
                database_url = f"{parts[0]}/gurukul_tenant_{slug}"
            else:
                database_url = base_url
        else:
            raise HTTPException(status_code=400, detail="database_url required when CENTRAL_DATABASE_URL is not set")
    with get_central_db() as db:
        if db is None:
            raise HTTPException(status_code=503, detail="Central tenant registry not configured")
        existing = db.query(TenantRegistry).filter(TenantRegistry.subdomain_slug == slug).first()
        if existing:
            return ProvisionTenantResponse(
                tenant_id=existing.id,
                subdomain_slug=existing.subdomain_slug or slug,
                message="Tenant already exists for this subdomain_slug",
            )

        # Create tenant PostgreSQL DB and apply app schema (DB-per-tenant). Done in Gurukul, not EMS.
        ok = create_tenant_database_and_schema(database_url)
        if not ok:
            raise HTTPException(
                status_code=503,
                detail="Tenant database creation or schema failed. Check backend logs and that DB user can CREATE DATABASE.",
            )

        row = TenantRegistry(
            id=tenant_id,
            name=body.name,
            type="INSTITUTION",
            database_url=database_url,
            subdomain_slug=slug,
        )
        db.add(row)
        db.commit()
    return ProvisionTenantResponse(
        tenant_id=tenant_id,
        subdomain_slug=slug,
        message="Tenant provisioned: database created and schema applied. Use X-Tenant-ID or subdomain to route.",
    )


# --- Admin Endpoints ---

@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Create a new School/Institution (Tenant)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can create tenants")
    
    new_tenant = Tenant(
        name=tenant.name,
        type=tenant.type
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return new_tenant

@router.post("/cohorts", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
async def create_cohort(
    cohort: CohortCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Create a Cohort (Class) within a Tenant"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can create cohorts")
    
    # Verify tenant exists
    if not db.query(Tenant).filter(Tenant.id == cohort.tenant_id).first():
        raise HTTPException(status_code=404, detail="Tenant not found")

    new_cohort = Cohort(
        name=cohort.name,
        tenant_id=cohort.tenant_id
    )
    db.add(new_cohort)
    db.commit()
    db.refresh(new_cohort)
    return new_cohort

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_within_tenant(
    user_in: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Add a User (Teacher/Student) to a Tenant"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can create users")

    # Check if email exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_in.password)
    
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role.upper(), # Ensure uppercase
        tenant_id=user_in.tenant_id,
        cohort_id=user_in.cohort_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users", response_model=List[UserResponse])
async def get_users_in_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: List all users in the tenant"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can list users")
    
    # For now, return all users (can filter by tenant later if needed)
    users = db.query(User).all()
    return users

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Update user details"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can update users")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(User.email == user_update.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_update.email
    if user_update.role is not None:
        user.role = user_update.role.upper()
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Delete a user"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can delete users")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete related records (same as in auth.py delete-account)
    from app.models.all_models import Profile, Summary, Flashcard, Reflection, StudentProgress
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile:
        db.delete(profile)
    
    summaries = db.query(Summary).filter(Summary.user_id == user_id).all()
    for summary in summaries:
        db.delete(summary)
    
    flashcards = db.query(Flashcard).filter(Flashcard.user_id == user_id).all()
    for flashcard in flashcards:
        db.delete(flashcard)
    
    reflections = db.query(Reflection).filter(Reflection.user_id == user_id).all()
    for reflection in reflections:
        db.delete(reflection)
    
    student_progress = db.query(StudentProgress).filter(StudentProgress.user_id == user_id).all()
    for progress in student_progress:
        db.delete(progress)
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully", "success": True}

# --- Teacher Endpoints ---

@router.get("/students/{student_id}/progress")
async def get_student_progress(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Teacher: View a specific Student's progress"""
    # Authorization: Admin or Teacher (in same tenant)
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role == "STUDENT":
        # Student can only view their own
        if current_user.id != student_id:
             raise HTTPException(status_code=403, detail="Cannot view other student's progress")
    elif current_user.role == "TEACHER":
         # Check tenant match
         if current_user.tenant_id and current_user.tenant_id != student.tenant_id:
             raise HTTPException(status_code=403, detail="Cannot view student from another institution")
    
    # Calculate Stats
    topics_count = db.query(Summary).filter(Summary.user_id == student_id).count()
    flashcards_count = db.query(Flashcard).filter(Flashcard.user_id == student_id).count()
    completed_milestones = db.query(StudentProgress).filter(
        StudentProgress.user_id == student_id, 
        StudentProgress.status == "COMPLETED"
    ).count()

    return {
        "studentName": student.full_name,
        "topicsStudied": topics_count,
        "flashcardsCreated": flashcards_count,
        "milestonesCompleted": completed_milestones,
        "lastActivity": "Today" # Placeholder
    }

# --- Dashboard Hooks (Restored for Frontend Compatibility) ---
# --- Dashboard Hooks (Restored for Frontend Compatibility) ---
@router.get("/dashboard/stats")
async def get_my_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get MY progress (Student View)"""
    return await get_student_progress(current_user.id, db, current_user)

@router.get("/admin/stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get System Stats for Admin Dashboard"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can view system stats")
        
    # Scope to tenant if tenant_id is set, else global?
    # Assuming Admin sees stats for their Tenant.
    
    base_query = db.query(User)
    if current_user.tenant_id:
        base_query = base_query.filter(User.tenant_id == current_user.tenant_id)
        
    total_users = base_query.count()
    active_users = base_query.filter(User.is_active == True).count()
    total_teachers = base_query.filter(User.role == "TEACHER").count()
    total_students = base_query.filter(User.role == "STUDENT").count()
    total_parents = base_query.filter(User.role == "PARENT").count()
    
    return {
        "totalUsers": total_users,
        "activeUsers": active_users,
        "totalTeachers": total_teachers,
        "totalStudents": total_students,
        "totalParents": total_parents,
        "systemHealth": "Healthy",
        "apiStatus": "Operational"
    }

@router.get("/admin/analytics")
async def get_admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics for Admin Reports & Analytics"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Admins can view analytics")
    
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func, extract
    
    # Base query filter by tenant if applicable
    base_user_query = db.query(User)
    if current_user.tenant_id:
        base_user_query = base_user_query.filter(User.tenant_id == current_user.tenant_id)
        user_ids = [u.id for u in base_user_query.all()]
    else:
        user_ids = None
    
    # User Statistics
    total_users = base_user_query.count()
    active_users = base_user_query.filter(User.is_active == True).count()
    total_students = base_user_query.filter(User.role == "STUDENT").count()
    total_teachers = base_user_query.filter(User.role == "TEACHER").count()
    total_parents = base_user_query.filter(User.role == "PARENT").count()
    
    # Learning Activity Statistics
    summaries_query = db.query(Summary)
    flashcards_query = db.query(Flashcard)
    reflections_query = db.query(Reflection)
    progress_query = db.query(StudentProgress)
    
    if user_ids:
        summaries_query = summaries_query.filter(Summary.user_id.in_(user_ids))
        flashcards_query = flashcards_query.filter(Flashcard.user_id.in_(user_ids))
        reflections_query = reflections_query.filter(Reflection.user_id.in_(user_ids))
        progress_query = progress_query.filter(StudentProgress.user_id.in_(user_ids))
    
    total_summaries = summaries_query.count()
    total_flashcards = flashcards_query.count()
    total_reflections = reflections_query.count()
    completed_milestones = progress_query.filter(StudentProgress.status == "COMPLETED").count()
    
    # Time-based statistics (last 30 days)
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # New users in last 30 days
    new_users_30d = base_user_query.filter(User.created_at >= thirty_days_ago).count()
    new_users_7d = base_user_query.filter(User.created_at >= seven_days_ago).count()
    
    # Activity in last 30 days
    summaries_30d = summaries_query.filter(Summary.created_at >= thirty_days_ago).count()
    flashcards_30d = flashcards_query.filter(Flashcard.created_at >= thirty_days_ago).count()
    reflections_30d = reflections_query.filter(Reflection.created_at >= thirty_days_ago).count()
    
    # User growth over time (last 7 days, daily)
    daily_user_growth = []
    for i in range(7):
        day_start = now - timedelta(days=6-i)
        day_end = day_start + timedelta(days=1)
        count = base_user_query.filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()
        daily_user_growth.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    
    # Activity over time (last 7 days)
    daily_activity = []
    for i in range(7):
        day_start = now - timedelta(days=6-i)
        day_end = day_start + timedelta(days=1)
        summaries_count = summaries_query.filter(
            Summary.created_at >= day_start,
            Summary.created_at < day_end
        ).count()
        flashcards_count = flashcards_query.filter(
            Flashcard.created_at >= day_start,
            Flashcard.created_at < day_end
        ).count()
        daily_activity.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "summaries": summaries_count,
            "flashcards": flashcards_count,
            "reflections": reflections_query.filter(
                Reflection.created_at >= day_start,
                Reflection.created_at < day_end
            ).count()
        })
    
    # Most active users (top 5 by summaries + flashcards)
    active_users_query = db.query(
        User.id,
        User.full_name,
        User.email,
        User.role,
        func.count(Summary.id).label('summary_count'),
        func.count(Flashcard.id).label('flashcard_count')
    ).outerjoin(Summary, User.id == Summary.user_id)\
     .outerjoin(Flashcard, User.id == Flashcard.user_id)
    
    # Apply tenant filter if applicable
    if current_user.tenant_id:
        active_users_query = active_users_query.filter(User.tenant_id == current_user.tenant_id)
    
    active_users_query = active_users_query.group_by(User.id)\
     .order_by((func.count(Summary.id) + func.count(Flashcard.id)).desc())\
     .limit(5).all()
    
    most_active_users = [{
        "id": u.id,
        "name": u.full_name or u.email,
        "email": u.email,
        "role": u.role,
        "summaryCount": u.summary_count or 0,
        "flashcardCount": u.flashcard_count or 0,
        "totalActivity": (u.summary_count or 0) + (u.flashcard_count or 0)
    } for u in active_users_query]
    
    # Role distribution
    role_distribution = {
        "STUDENT": total_students,
        "TEACHER": total_teachers,
        "PARENT": total_parents,
        "ADMIN": base_user_query.filter(User.role == "ADMIN").count()
    }
    
    return {
        "userStats": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
            "students": total_students,
            "teachers": total_teachers,
            "parents": total_parents,
            "newUsers30d": new_users_30d,
            "newUsers7d": new_users_7d
        },
        "learningStats": {
            "totalSummaries": total_summaries,
            "totalFlashcards": total_flashcards,
            "totalReflections": total_reflections,
            "completedMilestones": completed_milestones,
            "summaries30d": summaries_30d,
            "flashcards30d": flashcards_30d,
            "reflections30d": reflections_30d
        },
        "dailyUserGrowth": daily_user_growth,
        "dailyActivity": daily_activity,
        "mostActiveUsers": most_active_users,
        "roleDistribution": role_distribution,
        "generatedAt": now.isoformat()
    }


