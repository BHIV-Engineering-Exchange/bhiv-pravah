from sqlalchemy import Column, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class DashboardAlert(Base):
    __tablename__ = "dashboard_alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, nullable=False)  # e.g., "PACING", "COMPREHENSION", "ATTENDANCE", "INFRASTRUCTURE"
    priority = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)  # Assigned user ID (e.g., student or teacher)
    status = Column(String, nullable=False, default="OPEN")  # OPEN, RESOLVED, CLOSED
    created_by = Column(String, ForeignKey("users.id"), nullable=False)  # Creator user ID
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)  # Updater user ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Explicit relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="assigned_alerts")
    creator = relationship("User", foreign_keys=[created_by], backref="created_alerts")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_alerts")

class DashboardAction(Base):
    __tablename__ = "dashboard_actions"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)  # Assigned user ID
    status = Column(String, nullable=False, default="Created")  # Created, Assigned, In Progress, Completed, Closed, Cancelled
    created_by = Column(String, ForeignKey("users.id"), nullable=False)  # Creator user ID
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)  # Updater user ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Explicit relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="assigned_actions")
    creator = relationship("User", foreign_keys=[created_by], backref="created_actions")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_actions")

class DashboardAuditLog(Base):
    __tablename__ = "dashboard_audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)  # Who did the change
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)  # Additional audit tracker
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    entity = Column(String, nullable=False)  # "ALERT", "ACTION", etc.
    entity_id = Column(String, nullable=False)  # UUID of the target entity
    operation = Column(String, nullable=False)  # "CREATE", "ASSIGN", "UPDATE", "RESOLVE", "CLOSE", "CANCEL"
    status = Column(String, nullable=False)  # Status of target entity post-operation
    details = Column(JSON, nullable=True)  # Contextual JSON (e.g. old status, message)

    # Explicit relationship
    operator = relationship("User", foreign_keys=[created_by], backref="operations_performed")
