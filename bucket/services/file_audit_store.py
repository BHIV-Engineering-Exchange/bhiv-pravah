import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Iterator, List
from uuid import uuid4


class InsertOneResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class FileAuditCursor:
    def __init__(self, path: Path, query: Optional[Dict] = None):
        self.path = path
        self.query = query or {}
        self._limit = None
        self._sort = None

    def sort(self, key: str, direction: int):
        self._sort = (key, direction)
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def _match(self, entry: Dict[str, Any]) -> bool:
        # Basic exact-match filtering and limited $in support
        for k, v in self.query.items():
            if isinstance(v, dict) and "$in" in v:
                if entry.get(k) not in v["$in"]:
                    return False
            elif isinstance(v, dict) and "$in" not in v:
                # unsupported operator, skip filter
                continue
            else:
                if entry.get(k) != v:
                    return False
        return True

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if not self.path.exists():
            return iter(entries)

        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if self._match(entry):
                    entries.append(entry)

        # Apply sort if requested
        if self._sort:
            key, direction = self._sort
            reverse = direction < 0
            entries.sort(key=lambda e: e.get(key), reverse=reverse)

        # Apply limit
        if self._limit is not None:
            entries = entries[: self._limit]

        return iter(entries)


class FileAuditStore:
    """Simple JSONL-based audit store used as a persistent fallback when MongoDB is not available.

    Each audit entry is stored as a single JSON object per line. This store implements
    `insert_one` and `find` with a cursor-like API that supports `sort` and `limit`.
    """

    def __init__(self, file_path: Optional[str] = None):
        base = Path(file_path) if file_path else Path("data") / "audit.log"
        base_parent = base.parent
        base_parent.mkdir(parents=True, exist_ok=True)
        self.path = base

    @staticmethod
    def _json_default(value: Any):
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def insert_one(self, doc: Dict[str, Any]):
        # Ensure deterministic timestamp and id
        entry = dict(doc)
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.utcnow().isoformat()
        if "_id" not in entry:
            entry["_id"] = f"file_{uuid4().hex}"

        # Serialize and append as JSONL
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=self._json_default) + "\n")

        return InsertOneResult(inserted_id=entry["_id"])

    def find(self, query: Optional[Dict] = None):
        return FileAuditCursor(self.path, query=query)
