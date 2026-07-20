from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.dependencies import get_current_teacher
from app.models import (
    User, UserRole, Class, ClassStudent, Lesson, Lecture, 
    TimetableSlot, Subject, Announcement, Attendance,
    StudentSummary, StudentFlashcard, StudentTestResult, StudentSubjectData
)
from app.schemas import (
    ClassResponse, StudentResponse, 
    TimetableSlotResponse, AnnouncementResponse,
    AttendanceResponse, AttendanceBulkCreate,
    LessonCreate, LessonResponse, LectureCreate, LectureResponse,
    StudentSummaryResponse, StudentFlashcardResponse,
    StudentTestResultResponse, StudentSubjectDataResponse
)
from pydantic import BaseModel
from datetime import date, datetime

router = APIRouter(prefix="/teacher", tags=["teacher"])


# ==================== TEACHER DASHBOARD STATS ====================

class TeacherDashboardStats(BaseModel):
    total_classes: int
    total_students: int
    total_lessons: int
    upcoming_lessons: int


@router.get("/dashboard/stats", response_model=TeacherDashboardStats)
def get_teacher_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get teacher dashboard statistics."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Count classes assigned to this teacher
    total_classes = db.query(Class).filter(
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).count()
    
    # Count students in teacher's classes
    classes = db.query(Class).filter(
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).all()
    class_ids = [cls.id for cls in classes]
    total_students = db.query(ClassStudent).filter(
        ClassStudent.class_id.in_(class_ids)
    ).count() if class_ids else 0
    
    # Count total lessons
    total_lessons = db.query(Lesson).filter(
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id
    ).count()
    
    # Count upcoming lessons (today and future)
    today = date.today()
    upcoming_lessons = db.query(Lesson).filter(
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id,
        Lesson.lesson_date >= today
    ).count()
    
    return TeacherDashboardStats(
        total_classes=total_classes,
        total_students=total_students,
        total_lessons=total_lessons,
        upcoming_lessons=upcoming_lessons
    )


# ==================== TEACHER'S CLASSES ====================

@router.get("/classes", response_model=List[ClassResponse])
def get_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all classes assigned to the current teacher."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    classes = db.query(Class).filter(
        Class.teacher_id == teacher_id,
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


@router.get("/classes/{class_id}/students", response_model=List[StudentResponse])
def get_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all students in a specific class (only if teacher is assigned to that class)."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Verify teacher is assigned to this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you are not assigned to this class"
        )
    
    # Get all students enrolled in this class
    class_students = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id
    ).all()
    
    result = []
    for cs in class_students:
        student = db.query(User).filter(
            User.id == cs.student_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        ).first()
        
        if student:
            result.append(StudentResponse(
                id=student.id,
                name=student.name,
                email=student.email,
                grade=student.grade,
                school_id=student.school_id
            ))
    
    return result


# ==================== TEACHER'S LESSONS ====================

@router.get("/lessons")
def get_my_lessons(
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all lessons created by the current teacher."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    query = db.query(Lesson).filter(
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id
    )
    
    if class_id:
        query = query.filter(Lesson.class_id == class_id)
    
    lessons = query.order_by(Lesson.lesson_date.desc()).all()
    
    result = []
    for lesson in lessons:
        class_obj = db.query(Class).filter(Class.id == lesson.class_id).first()
        subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first() if class_obj else None
        lectures = db.query(Lecture).filter(Lecture.lesson_id == lesson.id).all()
        
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "class_id": lesson.class_id,
            "teacher_id": lesson.teacher_id,
            "lesson_date": lesson.lesson_date.isoformat(),
            "class_name": class_obj.name if class_obj else None,
            "subject_name": subject.name if subject else None,
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


