import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading

class ContextMemory:
    """SQLite-based context memory for storing user interactions"""
    
    def __init__(self, db_path: str = "data/context.db"):
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables"""
        # Enable WAL mode and set a busy timeout to improve concurrency
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            # Create table with module column
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    module TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    request_data TEXT NOT NULL,
                    response_data TEXT NOT NULL
                )
            """)
            # Generations table records canonical mapping from external generation_id -> interaction
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    generation_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    interaction_id INTEGER,
                    created_at TEXT,
                    payload TEXT
                )
            """)
            
            # Check if module column exists (for existing databases)
            cursor = conn.execute("PRAGMA table_info(interactions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'module' not in columns:
                try:
                    # Add module column to existing table
                    conn.execute("ALTER TABLE interactions ADD COLUMN module TEXT DEFAULT 'unknown'")
                except sqlite3.OperationalError:
                    # Column already exists, ignore
                    pass
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_module_timestamp 
                ON interactions(user_id, module, timestamp DESC)
            """)
    
    def _ensure_table_exists(self, conn):
        """Ensure table exists in current connection (for in-memory databases)"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                module TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                request_data TEXT NOT NULL,
                response_data TEXT NOT NULL
            )
        """)
        # Ensure generations table exists for in-memory DBs as well
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                generation_id TEXT PRIMARY KEY,
                user_id TEXT,
                interaction_id INTEGER,
                created_at TEXT,
                payload TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_module_timestamp 
            ON interactions(user_id, module, timestamp DESC)
        """)
    
    def store_interaction(self, user_id: str, request_data: Dict[str, Any], 
                         response_data: Dict[str, Any]):
        """Store a request-response interaction"""
        timestamp = datetime.now().isoformat()
        module = request_data.get("module", "unknown")

        # Use a lock to provide concurrency safety for writes from multiple threads/processes
        with self._lock:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                self._ensure_table_exists(conn)
                cursor = conn.cursor()
                try:
                    cursor.execute("BEGIN IMMEDIATE TRANSACTION")
                    cursor.execute(
                        """
                        INSERT INTO interactions (user_id, module, timestamp, request_data, response_data)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (user_id, module, timestamp, json.dumps(request_data), json.dumps(response_data))
                    )
                    interaction_id = cursor.lastrowid

                    # If response includes generation_id, persist mapping for deterministic lifecycle
                    try:
                        resp_result = response_data.get('result', {}) if isinstance(response_data, dict) else {}
                        gen_id = None
                        if isinstance(resp_result, dict):
                            gen_id = resp_result.get('generation_id')
                        # Also check top-level response_data for legacy payloads
                        if not gen_id and isinstance(response_data, dict):
                            gen_id = response_data.get('generation_id')

                        if gen_id:
                            cursor.execute(
                                """
                                INSERT OR REPLACE INTO generations (generation_id, user_id, interaction_id, created_at, payload)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (str(gen_id), user_id, interaction_id, timestamp, json.dumps({"request": request_data, "response": response_data}))
                            )
                    except Exception:
                        # Do not let generation mapping failures block main transaction
                        pass

                    # Deterministic retention: keep newest by timestamp, then id
                    cursor.execute(
                        """
                        DELETE FROM interactions
                        WHERE id IN (
                            SELECT id FROM interactions
                            WHERE user_id = ? AND module = ?
                            ORDER BY timestamp DESC, id DESC
                            LIMIT -1 OFFSET 5
                        )
                        """,
                        (user_id, module)
                    )

                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
    
    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get full interaction history for a user"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            self._ensure_table_exists(conn)
            cursor = conn.execute(
                """
                SELECT module, timestamp, request_data, response_data
                FROM interactions
                WHERE user_id = ?
                ORDER BY timestamp DESC, id DESC
            """,
                (user_id,)
            )

            return [
                {
                    "module": row[0],
                    "timestamp": row[1],
                    "request": json.loads(row[2]),
                    "response": json.loads(row[3])
                }
                for row in cursor.fetchall()
            ]
    
    def get_context(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent context (last N interactions) for a user"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            self._ensure_table_exists(conn)
            cursor = conn.execute(
                """
                SELECT module, timestamp, request_data, response_data
                FROM interactions
                WHERE user_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
            """,
                (user_id, limit)
            )

            return [
                {
                    "module": row[0],
                    "timestamp": row[1],
                    "request": json.loads(row[2]),
                    "response": json.loads(row[3])
                }
                for row in cursor.fetchall()
            ]

    def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored generation mapping and associated interaction payload."""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            self._ensure_table_exists(conn)
            cursor = conn.execute(
                """
                SELECT generation_id, user_id, interaction_id, created_at, payload
                FROM generations
                WHERE generation_id = ?
            """,
                (str(generation_id),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            payload = json.loads(row[4]) if row[4] else None
            # Fetch the interaction record if available
            inter = None
            if row[2]:
                c2 = conn.execute(
                    """
                    SELECT module, timestamp, request_data, response_data
                    FROM interactions
                    WHERE id = ?
                """,
                    (row[2],)
                )
                r2 = c2.fetchone()
                if r2:
                    inter = {
                        "module": r2[0],
                        "timestamp": r2[1],
                        "request": json.loads(r2[2]),
                        "response": json.loads(r2[3])
                    }

            return {
                "generation_id": row[0],
                "user_id": row[1],
                "interaction": inter,
                "created_at": row[3],
                "payload": payload
            }