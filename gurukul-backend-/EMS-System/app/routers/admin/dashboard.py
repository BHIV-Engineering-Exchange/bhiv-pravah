"""
School Admin Dashboard API endpoints.
All endpoints are filtered by school_id to ensure data isolation.
"""

import asyncio
from typing import List, Optional
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database import get_db
from app.dependencies import get_current_admin
from app.config import settings
from app.services.gurukul_sync import sync_student_to_gurukul
from app.models import (
    User, UserRole, School, Subject, Class, ClassStudent,
    StudentParent, Lesson, Lecture, TimetableSlot,
    Holiday, Event, Announcement,
    StudentSummary, StudentFlashcard, StudentTestResult, StudentSubjectData
)
from app.schemas import (
    TeacherCreate, TeacherResponse, TeacherUpdate,
    StudentCreate, StudentResponse, StudentUpdate,
    ParentCreate, ParentResponse, ParentUpdate, ExcelUploadResponse,
    SubjectCreate, SubjectResponse, ClassCreate, ClassResponse,
    TimetableSlotCreate, TimetableSlotResponse,
    HolidayCreate, HolidayResponse, HolidayUpdate,
    EventCreate, EventResponse, EventUpdate,
    AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate, DashboardStatsResponse,
    StudentParentLinkCreate, StudentParentLinkResponse,
    StudentWithParentsResponse, ParentWithStudentsResponse,
    ParentStudentStatsResponse,
    AnalyticsResponse, TeacherWorkloadResponse, GradeDistributionResponse,
    SubjectDistributionResponse, ParentStudentRelationResponse,
    StudentSummarySync, StudentFlashcardSync, StudentTestResultSync,
    StudentSubjectDataSync, StudentContentSyncResponse,
    StudentSummaryResponse, StudentFlashcardResponse,
    StudentTestResultResponse, StudentSubjectDataResponse
)
from app.utils.password_generator import generate_unique_password
from app.utils.excel_upload import upload_teachers_excel, upload_students_excel, upload_parents_excel
from app.utils.excel_upload_combined import upload_students_parents_combined_excel
from app.auth import get_password_hash
from app.email_service import send_login_credentials_email

router = APIRouter(prefix="/admin", tags=["school-admin"])


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get dashboard statistics for School Admin."""
    try:
        school_id = current_user.school_id
        
        # Count teachers
        total_teachers = db.query(User).filter(
            User.school_id == school_id,
            User.role == UserRole.TEACHER,
            User.is_active == True
        ).count()
        
        # Count students
        total_students = db.query(User).filter(
            User.school_id == school_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        ).count()
        
        # Count parents
        total_parents = db.query(User).filter(
            User.school_id == school_id,
            User.role == UserRole.PARENT,
            User.is_active == True
        ).count()
        
        # Count classes (handle case where table might not exist)
        try:
            total_classes = db.query(Class).filter(Class.school_id == school_id).count()
        except Exception:
            total_classes = 0
        
        # Count lessons (handle case where table might not exist)
        try:
            total_lessons = db.query(Lesson).filter(Lesson.school_id == school_id).count()
        except Exception:
            total_lessons = 0
        
        # Today's classes (classes with lessons today)
        today = date.today()
        try:
            todays_classes = db.query(Lesson).filter(
                Lesson.school_id == school_id,
                Lesson.lesson_date == today
            ).count()
        except Exception:
            todays_classes = 0
        
        # Upcoming holidays (next 30 days)
        try:
            upcoming_holidays = db.query(Holiday).filter(
                Holiday.school_id == school_id,
                Holiday.start_date >= today,
                Holiday.start_date <= date.today().replace(day=1) if date.today().month < 12 else date.today().replace(year=date.today().year + 1, month=1, day=1)
            ).count()
        except Exception:
            upcoming_holidays = 0
        
        # Upcoming events (next 30 days)
        try:
            upcoming_events = db.query(Event).filter(
                Event.school_id == school_id,
                Event.event_date >= today,
                Event.event_date <= date.today().replace(day=1) if date.today().month < 12 else date.today().replace(year=date.today().year + 1, month=1, day=1)
            ).count()
        except Exception:
            upcoming_events = 0
        
        return DashboardStatsResponse(
            total_teachers=total_teachers,
            total_students=total_students,
            total_parents=total_parents,
            total_classes=total_classes,
            total_lessons=total_lessons,
            todays_classes=todays_classes,
            upcoming_holidays=upcoming_holidays,
            upcoming_events=upcoming_events
        )
    except Exception as e:
        print(f"Error in get_dashboard_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard statistics: {str(e)}"
        )


# ==================== TEACHERS MANAGEMENT ====================

@router.get("/teachers", response_model=List[TeacherResponse])
def get_teachers(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all teachers in the school."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.TEACHER,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    teachers = query.all()
    return [TeacherResponse(id=t.id, name=t.name, email=t.email, subject=t.subject, school_id=t.school_id) for t in teachers]


@router.post("/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new teacher."""
    try:
        school_id = current_user.school_id
        
        if school_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin account is not associated with a school"
            )
        
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == teacher_data.email
        ).first()
        
        if existing_user:
            # If user is active, email is taken
            if existing_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            # If user is inactive, we need to free up the email
            # Change the inactive user's email to make it unique
            inactive_email = f"{existing_user.email}_deleted_{existing_user.id}_{int(datetime.utcnow().timestamp())}"
            existing_user.email = inactive_email
            db.commit()
        
        # Generate unique password
        password = generate_unique_password(db, teacher_data.email, teacher_data.name, UserRole.TEACHER.value, school_id)
        hashed_password = get_password_hash(password)
        
        # Debug: Log password generation (remove in production)
        print(f"[TEACHER CREATION] Generated password for {teacher_data.email}: {password}")
        print(f"[TEACHER CREATION] Password hash length: {len(hashed_password)}")
        
        # Create teacher
        teacher = User(
            name=teacher_data.name,
            email=teacher_data.email,
            password=hashed_password,
            role=UserRole.TEACHER,
            school_id=school_id,
            is_active=True,  # Ensure user is active
            subject=teacher_data.subject
        )
        
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        # Verify password was stored correctly
        from app.auth import verify_password
        password_verified = verify_password(password, teacher.password)
        print(f"[TEACHER CREATION] Password verification test: {'PASSED' if password_verified else 'FAILED'}")
        
        # Send login credentials email
        try:
            await send_login_credentials_email(db, teacher, password, UserRole.TEACHER.value)
        except Exception as e:
            print(f"Warning: Failed to send email to {teacher.email}: {str(e)}")
        
        return TeacherResponse(id=teacher.id, name=teacher.name, email=teacher.email, subject=teacher_data.subject, school_id=teacher.school_id)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating teacher: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create teacher: {str(e)}"
        )