@router.post("/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    lesson_data: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Create a new lesson with optional lectures."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Verify class belongs to this teacher
    class_obj = db.query(Class).filter(
        Class.id == lesson_data.class_id,
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you are not assigned to this class"
        )
    
    # Create lesson
    lesson = Lesson(
        title=lesson_data.title,
        description=lesson_data.description,
        class_id=lesson_data.class_id,
        teacher_id=teacher_id,
        school_id=school_id,
        lesson_date=lesson_data.lesson_date
    )
    
    db.add(lesson)
    db.flush()  # Get the lesson ID
    
    # Create lectures if provided
    created_lectures = []
    if lesson_data.lectures:
        for lecture_data in lesson_data.lectures:
            # Parse time strings to time objects
            start_time_obj = None
            end_time_obj = None
            
            if lecture_data.start_time:
                try:
                    start_time_obj = datetime.strptime(lecture_data.start_time, "%H:%M").time()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_time format. Use HH:MM format (e.g., 09:00). Got: {lecture_data.start_time}"
                    )
            
            if lecture_data.end_time:
                try:
                    end_time_obj = datetime.strptime(lecture_data.end_time, "%H:%M").time()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_time format. Use HH:MM format (e.g., 10:30). Got: {lecture_data.end_time}"
                    )
            
            lecture = Lecture(
                lesson_id=lesson.id,
                title=lecture_data.title,
                content=lecture_data.content,
                lecture_date=lecture_data.lecture_date,
                start_time=start_time_obj,
                end_time=end_time_obj
            )
            db.add(lecture)
            created_lectures.append(lecture)
    
    db.commit()
    db.refresh(lesson)
    
    # Refresh lectures to get their IDs
    for lecture in created_lectures:
        db.refresh(lecture)
    
    # Get class and subject names for response
    subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first()
    
    # Build lecture responses
    lecture_responses = []
    for lecture in created_lectures:
        lecture_responses.append(LectureResponse(
            id=lecture.id,
            lesson_id=lecture.lesson_id,
            title=lecture.title,
            content=lecture.content,
            lecture_date=lecture.lecture_date,
            start_time=lecture.start_time.strftime("%H:%M") if lecture.start_time else None,
            end_time=lecture.end_time.strftime("%H:%M") if lecture.end_time else None
        ))
    
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        class_id=lesson.class_id,
        teacher_id=lesson.teacher_id,
        school_id=lesson.school_id,
        lesson_date=lesson.lesson_date,
        class_name=class_obj.name,
        subject_name=subject.name if subject else None,
        lectures=lecture_responses
    )


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: int,
    lesson_data: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Update a lesson."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Get lesson
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id
    ).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found or you are not authorized to update it"
        )
    
    # Verify class belongs to this teacher
    class_obj = db.query(Class).filter(
        Class.id == lesson_data.class_id,
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you are not assigned to this class"
        )
    
    # Update lesson fields
    lesson.title = lesson_data.title
    lesson.description = lesson_data.description
    lesson.class_id = lesson_data.class_id
    lesson.lesson_date = lesson_data.lesson_date
    
    # Delete existing lectures
    existing_lectures = db.query(Lecture).filter(Lecture.lesson_id == lesson_id).all()
    for lecture in existing_lectures:
        db.delete(lecture)
    
    # Create new lectures if provided
    created_lectures = []
    if lesson_data.lectures:
        for lecture_data in lesson_data.lectures:
            start_time_obj = None
            end_time_obj = None
            
            if lecture_data.start_time:
                try:
                    start_time_obj = datetime.strptime(lecture_data.start_time, "%H:%M").time()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_time format. Use HH:MM format (e.g., 09:00). Got: {lecture_data.start_time}"
                    )
            
            if lecture_data.end_time:
                try:
                    end_time_obj = datetime.strptime(lecture_data.end_time, "%H:%M").time()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_time format. Use HH:MM format (e.g., 10:30). Got: {lecture_data.end_time}"
                    )
            
            lecture = Lecture(
                lesson_id=lesson.id,
                title=lecture_data.title,
                content=lecture_data.content,
                lecture_date=lecture_data.lecture_date,
                start_time=start_time_obj,
                end_time=end_time_obj
            )
            db.add(lecture)
            created_lectures.append(lecture)
    
    db.commit()
    db.refresh(lesson)
    
    # Refresh lectures to get their IDs
    for lecture in created_lectures:
        db.refresh(lecture)
    
    # Get class and subject names for response
    subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first()
    
    # Build lecture responses
    lecture_responses = []
    for lecture in created_lectures:
        lecture_responses.append(LectureResponse(
            id=lecture.id,
            lesson_id=lecture.lesson_id,
            title=lecture.title,
            content=lecture.content,
            lecture_date=lecture.lecture_date,
            start_time=lecture.start_time.strftime("%H:%M") if lecture.start_time else None,
            end_time=lecture.end_time.strftime("%H:%M") if lecture.end_time else None
        ))
    
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        class_id=lesson.class_id,
        teacher_id=lesson.teacher_id,
        school_id=lesson.school_id,
        lesson_date=lesson.lesson_date,
        class_name=class_obj.name,
        subject_name=subject.name if subject else None,
        lectures=lecture_responses
    )


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Delete a lesson."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Get lesson
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id
    ).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found or you are not authorized to delete it"
        )
    
    print(f"[LESSON DELETION] Teacher {teacher_id} deleting lesson {lesson_id} from school {school_id}")
    try:
        # Delete associated lectures first
        lectures_count = db.query(Lecture).filter(Lecture.lesson_id == lesson_id).delete()
        print(f"[LESSON DELETION] Deleted {lectures_count} associated lectures")
        
        # Delete lesson
        db.delete(lesson)
        db.commit()
        print(f"[LESSON DELETION] Successfully deleted lesson {lesson_id}")
    except Exception as e:
        db.rollback()
        print(f"[LESSON DELETION] Failed to delete lesson {lesson_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson: {str(e)}"
        )
    
    return None


