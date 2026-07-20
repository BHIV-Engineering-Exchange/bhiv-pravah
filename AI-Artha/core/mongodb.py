"""
MongoDB Connection Manager
Replaces psycopg2, sqlite3, and SQLModel engine with a single MongoDB backend.
"""

import os
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database as MongoDatabase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_agent")

_client: MongoClient = None
_database: MongoDatabase = None


def get_client() -> MongoClient:
    """Get or create the shared MongoClient (singleton)."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
        # Verify connection
        try:
            _client.admin.command("ping")
            print(f"SUCCESS: Connected to MongoDB at {MONGO_URI}")
        except Exception as e:
            print(f"WARNING: MongoDB connection failed: {e}")
            print("INFO: Running without persistent database")
    return _client


def get_database() -> MongoDatabase:
    """Get or create the shared database reference."""
    global _database
    if _database is None:
        client = get_client()
        if client is not None:
            _database = client[MONGO_DB_NAME]
    return _database


def get_collection(name: str) -> Collection:
    """Get a collection by name, creating indexes if needed."""
    db = get_database()
    if db is None:
        return None
    return db[name]


def ensure_indexes():
    """Create indexes for all collections. Called once at startup."""
    db = get_database()
    if db is None:
        return

    try:
        # Users
        db["users"].create_index([("username", ASCENDING)], unique=True)
        db["users"].create_index([("user_id", ASCENDING)], unique=True)
        db["users"].create_index([("email", ASCENDING)], sparse=True)

        # Content
        db["content"].create_index([("content_id", ASCENDING)], unique=True)
        db["content"].create_index([("uploader_id", ASCENDING)])
        db["content"].create_index([("uploaded_at", DESCENDING)])

        # Feedback
        db["feedback"].create_index([("content_id", ASCENDING)])
        db["feedback"].create_index([("user_id", ASCENDING)])
        db["feedback"].create_index([("timestamp", DESCENDING)])

        # Scripts
        db["scripts"].create_index([("script_id", ASCENDING)], unique=True)
        db["scripts"].create_index([("content_id", ASCENDING)])
        db["scripts"].create_index([("user_id", ASCENDING)])

        # Audit logs
        db["audit_logs"].create_index([("timestamp", DESCENDING)])
        db["audit_logs"].create_index([("user_id", ASCENDING)])
        db["audit_logs"].create_index([("action", ASCENDING)])

        # Analytics
        db["analytics"].create_index([("timestamp", DESCENDING)])
        db["analytics"].create_index([("event_type", ASCENDING)])
        db["analytics"].create_index([("user_id", ASCENDING)])

        # System logs
        db["system_logs"].create_index([("timestamp", DESCENDING)])
        db["system_logs"].create_index([("level", ASCENDING)])
        db["system_logs"].create_index([("module", ASCENDING)])

        # Invitations
        db["invitations"].create_index([("invitation_token", ASCENDING)], unique=True)
        db["invitations"].create_index([("email", ASCENDING)])

        # Ratings (from bhiv_core)
        db["ratings"].create_index([("content_id", ASCENDING)])
        db["ratings"].create_index([("user_id", ASCENDING)])

        print("SUCCESS: MongoDB indexes created/verified")
    except Exception as e:
        print(f"WARNING: MongoDB index creation failed: {e}")


def close_connection():
    """Close the MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
        print("INFO: MongoDB connection closed")
