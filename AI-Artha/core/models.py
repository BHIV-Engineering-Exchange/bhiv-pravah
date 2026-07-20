"""
Database Models - Compatibility Layer
All models are now MongoDB documents defined in core/mongo_models.py.
This module exists for backward compatibility with imports like:
    from core.models import User, Content, Feedback
"""

from core.mongo_models import (
    user_document as User,
    content_document as Content,
    feedback_document as Feedback,
    script_document as Script,
    audit_log_document as AuditLog,
    invitation_document as Invitation,
    analytics_document as Analytics,
    system_log_document as SystemLog,
)

# Re-export for any code that imports these directly
__all__ = [
    "User", "Content", "Feedback", "Script",
    "AuditLog", "Invitation", "Analytics", "SystemLog",
]
