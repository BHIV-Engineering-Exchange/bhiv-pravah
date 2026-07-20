from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import date, datetime
from app.models import UserRole


# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: UserRole
    school_id: Optional[int] = None


# User Schemas (core)
class UserBase(BaseModel):
    """
    Base schema for user data where strict email validation is desired
    (e.g. auth flows, user creation).
    """
    name: str
    email: EmailStr
    role: UserRole
    school_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True


class UserDashboardResponse(BaseModel):
    """
    Relaxed response schema for Super Admin dashboard listings.
    Uses plain string for email so a single bad row in the DB
    does not crash the whole /dashboard/users endpoint.
    """
    id: int
    name: str
    email: str  # deliberately not EmailStr to avoid ResponseValidationError on bad data
    role: UserRole
    school_id: Optional[int] = None

    class Config:
        from_attributes = True


# Super Admin Setup Response
class SuperAdminSetupResponse(BaseModel):
    success: bool
    message: str
    already_exists: bool = False


# Password Setup Schemas
class SetPasswordRequest(BaseModel):
    token: str
    password: str


class SetPasswordResponse(BaseModel):
    success: bool
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    old_password: str  # Current password (required for security)
    new_password: str


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    success: bool
    message: str


class InviteAdminRequest(BaseModel):
    name: str
    email: EmailStr
    school_id: int


class InviteAdminResponse(BaseModel):
    success: bool
    message: str
    admin_id: int
    email: str


# ==================== SCHOOL ADMIN DASHBOARD SCHEMAS ====================

# Teacher Schemas
class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    subject: Optional[str] = None
    school_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    subject: Optional[str] = None


# Student Schemas
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    grade: str
    parent_email: Optional[EmailStr] = None
    parent_name: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    grade: Optional[str] = None
    school_id: Optional[int] = None
    parent_emails: Optional[List[str]] = None  # List of linked parent emails
    parent_names: Optional[List[str]] = None  # List of linked parent names
    
    class Config:
        from_attributes = True


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    grade: Optional[str] = None


# Parent Schemas
class ParentCreate(BaseModel):
    name: str
    email: EmailStr
    student_email: Optional[EmailStr] = None


class ParentResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    school_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class ParentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


# Subject Schemas
class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    school_id: int
    
    class Config:
        from_attributes = True


# Class Schemas
class ClassCreate(BaseModel):
    name: str
    grade: str
    subject_id: int
    teacher_id: int
    academic_year: Optional[str] = None


class ClassResponse(BaseModel):
    id: int
    name: str
    grade: str
    subject_id: int
    teacher_id: int
    school_id: int
    academic_year: Optional[str] = None
    subject_name: Optional[str] = None  # Subject name for display
    teacher_name: Optional[str] = None  # Teacher name for display
    
    class Config:
        from_attributes = True


class TeacherWithClassesResponse(BaseModel):
    """Response schema for teacher with their classes."""
    id: int
    name: str
    email: str
    classes: List[ClassResponse]  # Classes this teacher teaches that the student is enrolled in
    
    class Config:
        from_attributes = True


