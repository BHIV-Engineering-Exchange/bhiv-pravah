import os
import threading
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
import logging

logger = logging.getLogger(__name__)

_client_lock = threading.Lock()
_client: MongoClient = None
_db = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                try:
                    max_pool = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
                    min_pool = int(os.getenv("MONGO_MIN_POOL_SIZE", "0"))
                    server_sel_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
                    connect_timeout = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
                    _client = MongoClient(
                        MONGO_URI,
                        maxPoolSize=max_pool,
                        minPoolSize=min_pool,
                        serverSelectionTimeoutMS=server_sel_timeout,
                        connectTimeoutMS=connect_timeout,
                    )
                    # Test connection
                    _client.admin.command('ping')
                    logger.info("MongoDB connection established")
                except Exception as e:
                    logger.warning(f"MongoDB connection failed: {e}")
                    _client = None
    return _client

def get_db():
    global _db
    if _db is None:
        client = get_client()
        if client:
            _db = client[DB_NAME]
    return _db

# Define separate collections for each data type with lazy loading
def _get_collection(name):
    db = get_db()
    return db[name] if db else None

@property
def users_col():
    return _get_collection("users")

@property  
def transactions_col():
    return _get_collection("transactions")

@property
def qtable_col():
    return _get_collection("q_table")

@property
def appeals_col():
    return _get_collection("appeals")

@property
def atonements_col():
    return _get_collection("atonements")

@property
def death_events_col():
    return _get_collection("death_events")

@property
def karma_events_col():
    return _get_collection("karma_events")

@property
def rnanubandhan_col():
    return _get_collection("rnanubandhan_relationships")

# Fallback for direct access (backwards compatibility)
try:
    db = get_db()
    if db is not None:
        users_col = db["users"]
        transactions_col = db["transactions"]
        qtable_col = db["q_table"]
        appeals_col = db["appeals"]
        atonements_col = db["atonements"]
        death_events_col = db["death_events"]
        karma_events_col = db["karma_events"]
        rnanubandhan_col = db["rnanubandhan_relationships"]
    else:
        # Create mock collections that return empty results
        class MockCollection:
            def find(self, *args, **kwargs):
                return []
            def count_documents(self, *args, **kwargs):
                return 0
            def find_one(self, *args, **kwargs):
                return None
        
        users_col = MockCollection()
        transactions_col = MockCollection()
        qtable_col = MockCollection()
        appeals_col = MockCollection()
        atonements_col = MockCollection()
        death_events_col = MockCollection()
        karma_events_col = MockCollection()
        rnanubandhan_col = MockCollection()
except Exception as e:
    logger.warning(f"Database initialization failed: {e}")
    # Create mock collections
    class MockCollection:
        def find(self, *args, **kwargs):
            return []
        def count_documents(self, *args, **kwargs):
            return 0
        def find_one(self, *args, **kwargs):
            return None
    
    users_col = MockCollection()
    transactions_col = MockCollection()
    qtable_col = MockCollection()
    appeals_col = MockCollection()
    atonements_col = MockCollection()
    death_events_col = MockCollection()
    karma_events_col = MockCollection()
    rnanubandhan_col = MockCollection()

def close_client():
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None