"""
MongoDB Document Models
Replaces SQLModel ORM models with MongoDB document schemas.
Each model defines the shape of documents in its collection.
"""

import time
from typing import Optional, Dict, Any


def _now() -> float:
    return time.time()


# --- User ---
def user_document(
    user_id: str,
    username: str,
    password_hash: Optional[str] = None,
    email: Optional[str] = None,
    email_verified: bool = False,
    verification_token: Optional[str] = None,
    sub: Optional[str] = None,
    role: str = "user",
    last_login: Optional[float] = None,
    created_at: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "username": username,
        "password_hash": password_hash,
        "email": email,
        "email_verified": email_verified,
        "verification_token": verification_token,
        "sub": sub,
        "role": role,
        "last_login": last_login,
        "created_at": created_at or _now(),
    }


# --- Content ---
def content_document(
    content_id: str,
    uploader_id: str,
    title: str,
    file_path: str,
    content_type: str,
    description: Optional[str] = None,
    duration_ms: int = 0,
    uploaded_at: Optional[float] = None,
    authenticity_score: float = 0.0,
    current_tags: Optional[str] = None,
    views: int = 0,
    likes: int = 0,
    shares: int = 0,
) -> Dict[str, Any]:
    return {
        "content_id": content_id,
        "uploader_id": uploader_id,
        "title": title,
        "description": description,
        "file_path": file_path,
        "content_type": content_type,
        "duration_ms": duration_ms,
        "uploaded_at": uploaded_at or _now(),
        "authenticity_score": authenticity_score,
        "current_tags": current_tags,
        "views": views,
        "likes": likes,
        "shares": shares,
    }


# --- Feedback ---
def feedback_document(
    content_id: str,
    user_id: str,
    event_type: str,
    watch_time_ms: int = 0,
    reward: float = 0.0,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    sentiment: Optional[str] = None,
    engagement_score: Optional[float] = None,
    ip_address: Optional[str] = None,
    timestamp: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "content_id": content_id,
        "user_id": user_id,
        "event_type": event_type,
        "watch_time_ms": watch_time_ms,
        "reward": reward,
        "rating": rating,
        "comment": comment,
        "sentiment": sentiment,
        "engagement_score": engagement_score,
        "ip_address": ip_address,
        "timestamp": timestamp or _now(),
    }


# --- Script ---
def script_document(
    script_id: str,
    user_id: str,
    title: str,
    script_content: str,
    content_id: Optional[str] = None,
    script_type: str = "text",
    file_path: Optional[str] = None,
    created_at: Optional[float] = None,
    used_for_generation: bool = False,
    version: str = "1.0",
    script_metadata: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "script_id": script_id,
        "content_id": content_id,
        "user_id": user_id,
        "title": title,
        "script_content": script_content,
        "script_type": script_type,
        "file_path": file_path,
        "created_at": created_at or _now(),
        "used_for_generation": used_for_generation,
        "version": version,
        "script_metadata": script_metadata,
    }


# --- AuditLog ---
def audit_log_document(
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: Optional[str] = None,
    timestamp: Optional[float] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    details: Optional[str] = None,
    status: str = "success",
) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "timestamp": timestamp or _now(),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
        "details": details,
        "status": status,
    }


# --- Invitation ---
def invitation_document(
    email: str,
    inviter_id: str,
    invitation_token: str,
    created_at: Optional[float] = None,
    expires_at: float = 0.0,
    used: bool = False,
    used_at: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "email": email,
        "inviter_id": inviter_id,
        "invitation_token": invitation_token,
        "created_at": created_at or _now(),
        "expires_at": expires_at,
        "used": used,
        "used_at": used_at,
    }


# --- Analytics ---
def analytics_document(
    event_type: str,
    user_id: Optional[str] = None,
    content_id: Optional[str] = None,
    event_data: Optional[str] = None,
    timestamp: Optional[float] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "event_type": event_type,
        "user_id": user_id,
        "content_id": content_id,
        "event_data": event_data,
        "timestamp": timestamp or _now(),
        "ip_address": ip_address,
    }


# --- SystemLog ---
def system_log_document(
    level: str,
    message: str,
    module: Optional[str] = None,
    timestamp: Optional[float] = None,
    user_id: Optional[str] = None,
    extra_data: Optional[str] = None,
    error_details: Optional[str] = None,
    traceback: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "level": level,
        "message": message,
        "module": module,
        "timestamp": timestamp or _now(),
        "user_id": user_id,
        "extra_data": extra_data,
        "error_details": error_details,
        "traceback": traceback,
    }


# --- Rating (bhiv_core) ---
def rating_document(
    content_id: str,
    rating: Optional[int] = None,
    user_id: Optional[str] = None,
    comment: Optional[str] = None,
    created_at: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "content_id": content_id,
        "rating": rating,
        "user_id": user_id,
        "comment": comment,
        "created_at": created_at or _now(),
    }
