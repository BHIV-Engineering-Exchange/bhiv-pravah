"""
Unified Database Manager - MongoDB Backend
Replaces the triple-layered psycopg2/SQLModel/sqlite3 architecture.
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
load_dotenv()

from core.mongodb import get_database, get_collection, ensure_indexes
from core.mongo_models import (
    user_document, content_document, feedback_document,
    script_document, audit_log_document, analytics_document,
    system_log_document,
)

logger = logging.getLogger(__name__)

# Collection names
COL_USERS = "users"
COL_CONTENT = "content"
COL_FEEDBACK = "feedback"
COL_SCRIPTS = "scripts"
COL_AUDIT = "audit_logs"
COL_ANALYTICS = "analytics"
COL_SYSTEM_LOGS = "system_logs"
COL_INVITATIONS = "invitations"


def create_db_and_tables():
    """Create MongoDB indexes (equivalent to SQL CREATE TABLE)."""
    ensure_indexes()


class DatabaseManager:
    """Unified database manager using MongoDB."""

    # ── Users ──────────────────────────────────────────────

    @staticmethod
    def create_user(user_data: dict) -> Any:
        col = get_collection(COL_USERS)
        if col is None:
            raise Exception("MongoDB not available")
        doc = user_document(**user_data)
        col.update_one(
            {"user_id": doc["user_id"]},
            {"$set": doc},
            upsert=True,
        )
        logger.info("User created/updated: %s", doc["username"])
        return _AttrDict(doc)

    @staticmethod
    def get_user_by_username(username: str):
        col = get_collection(COL_USERS)
        if col is None:
            return None
        doc = col.find_one({"username": username})
        return _AttrDict(doc) if doc else None

    @staticmethod
    def get_user_by_id(user_id: str):
        col = get_collection(COL_USERS)
        if col is None:
            return None
        doc = col.find_one({"user_id": user_id})
        return _AttrDict(doc) if doc else None

    @staticmethod
    def update_user(user_id: str, update_data: dict) -> bool:
        col = get_collection(COL_USERS)
        if col is None:
            return False
        result = col.update_one({"user_id": user_id}, {"$set": update_data})
        return result.modified_count > 0

    # ── Content ────────────────────────────────────────────

    @staticmethod
    def create_content(content_data: dict) -> Any:
        col = get_collection(COL_CONTENT)
        if col is None:
            raise Exception("MongoDB not available")
        doc = content_document(**content_data)
        col.update_one(
            {"content_id": doc["content_id"]},
            {"$set": doc},
            upsert=True,
        )
        logger.info("Content saved: %s", doc["content_id"])
        return _AttrDict(doc)

    @staticmethod
    def get_content_by_id(content_id: str):
        col = get_collection(COL_CONTENT)
        if col is None:
            return None
        doc = col.find_one({"content_id": content_id})
        return _AttrDict(doc) if doc else None

    @staticmethod
    def get_recent_content(limit: int = 20) -> list:
        col = get_collection(COL_CONTENT)
        if col is None:
            return []
        docs = list(col.find().sort("uploaded_at", -1).limit(limit))
        return [_AttrDict(d) for d in docs]

    @staticmethod
    def update_content(content_id: str, update_data: dict) -> bool:
        col = get_collection(COL_CONTENT)
        if col is None:
            return False
        result = col.update_one({"content_id": content_id}, {"$set": update_data})
        return result.modified_count > 0

    @staticmethod
    def increment_content_views(content_id: str, count: int = 1) -> bool:
        col = get_collection(COL_CONTENT)
        if col is None:
            return False
        result = col.update_one(
            {"content_id": content_id},
            {"$inc": {"views": count}},
        )
        return result.modified_count > 0

    # ── Feedback ───────────────────────────────────────────

    @staticmethod
    def create_feedback(feedback_data: dict):
        col = get_collection(COL_FEEDBACK)
        if col is None:
            raise Exception("MongoDB not available")
        doc = feedback_document(**feedback_data)
        result = col.insert_one(doc)
        logger.info("Feedback saved: %s", result.inserted_id)
        return str(result.inserted_id)

    # ── Scripts ────────────────────────────────────────────

    @staticmethod
    def create_script(script_data: dict):
        col = get_collection(COL_SCRIPTS)
        if col is None:
            raise Exception("MongoDB not available")
        doc = script_document(**script_data)
        col.update_one(
            {"script_id": doc["script_id"]},
            {"$set": doc},
            upsert=True,
        )
        logger.info("Script saved: %s", doc["script_id"])
        return doc["script_id"]

    @staticmethod
    def get_script_by_id(script_id: str):
        col = get_collection(COL_SCRIPTS)
        if col is None:
            return None
        doc = col.find_one({"script_id": script_id})
        return _AttrDict(doc) if doc else None

    # ── Audit Logs ─────────────────────────────────────────

    @staticmethod
    def create_audit_log(audit_data: dict) -> bool:
        col = get_collection(COL_AUDIT)
        if col is None:
            return False
        doc = audit_log_document(**audit_data)
        col.insert_one(doc)
        return True

    # ── Analytics ──────────────────────────────────────────

    @staticmethod
    def save_analytics(event_type: str, user_id: str = None, content_id: str = None,
                       event_data: dict = None, ip_address: str = None) -> bool:
        col = get_collection(COL_ANALYTICS)
        if col is None:
            return False
        doc = analytics_document(
            event_type=event_type,
            user_id=user_id,
            content_id=content_id,
            event_data=json.dumps(event_data) if event_data else None,
            ip_address=ip_address,
        )
        col.insert_one(doc)
        return True

    @staticmethod
    def get_analytics_data() -> dict:
        col_a = get_collection(COL_ANALYTICS)
        col_u = get_collection(COL_USERS)
        col_c = get_collection(COL_CONTENT)
        col_f = get_collection(COL_FEEDBACK)
        col_s = get_collection(COL_SCRIPTS)

        try:
            total_users = col_u.estimated_document_count() if col_u else 0
            total_content = col_c.estimated_document_count() if col_c else 0
            total_feedback = col_f.estimated_document_count() if col_f else 0
            total_scripts = col_s.estimated_document_count() if col_s else 0

            # Average rating
            avg_rating = 0.0
            avg_engagement = 0.0
            sentiment_counts = {}

            if col_f:
                pipeline = [
                    {"$match": {"rating": {"$ne": None}}},
                    {"$group": {"_id": None, "avg": {"$avg": "$rating"}}},
                ]
                result = list(col_f.aggregate(pipeline))
                if result:
                    avg_rating = round(result[0]["avg"], 2)

                # Sentiment breakdown
                sentiment_pipeline = [
                    {"$match": {"sentiment": {"$ne": None}}},
                    {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
                ]
                sentiment_docs = list(col_f.aggregate(sentiment_pipeline))
                sentiment_counts = {d["_id"]: d["count"] for d in sentiment_docs}

                # Average engagement
                eng_pipeline = [
                    {"$match": {"engagement_score": {"$ne": None}}},
                    {"$group": {"_id": None, "avg": {"$avg": "$engagement_score"}}},
                ]
                eng_result = list(col_f.aggregate(eng_pipeline))
                if eng_result:
                    avg_engagement = round(eng_result[0]["avg"], 2)

            return {
                "total_users": total_users,
                "total_content": total_content,
                "total_feedback": total_feedback,
                "total_scripts": total_scripts,
                "average_rating": avg_rating,
                "average_engagement": avg_engagement,
                "sentiment_breakdown": sentiment_counts,
            }
        except Exception as e:
            logger.error("Analytics query failed: %s", e)
            return {
                "total_users": 0, "total_content": 0, "total_feedback": 0,
                "total_scripts": 0, "average_rating": 0.0, "average_engagement": 0.0,
                "sentiment_breakdown": {}, "error": str(e),
            }

    # ── System Logs ────────────────────────────────────────

    @staticmethod
    def save_system_log(level: str, message: str, module: str = None,
                        user_id: str = None, error_details: str = None,
                        traceback_str: str = None) -> bool:
        col = get_collection(COL_SYSTEM_LOGS)
        if col is None:
            return False
        doc = system_log_document(
            level=level, message=message, module=module,
            user_id=user_id, error_details=error_details,
            traceback=traceback_str,
        )
        col.insert_one(doc)
        return True

    # ── GDPR ───────────────────────────────────────────────

    @staticmethod
    def delete_user_data(user_id: str) -> bool:
        try:
            for name in [COL_FEEDBACK, COL_SCRIPTS, COL_CONTENT, COL_AUDIT, COL_ANALYTICS]:
                col = get_collection(name)
                if col is None:
                    continue
                if name == COL_CONTENT:
                    col.delete_many({"uploader_id": user_id})
                else:
                    col.delete_many({"user_id": user_id})
            col_u = get_collection(COL_USERS)
            if col_u:
                col_u.delete_one({"user_id": user_id})
            return True
        except Exception as e:
            logger.error("GDPR delete failed: %s", e)
            return False

    @staticmethod
    def export_user_data(user_id: str) -> dict:
        try:
            result = {}
            col_u = get_collection(COL_USERS)
            if col_u:
                result["user"] = col_u.find_one({"user_id": user_id})
            col_c = get_collection(COL_CONTENT)
            if col_c:
                result["content"] = list(col_c.find({"uploader_id": user_id}))
            for name in [COL_FEEDBACK, COL_SCRIPTS]:
                col = get_collection(name)
                if col:
                    result[name] = list(col.find({"user_id": user_id}))
            return result
        except Exception as e:
            logger.error("GDPR export failed: %s", e)
            return {}


class _AttrDict:
    """Dict-like object with attribute access (replaces MockUser/SupabaseUser classes)."""
    def __init__(self, data: dict):
        self._data = data or {}

    def __getattr__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        try:
            return self._data[name]
        except KeyError:
            return None

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return f"_AttrDict({self._data})"

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()


# Initialize database
create_db_and_tables()
db = DatabaseManager()
