import sqlite3
from pathlib import Path


class NonceStore:
    """Simple SQLite-backed nonce store to prevent replay attacks.

    Stores nonces with timestamps and provides an `is_used` check.
    """

    def __init__(self, db_path: str = "db/nonce_store.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(exist_ok=True)
        # For in-memory DBs, keep a single connection open so the schema persists
        self._conn = None
        if db_path == ":memory:":
            import sqlite3
            self._conn = sqlite3.connect(self.db_path)
            self._init_db()
        else:
            self._init_db()

    def _init_db(self):
        # Accept optional connection for in-memory usage
        import sqlite3
        def _create(conn):
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nonces (
                    nonce TEXT PRIMARY KEY,
                    created_at REAL
                )
                """
            )

        if hasattr(self, "_conn") and self._conn:
            _create(self._conn)
            return

        with sqlite3.connect(self.db_path) as conn:
            _create(conn)

    def use_nonce(self, nonce: str) -> bool:
        """Return True if nonce is newly recorded; False if already existed."""
        import sqlite3
        if self._conn:
            conn = self._conn
            cur = conn.execute("SELECT 1 FROM nonces WHERE nonce = ?", (nonce,))
            if cur.fetchone():
                return False
            conn.execute("INSERT INTO nonces (nonce, created_at) VALUES (?, strftime('%s','now'))", (nonce,))
            conn.commit()
            return True

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT 1 FROM nonces WHERE nonce = ?", (nonce,))
            if cur.fetchone():
                return False
            conn.execute("INSERT INTO nonces (nonce, created_at) VALUES (?, strftime('%s','now'))", (nonce,))
            return True