@router.post("/teachers/upload-excel", response_model=ExcelUploadResponse)
async def upload_teachers_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload teachers from Excel file."""
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_teachers_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} teachers created, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


@router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a teacher's information."""
    school_id = current_user.school_id
    
    # Get teacher
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found or does not belong to this school"
        )
    
    # Update fields if provided
    if teacher_data.name is not None:
        teacher.name = teacher_data.name
    
    if teacher_data.email is not None and teacher_data.email != teacher.email:
        # Check if new email already exists (only for active users)
        existing_user = db.query(User).filter(
            User.email == teacher_data.email,
            User.id != teacher_id,
            User.is_active == True
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        teacher.email = teacher_data.email
    
    if teacher_data.subject is not None:
        teacher.subject = teacher_data.subject
    
    db.commit()
    db.refresh(teacher)
    
    return TeacherResponse(
        id=teacher.id,
        name=teacher.name,
        email=teacher.email,
        subject=teacher.subject,
        school_id=teacher.school_id
    )


@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete (deactivate) a teacher."""
    school_id = current_user.school_id
    
    # Get teacher
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found or does not belong to this school"
        )
    
    print(f"[TEACHER DELETION] Deactivating teacher ID {teacher_id} for school {school_id}")
    # Soft delete: set is_active to False
    teacher.is_active = False
    try:
        db.commit()
        print(f"[TEACHER DELETION] Successfully deactivated teacher {teacher_id}")
    except Exception as e:
        db.rollback()
        print(f"[TEACHER DELETION] Failed to deactivate teacher {teacher_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete teacher: {str(e)}"
        )
    
    return None


# ==================== STUDENTS MANAGEMENT ====================

@router.get("/students", response_model=List[StudentResponse])
def get_students(
    search: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students in the school."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    students = query.all()
    result = []
    for s in students:
        # Get all linked parent emails and names for this student
        parent_links = db.query(StudentParent).filter(StudentParent.student_id == s.id).all()
        parent_emails = []
        parent_names = []
        for link in parent_links:
            parent = db.query(User).filter(User.id == link.parent_id).first()
            if parent and parent.is_active:
                parent_emails.append(parent.email)
                parent_names.append(parent.name)
        
        result.append(StudentResponse(
            id=s.id,
            name=s.name,
            email=s.email,
            grade=s.grade,
            school_id=s.school_id,
            parent_emails=parent_emails if parent_emails else None,
            parent_names=parent_names if parent_names else None
        ))
    return result


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new student."""
    school_id = current_user.school_id
    
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == student_data.email
    ).first()
    
    if existing_user:
        # If user is active, email is taken
        if existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        # If user is inactive, free up the email by changing the inactive user's email
        inactive_email = f"{existing_user.email}_deleted_{existing_user.id}_{int(datetime.utcnow().timestamp())}"
        existing_user.email = inactive_email
        db.commit()
    
    # Generate unique password
    password = generate_unique_password(db, student_data.email, student_data.name, UserRole.STUDENT.value, school_id)
    hashed_password = get_password_hash(password)
    
    # Debug: Log password generation (remove in production)
    print(f"[STUDENT CREATION] Generated password for {student_data.email}: {password}")
    print(f"[STUDENT CREATION] Password hash length: {len(hashed_password)}")
    
    # Create student
    student = User(
        name=student_data.name,
        email=student_data.email,
        password=hashed_password,
        role=UserRole.STUDENT,
        school_id=school_id,
        is_active=True,  # Ensure user is active
        grade=student_data.grade
    )
    
    db.add(student)
    db.flush()
    
    # Link to parent if provided
    if student_data.parent_email:
        # Check if parent exists (active or inactive)
        parent = db.query(User).filter(
            User.email == student_data.parent_email,
            User.role == UserRole.PARENT,
            User.school_id == school_id
        ).first()
        
        if not parent:
            # Parent doesn't exist, create it
            parent_name = student_data.parent_name if student_data.parent_name else "Parent"
            parent_password = generate_unique_password(db, student_data.parent_email, parent_name, UserRole.PARENT.value, school_id)
            parent_hashed_password = get_password_hash(parent_password)
            
            # Debug: Log password generation for parent
            print(f"[PARENT CREATION] Generated password for {student_data.parent_email}: {parent_password}")
            print(f"[PARENT CREATION] Password hash length: {len(parent_hashed_password)}")
            
            parent = User(
                name=parent_name,
                email=student_data.parent_email,
                password=parent_hashed_password,
                role=UserRole.PARENT,
                school_id=school_id,
                is_active=True  # Ensure user is active
            )
            db.add(parent)
            db.flush()
            
            # Verify password was stored correctly for parent
            from app.auth import verify_password
            parent_password_verified = verify_password(parent_password, parent.password)
            print(f"[PARENT CREATION] Password verification test: {'PASSED' if parent_password_verified else 'FAILED'}")
            
            # Send login credentials email to parent
            try:
                await send_login_credentials_email(db, parent, parent_password, UserRole.PARENT.value)
            except Exception as e:
                print(f"Warning: Failed to send email to {parent.email}: {str(e)}")
        else:
            # Parent exists - update name if provided and current name is default or empty
            if student_data.parent_name and student_data.parent_name.strip():
                # Update name if current name is default/empty or if we want to always update
                if not parent.name or parent.name.strip() == "" or parent.name == "Parent":
                    parent.name = student_data.parent_name.strip()
                    db.flush()
            
            if not parent.is_active:
                # Reactivate inactive parent
                parent.is_active = True
                db.flush()
        
        # Check if link already exists
        existing_link = db.query(StudentParent).filter(
            StudentParent.student_id == student.id,
            StudentParent.parent_id == parent.id
        ).first()
        
        if not existing_link:
            # Create the link
            student_parent = StudentParent(
                student_id=student.id,
                parent_id=parent.id,
                relationship_type="Parent"
            )
            db.add(student_parent)
    
    db.commit()
    db.refresh(student)
    
    # Verify password was stored correctly for student
    from app.auth import verify_password
    password_verified = verify_password(password, student.password)
    print(f"[STUDENT CREATION] Password verification test: {'PASSED' if password_verified else 'FAILED'}")
    
    # Send login credentials email
    try:
        await send_login_credentials_email(db, student, password, UserRole.STUDENT.value)
    except Exception as e:
        print(f"Warning: Failed to send email to {student.email}: {str(e)}")
    
    # Sync student to Gurukul so they can log in there too (fire-and-forget)
    if settings.GURUKUL_API_BASE_URL:
        asyncio.create_task(
            asyncio.to_thread(
                sync_student_to_gurukul,
                settings.GURUKUL_API_BASE_URL,
                student.email,
                password,
                student.name,
            )
        )
    
    # Get linked parent emails and names for response
    parent_links = db.query(StudentParent).filter(StudentParent.student_id == student.id).all()
    parent_emails = []
    parent_names = []
    for link in parent_links:
        parent = db.query(User).filter(User.id == link.parent_id).first()
        if parent and parent.is_active:
            parent_emails.append(parent.email)
            parent_names.append(parent.name)
    
    return StudentResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        grade=student_data.grade,
        school_id=student.school_id,
        parent_emails=parent_emails if parent_emails else None,
        parent_names=parent_names if parent_names else None
    )


@router.post("/students/{student_id}/reset-password")
async def reset_student_password(
    student_id: int,
    new_password: str = Body(..., embed=True, description="New password to set"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reset a student's password to a specific value.
    Useful when the password in the email doesn't match what's stored.
    """
    school_id = current_user.school_id
    
    # Get student
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT,
        User.school_id == school_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Validate password length
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash and set new password
    hashed_password = get_password_hash(new_password)
    student.password = hashed_password
    db.commit()
    db.refresh(student)
    
    return {
        "message": f"Password reset successfully for student {student.name} ({student.email})",
        "student_id": student.id,
        "student_email": student.email
    }


@router.post("/students/upload-excel", response_model=ExcelUploadResponse)
async def upload_students_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload students from Excel file."""
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_students_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} students created, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a student's information."""
    school_id = current_user.school_id
    
    # Get student
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to this school"
        )
    
    # Update fields if provided
    if student_data.name is not None:
        student.name = student_data.name
    
    if student_data.email is not None and student_data.email != student.email:
        # Check if new email already exists (only for active users)
        existing_user = db.query(User).filter(
            User.email == student_data.email,
            User.id != student_id,
            User.is_active == True
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        student.email = student_data.email
    
    if student_data.grade is not None:
        student.grade = student_data.grade
    
    db.commit()
    db.refresh(student)
    
    return StudentResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        grade=student.grade,
        school_id=student.school_id
    )


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete (deactivate) a student."""
    school_id = current_user.school_id
    
    # Get student
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to this school"
        )
    
    print(f"[STUDENT DELETION] Deactivating student ID {student_id} for school {school_id}")
    # Soft delete: set is_active to False
    student.is_active = False
    try:
        db.commit()
        print(f"[STUDENT DELETION] Successfully deactivated student {student_id}")
    except Exception as e:
        db.rollback()
        print(f"[STUDENT DELETION] Failed to deactivate student {student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete student: {str(e)}"
        )
    
    return None


# ==================== PARENTS MANAGEMENT ====================

@router.get("/parents", response_model=List[ParentResponse])
def get_parents(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all parents in the school."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    parents = query.all()
    return [ParentResponse(id=p.id, name=p.name, email=p.email, school_id=p.school_id) for p in parents]


@router.post("/parents", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent(
    parent_data: ParentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new parent."""
    school_id = current_user.school_id
    
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == parent_data.email
    ).first()
    
    if existing_user:
        # If user is active, email is taken
        if existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        # If user is inactive, free up the email by changing the inactive user's email
        inactive_email = f"{existing_user.email}_deleted_{existing_user.id}_{int(datetime.utcnow().timestamp())}"
        existing_user.email = inactive_email
        db.commit()
    
    # Generate unique password
    password = generate_unique_password(db, parent_data.email, parent_data.name, UserRole.PARENT.value, school_id)
    hashed_password = get_password_hash(password)
    
    # Debug: Log password generation (remove in production)
    print(f"[PARENT CREATION] Generated password for {parent_data.email}: {password}")
    print(f"[PARENT CREATION] Password hash length: {len(hashed_password)}")
    
    # Create parent
    parent = User(
        name=parent_data.name,
        email=parent_data.email,
        password=hashed_password,
        role=UserRole.PARENT,
        school_id=school_id,
        is_active=True  # Ensure user is active
    )
    
    db.add(parent)
    db.flush()
    
    # Link to student if provided
    if parent_data.student_email:
        student = db.query(User).filter(
            User.email == parent_data.student_email,
            User.role == UserRole.STUDENT,
            User.school_id == school_id
        ).first()
        
        if student:
            student_parent = StudentParent(
                student_id=student.id,
                parent_id=parent.id,
                relationship_type="Parent"
            )
            db.add(student_parent)
    
    db.commit()
    db.refresh(parent)
    
    # Verify password was stored correctly
    from app.auth import verify_password
    password_verified = verify_password(password, parent.password)
    print(f"[PARENT CREATION] Password verification test: {'PASSED' if password_verified else 'FAILED'}")
    
    # Send login credentials email
    try:
        await send_login_credentials_email(db, parent, password, UserRole.PARENT.value)
    except Exception as e:
        print(f"Warning: Failed to send email to {parent.email}: {str(e)}")
    
    return ParentResponse(id=parent.id, name=parent.name, email=parent.email, school_id=parent.school_id)


