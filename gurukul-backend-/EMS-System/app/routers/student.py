from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.dependencies import get_current_student
from app.models import (
    User, UserRole, Class, ClassStudent, Lesson, Lecture, 
    TimetableSlot, Subject, Announcement, Attendance
)
from app.schemas import (
    ClassResponse, LessonResponse, 
    TimetableSlotResponse, AnnouncementResponse, AttendanceResponse,
    TeacherWithClassesResponse
)
from pydantic import BaseModel
from datetime import date, datetime

router = APIRouter(prefix="/student", tags=["student"])


# ==================== STUDENT DASHBOARD STATS ====================

class StudentDashboardStats(BaseModel):
    total_classes: int
    total_lessons: int
    upcoming_lessons: int
    recent_announcements: int


@router.get("/dashboard/stats", response_model=StudentDashboardStats)
def get_student_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get student dashboard statistics."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get classes this student is enrolled in
    class_enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    class_ids = [enrollment.class_id for enrollment in class_enrollments]
    total_classes = len(class_ids)
    
    # Count lessons for student's classes
    total_lessons = 0
    upcoming_lessons = 0
    if class_ids:
        today = date.today()
        all_lessons = db.query(Lesson).filter(
            Lesson.class_id.in_(class_ids),
            Lesson.school_id == school_id
        ).all()
        total_lessons = len(all_lessons)
        upcoming_lessons = len([l for l in all_lessons if l.lesson_date >= today])
    
    # Count recent announcements (from last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_announcements = db.query(Announcement).filter(
        Announcement.school_id == school_id,
        or_(
            Announcement.target_audience == "STUDENTS",
            Announcement.target_audience == "EVERYONE"
        ),
        Announcement.published_at >= week_ago
    ).count()
    
    return StudentDashboardStats(
        total_classes=total_classes,
        total_lessons=total_lessons,
        upcoming_lessons=upcoming_lessons,
        recent_announcements=recent_announcements
    )


# ==================== STUDENT'S CLASSES ====================

@router.get("/classes", response_model=List[ClassResponse])
def get_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get all classes the student is enrolled in."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get class enrollments
    enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    
    class_ids = [enrollment.class_id for enrollment in enrollments]
    if not class_ids:
        return []
    
    classes = db.query(Class).filter(
        Class.id.in_(class_ids),
        Class.school_id == school_id
    ).all()
    
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


# ==================== STUDENT'S LESSONS ====================

@router.get("/lessons")
def get_my_lessons(
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get lessons for classes the student is enrolled in."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get classes this student is enrolled in
    enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    
    class_ids = [enrollment.class_id for enrollment in enrollments]
    if not class_ids:
        return []
    
    # Filter by class_id if provided
    if class_id:
        if class_id not in class_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
        class_ids = [class_id]
    
    # Get lessons
    lessons = db.query(Lesson).filter(
        Lesson.class_id.in_(class_ids),
        Lesson.school_id == school_id
    ).order_by(Lesson.lesson_date.desc()).all()
    
    result = []
    for lesson in lessons:
        class_obj = db.query(Class).filter(Class.id == lesson.class_id).first()
        subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first() if class_obj else None
        
        # Get lectures for this lesson
        lectures = db.query(Lecture).filter(Lecture.lesson_id == lesson.id).all()
        
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "class_id": lesson.class_id,
            "teacher_id": lesson.teacher_id,
            "school_id": lesson.school_id,
            "lesson_date": lesson.lesson_date,
            "class_name": class_obj.name if class_obj else None,
            "subject_name": subject.name if subject else None,
            "lectures": [
                {
                    "id": l.id,
                    "lesson_id": l.lesson_id,
                    "title": l.title,
                    "content": l.content,
                    "lecture_date": l.lecture_date,
                    "start_time": l.start_time.strftime("%H:%M") if l.start_time else None,
                    "end_time": l.end_time.strftime("%H:%M") if l.end_time else None
                }
                for l in lectures
            ]
        })
    
    return result


# ==================== STUDENT'S TIMETABLE/SCHEDULE ====================

