import sqlite3
import json
import threading
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for production-ready data storage"""
    
    def __init__(self, db_path: str = "data/hr_system.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self.init_database()
    
    @property
    def connection(self):
        """Thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.transaction() as conn:
            # Candidates table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    skills TEXT NOT NULL,  -- JSON array
                    match_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Feedback table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    feedback_score INTEGER NOT NULL CHECK (feedback_score BETWEEN 1 AND 5),
                    comment TEXT NOT NULL,
                    actual_outcome TEXT NOT NULL CHECK (actual_outcome IN ('accept', 'reject', 'reconsider')),
                    hr_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                )
            """)
            
            # Communication logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS communication_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    channel TEXT NOT NULL,  -- email, whatsapp, voice
                    event_type TEXT NOT NULL,
                    status TEXT NOT NULL,  -- success, failed, pending
                    message TEXT,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                )
            """)
            
            # System logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
                    event TEXT NOT NULL,
                    message TEXT,
                    details TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table for authentication
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    permissions TEXT,  -- JSON array
                    active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates (email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_candidate ON feedback (candidate_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_comm_logs_candidate ON communication_logs (candidate_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_created ON system_logs (created_at)")
    
    # Candidate operations
    def add_candidate(self, candidate_data: Dict[str, Any]) -> int:
        """Add new candidate to database"""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO candidates (name, email, phone, skills, match_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                candidate_data['name'],
                candidate_data['email'],
                candidate_data['phone'],
                json.dumps(candidate_data['skills']),
                candidate_data.get('match_score', 0.0)
            ))
            return cursor.lastrowid
    
    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """Get candidate by ID"""
        cursor = self.connection.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        )
        row = cursor.fetchone()
        if row:
            candidate = dict(row)
            candidate['skills'] = json.loads(candidate['skills'])
            return candidate
        return None
    
    def get_all_candidates(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all candidates"""
        query = "SELECT * FROM candidates"
        params = ()
        
        if active_only:
            query += " WHERE status = ?"
            params = ('active',)
        
        query += " ORDER BY created_at DESC"
        
        cursor = self.connection.execute(query, params)
        candidates = []
        for row in cursor.fetchall():
            candidate = dict(row)
            candidate['skills'] = json.loads(candidate['skills'])
            candidates.append(candidate)
        return candidates
    
    # Feedback operations
    def add_feedback(self, feedback_data: Dict[str, Any]) -> int:
        """Add feedback to database"""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO feedback (candidate_id, feedback_score, comment, actual_outcome, hr_name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                feedback_data['candidate_id'],
                feedback_data['feedback_score'],
                feedback_data['comment'],
                feedback_data['actual_outcome'],
                feedback_data.get('hr_name', 'System')
            ))
            return cursor.lastrowid
    
    # Communication logging
    def log_communication(self, log_data: Dict[str, Any]) -> int:
        """Log communication attempt"""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO communication_logs (candidate_id, channel, event_type, status, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_data['candidate_id'],
                log_data['channel'],
                log_data['event_type'],
                log_data['status'],
                log_data.get('message', ''),
                json.dumps(log_data.get('metadata', {}))
            ))
            return cursor.lastrowid
    
    # System logging
    def log_system_event(self, level: str, event: str, message: str = "", details: Dict[str, Any] = None):
        """Log system event"""
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO system_logs (level, event, message, details)
                VALUES (?, ?, ?, ?)
            """, (level, event, message, json.dumps(details or {})))
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create database backup"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/hr_system_backup_{timestamp}.db"
        
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use SQLite backup API
        source = self.connection
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        backup.close()
        
        return str(backup_path)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        tables = ['candidates', 'feedback', 'communication_logs', 'system_logs', 'users']
        for table in tables:
            try:
                cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            except:
                stats[f"{table}_count"] = 0
        
        return stats
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        cursor = self.connection.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
        )
        row = cursor.fetchone()
        if row:
            user = dict(row)
            user['permissions'] = json.loads(user['permissions'])
            return user
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create new user"""
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO users (username, password_hash, role, permissions)
                VALUES (?, ?, ?, ?)
            """, (
                user_data['username'],
                user_data['password_hash'],
                user_data.get('role', 'user'),
                json.dumps(user_data.get('permissions', ['read']))
            ))
            return cursor.lastrowid
    
    def get_feedback_by_candidate(self, candidate_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a candidate"""
        cursor = self.connection.execute(
            "SELECT * FROM feedback WHERE candidate_id = ? ORDER BY created_at DESC",
            (candidate_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_communication_history(self, candidate_id: int) -> List[Dict[str, Any]]:
        """Get communication history for candidate"""
        cursor = self.connection.execute(
            "SELECT * FROM communication_logs WHERE candidate_id = ? ORDER BY created_at DESC",
            (candidate_id,)
        )
        logs = []
        for row in cursor.fetchall():
            log = dict(row)
            log['metadata'] = json.loads(log['metadata'])
            logs.append(log)
        return logs
    
    def get_system_logs(self, level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs"""
        query = "SELECT * FROM system_logs"
        params = ()
        
        if level:
            query += " WHERE level = ?"
            params = (level,)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        
        cursor = self.connection.execute(query, params)
        logs = []
        for row in cursor.fetchall():
            log = dict(row)
            log['details'] = json.loads(log['details'])
            logs.append(log)
        return logs
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log entries"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM system_logs WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            )
            system_deleted = cursor.rowcount
            
            cursor = conn.execute(
                "DELETE FROM communication_logs WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            )
            comm_deleted = cursor.rowcount
            
            return {
                'system_logs_deleted': system_deleted,
                'communication_logs_deleted': comm_deleted
            }

# Global database instance
db_manager = DatabaseManager()

# Migration utilities
class DatabaseMigration:
    """Handle database schema migrations"""
    
    @staticmethod
    def migrate_from_json():
        """Migrate existing JSON data to database"""
        from app.utils.helpers import load_json
        
        try:
            candidates = load_json("data/candidates.json", [])
            for candidate in candidates:
                try:
                    if 'id' in candidate:
                        del candidate['id']
                    db_manager.add_candidate(candidate)
                except Exception as e:
                    logger.error(f"Failed to migrate candidate {candidate.get('name', 'unknown')}: {e}")
            
            logger.info(f"Migrated {len(candidates)} candidates to database")
            
        except Exception as e:
            logger.warning(f"JSON migration failed (normal for new installations): {e}")