@router.post("/parents/upload-excel", response_model=ExcelUploadResponse)
async def upload_parents_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload parents from Excel file."""
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_parents_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} parents created, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


@router.put("/parents/{parent_id}", response_model=ParentResponse)
def update_parent(
    parent_id: int,
    parent_data: ParentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a parent's information."""
    school_id = current_user.school_id
    
    # Get parent
    parent = db.query(User).filter(
        User.id == parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found or does not belong to this school"
        )
    
    # Update fields if provided
    if parent_data.name is not None:
        parent.name = parent_data.name
    
    if parent_data.email is not None and parent_data.email != parent.email:
        # Check if new email already exists (only for active users)
        existing_user = db.query(User).filter(
            User.email == parent_data.email,
            User.id != parent_id,
            User.is_active == True
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        parent.email = parent_data.email
    
    db.commit()
    db.refresh(parent)
    
    return ParentResponse(
        id=parent.id,
        name=parent.name,
        email=parent.email,
        school_id=parent.school_id
    )


@router.delete("/parents/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete (deactivate) a parent."""
    school_id = current_user.school_id
    
    # Get parent
    parent = db.query(User).filter(
        User.id == parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found or does not belong to this school"
        )
    
    print(f"[PARENT DELETION] Deactivating parent ID {parent_id} for school {school_id}")
    # Soft delete: set is_active to False
    parent.is_active = False
    try:
        db.commit()
        print(f"[PARENT DELETION] Successfully deactivated parent {parent_id}")
    except Exception as e:
        db.rollback()
        print(f"[PARENT DELETION] Failed to deactivate parent {parent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete parent: {str(e)}"
        )
    
    return None


# ==================== SUBJECTS MANAGEMENT ====================

@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all subjects in the school."""
    school_id = current_user.school_id
    
    subjects = db.query(Subject).filter(Subject.school_id == school_id).all()
    return subjects


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new subject."""
    school_id = current_user.school_id
    
    subject = Subject(
        name=subject_data.name,
        code=subject_data.code,
        school_id=school_id
    )
    
    db.add(subject)
    db.commit()
    db.refresh(subject)
    
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a subject."""
    school_id = current_user.school_id
    
    # Get subject
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found or does not belong to this school"
        )
    
    # Update fields
    subject.name = subject_data.name
    subject.code = subject_data.code
    
    db.commit()
    db.refresh(subject)
    
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a subject."""
    school_id = current_user.school_id
    
    # Get subject
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found or does not belong to this school"
        )
    
    # Check if subject is used in classes
    classes_count = db.query(Class).filter(Class.subject_id == subject_id).count()
    if classes_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete subject: it is used in {classes_count} class(es)"
        )
    
    db.delete(subject)
    db.commit()
    
    return None


# ==================== CLASSES MANAGEMENT ====================

@router.get("/classes", response_model=List[ClassResponse])
def get_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all classes in the school."""
    school_id = current_user.school_id
    
    classes = db.query(Class).filter(Class.school_id == school_id).all()
    
    # Get subject and teacher names for each class
    result = []
    for cls in classes:
        subject = db.query(Subject).filter(Subject.id == cls.subject_id).first()
        teacher = db.query(User).filter(User.id == cls.teacher_id).first()
        
        result.append(ClassResponse(
            id=cls.id,
            name=cls.name,
            grade=cls.grade,
            subject_id=cls.subject_id,
            teacher_id=cls.teacher_id,
            school_id=cls.school_id,
            academic_year=cls.academic_year,
            subject_name=subject.name if subject else None,
            teacher_name=teacher.name if teacher else None
        ))
    
    return result


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new class."""
    school_id = current_user.school_id
    
    # Verify teacher belongs to this school
    teacher = db.query(User).filter(
        User.id == class_data.teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher not found or does not belong to this school"
        )
    
    # Verify subject belongs to this school
    subject = db.query(Subject).filter(
        Subject.id == class_data.subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject not found or does not belong to this school"
        )
    
    class_obj = Class(
        name=class_data.name,
        grade=class_data.grade,
        subject_id=class_data.subject_id,
        teacher_id=class_data.teacher_id,
        school_id=school_id,
        academic_year=class_data.academic_year
    )
    
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    
    # Get subject and teacher names for response
    subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first()
    teacher = db.query(User).filter(User.id == class_obj.teacher_id).first()
    
    return ClassResponse(
        id=class_obj.id,
        name=class_obj.name,
        grade=class_obj.grade,
        subject_id=class_obj.subject_id,
        teacher_id=class_obj.teacher_id,
        school_id=class_obj.school_id,
        academic_year=class_obj.academic_year,
        subject_name=subject.name if subject else None,
        teacher_name=teacher.name if teacher else None
    )


