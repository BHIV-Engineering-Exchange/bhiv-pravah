"""Cross-layer audit persistence for integration readiness validation."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import DATA_DIR, LOGS_DIR


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class IntegrationAuditStore:
    """SQLite-backed request, portfolio, news, and log proof store."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        log_path: Optional[Path] = None,
    ) -> None:
        self.db_path = Path(db_path or (DATA_DIR / "integration_audit.db"))
        self.log_path = Path(log_path or (LOGS_DIR / "integration_audit.jsonl"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS integration_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    symbol TEXT,
                    price REAL,
                    quantity REAL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    portfolio_json TEXT NOT NULL,
                    log_json TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    success INTEGER NOT NULL,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS portfolio_positions (
                    symbol TEXT PRIMARY KEY,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    last_price REAL NOT NULL,
                    updated_at TEXT NOT NULL,
                    request_id TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS news_items (
                    news_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT,
                    region TEXT,
                    sentiment TEXT NOT NULL,
                    impact_score REAL NOT NULL,
                    tags_json TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    response_json TEXT NOT NULL
                );
                """
            )

    def get_portfolio_state(self) -> Dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT symbol, quantity, avg_price, last_price, updated_at, request_id "
                "FROM portfolio_positions ORDER BY symbol"
            ).fetchall()

        positions = []
        total_value = 0.0
        for row in rows:
            value = float(row["quantity"]) * float(row["last_price"])
            total_value += value
            positions.append(
                {
                    "symbol": row["symbol"],
                    "quantity": row["quantity"],
                    "avg_price": row["avg_price"],
                    "last_price": row["last_price"],
                    "market_value": round(value, 4),
                    "timestamp": row["updated_at"],
                    "request_id": row["request_id"],
                }
            )
        return {
            "positions": positions,
            "total_positions": len(positions),
            "total_value": round(total_value, 4),
        }

    def record_event(
        self,
        *,
        endpoint: str,
        request_id: str,
        timestamp: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
        symbol: Optional[str],
        price: Optional[float],
        quantity: Optional[float],
        portfolio_state: Dict[str, Any],
        status_code: int,
        success: bool,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        log_entry = {
            "endpoint": endpoint,
            "request_id": request_id,
            "timestamp": timestamp,
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "status_code": status_code,
            "success": success,
            "error": error,
        }
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute(
                """
                INSERT INTO integration_events (
                    endpoint, request_id, timestamp, symbol, price, quantity,
                    request_json, response_json, portfolio_json, log_json,
                    status_code, success, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    endpoint,
                    request_id,
                    timestamp,
                    symbol,
                    price,
                    quantity,
                    json.dumps(request_payload, sort_keys=True, default=str),
                    json.dumps(response_payload, sort_keys=True, default=str),
                    json.dumps(portfolio_state, sort_keys=True, default=str),
                    json.dumps(log_entry, sort_keys=True, default=str),
                    status_code,
                    1 if success else 0,
                    error,
                ),
            )
            conn.commit()

        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log_entry, sort_keys=True, default=str) + "\n")
        return log_entry

    def update_portfolio(
        self,
        *,
        request_id: str,
        timestamp: str,
        symbol: str,
        price: float,
        quantity: float,
    ) -> Dict[str, Any]:
        if quantity == 0:
            raise ValueError("quantity must not be zero")

        with self._connect() as conn:
            conn.execute("BEGIN")
            existing = conn.execute(
                "SELECT quantity, avg_price FROM portfolio_positions WHERE symbol = ?",
                (symbol,),
            ).fetchone()
            if existing:
                old_qty = float(existing["quantity"])
                old_avg = float(existing["avg_price"])
                new_qty = old_qty + quantity
                if new_qty < 0:
                    raise ValueError("portfolio update would make quantity negative")
                if new_qty == 0:
                    conn.execute("DELETE FROM portfolio_positions WHERE symbol = ?", (symbol,))
                else:
                    avg_price = (
                        ((old_qty * old_avg) + (quantity * price)) / new_qty
                        if quantity > 0
                        else old_avg
                    )
                    conn.execute(
                        """
                        UPDATE portfolio_positions
                        SET quantity = ?, avg_price = ?, last_price = ?, updated_at = ?, request_id = ?
                        WHERE symbol = ?
                        """,
                        (new_qty, avg_price, price, timestamp, request_id, symbol),
                    )
            else:
                if quantity < 0:
                    raise ValueError("cannot sell a symbol that is not in the portfolio")
                conn.execute(
                    """
                    INSERT INTO portfolio_positions
                        (symbol, quantity, avg_price, last_price, updated_at, request_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (symbol, quantity, price, price, timestamp, request_id),
                )
            conn.commit()

        return self.get_portfolio_state()

    def record_news(
        self,
        *,
        request_id: str,
        timestamp: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
        sentiment: str,
        impact_score: float,
        tags: list[str],
    ) -> None:
        metadata = request_payload.get("metadata") or {}
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute(
                """
                INSERT INTO news_items (
                    news_id, request_id, timestamp, title, content, source,
                    category, region, sentiment, impact_score, tags_json,
                    raw_json, response_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_payload["news_id"],
                    request_id,
                    timestamp,
                    request_payload["title"],
                    request_payload["content"],
                    request_payload["source"],
                    metadata.get("category"),
                    metadata.get("region"),
                    sentiment,
                    impact_score,
                    json.dumps(tags, sort_keys=True),
                    json.dumps(request_payload, sort_keys=True, default=str),
                    json.dumps(response_payload, sort_keys=True, default=str),
                ),
            )
            conn.commit()

    def get_event_by_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM integration_events WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return self._event_row_to_dict(row) if row else None

    def latest_event_for_endpoint(self, endpoint: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM integration_events WHERE endpoint = ? ORDER BY id DESC LIMIT 1",
                (endpoint,),
            ).fetchone()
        return self._event_row_to_dict(row) if row else None

    def latest_news(self, news_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM news_items"
        params: tuple[Any, ...] = ()
        if news_id:
            query += " WHERE news_id = ?"
            params = (news_id,)
        query += " ORDER BY rowid DESC LIMIT 1"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if not row:
            return None
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        item["raw"] = json.loads(item.pop("raw_json"))
        item["response"] = json.loads(item.pop("response_json"))
        return item

    @staticmethod
    def _event_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        for key in ("request_json", "response_json", "portfolio_json", "log_json"):
            data[key.replace("_json", "")] = json.loads(data.pop(key))
        data["success"] = bool(data["success"])
        return data

