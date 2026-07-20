
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, JSON, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# --- PRANA Integrity Models (Alpha-Veda Layer) ---
from app.models.prana_models import PranaPacket, ReviewOutputVersion, NextTaskVersion

# --- Dashboard Models ---
from app.models.dashboard_models import DashboardAlert, DashboardAction, DashboardAuditLog


# --- EMS & Governance Models ---

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # INSTITUTION, FAMILY
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="tenant")
    cohorts = relationship("Cohort", back_populates="tenant")

class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False) # e.g. "Grade 10-A"
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="cohorts")
    users = relationship("User", back_populates="cohort")

# Teacher-Student Assignment (Many-to-Many Relationship)
class TeacherStudentAssignment(Base):
    __tablename__ = "teacher_student_assignments"

    id = Column(String, primary_key=True, default=generate_uuid)
    teacher_id = Column(String, ForeignKey("users.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    cohort_id = Column(String, ForeignKey("cohorts.id"), nullable=True)  # Optional: specific class
    subject = Column(String, nullable=True)  # Optional: specific subject teacher teaches
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="taught_students")
    student = relationship("User", foreign_keys=[student_id], back_populates="assigned_teachers")
    cohort = relationship("Cohort")

    # Prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint('teacher_id', 'student_id', 'cohort_id', 'subject', name='unique_teacher_student_assignment'),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False) # ADMIN, TEACHER, PARENT, STUDENT
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    cohort_id = Column(String, ForeignKey("cohorts.id"), nullable=True) # For Students
    parent_id = Column(String, ForeignKey("users.id"), nullable=True) # For Students to link to Parent
    is_active = Column(Boolean, default=True)
    assessment_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # EMS Integration - Store token for one-time authentication
    ems_token = Column(String, nullable=True)  # Stored EMS JWT token
    ems_token_expires_at = Column(DateTime(timezone=True), nullable=True)  # Token expiration time

    tenant = relationship("Tenant", back_populates="users")
    cohort = relationship("Cohort", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False)
    lessons = relationship("Lesson", back_populates="user")
    summaries = relationship("Summary", back_populates="user")
    flashcards = relationship("Flashcard", back_populates="user")
    reflections = relationship("Reflection", back_populates="user")
    test_results = relationship("TestResult", back_populates="user")
    subject_data = relationship("SubjectData", back_populates="user")
    
    # Parent-Child relationships
    parent = relationship("User", remote_side=[id], foreign_keys=[parent_id], back_populates="children")
    children = relationship("User", foreign_keys=[parent_id], back_populates="parent")
    
    # Teacher-Student relationships (many-to-many)
    # Teachers have many assignments (use .taught_students to get assignment objects)
    # Then access .student on each assignment to get the student
    taught_students = relationship(
        "TeacherStudentAssignment",
        foreign_keys="[TeacherStudentAssignment.teacher_id]",
        back_populates="teacher",
        cascade="all, delete-orphan"
    )
    # Students have many assignments (use .assigned_teachers to get assignment objects)
    # Then access .teacher on each assignment to get the teacher
    assigned_teachers = relationship(
        "TeacherStudentAssignment",
        foreign_keys="[TeacherStudentAssignment.student_id]",
        back_populates="student",
        cascade="all, delete-orphan"
    )

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Generic JSON bag for Student/Teacher specific data
    # Student: grade, subjects, learning_style
    # Teacher: subjects_taught, qualifications
    data = Column(JSON, default={})
    
    user = relationship("User", back_populates="profile")

# --- Soul & Pedagogy Models ---

class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mood_score = Column(Integer, nullable=True) # 1-10
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reflections")

class LearningTrack(Base):
    __tablename__ = "learning_tracks"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True) # Optional: Global vs Tenant specific
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    milestones = relationship("Milestone", back_populates="track")

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(String, primary_key=True, default=generate_uuid)
    track_id = Column(String, ForeignKey("learning_tracks.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    
    track = relationship("LearningTrack", back_populates="milestones")
    student_progress = relationship("StudentProgress", back_populates="milestone")

class StudentProgress(Base):
    __tablename__ = "student_progress"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    milestone_id = Column(String, ForeignKey("milestones.id"), nullable=False)
    status = Column(String, default="NOT_STARTED") # NOT_STARTED, IN_PROGRESS, COMPLETED
    evidence = Column(Text, nullable=True) # Link to artifact or summary
    reflection_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User") # Simplify relationship for now
    milestone = relationship("Milestone", back_populates="student_progress")

# --- Learning Models ---

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, archived, draft
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="lessons")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Optional for now if guest access allowed
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_ = Column("metadata", JSON, default={}) # metadata is reserved in SQLAlchemy Base

    user = relationship("User", back_populates="summaries")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    question_type = Column(String, default="conceptual")
    days_until_review = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="flashcards")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, default="medium")
    num_questions = Column(Integer, nullable=False)
    questions = Column(JSON, nullable=False)  # Store all questions with options and correct answers
    user_answers = Column(JSON, nullable=False)  # Store user's selected answers
    score = Column(Integer, nullable=False)  # Number of correct answers
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)  # Score percentage
    time_taken = Column(Integer, nullable=True)  # Time taken in seconds (optional)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    synced_to_ems = Column(Boolean, default=False)  # Track if synced to EMS
    ems_sync_id = Column(String, nullable=True)  # Store EMS record ID after sync

    user = relationship("User", back_populates="test_results")

class SubjectData(Base):
    __tablename__ = "subject_data"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    notes = Column(Text, nullable=False)  # Generated notes/content
    provider = Column(String, default="groq")  # LLM provider used (groq, ollama)
    youtube_recommendations = Column(JSON, default=[])  # Store YouTube video recommendations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    synced_to_ems = Column(Boolean, default=False)  # Track if synced to EMS
    ems_sync_id = Column(String, nullable=True)  # Store EMS record ID after sync

    user = relationship("User", back_populates="subject_data")


# --- MDU Registry Hardened Persistence Models ---

class MduDataset(Base):
    __tablename__ = "mdu_datasets"

    id = Column(String, primary_key=True)  # e.g., "NCERT-S10-EN"
    board = Column(String, nullable=False)
    medium = Column(String, nullable=False)
    class_standard = Column(Integer, nullable=False)
    textbook_code = Column(String, nullable=False)
    canonical_name = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="DRAFT")  # ACTIVE, DRAFT, DEPRECATED, ROLLBACK_VERIFIED
    chunk_count = Column(Integer, nullable=False, default=0)
    trust_score = Column(Float, nullable=False, default=1.0)
    onboarding_state = Column(String, nullable=False, default="VALIDATION_STAGE")  # VALIDATION_STAGE, COMPLETED
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    lineage_nodes = Column(JSON, nullable=False)  # Node definitions
    lineage_links = Column(JSON, nullable=False)  # Link definitions

class MduProvenanceEvent(Base):
    __tablename__ = "mdu_provenance_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    operator = Column(String, nullable=False)
    action = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    hash = Column(String(64), nullable=False)

class MduReconciliationHistory(Base):
    __tablename__ = "mdu_reconciliation_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False)
    profile_audit_count = Column(Integer, nullable=False)
    board_preferences = Column(JSON, nullable=False)
    leakage_checks = Column(JSON, nullable=False)
    reconciliation_trace = Column(JSON, nullable=False)