@router.post("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_201_CREATED)
def assign_student_to_class(
    class_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Assign a student to a class."""
    school_id = current_user.school_id
    
    # Verify class belongs to school
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify student belongs to school
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if already assigned
    existing = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id,
        ClassStudent.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already assigned to this class"
        )
    
    class_student = ClassStudent(
        class_id=class_id,
        student_id=student_id
    )
    
    db.add(class_student)
    db.commit()
    
    return {"success": True, "message": "Student assigned to class"}


@router.put("/classes/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a class."""
    school_id = current_user.school_id
    
    # Get class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or does not belong to this school"
        )
    
    # Verify subject belongs to this school
    subject = db.query(Subject).filter(
        Subject.id == class_data.subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject not found or does not belong to this school"
        )
    
    # Verify teacher belongs to this school
    teacher = db.query(User).filter(
        User.id == class_data.teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER,
        User.is_active == True
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher not found or does not belong to this school"
        )
    
    # Update fields
    class_obj.name = class_data.name
    class_obj.grade = class_data.grade
    class_obj.subject_id = class_data.subject_id
    class_obj.teacher_id = class_data.teacher_id
    if class_data.academic_year:
        class_obj.academic_year = class_data.academic_year
    
    db.commit()
    db.refresh(class_obj)
    
    # Get subject and teacher names
    subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first()
    teacher = db.query(User).filter(User.id == class_obj.teacher_id).first()
    
    return ClassResponse(
        id=class_obj.id,
        name=class_obj.name,
        grade=class_obj.grade,
        subject_id=class_obj.subject_id,
        teacher_id=class_obj.teacher_id,
        school_id=class_obj.school_id,
        academic_year=class_obj.academic_year,
        subject_name=subject.name if subject else None,
        teacher_name=teacher.name if teacher else None
    )


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a class."""
    school_id = current_user.school_id
    
    # Get class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or does not belong to this school"
        )
    
    # Check if class has students
    students_count = db.query(ClassStudent).filter(ClassStudent.class_id == class_id).count()
    if students_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete class: it has {students_count} student(s) assigned"
        )
    
    # Check if class has lessons
    lessons_count = db.query(Lesson).filter(Lesson.class_id == class_id).count()
    if lessons_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete class: it has {lessons_count} lesson(s)"
        )
    
    # Check if class has timetable slots
    timetable_count = db.query(TimetableSlot).filter(TimetableSlot.class_id == class_id).count()
    if timetable_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete class: it has {timetable_count} timetable slot(s)"
        )
    
    db.delete(class_obj)
    db.commit()
    
    return None


@router.get("/classes/{class_id}/students", response_model=List[StudentResponse])
def get_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students enrolled in a specific class."""
    school_id = current_user.school_id
    
    # Verify class belongs to school
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get all students enrolled in this class
    class_students = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id
    ).all()
    
    result = []
    for cs in class_students:
        student = db.query(User).filter(
            User.id == cs.student_id,
            User.is_active == True
        ).first()
        if student:
            # Get parent info
            parent_links = db.query(StudentParent).filter(StudentParent.student_id == student.id).all()
            parent_emails = []
            parent_names = []
            for link in parent_links:
                parent = db.query(User).filter(User.id == link.parent_id).first()
                if parent and parent.is_active:
                    parent_emails.append(parent.email)
                    parent_names.append(parent.name)
            
            result.append(StudentResponse(
                id=student.id,
                name=student.name,
                email=student.email,
                grade=student.grade,
                school_id=student.school_id,
                parent_emails=parent_emails if parent_emails else None,
                parent_names=parent_names if parent_names else None
            ))
    
    return result


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_from_class(
    class_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Remove a student from a class."""
    school_id = current_user.school_id
    
    # Verify class belongs to school
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Find the enrollment
    enrollment = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id,
        ClassStudent.student_id == student_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in this class"
        )
    
    db.delete(enrollment)
    db.commit()
    
    return None


# ==================== TIMETABLE MANAGEMENT ====================

@router.get("/timetable", response_model=List[TimetableSlotResponse])
def get_timetable(
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get timetable slots."""
    school_id = current_user.school_id
    
    query = db.query(TimetableSlot).filter(TimetableSlot.school_id == school_id)
    
    if class_id:
        query = query.filter(TimetableSlot.class_id == class_id)
    
    slots = query.all()
    # Convert time objects to strings for the response
    return [
        TimetableSlotResponse(
            id=slot.id,
            class_id=slot.class_id,
            subject_id=slot.subject_id,
            teacher_id=slot.teacher_id,
            school_id=slot.school_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time.strftime("%H:%M") if slot.start_time else "",
            end_time=slot.end_time.strftime("%H:%M") if slot.end_time else "",
            room=slot.room
        )
        for slot in slots
    ]


@router.post("/timetable", response_model=TimetableSlotResponse, status_code=status.HTTP_201_CREATED)
def create_timetable_slot(
    slot_data: TimetableSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a timetable slot."""
    try:
        school_id = current_user.school_id
        
        # Log the incoming data for debugging
        print(f"Creating timetable slot: class_id={slot_data.class_id}, subject_id={slot_data.subject_id}, teacher_id={slot_data.teacher_id}, day_of_week={slot_data.day_of_week}, start_time={slot_data.start_time}, end_time={slot_data.end_time}, room={slot_data.room}")
        
        # Validate required fields
        if not slot_data.start_time or not slot_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time and end_time are required"
            )
        
        # Parse time strings
        try:
            start_time_obj = datetime.strptime(slot_data.start_time, "%H:%M").time()
            end_time_obj = datetime.strptime(slot_data.end_time, "%H:%M").time()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time format. Use HH:MM format (e.g., 09:00, 14:30). Error: {str(e)}"
            )
        
        # Validate that end_time is after start_time
        if end_time_obj <= start_time_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time"
            )
        
        # Verify class, subject, and teacher belong to this school
        class_obj = db.query(Class).filter(
            Class.id == slot_data.class_id,
            Class.school_id == school_id
        ).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found or does not belong to this school"
            )
        
        subject_obj = db.query(Subject).filter(
            Subject.id == slot_data.subject_id,
            Subject.school_id == school_id
        ).first()
        if not subject_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found or does not belong to this school"
            )
        
        teacher_obj = db.query(User).filter(
            User.id == slot_data.teacher_id,
            User.school_id == school_id,
            User.role == UserRole.TEACHER
        ).first()
        if not teacher_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found or does not belong to this school"
            )
        
        # Check for conflicts (same teacher, same day, overlapping time)
        conflicting = db.query(TimetableSlot).filter(
            TimetableSlot.school_id == school_id,
            TimetableSlot.teacher_id == slot_data.teacher_id,
            TimetableSlot.day_of_week == slot_data.day_of_week,
            or_(
                and_(TimetableSlot.start_time <= start_time_obj, TimetableSlot.end_time > start_time_obj),
                and_(TimetableSlot.start_time < end_time_obj, TimetableSlot.end_time >= end_time_obj),
                and_(TimetableSlot.start_time >= start_time_obj, TimetableSlot.end_time <= end_time_obj)
            )
        ).first()
        
        if conflicting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher has a conflicting schedule at this time"
            )
        
        slot = TimetableSlot(
            class_id=slot_data.class_id,
            subject_id=slot_data.subject_id,
            teacher_id=slot_data.teacher_id,
            school_id=school_id,
            day_of_week=slot_data.day_of_week,
            start_time=start_time_obj,
            end_time=end_time_obj,
            room=slot_data.room
        )
        
        db.add(slot)
        db.commit()
        db.refresh(slot)
        
        return TimetableSlotResponse(
            id=slot.id,
            class_id=slot.class_id,
            subject_id=slot.subject_id,
            teacher_id=slot.teacher_id,
            school_id=slot.school_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time.strftime("%H:%M"),
            end_time=slot.end_time.strftime("%H:%M"),
            room=slot.room
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating timetable slot: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating timetable slot: {str(e)}"
        )


@router.put("/timetable/{slot_id}", response_model=TimetableSlotResponse)
def update_timetable_slot(
    slot_id: int,
    slot_data: TimetableSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a timetable slot."""
    try:
        school_id = current_user.school_id
        
        # Get slot
        slot = db.query(TimetableSlot).filter(
            TimetableSlot.id == slot_id,
            TimetableSlot.school_id == school_id
        ).first()
        
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timetable slot not found or does not belong to this school"
            )
        
        # Validate required fields
        if not slot_data.start_time or not slot_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time and end_time are required"
            )
        
        # Parse time strings
        try:
            start_time_obj = datetime.strptime(slot_data.start_time, "%H:%M").time()
            end_time_obj = datetime.strptime(slot_data.end_time, "%H:%M").time()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time format. Use HH:MM format (e.g., 09:00, 14:30). Error: {str(e)}"
            )
        
        # Validate that end_time is after start_time
        if end_time_obj <= start_time_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time"
            )
        
        # Verify class, subject, and teacher belong to this school
        class_obj = db.query(Class).filter(
            Class.id == slot_data.class_id,
            Class.school_id == school_id
        ).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found or does not belong to this school"
            )
        
        subject_obj = db.query(Subject).filter(
            Subject.id == slot_data.subject_id,
            Subject.school_id == school_id
        ).first()
        if not subject_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found or does not belong to this school"
            )
        
        teacher_obj = db.query(User).filter(
            User.id == slot_data.teacher_id,
            User.school_id == school_id,
            User.role == UserRole.TEACHER
        ).first()
        if not teacher_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found or does not belong to this school"
            )
        
        # Update fields
        slot.class_id = slot_data.class_id
        slot.subject_id = slot_data.subject_id
        slot.teacher_id = slot_data.teacher_id
        slot.day_of_week = slot_data.day_of_week
        slot.start_time = start_time_obj
        slot.end_time = end_time_obj
        slot.room = slot_data.room
        
        db.commit()
        db.refresh(slot)
        
        return TimetableSlotResponse(
            id=slot.id,
            class_id=slot.class_id,
            subject_id=slot.subject_id,
            teacher_id=slot.teacher_id,
            school_id=slot.school_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time.strftime("%H:%M") if slot.start_time else "",
            end_time=slot.end_time.strftime("%H:%M") if slot.end_time else "",
            room=slot.room
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update timetable slot: {str(e)}"
        )


