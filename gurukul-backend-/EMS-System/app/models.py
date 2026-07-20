from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, DateTime, Text, Date, Time, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from datetime import datetime, date, time
import enum
from app.database import Base, engine


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    STUDENT = "STUDENT"


# Create the ENUM type in PostgreSQL if it doesn't exist
user_role_enum = PG_ENUM(UserRole, name="user_role", create_type=True)


class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="school")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True)  # Hashed password (nullable until set)
    role = Column(user_role_enum, nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    subject = Column(String(255), nullable=True)  # Subject for teachers (nullable for other roles)
    grade = Column(String(50), nullable=True)  # Grade for students (nullable for other roles)
    
    # Relationships
    school = relationship("School", back_populates="users")
    password_tokens = relationship("PasswordToken", back_populates="user", cascade="all, delete-orphan")

class PasswordToken(Base):
    __tablename__ = "password_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="password_tokens")


# School Admin Dashboard Models

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    school = relationship("School")
    classes = relationship("Class", back_populates="subject")


class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # e.g., "Grade 5A", "Class 10B"
    grade = Column(String(50), nullable=False, index=True)  # e.g., "5", "10"
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=True)  # e.g., "2024-2025"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    subject = relationship("Subject", back_populates="classes")
    teacher = relationship("User", foreign_keys=[teacher_id])
    school = relationship("School")
    class_students = relationship("ClassStudent", back_populates="class_obj", cascade="all, delete-orphan")
    timetable_slots = relationship("TimetableSlot", back_populates="class_obj", cascade="all, delete-orphan")


class ClassStudent(Base):
    """Many-to-many relationship between Classes and Students"""
    __tablename__ = "class_students"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    class_obj = relationship("Class", back_populates="class_students")
    student = relationship("User", foreign_keys=[student_id])


class StudentParent(Base):
    """Many-to-many relationship between Students and Parents"""
    __tablename__ = "student_parents"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=True)  # e.g., "Father", "Mother", "Guardian"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    parent = relationship("User", foreign_keys=[parent_id])


class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    lesson_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    class_obj = relationship("Class")
    teacher = relationship("User", foreign_keys=[teacher_id])
    school = relationship("School")
    lectures = relationship("Lecture", back_populates="lesson", cascade="all, delete-orphan")


class Lecture(Base):
    __tablename__ = "lectures"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    lecture_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="lectures")


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    class_obj = relationship("Class", back_populates="timetable_slots")
    subject = relationship("Subject")
    teacher = relationship("User", foreign_keys=[teacher_id])
    school = relationship("School")


class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    school = relationship("School")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_date = Column(Date, nullable=False, index=True)
    event_time = Column(Time, nullable=True)
    event_type = Column(String(50), nullable=False, index=True)  # e.g., "Exam", "PTM", "Annual Day"
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    school = relationship("School")


class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    target_audience = Column(String(50), nullable=False, index=True)  # "TEACHERS", "STUDENTS", "PARENTS", "EVERYONE"
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    published_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    school = relationship("School")
    creator = relationship("User", foreign_keys=[created_by])


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # "PRESENT", "ABSENT", "LATE", "EXCUSED"
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    class_obj = relationship("Class")
    teacher = relationship("User", foreign_keys=[teacher_id])
    school = relationship("School")


# Student-Generated Content Models (Synced from Gurukul)

class StudentSummary(Base):
    """Student-generated PDF summaries and text summaries from Gurukul"""
    __tablename__ = "student_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    gurukul_id = Column(String(255), nullable=False, unique=True, index=True)  # Gurukul record ID for syncing
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)  # Source file/URL
    source_type = Column(String(50), nullable=True)  # "pdf", "text", "manual"
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata from Gurukul (renamed from 'metadata' - reserved word)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    school = relationship("School")


class StudentFlashcard(Base):
    """Student-generated flashcards from Gurukul"""
    __tablename__ = "student_flashcards"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    gurukul_id = Column(String(255), nullable=False, unique=True, index=True)  # Gurukul record ID for syncing
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    question_type = Column(String(50), default="conceptual")
    days_until_review = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    school = relationship("School")


class StudentTestResult(Base):
    """Student test/quiz results from Gurukul"""
    __tablename__ = "student_test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    gurukul_id = Column(String(255), nullable=False, unique=True, index=True)  # Gurukul record ID for syncing
    subject = Column(String(255), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    difficulty = Column(String(50), default="medium")
    num_questions = Column(Integer, nullable=False)
    questions = Column(JSON, nullable=False)  # All questions with options and correct answers
    user_answers = Column(JSON, nullable=False)  # Student's selected answers
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    time_taken = Column(Integer, nullable=True)  # Time taken in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    school = relationship("School")


class StudentSubjectData(Base):
    """Student-generated subject explorer content from Gurukul"""
    __tablename__ = "student_subject_data"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    gurukul_id = Column(String(255), nullable=False, unique=True, index=True)  # Gurukul record ID for syncing
    subject = Column(String(255), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    notes = Column(Text, nullable=False)  # Generated notes/content
    provider = Column(String(50), default="groq")  # LLM provider used
    youtube_recommendations = Column(JSON, default=[])  # YouTube video recommendations
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    school = relationship("School")


# --- PRANA-E / BHIV Bucket Ledger ---

class PranaPacket(Base):
    """Append-only ledger of PRANA-E telemetry packets (EMS side BHIV Bucket)."""
    __tablename__ = "prana_packets"

    id = Column(Integer, primary_key=True, index=True)
    packet_id = Column(String(64), unique=True, nullable=False, index=True)
    employee_id = Column(String(255), nullable=False, index=True)
    state = Column(String(32), nullable=False, index=True)  # WORKING | IDLE | AWAY | DISTRACTED | FAKING
    integrity_score = Column(Float, nullable=False)
    active_seconds = Column(Float, nullable=False)
    idle_seconds = Column(Float, nullable=False)
    away_seconds = Column(Float, nullable=False)
    raw_signals = Column(JSON, nullable=False)  # stored as-is (no mutation)
    client_timestamp = Column(DateTime, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)