# ==================== TEACHER'S TIMETABLE ====================

@router.get("/timetable", response_model=List[TimetableSlotResponse])
def get_my_timetable(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get the current teacher's timetable/schedule."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    timetable_slots = db.query(TimetableSlot).filter(
        TimetableSlot.teacher_id == teacher_id,
        TimetableSlot.school_id == school_id
    ).order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
    
    result = []
    for slot in timetable_slots:
        class_obj = db.query(Class).filter(Class.id == slot.class_id).first()
        subject = db.query(Subject).filter(Subject.id == slot.subject_id).first()
        
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
            teacher_name=current_user.name
        ))
    
    return result


# ==================== TEACHER'S ANNOUNCEMENTS ====================

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_my_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get announcements targeted to teachers."""
    school_id = current_user.school_id
    
    announcements = db.query(Announcement).filter(
        Announcement.school_id == school_id,
        or_(
            Announcement.target_audience == "TEACHERS",
            Announcement.target_audience == "EVERYONE"
        )
    ).order_by(Announcement.published_at.desc()).all()
    
    result = []
    for ann in announcements:
        creator = db.query(User).filter(User.id == ann.created_by).first()
        
        result.append(AnnouncementResponse(
            id=ann.id,
            title=ann.title,
            content=ann.content,
            target_audience=ann.target_audience,
            school_id=ann.school_id,
            published_at=ann.published_at,
            created_by=ann.created_by,
            created_by_name=creator.name if creator else None
        ))
    
    return result


# ==================== ATTENDANCE MANAGEMENT ====================

@router.get("/attendance", response_model=List[AttendanceResponse])
def get_attendance(
    class_id: int = Query(..., description="Class ID"),
    attendance_date: Optional[date] = Query(None, description="Attendance date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get attendance records for a class on a specific date (defaults to today)."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Verify teacher is assigned to this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you are not assigned to this class"
        )
    
    # Default to today if no date provided
    if not attendance_date:
        attendance_date = date.today()
    
    # Get attendance records
    attendance_records = db.query(Attendance).filter(
        Attendance.class_id == class_id,
        Attendance.attendance_date == attendance_date,
        Attendance.school_id == school_id
    ).all()
    
    result = []
    for att in attendance_records:
        student = db.query(User).filter(User.id == att.student_id).first()
        result.append(AttendanceResponse(
            id=att.id,
            student_id=att.student_id,
            class_id=att.class_id,
            teacher_id=att.teacher_id,
            school_id=att.school_id,
            attendance_date=att.attendance_date,
            status=att.status,
            remarks=att.remarks,
            created_at=att.created_at,
            student_name=student.name if student else None,
            class_name=class_obj.name
        ))
    
    return result


@router.post("/attendance/mark", response_model=List[AttendanceResponse])
def mark_attendance(
    attendance_data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Mark attendance for multiple students in a class."""
    try:
        teacher_id = current_user.id
        school_id = current_user.school_id
        
        # Verify teacher is assigned to this class
        class_obj = db.query(Class).filter(
            Class.id == attendance_data.class_id,
            Class.teacher_id == teacher_id,
            Class.school_id == school_id
        ).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found or you are not assigned to this class"
            )
        
        # Validate status values
        valid_statuses = ["PRESENT", "ABSENT", "LATE", "EXCUSED"]
        
        # Check if attendance already exists for this date
        existing_attendance = db.query(Attendance).filter(
            Attendance.class_id == attendance_data.class_id,
            Attendance.attendance_date == attendance_data.attendance_date,
            Attendance.school_id == school_id
        ).all()
        
        # Delete existing attendance for this date/class
        for existing in existing_attendance:
            db.delete(existing)
        
        # Create new attendance records
        created_records = []
        for record in attendance_data.attendance_records:
            if record.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {record.status}. Must be one of: {', '.join(valid_statuses)}"
                )
            
            # Verify student is enrolled in this class
            enrollment = db.query(ClassStudent).filter(
                ClassStudent.class_id == attendance_data.class_id,
                ClassStudent.student_id == record.student_id
            ).first()
            
            if not enrollment:
                continue  # Skip students not enrolled in this class
            
            attendance = Attendance(
                student_id=record.student_id,
                class_id=attendance_data.class_id,
                teacher_id=teacher_id,
                school_id=school_id,
                attendance_date=attendance_data.attendance_date,
                status=record.status,
                remarks=record.remarks
            )
            
            db.add(attendance)
            created_records.append(attendance)
        
        db.commit()
        
        # Refresh and return created records
        result = []
        for att in created_records:
            db.refresh(att)
            student = db.query(User).filter(User.id == att.student_id).first()
            result.append(AttendanceResponse(
                id=att.id,
                student_id=att.student_id,
                class_id=att.class_id,
                teacher_id=att.teacher_id,
                school_id=att.school_id,
                attendance_date=att.attendance_date,
                status=att.status,
                remarks=att.remarks,
                created_at=att.created_at,
                student_name=student.name if student else None,
                class_name=class_obj.name
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error marking attendance: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking attendance: {str(e)}"
        )


# ==================== STUDENT-GENERATED CONTENT (GURUKUL) ====================

@router.get("/students/{student_id}/content/summaries", response_model=List[StudentSummaryResponse])
def get_student_summaries(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all summaries generated by a student in Gurukul (for teacher's assigned students)"""
    # Verify student is in teacher's classes
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    if not class_ids:
        return []
    
    student_enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id,
        ClassStudent.class_id.in_(class_ids)
    ).first()
    
    if not student_enrollments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view content for students in your classes"
        )
    
    # Get summaries
    summaries = db.query(StudentSummary).filter(
        StudentSummary.student_id == student_id
    ).order_by(StudentSummary.created_at.desc()).all()
    
    student = db.query(User).filter(User.id == student_id).first()
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
def get_student_flashcards(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all flashcards generated by a student in Gurukul (for teacher's assigned students)"""
    # Verify student is in teacher's classes
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    if not class_ids:
        return []
    
    student_enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id,
        ClassStudent.class_id.in_(class_ids)
    ).first()
    
    if not student_enrollments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view content for students in your classes"
        )
    
    # Get flashcards
    flashcards = db.query(StudentFlashcard).filter(
        StudentFlashcard.student_id == student_id
    ).order_by(StudentFlashcard.created_at.desc()).all()
    
    student = db.query(User).filter(User.id == student_id).first()
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
def get_student_test_results(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all test results for a student from Gurukul (for teacher's assigned students)"""
    # Verify student is in teacher's classes
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    if not class_ids:
        return []
    
    student_enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id,
        ClassStudent.class_id.in_(class_ids)
    ).first()
    
    if not student_enrollments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view content for students in your classes"
        )
    
    # Get test results
    test_results = db.query(StudentTestResult).filter(
        StudentTestResult.student_id == student_id
    ).order_by(StudentTestResult.created_at.desc()).all()
    
    student = db.query(User).filter(User.id == student_id).first()
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
def get_student_subject_data(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all subject explorer data for a student from Gurukul (for teacher's assigned students)"""
    # Verify student is in teacher's classes
    teacher_classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_ids = [c.id for c in teacher_classes]
    
    if not class_ids:
        return []
    
    student_enrollments = db.query(ClassStudent).filter(
        ClassStudent.student_id == student_id,
        ClassStudent.class_id.in_(class_ids)
    ).first()
    
    if not student_enrollments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view content for students in your classes"
        )
    
    # Get subject data
    subject_data = db.query(StudentSubjectData).filter(
        StudentSubjectData.student_id == student_id
    ).order_by(StudentSubjectData.created_at.desc()).all()
    
    student = db.query(User).filter(User.id == student_id).first()
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