@router.delete("/timetable/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a timetable slot."""
    school_id = current_user.school_id
    
    # Get slot
    slot = db.query(TimetableSlot).filter(
        TimetableSlot.id == slot_id,
        TimetableSlot.school_id == school_id
    ).first()
    
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable slot not found or does not belong to this school"
        )
    
    db.delete(slot)
    db.commit()
    
    return None


# ==================== HOLIDAYS & EVENTS ====================

@router.get("/holidays", response_model=List[HolidayResponse])
def get_holidays(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all holidays."""
    school_id = current_user.school_id
    
    holidays = db.query(Holiday).filter(Holiday.school_id == school_id).order_by(Holiday.start_date).all()
    return holidays


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(
    holiday_data: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a holiday."""
    school_id = current_user.school_id
    
    holiday = Holiday(
        name=holiday_data.name,
        start_date=holiday_data.start_date,
        end_date=holiday_data.end_date,
        description=holiday_data.description,
        school_id=school_id
    )
    
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    
    return holiday


@router.put("/holidays/{holiday_id}", response_model=HolidayResponse)
def update_holiday(
    holiday_id: int,
    holiday_data: HolidayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a holiday."""
    school_id = current_user.school_id
    
    # Get holiday
    holiday = db.query(Holiday).filter(
        Holiday.id == holiday_id,
        Holiday.school_id == school_id
    ).first()
    
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found or does not belong to this school"
        )
    
    # Update fields if provided
    if holiday_data.name is not None:
        holiday.name = holiday_data.name
    if holiday_data.start_date is not None:
        holiday.start_date = holiday_data.start_date
    if holiday_data.end_date is not None:
        holiday.end_date = holiday_data.end_date
    if holiday_data.description is not None:
        holiday.description = holiday_data.description
    
    db.commit()
    db.refresh(holiday)
    
    return holiday


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a holiday."""
    school_id = current_user.school_id
    
    # Get holiday
    holiday = db.query(Holiday).filter(
        Holiday.id == holiday_id,
        Holiday.school_id == school_id
    ).first()
    
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found or does not belong to this school"
        )
    
    db.delete(holiday)
    db.commit()
    
    return None


@router.get("/events", response_model=List[EventResponse])
def get_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all events."""
    school_id = current_user.school_id
    
    events = db.query(Event).filter(Event.school_id == school_id).order_by(Event.event_date).all()
    
    # Convert Event objects to EventResponse format
    return [
        EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            event_date=event.event_date,
            event_time=event.event_time.strftime("%H:%M") if event.event_time else None,
            event_type=event.event_type,
            school_id=event.school_id
        )
        for event in events
    ]


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create an event."""
    school_id = current_user.school_id
    
    event_time_obj = None
    if event_data.event_time:
        event_time_obj = datetime.strptime(event_data.event_time, "%H:%M").time()
    
    event = Event(
        title=event_data.title,
        description=event_data.description,
        event_date=event_data.event_date,
        event_time=event_time_obj,
        event_type=event_data.event_type,
        school_id=school_id
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        event_time=event.event_time.strftime("%H:%M") if event.event_time else None,
        event_type=event.event_type,
        school_id=event.school_id
    )


@router.put("/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an event."""
    school_id = current_user.school_id
    
    # Get event
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.school_id == school_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or does not belong to this school"
        )
    
    # Update fields if provided
    if event_data.title is not None:
        event.title = event_data.title
    if event_data.description is not None:
        event.description = event_data.description
    if event_data.event_date is not None:
        event.event_date = event_data.event_date
    if event_data.event_time is not None:
        event.event_time = datetime.strptime(event_data.event_time, "%H:%M").time()
    if event_data.event_type is not None:
        event.event_type = event_data.event_type
    
    db.commit()
    db.refresh(event)
    
    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        event_time=event.event_time.strftime("%H:%M") if event.event_time else None,
        event_type=event.event_type,
        school_id=event.school_id
    )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete an event."""
    school_id = current_user.school_id
    
    # Get event
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.school_id == school_id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or does not belong to this school"
        )
    
    db.delete(event)
    db.commit()
    
    return None


# ==================== ANNOUNCEMENTS ====================

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_announcements(
    target_audience: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all announcements."""
    school_id = current_user.school_id
    
    query = db.query(Announcement).filter(Announcement.school_id == school_id)
    
    if target_audience:
        query = query.filter(Announcement.target_audience == target_audience)
    
    announcements = query.order_by(Announcement.published_at.desc()).all()
    return announcements


@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement_data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create an announcement."""
    school_id = current_user.school_id
    
    valid_audiences = ["TEACHERS", "STUDENTS", "PARENTS", "EVERYONE"]
    if announcement_data.target_audience not in valid_audiences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"target_audience must be one of: {', '.join(valid_audiences)}"
        )
    
    announcement = Announcement(
        title=announcement_data.title,
        content=announcement_data.content,
        target_audience=announcement_data.target_audience,
        school_id=school_id,
        created_by=current_user.id
    )
    
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    return announcement


@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    announcement_data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update an announcement."""
    school_id = current_user.school_id
    
    # Get announcement
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.school_id == school_id
    ).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found or does not belong to this school"
        )
    
    valid_audiences = ["TEACHERS", "STUDENTS", "PARENTS", "EVERYONE"]
    if announcement_data.target_audience not in valid_audiences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"target_audience must be one of: {', '.join(valid_audiences)}"
        )
    
    # Update fields
    announcement.title = announcement_data.title
    announcement.content = announcement_data.content
    announcement.target_audience = announcement_data.target_audience
    
    db.commit()
    db.refresh(announcement)
    
    return announcement


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete an announcement."""
    school_id = current_user.school_id
    
    # Get announcement
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.school_id == school_id
    ).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found or does not belong to this school"
        )
    
    db.delete(announcement)
    db.commit()
    
    return None


# ==================== LESSONS & LECTURES (VIEW MODE) ====================

@router.get("/lessons", response_model=List[dict])
def get_lessons(
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all lessons (view mode for admin)."""
    school_id = current_user.school_id
    
    query = db.query(Lesson).filter(Lesson.school_id == school_id)
    
    if class_id:
        query = query.filter(Lesson.class_id == class_id)
    
    lessons = query.order_by(Lesson.lesson_date.desc()).all()
    
    result = []
    for lesson in lessons:
        lectures = db.query(Lecture).filter(Lecture.lesson_id == lesson.id).all()
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "class_id": lesson.class_id,
            "teacher_id": lesson.teacher_id,
            "lesson_date": lesson.lesson_date.isoformat(),
            "lectures": [
                {
                    "id": l.id,
                    "title": l.title,
                    "content": l.content,
                    "lecture_date": l.lecture_date.isoformat(),
                    "start_time": l.start_time.strftime("%H:%M") if l.start_time else None,
                    "end_time": l.end_time.strftime("%H:%M") if l.end_time else None
                }
                for l in lectures
            ]
        })
    
    return result


# ==================== PARENT-STUDENT MAPPING MANAGEMENT ====================