# Timetable Schemas
class TimetableSlotCreate(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: int
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # Format: "HH:MM"
    end_time: str  # Format: "HH:MM"
    room: Optional[str] = None


class TimetableSlotResponse(BaseModel):
    id: int
    class_id: int
    subject_id: int
    teacher_id: int
    school_id: int
    day_of_week: int
    start_time: str
    end_time: str
    room: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Holiday Schemas
class HolidayCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    description: Optional[str] = None


class HolidayResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    description: Optional[str] = None
    school_id: int
    
    class Config:
        from_attributes = True


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


# Event Schemas
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    event_time: Optional[str] = None
    event_type: str  # "Exam", "PTM", "Annual Day", etc.


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    event_date: date
    event_time: Optional[str] = None
    event_type: str
    school_id: int
    
    class Config:
        from_attributes = True


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    event_time: Optional[str] = None
    event_type: Optional[str] = None


# Announcement Schemas
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    target_audience: str  # "TEACHERS", "STUDENTS", "PARENTS", "EVERYONE"


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    target_audience: str
    school_id: int
    published_at: datetime
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_audience: Optional[str] = None


class DashboardStatsResponse(BaseModel):
    total_teachers: int
    total_students: int
    total_parents: int
    total_classes: int
    total_lessons: int
    todays_classes: int
    upcoming_holidays: int
    upcoming_events: int


class ExcelUploadResponse(BaseModel):
    success: bool
    message: str
    success_count: int
    failed_count: int
    failed_rows: List[dict] = []


# Parent-Student Mapping Schemas
class StudentParentLinkCreate(BaseModel):
    student_id: int
    parent_id: int
    relationship_type: Optional[str] = "Parent"


class StudentParentLinkResponse(BaseModel):
    id: int
    student_id: int
    parent_id: int
    relationship_type: Optional[str] = None
    student_name: str
    student_email: str
    parent_name: str
    parent_email: str
    
    class Config:
        from_attributes = True


class StudentWithParentsResponse(BaseModel):
    id: int
    name: str
    email: str
    grade: Optional[str] = None
    school_id: Optional[int] = None
    linked_parents: List[dict] = []
    
    class Config:
        from_attributes = True


class ParentWithStudentsResponse(BaseModel):
    id: int
    name: str
    email: str
    school_id: Optional[int] = None
    linked_students: List[dict] = []
    
    class Config:
        from_attributes = True


class ParentStudentStatsResponse(BaseModel):
    total_parents: int
    total_students: int
    unlinked_students: int
    unlinked_parents: int
    total_links: int
    students_per_parent: List[dict] = []
    parents_per_student: List[dict] = []


# Analytics/Visualization Schemas
class TeacherWorkloadResponse(BaseModel):
    teacher_id: int
    teacher_name: str
    subject: Optional[str] = None
    total_classes: int
    total_students: int


class GradeDistributionResponse(BaseModel):
    grade: str
    student_count: int
    teacher_count: int
    class_count: int


class SubjectDistributionResponse(BaseModel):
    subject_id: int
    subject_name: str
    student_count: int
    teacher_count: int
    class_count: int


class ParentStudentRelationResponse(BaseModel):
    parent_id: int
    parent_name: str
    parent_email: str
    children_count: int
    children: List[dict] = []


class AnalyticsResponse(BaseModel):
    # Teacher Analytics
    teacher_workload: List[TeacherWorkloadResponse] = []
    teachers_by_subject: List[dict] = []
    
    # Student Analytics
    students_by_grade: List[GradeDistributionResponse] = []
    students_by_subject: List[SubjectDistributionResponse] = []
    
    # Parent Analytics
    parents_by_children_count: List[dict] = []
    parent_student_relations: List[ParentStudentRelationResponse] = []
    
    # Summary Stats
    total_teachers: int = 0
    total_students: int = 0
    total_parents: int = 0
    total_classes: int = 0
    total_subjects: int = 0
    
    # Linking Stats
    linked_students: int = 0
    unlinked_students: int = 0


# ==================== LESSON SCHEMAS ====================

class LectureCreate(BaseModel):
    title: str
    content: Optional[str] = None
    lecture_date: date
    start_time: Optional[str] = None  # Format: "HH:MM"
    end_time: Optional[str] = None  # Format: "HH:MM"


class LessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    class_id: int
    lesson_date: date
    lectures: Optional[List[LectureCreate]] = []


class LectureResponse(BaseModel):
    id: int
    lesson_id: int
    title: str
    content: Optional[str] = None
    lecture_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    class Config:
        from_attributes = True


class LessonResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    class_id: int
    teacher_id: int
    school_id: int
    lesson_date: date
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    lectures: List[LectureResponse] = []
    
    class Config:
        from_attributes = True


# ==================== ATTENDANCE SCHEMAS ====================

class AttendanceRecord(BaseModel):
    student_id: int
    status: str  # "PRESENT", "ABSENT", "LATE", "EXCUSED"
    remarks: Optional[str] = None


class AttendanceCreate(BaseModel):
    student_id: int
    class_id: int
    attendance_date: date
    status: str  # "PRESENT", "ABSENT", "LATE", "EXCUSED"
    remarks: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    class_id: int
    attendance_date: date
    attendance_records: List[AttendanceRecord]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    class_id: int
    teacher_id: int
    school_id: int
    attendance_date: date
    status: str
    remarks: Optional[str] = None
    created_at: datetime
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Student Content Sync Schemas (from Gurukul)

class StudentContentSyncBase(BaseModel):
    student_email: EmailStr
    school_id: Optional[int] = None
    gurukul_id: str  # Gurukul record ID for tracking


class StudentSummarySync(StudentContentSyncBase):
    title: str
    content: str
    source: Optional[str] = None
    source_type: str = "text"
    extra_metadata: Optional[Dict] = None  # Renamed from 'metadata' (reserved word)


class StudentFlashcardSync(StudentContentSyncBase):
    question: str
    answer: str
    question_type: str = "conceptual"
    days_until_review: int = 0
    confidence: float = 0.0


class StudentTestResultSync(StudentContentSyncBase):
    subject: str
    topic: str
    difficulty: str = "medium"
    num_questions: int
    questions: List[Dict]  # All questions with options and correct answers
    user_answers: Dict  # Student's selected answers
    score: int
    total_questions: int
    percentage: float
    time_taken: Optional[int] = None


class StudentSubjectDataSync(StudentContentSyncBase):
    subject: str
    topic: str
    notes: str
    provider: str = "groq"
    youtube_recommendations: Optional[List[Dict]] = None


class StudentContentSyncResponse(BaseModel):
    id: int
    message: str
    synced_at: datetime
    
    class Config:
        from_attributes = True


# Response schemas for viewing student-generated content
class StudentSummaryResponse(BaseModel):
    id: int
    gurukul_id: str
    student_id: int
    student_name: str
    student_email: str
    title: str
    content: str
    source: Optional[str] = None
    source_type: Optional[str] = None
    extra_metadata: Optional[Dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudentFlashcardResponse(BaseModel):
    id: int
    gurukul_id: str
    student_id: int
    student_name: str
    student_email: str
    question: str
    answer: str
    question_type: Optional[str] = None
    days_until_review: int
    confidence: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudentTestResultResponse(BaseModel):
    id: int
    gurukul_id: str
    student_id: int
    student_name: str
    student_email: str
    subject: str
    topic: str
    difficulty: Optional[str] = None
    total_questions: int
    correct_answers: int
    score_percentage: float
    results_data: Optional[Dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudentSubjectDataResponse(BaseModel):
    id: int
    gurukul_id: str
    student_id: int
    student_name: str
    student_email: str
    subject: str
    topic: str
    notes: str
    provider: Optional[str] = None
    youtube_recommendations: Optional[List[Dict]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