@router.get("/timetable", response_model=List[TimetableSlotResponse])
def get_my_timetable(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get the student's timetable/schedule."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get classes this student is enrolled in
    enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    
    class_ids = [enrollment.class_id for enrollment in enrollments]
    if not class_ids:
        return []
    
    # Get timetable slots for student's classes
    timetable_slots = db.query(TimetableSlot).filter(
        TimetableSlot.class_id.in_(class_ids),
        TimetableSlot.school_id == school_id
    ).order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
    
    result = []
    for slot in timetable_slots:
        class_obj = db.query(Class).filter(Class.id == slot.class_id).first()
        subject = db.query(Subject).filter(Subject.id == slot.subject_id).first()
        teacher = db.query(User).filter(User.id == slot.teacher_id).first()
        
        result.append(TimetableSlotResponse(
            id=slot.id,
            class_id=slot.class_id,
            subject_id=slot.subject_id,
            teacher_id=slot.teacher_id,
            school_id=slot.school_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time.strftime("%H:%M") if slot.start_time else "",
            end_time=slot.end_time.strftime("%H:%M") if slot.end_time else "",
            room=slot.room,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            teacher_name=teacher.name if teacher else None
        ))
    
    return result


# ==================== STUDENT'S ANNOUNCEMENTS ====================

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_my_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get announcements targeted to students."""
    school_id = current_user.school_id
    
    announcements = db.query(Announcement).filter(
        Announcement.school_id == school_id,
        or_(
            Announcement.target_audience == "STUDENTS",
            Announcement.target_audience == "EVERYONE"
        )
    ).order_by(Announcement.published_at.desc()).all()
    
    return announcements


# ==================== STUDENT'S ATTENDANCE ====================

@router.get("/attendance", response_model=List[AttendanceResponse])
def get_my_attendance(
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    attendance_date: Optional[date] = Query(None, description="Filter by date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get the student's attendance records."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get classes this student is enrolled in
    enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    
    class_ids = [enrollment.class_id for enrollment in enrollments]
    if not class_ids:
        return []
    
    # Filter by class_id if provided
    if class_id:
        if class_id not in class_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
        class_ids = [class_id]
    
    # Get attendance records (filter by date only if provided)
    query = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.class_id.in_(class_ids),
        Attendance.school_id == school_id
    )
    
    if attendance_date:
        query = query.filter(Attendance.attendance_date == attendance_date)
    
    attendance_records = query.order_by(Attendance.attendance_date.desc()).all()
    
    result = []
    for record in attendance_records:
        class_obj = db.query(Class).filter(Class.id == record.class_id).first()
        
        result.append(AttendanceResponse(
            id=record.id,
            student_id=record.student_id,
            class_id=record.class_id,
            teacher_id=record.teacher_id,
            school_id=record.school_id,
            attendance_date=record.attendance_date,
            status=record.status,
            remarks=record.remarks,
            created_at=record.created_at,
            class_name=class_obj.name if class_obj else None
        ))
    
    return result


# ==================== STUDENT'S TEACHERS ====================

@router.get("/teachers", response_model=List[TeacherWithClassesResponse])
def get_my_teachers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get all teachers connected to the student through their enrolled classes."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get classes this student is enrolled in
    enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    
    class_ids = [enrollment.class_id for enrollment in enrollments]
    if not class_ids:
        return []
    
    # Get all classes with their teacher info
    classes = db.query(Class).filter(
        Class.id.in_(class_ids),
        Class.school_id == school_id
    ).all()
    
    # Group classes by teacher_id
    teacher_classes_map = {}
    for cls in classes:
        teacher_id = cls.teacher_id
        if teacher_id not in teacher_classes_map:
            teacher_classes_map[teacher_id] = []
        teacher_classes_map[teacher_id].append(cls)
    
    # Build response with unique teachers and their classes
    result = []
    for teacher_id, teacher_classes in teacher_classes_map.items():
        teacher = db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        
        if not teacher:
            continue
        
        # Build ClassResponse for each class
        class_responses = []
        for cls in teacher_classes:
            subject = db.query(Subject).filter(Subject.id == cls.subject_id).first()
            
            class_responses.append(ClassResponse(
                id=cls.id,
                name=cls.name,
                grade=cls.grade,
                subject_id=cls.subject_id,
                teacher_id=cls.teacher_id,
                school_id=cls.school_id,
                academic_year=cls.academic_year,
                subject_name=subject.name if subject else None,
                teacher_name=teacher.name
            ))
        
        result.append(TeacherWithClassesResponse(
            id=teacher.id,
            name=teacher.name,
            email=teacher.email,
            classes=class_responses
        ))
    
    return result


# ==================== STUDENT'S GRADES ====================

# Note: Grades/Assessments would typically be in a separate model
# For now, we'll return a placeholder endpoint
@router.get("/grades")
def get_my_grades(
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Get the student's grades/assessments."""
    student_id = current_user.id
    school_id = current_user.school_id
    
    # Get classes this student is enrolled in
    enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id
    ).all()
    
    class_ids = [enrollment.class_id for enrollment in enrollments]
    if not class_ids:
        return []
    
    # Filter by class_id if provided
    if class_id:
        if class_id not in class_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
        class_ids = [class_id]
    
    # TODO: Implement grades model and return actual grades
    # For now, return empty list
    return []