@router.get("/students/{student_id}/parents", response_model=List[StudentParentLinkResponse])
def get_student_parents(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all parents linked to a specific student."""
    school_id = current_user.school_id
    
    # Verify student belongs to this school
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to this school"
        )
    
    # Get all parent-student links for this student
    links = db.query(StudentParent).filter(
        StudentParent.student_id == student_id
    ).all()
    
    result = []
    for link in links:
        parent = db.query(User).filter(User.id == link.parent_id).first()
        if parent and parent.school_id == school_id:
            result.append(StudentParentLinkResponse(
                id=link.id,
                student_id=link.student_id,
                parent_id=link.parent_id,
                relationship_type=link.relationship_type,
                student_name=student.name,
                student_email=student.email,
                parent_name=parent.name,
                parent_email=parent.email
            ))
    
    return result


@router.get("/parents/{parent_id}/students", response_model=List[StudentParentLinkResponse])
def get_parent_students(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students linked to a specific parent."""
    school_id = current_user.school_id
    
    # Verify parent belongs to this school
    parent = db.query(User).filter(
        User.id == parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found or does not belong to this school"
        )
    
    # Get all parent-student links for this parent
    links = db.query(StudentParent).filter(
        StudentParent.parent_id == parent_id
    ).all()
    
    result = []
    for link in links:
        student = db.query(User).filter(User.id == link.student_id).first()
        if student and student.school_id == school_id:
            result.append(StudentParentLinkResponse(
                id=link.id,
                student_id=link.student_id,
                parent_id=link.parent_id,
                relationship_type=link.relationship_type,
                student_name=student.name,
                student_email=student.email,
                parent_name=parent.name,
                parent_email=parent.email
            ))
    
    return result


@router.post("/parent-student/link", response_model=StudentParentLinkResponse, status_code=status.HTTP_201_CREATED)
def create_parent_student_link(
    link_data: StudentParentLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a link between a parent and a student."""
    school_id = current_user.school_id
    
    # Verify student belongs to this school
    student = db.query(User).filter(
        User.id == link_data.student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found or does not belong to this school"
        )
    
    # Verify parent belongs to this school
    parent = db.query(User).filter(
        User.id == link_data.parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent not found or does not belong to this school"
        )
    
    # Check if link already exists
    existing_link = db.query(StudentParent).filter(
        StudentParent.student_id == link_data.student_id,
        StudentParent.parent_id == link_data.parent_id
    ).first()
    
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link between this parent and student already exists"
        )
    
    # Create the link
    link = StudentParent(
        student_id=link_data.student_id,
        parent_id=link_data.parent_id,
        relationship_type=link_data.relationship_type
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    return StudentParentLinkResponse(
        id=link.id,
        student_id=link.student_id,
        parent_id=link.parent_id,
        relationship_type=link.relationship_type,
        student_name=student.name,
        student_email=student.email,
        parent_name=parent.name,
        parent_email=parent.email
    )


@router.delete("/parent-student/link/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent_student_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a parent-student link."""
    school_id = current_user.school_id
    
    # Get the link
    link = db.query(StudentParent).filter(StudentParent.id == link_id).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Verify both student and parent belong to this school
    student = db.query(User).filter(User.id == link.student_id).first()
    parent = db.query(User).filter(User.id == link.parent_id).first()
    
    if not student or not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student or parent not found"
        )
    
    if student.school_id != school_id or parent.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete link: student or parent does not belong to this school"
        )
    
    db.delete(link)
    db.commit()
    
    return None


