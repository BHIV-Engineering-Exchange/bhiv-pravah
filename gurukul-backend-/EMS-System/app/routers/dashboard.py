from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.dependencies import get_current_super_admin
from app.models import School, User, UserRole
from app.schemas import UserDashboardResponse
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_schools: int
    total_admins: int
    total_users: int
    total_teachers: int
    total_students: int
    total_parents: int


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Get dashboard statistics.
    Only SUPER_ADMIN can view statistics.
    """
    total_schools = db.query(func.count(School.id)).scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar() or 0
    total_teachers = db.query(func.count(User.id)).filter(User.role == UserRole.TEACHER).scalar() or 0
    total_students = db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0
    total_parents = db.query(func.count(User.id)).filter(User.role == UserRole.PARENT).scalar() or 0
    # Total users excludes SUPER_ADMIN (only counts regular users: ADMIN, TEACHER, STUDENT, PARENT)
    total_users = db.query(func.count(User.id)).filter(User.role != UserRole.SUPER_ADMIN).scalar() or 0
    
    return DashboardStats(
        total_schools=total_schools,
        total_admins=total_admins,
        total_users=total_users,
        total_teachers=total_teachers,
        total_students=total_students,
        total_parents=total_parents
    )


@router.get("/users", response_model=List[UserDashboardResponse])
def get_all_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    school_id: Optional[int] = Query(None, description="Filter by school ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Get all users with optional search and filters.
    Only SUPER_ADMIN can view all users.
    """
    query = db.query(User)
    
    # Filter by role
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
    
    # Filter by school
    if school_id:
        query = query.filter(User.school_id == school_id)
    
    # Search filter
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    users = query.all()
    return users


@router.get("/users/{user_id}", response_model=UserDashboardResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Get a specific user by ID.
    Only SUPER_ADMIN can view user details.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user
