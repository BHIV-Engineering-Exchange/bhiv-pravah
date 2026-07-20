"""
PRANA Packet Models

Database models for storing PRANA packets from the frontend and the
monitoring-only PRANA runtime integrity stream.
"""

from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Boolean, Index, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class PranaPacket(Base):
    """
    PRANA Packet - Stores packets from PRANA system before Karma Tracker processes them.
    
    Each packet represents 5 seconds of user activity data.
    """
    __tablename__ = "prana_packets"

    # Primary key
    packet_id = Column(String, primary_key=True, default=generate_uuid, index=True)
    
    # User identification
    user_id = Column(String, nullable=True, index=True)  # Gurukul user ID
    employee_id = Column(String, nullable=True, index=True)  # EMS employee ID (legacy)
    session_id = Column(String, nullable=True, index=True)
    lesson_id = Column(String, nullable=True)
    
    # System context
    system_type = Column(String, nullable=True)  # "gurukul" or "ems"
    role = Column(String, nullable=True)  # "student" or "employee"
    
    # Timestamps
    client_timestamp = Column(DateTime(timezone=True), nullable=False)  # When PRANA created the packet
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # When bucket received it
    processed_at = Column(DateTime(timezone=True), nullable=True)  # When Karma Tracker processed it
    
    # Cognitive state
    cognitive_state = Column(String, nullable=True)  # Unified states: ON_TASK, THINKING, IDLE, etc.
    state = Column(String, nullable=True)  # Legacy state field
    
    # Time accounting (must sum to 5.0)
    active_seconds = Column(Float, nullable=False)
    idle_seconds = Column(Float, nullable=False)
    away_seconds = Column(Float, nullable=False)
    
    # Scores
    focus_score = Column(Float, nullable=True)  # 0-100
    integrity_score = Column(Float, nullable=True)  # 0-1 (legacy)
    
    # Raw signals (stored as JSON)
    raw_signals = Column(JSON, nullable=False, default=dict)
    
    # Processing status
    processed_by_karma = Column(Boolean, default=False, nullable=False, index=True)
    karma_actions = Column(JSON, nullable=True, default=list)  # List of karma actions generated from this packet
    processing_error = Column(Text, nullable=True)  # Error message if processing failed
    
    # Integrity Hardening (Phase 1)
    previous_hash = Column(String(64), nullable=True, index=True)
    current_hash = Column(String(64), nullable=True, index=True)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_processed', 'user_id', 'processed_by_karma'),
        Index('idx_received_at', 'received_at'),
        Index('idx_processed_at', 'processed_at'),
        Index('idx_integrity_chain', 'previous_hash', 'current_hash'),
    )


class ReviewOutputVersion(Base):
    """
    Versioning for PRANA Evaluation Reviews.
    Ensures that every revision of a review is tracked and chained.
    """
    __tablename__ = "review_output_versions"

    id = Column(Integer, primary_key=True)
    submission_id = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    review_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Integrity
    previous_hash = Column(String(64), nullable=True, index=True)
    current_hash = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        Index('idx_review_version', 'submission_id', 'version', unique=True),
    )


class NextTaskVersion(Base):
    """
    Versioning for PRANA Next-Task recommendations.
    Ensures that every change to the recommended next task is cryptographically chained.
    """
    __tablename__ = "next_task_versions"

    id = Column(Integer, primary_key=True)
    submission_id = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    next_task_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Integrity
    previous_hash = Column(String(64), nullable=True, index=True)
    current_hash = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        Index('idx_task_version', 'submission_id', 'version', unique=True),
    )


class PranaIntegrityLog(Base):
    """
    Append-only integrity events emitted by the monitoring-only PRANA runtime.
    """
    __tablename__ = "prana_integrity_log"

    event_id = Column(String, primary_key=True, default=generate_uuid, index=True)
    submission_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    freshness_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    payload_hash = Column(String(64), nullable=False, index=True)
    source_system = Column(String, nullable=False, index=True)
    expected_sequence = Column(Integer, nullable=False, default=1)
    actual_sequence = Column(Integer, nullable=True)
    gap_detected = Column(Boolean, nullable=False, default=False, index=True)
    out_of_order = Column(Boolean, nullable=False, default=False, index=True)
    anomaly_count = Column(Integer, nullable=False, default=0)
    replay_status = Column(String, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_prana_integrity_source_submission", "source_system", "submission_id", "received_at"),
        Index("idx_prana_integrity_sequence", "source_system", "submission_id", "expected_sequence"),
    )


class PranaAnomalyEvent(Base):
    """
    Detected anomaly markers for PRANA runtime signals.
    """
    __tablename__ = "anomaly_event"

    id = Column(Integer, primary_key=True)
    event_id = Column(String, nullable=True, index=True)
    submission_id = Column(String, nullable=False, index=True)
    source_system = Column(String, nullable=False, index=True)
    anomaly_type = Column(String, nullable=False, index=True)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class PranaVitalityMetric(Base):
    """
    Current vitality view for a monitored source stream.
    """
    __tablename__ = "prana_vitality"

    stream_key = Column(String, primary_key=True)
    source_system = Column(String, nullable=False, index=True)
    submission_id = Column(String, nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    gap_count = Column(Integer, nullable=False, default=0)
    anomaly_count = Column(Integer, nullable=False, default=0)
    freshness_status = Column(String, nullable=False, default="unknown", index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_prana_vitality_stream", "source_system", "submission_id", unique=True),
    )


class ReplayValidationLog(Base):
    """
    Append-only replay verification results for integrity events.
    """
    __tablename__ = "replay_validation_log"

    validation_id = Column(String, primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String, nullable=False, index=True)
    replay_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    computed_hash = Column(String(64), nullable=False)
    stored_hash = Column(String(64), nullable=False)
    validation_result = Column(String, nullable=False, index=True)
    source_system = Column(String, nullable=False, index=True)