@router.get("/students-with-parents", response_model=List[StudentWithParentsResponse])
def get_students_with_parents(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students with their linked parents."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    students = query.all()
    result = []
    
    for student in students:
        # Get linked parents
        links = db.query(StudentParent).filter(
            StudentParent.student_id == student.id
        ).all()
        
        linked_parents = []
        for link in links:
            parent = db.query(User).filter(User.id == link.parent_id).first()
            if parent and parent.school_id == school_id:
                linked_parents.append({
                    "id": parent.id,
                    "name": parent.name,
                    "email": parent.email,
                    "relationship_type": link.relationship_type
                })
        
        result.append(StudentWithParentsResponse(
            id=student.id,
            name=student.name,
            email=student.email,
            grade=None,  # Grade would need to be stored separately or fetched from classes
            school_id=student.school_id,
            linked_parents=linked_parents
        ))
    
    return result


@router.get("/parents-with-students", response_model=List[ParentWithStudentsResponse])
def get_parents_with_students(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all parents with their linked students."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    parents = query.all()
    result = []
    
    for parent in parents:
        # Get linked students
        links = db.query(StudentParent).filter(
            StudentParent.parent_id == parent.id
        ).all()
        
        linked_students = []
        for link in links:
            student = db.query(User).filter(User.id == link.student_id).first()
            if student and student.school_id == school_id:
                linked_students.append({
                    "id": student.id,
                    "name": student.name,
                    "email": student.email,
                    "relationship_type": link.relationship_type
                })
        
        result.append(ParentWithStudentsResponse(
            id=parent.id,
            name=parent.name,
            email=parent.email,
            school_id=parent.school_id,
            linked_students=linked_students
        ))
    
    return result


@router.get("/parent-student/stats", response_model=ParentStudentStatsResponse)
def get_parent_student_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get statistics about parent-student relationships."""
    school_id = current_user.school_id
    
    # Count total parents and students
    total_parents = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    ).count()
    
    total_students = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).count()
    
    # Get all links for this school
    all_students = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).all()
    
    all_parents = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    ).all()
    
    # Count linked and unlinked
    linked_student_ids = set()
    linked_parent_ids = set()
    
    for student in all_students:
        links = db.query(StudentParent).filter(
            StudentParent.student_id == student.id
        ).all()
        if links:
            # Only count if parent is active
            for link in links:
                parent = db.query(User).filter(
                    User.id == link.parent_id,
                    User.school_id == school_id,
                    User.is_active == True
                ).first()
                if parent:
                    linked_student_ids.add(student.id)
                    linked_parent_ids.add(parent.id)
    
    unlinked_students = total_students - len(linked_student_ids)
    unlinked_parents = total_parents - len(linked_parent_ids)
    
    # Count total links (only active students and parents)
    total_links = db.query(StudentParent).join(
        User, StudentParent.student_id == User.id
    ).filter(
        User.school_id == school_id,
        User.is_active == True
    ).count()
    
    # Students per parent (for chart) - only count active students
    students_per_parent = []
    for parent in all_parents:
        links = db.query(StudentParent).join(
            User, StudentParent.student_id == User.id
        ).filter(
            StudentParent.parent_id == parent.id,
            User.is_active == True
        ).count()
        if links > 0:
            students_per_parent.append({
                "parent_name": parent.name,
                "student_count": links
            })
    
    # Parents per student (for chart) - only count active parents
    parents_per_student = []
    for student in all_students:
        links = db.query(StudentParent).join(
            User, StudentParent.parent_id == User.id
        ).filter(
            StudentParent.student_id == student.id,
            User.is_active == True
        ).count()
        if links > 0:
            parents_per_student.append({
                "student_name": student.name,
                "parent_count": links
            })
    
    return ParentStudentStatsResponse(
        total_parents=total_parents,
        total_students=total_students,
        unlinked_students=unlinked_students,
        unlinked_parents=unlinked_parents,
        total_links=total_links,
        students_per_parent=students_per_parent,
        parents_per_student=parents_per_student
    )


@router.post("/parent-student/upload-combined-excel", response_model=ExcelUploadResponse)
async def upload_students_parents_combined_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Upload students and parents from a combined Excel file.
    Expected columns: Student Name, Student Email, Grade/Class, Parent Name, Parent Email
    """
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_students_parents_combined_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} records processed, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


# ==================== ANALYTICS & VISUALIZATIONS ====================

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get comprehensive analytics data for visualizations."""
    school_id = current_user.school_id
    
    # Get all active teachers
    teachers = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.TEACHER,
        User.is_active == True
    ).all()
    
    # Get all active students
    students = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).all()
    
    # Get all active parents
    parents = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    ).all()
    
    # Get all classes
    classes = db.query(Class).filter(Class.school_id == school_id).all()
    
    # Get all subjects
    subjects = db.query(Subject).filter(Subject.school_id == school_id).all()
    
    # ========== TEACHER ANALYTICS ==========
    
    # Teacher Workload (classes per teacher)
    teacher_workload = []
    teachers_by_subject = {}
    
    for teacher in teachers:
        teacher_classes = [c for c in classes if c.teacher_id == teacher.id]
        total_students = 0
        
        for cls in teacher_classes:
            # Count only active students in this class
            class_students = db.query(ClassStudent).join(User).filter(
                ClassStudent.class_id == cls.id,
                User.id == ClassStudent.student_id,
                User.is_active == True
            ).count()
            total_students += class_students
        
        teacher_workload.append(TeacherWorkloadResponse(
            teacher_id=teacher.id,
            teacher_name=teacher.name,
            subject=teacher.subject,
            total_classes=len(teacher_classes),
            total_students=total_students
        ))
        
        # Count teachers by subject
        if teacher.subject:
            if teacher.subject not in teachers_by_subject:
                teachers_by_subject[teacher.subject] = 0
            teachers_by_subject[teacher.subject] += 1
    
    teachers_by_subject_list = [{"subject": k, "count": v} for k, v in teachers_by_subject.items()]
    
    # ========== STUDENT ANALYTICS ==========
    
    # Students by Grade
    students_by_grade = {}
    for student in students:
        grade = student.grade or "Unknown"
        if grade not in students_by_grade:
            students_by_grade[grade] = {"students": 0, "teachers": set(), "classes": set()}
        students_by_grade[grade]["students"] += 1
        
        # Get classes for this student (only active classes)
        student_classes = db.query(ClassStudent).filter(ClassStudent.student_id == student.id).all()
        for sc in student_classes:
            cls = db.query(Class).filter(Class.id == sc.class_id).first()
            if cls:
                students_by_grade[grade]["classes"].add(cls.id)
                students_by_grade[grade]["teachers"].add(cls.teacher_id)
    
    grade_distribution = []
    for grade, data in students_by_grade.items():
        grade_distribution.append(GradeDistributionResponse(
            grade=grade,
            student_count=data["students"],
            teacher_count=len(data["teachers"]),
            class_count=len(data["classes"])
        ))
    
    # Students by Subject
    students_by_subject = {}
    for subject in subjects:
        subject_classes = [c for c in classes if c.subject_id == subject.id]
        student_ids = set()
        teacher_ids = set()
        
        for cls in subject_classes:
            teacher_ids.add(cls.teacher_id)
            # Only count active students
            class_students = db.query(ClassStudent).join(User).filter(
                ClassStudent.class_id == cls.id,
                User.id == ClassStudent.student_id,
                User.is_active == True
            ).all()
            for cs in class_students:
                student_ids.add(cs.student_id)
        
        students_by_subject[subject.id] = {
            "subject_name": subject.name,
            "student_count": len(student_ids),
            "teacher_count": len(teacher_ids),
            "class_count": len(subject_classes)
        }
    
    subject_distribution = [
        SubjectDistributionResponse(
            subject_id=subj_id,
            subject_name=data["subject_name"],
            student_count=data["student_count"],
            teacher_count=data["teacher_count"],
            class_count=data["class_count"]
        )
        for subj_id, data in students_by_subject.items()
    ]
    
    # ========== PARENT ANALYTICS ==========
    
    # Parents by children count
    parents_by_children = {}
    parent_student_relations = []
    
    for parent in parents:
        parent_links = db.query(StudentParent).filter(StudentParent.parent_id == parent.id).all()
        
        # Get children details (only active students)
        children = []
        for link in parent_links:
            student = db.query(User).filter(
                User.id == link.student_id,
                User.is_active == True
            ).first()
            if student:
                children.append({
                    "id": student.id,
                    "name": student.name,
                    "email": student.email,
                    "grade": student.grade
                })
        
        # Only count active children
        children_count = len(children)
        
        # Only include parents with active children in the count
        if children_count == 0:
            continue  # Skip parents whose children are all deleted
        
        if children_count not in parents_by_children:
            parents_by_children[children_count] = 0
        parents_by_children[children_count] += 1
        
        parent_student_relations.append(ParentStudentRelationResponse(
            parent_id=parent.id,
            parent_name=parent.name,
            parent_email=parent.email,
            children_count=children_count,
            children=children
        ))
    
    parents_by_children_list = [{"children_count": k, "parent_count": v} for k, v in sorted(parents_by_children.items())]
    
    # ========== LINKED/UNLINKED STUDENTS ==========
    
    linked_student_ids = set()
    for link in db.query(StudentParent).all():
        student = db.query(User).filter(
            User.id == link.student_id,
            User.school_id == school_id,
            User.is_active == True
        ).first()
        if student:
            linked_student_ids.add(link.student_id)
    
    linked_students = len(linked_student_ids)
    unlinked_students = len(students) - linked_students
    
    return AnalyticsResponse(
        teacher_workload=teacher_workload,
        teachers_by_subject=teachers_by_subject_list,
        students_by_grade=grade_distribution,
        students_by_subject=subject_distribution,
        parents_by_children_count=parents_by_children_list,
        parent_student_relations=parent_student_relations,
        total_teachers=len(teachers),
        total_students=len(students),
        total_parents=len(parents),
        total_classes=len(classes),
        total_subjects=len(subjects),
        linked_students=linked_students,
        unlinked_students=unlinked_students
    )


# ==================== STUDENT CONTENT SYNC (from Gurukul) ====================

@router.post("/student-content/summaries", response_model=StudentContentSyncResponse, status_code=status.HTTP_201_CREATED)
async def sync_student_summary(
    summary_data: StudentSummarySync,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Sync a student summary from Gurukul to EMS"""
    # Find student by email
    student = db.query(User).filter(
        User.email == summary_data.student_email,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with email {summary_data.student_email} not found"
        )
    
    # Use provided school_id or student's school_id
    school_id = summary_data.school_id or student.school_id
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School ID is required"
        )
    
    # Check if already synced (prevent duplicates)
    existing = db.query(StudentSummary).filter(
        StudentSummary.gurukul_id == summary_data.gurukul_id
    ).first()
    
    if existing:
        return StudentContentSyncResponse(
            id=existing.id,
            message="Summary already synced",
            synced_at=existing.synced_at
        )
    
    # Create new summary record
    student_summary = StudentSummary(
        student_id=student.id,
        school_id=school_id,
        gurukul_id=summary_data.gurukul_id,
        title=summary_data.title,
        content=summary_data.content,
        source=summary_data.source,
        source_type=summary_data.source_type or "text",
        extra_metadata=summary_data.extra_metadata or {}
    )
    
    db.add(student_summary)
    db.commit()
    db.refresh(student_summary)
    
    return StudentContentSyncResponse(
        id=student_summary.id,
        message="Summary synced successfully",
        synced_at=student_summary.synced_at
    )


