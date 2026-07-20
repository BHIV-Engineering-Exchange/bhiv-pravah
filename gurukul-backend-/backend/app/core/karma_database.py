import os
import threading
import sys
from pymongo import MongoClient
from app.core.karma_config import MONGO_URI, DB_NAME

print("[Karma DB] Module loading...", flush=True)
sys.stdout.flush()

_client_lock = threading.Lock()
_client: MongoClient = None
_db = None

def get_client() -> MongoClient:
    """Lazy MongoDB client - only connects when actually needed with retry logic"""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                print("[Karma DB] Creating MongoDB client (lazy connection)...", flush=True)
                sys.stdout.flush()
                max_pool = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
                min_pool = int(os.getenv("MONGO_MIN_POOL_SIZE", "0"))
                server_sel_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
                connect_timeout = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
                
                try:
                    _client = MongoClient(
                        MONGO_URI,
                        maxPoolSize=max_pool,
                        minPoolSize=min_pool,
                        serverSelectionTimeoutMS=server_sel_timeout,
                        connectTimeoutMS=connect_timeout,
                        connect=False,  # Still lazy, but prepared
                    )
                    # Verify on first access
                    print("[Karma DB] MongoDB client created. Host: " + MONGO_URI.split('@')[-1].split('/')[0] if '@' in MONGO_URI else 'Localhost', flush=True)
                except Exception as e:
                    print(f"[Karma DB] [FAIL] Critical error creating MongoClient: {e}")
                    raise
    
    # Check if client is still alive
    try:
        _client.admin.command('ping')
    except Exception as e:
        print(f"[Karma DB] Connection lost or stale. Attempting to refresh client... {e}")
        with _client_lock:
            _client = None
            return get_client()
            
    return _client

def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db

# Lazy collection loader class to avoid blocking during import
class LazyCollection:
    """Lazy-loads MongoDB collections only when accessed"""
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._collection = None
    
    def _ensure_collection(self):
        """Ensure collection is loaded"""
        if self._collection is None:
            try:
                self._collection = get_db()[self.collection_name]
            except Exception as e:
                print(f"[Karma DB] Warning: Could not access collection '{self.collection_name}': {e}")
                raise RuntimeError(f"MongoDB collection '{self.collection_name}' is not available: {e}")
        return self._collection
    
    def __getattr__(self, name):
        return getattr(self._ensure_collection(), name)
    
    def __getitem__(self, key):
        return self._ensure_collection()[key]
    
    def __setitem__(self, key, value):
        self._ensure_collection()[key] = value
    
    def __iter__(self):
        return iter(self._ensure_collection())
    
    def __len__(self):
        return len(self._ensure_collection())
    
    def __call__(self, *args, **kwargs):
        return self._ensure_collection()(*args, **kwargs)

# Define separate collections for each data type - lazy loaded to avoid blocking on import
users_col = LazyCollection("users")
transactions_col = LazyCollection("transactions")
qtable_col = LazyCollection("q_table")
appeals_col = LazyCollection("appeals")
atonements_col = LazyCollection("atonements")
death_events_col = LazyCollection("death_events")
karma_events_col = LazyCollection("karma_events")
rnanubandhan_col = LazyCollection("rnanubandhan_relationships")

def close_client():
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None