@router.post("/student-content/flashcards", response_model=StudentContentSyncResponse, status_code=status.HTTP_201_CREATED)
async def sync_student_flashcard(
    flashcard_data: StudentFlashcardSync,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Sync a student flashcard from Gurukul to EMS"""
    # Find student by email
    student = db.query(User).filter(
        User.email == flashcard_data.student_email,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with email {flashcard_data.student_email} not found"
        )
    
    # Use provided school_id or student's school_id
    school_id = flashcard_data.school_id or student.school_id
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School ID is required"
        )
    
    # Check if already synced
    existing = db.query(StudentFlashcard).filter(
        StudentFlashcard.gurukul_id == flashcard_data.gurukul_id
    ).first()
    
    if existing:
        return StudentContentSyncResponse(
            id=existing.id,
            message="Flashcard already synced",
            synced_at=existing.synced_at
        )
    
    # Create new flashcard record
    student_flashcard = StudentFlashcard(
        student_id=student.id,
        school_id=school_id,
        gurukul_id=flashcard_data.gurukul_id,
        question=flashcard_data.question,
        answer=flashcard_data.answer,
        question_type=flashcard_data.question_type,
        days_until_review=flashcard_data.days_until_review,
        confidence=flashcard_data.confidence
    )
    
    db.add(student_flashcard)
    db.commit()
    db.refresh(student_flashcard)
    
    return StudentContentSyncResponse(
        id=student_flashcard.id,
        message="Flashcard synced successfully",
        synced_at=student_flashcard.synced_at
    )


@router.post("/student-content/test-results", response_model=StudentContentSyncResponse, status_code=status.HTTP_201_CREATED)
async def sync_student_test_result(
    test_data: StudentTestResultSync,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Sync a student test result from Gurukul to EMS"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Syncing test result for student email: {test_data.student_email}, gurukul_id: {test_data.gurukul_id}")
    
    # Find student by email
    student = db.query(User).filter(
        User.email == test_data.student_email,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).first()
    
    if not student:
        logger.error(f"Student not found for email: {test_data.student_email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with email {test_data.student_email} not found"
        )
    
    logger.info(f"Found student: {student.name} (ID: {student.id})")
    
    # Use provided school_id or student's school_id
    school_id = test_data.school_id or student.school_id
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School ID is required"
        )
    
    # Check if already synced
    existing = db.query(StudentTestResult).filter(
        StudentTestResult.gurukul_id == test_data.gurukul_id
    ).first()
    
    if existing:
        return StudentContentSyncResponse(
            id=existing.id,
            message="Test result already synced",
            synced_at=existing.synced_at
        )
    
    # Create new test result record
    test_result = StudentTestResult(
        student_id=student.id,
        school_id=school_id,
        gurukul_id=test_data.gurukul_id,
        subject=test_data.subject,
        topic=test_data.topic,
        difficulty=test_data.difficulty,
        num_questions=test_data.num_questions,
        questions=test_data.questions,
        user_answers=test_data.user_answers,
        score=test_data.score,
        total_questions=test_data.total_questions,
        percentage=test_data.percentage,
        time_taken=test_data.time_taken
    )
    
    db.add(test_result)
    db.commit()
    db.refresh(test_result)
    
    return StudentContentSyncResponse(
        id=test_result.id,
        message="Test result synced successfully",
        synced_at=test_result.synced_at
    )


@router.post("/student-content/subject-data", response_model=StudentContentSyncResponse, status_code=status.HTTP_201_CREATED)
async def sync_student_subject_data(
    subject_data: StudentSubjectDataSync,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Sync student subject explorer data from Gurukul to EMS"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Syncing subject data for student email: {subject_data.student_email}, gurukul_id: {subject_data.gurukul_id}")
    
    # Find student by email
    student = db.query(User).filter(
        User.email == subject_data.student_email,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).first()
    
    if not student:
        logger.error(f"Student not found for email: {subject_data.student_email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with email {subject_data.student_email} not found"
        )
    
    logger.info(f"Found student: {student.name} (ID: {student.id})")
    
    # Use provided school_id or student's school_id
    school_id = subject_data.school_id or student.school_id
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School ID is required"
        )
    
    # Check if already synced
    existing = db.query(StudentSubjectData).filter(
        StudentSubjectData.gurukul_id == subject_data.gurukul_id
    ).first()
    
    if existing:
        return StudentContentSyncResponse(
            id=existing.id,
            message="Subject data already synced",
            synced_at=existing.synced_at
        )
    
    # Create new subject data record
    student_subject_data = StudentSubjectData(
        student_id=student.id,
        school_id=school_id,
        gurukul_id=subject_data.gurukul_id,
        subject=subject_data.subject,
        topic=subject_data.topic,
        notes=subject_data.notes,
        provider=subject_data.provider,
        youtube_recommendations=subject_data.youtube_recommendations or []
    )
    
    db.add(student_subject_data)
    db.commit()
    db.refresh(student_subject_data)
    
    return StudentContentSyncResponse(
        id=student_subject_data.id,
        message="Subject data synced successfully",
        synced_at=student_subject_data.synced_at
    )


# ==================== VIEW STUDENT-GENERATED CONTENT (GURUKUL) ====================

@router.get("/students/{student_id}/content/summaries", response_model=List[StudentSummaryResponse])
def view_student_summaries(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all summaries generated by a student in Gurukul (admin can view any student in their school)"""
    # Verify student is in admin's school
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT,
        User.school_id == current_user.school_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your school"
        )
    
    # Get summaries
    summaries = db.query(StudentSummary).filter(
        StudentSummary.student_id == student_id
    ).order_by(StudentSummary.created_at.desc()).all()
    
    student_name = student.name if student else "Unknown"
    student_email = student.email if student else "Unknown"
    
    return [StudentSummaryResponse(
        id=s.id,
        gurukul_id=s.gurukul_id,
        student_id=s.student_id,
        student_name=student_name,
        student_email=student_email,
        title=s.title,
        content=s.content,
        source=s.source,
        source_type=s.source_type,
        extra_metadata=s.extra_metadata,
        created_at=s.created_at
    ) for s in summaries]


@router.get("/students/{student_id}/content/flashcards", response_model=List[StudentFlashcardResponse])
def view_student_flashcards(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all flashcards generated by a student in Gurukul (admin can view any student in their school)"""
    # Verify student is in admin's school
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT,
        User.school_id == current_user.school_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your school"
        )
    
    # Get flashcards
    flashcards = db.query(StudentFlashcard).filter(
        StudentFlashcard.student_id == student_id
    ).order_by(StudentFlashcard.created_at.desc()).all()
    
    student_name = student.name if student else "Unknown"
    student_email = student.email if student else "Unknown"
    
    return [StudentFlashcardResponse(
        id=f.id,
        gurukul_id=f.gurukul_id,
        student_id=f.student_id,
        student_name=student_name,
        student_email=student_email,
        question=f.question,
        answer=f.answer,
        question_type=f.question_type,
        days_until_review=f.days_until_review,
        confidence=f.confidence,
        created_at=f.created_at
    ) for f in flashcards]


@router.get("/students/{student_id}/content/test-results", response_model=List[StudentTestResultResponse])
def view_student_test_results(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all test results for a student from Gurukul (admin can view any student in their school)"""
    # Verify student is in admin's school
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT,
        User.school_id == current_user.school_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your school"
        )
    
    # Get test results
    test_results = db.query(StudentTestResult).filter(
        StudentTestResult.student_id == student_id
    ).order_by(StudentTestResult.created_at.desc()).all()
    
    student_name = student.name if student else "Unknown"
    student_email = student.email if student else "Unknown"
    
    return [StudentTestResultResponse(
        id=t.id,
        gurukul_id=t.gurukul_id,
        student_id=t.student_id,
        student_name=student_name,
        student_email=student_email,
        subject=t.subject,
        topic=t.topic,
        difficulty=t.difficulty,
        total_questions=t.total_questions,
        correct_answers=t.score,  # score is the number of correct answers
        score_percentage=t.percentage,  # percentage is the score percentage
        results_data={"questions": t.questions, "user_answers": t.user_answers} if t.questions and t.user_answers else None,
        created_at=t.created_at
    ) for t in test_results]


@router.get("/students/{student_id}/content/subject-data", response_model=List[StudentSubjectDataResponse])
def view_student_subject_data(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all subject explorer data for a student from Gurukul (admin can view any student in their school)"""
    # Verify student is in admin's school
    student = db.query(User).filter(
        User.id == student_id,
        User.role == UserRole.STUDENT,
        User.school_id == current_user.school_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your school"
        )
    
    # Get subject data
    subject_data = db.query(StudentSubjectData).filter(
        StudentSubjectData.student_id == student_id
    ).order_by(StudentSubjectData.created_at.desc()).all()
    
    student_name = student.name if student else "Unknown"
    student_email = student.email if student else "Unknown"
    
    return [StudentSubjectDataResponse(
        id=s.id,
        gurukul_id=s.gurukul_id,
        student_id=s.student_id,
        student_name=student_name,
        student_email=student_email,
        subject=s.subject,
        topic=s.topic,
        notes=s.notes,
        provider=s.provider,
        youtube_recommendations=s.youtube_recommendations,
        created_at=s.created_at
    ) for s in subject_data]
