"""Baseline and final system state capture for Control Center E2E."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from .auth_helpers import api_key_headers
from .config import E2EConfig


@dataclass
class SystemState:
    label: str
    captured_at: float
    candidate_stats: Dict[str, Any] = field(default_factory=dict)
    dashboard_aggregates: Dict[str, Any] = field(default_factory=dict)
    audit_replay: Dict[str, Any] = field(default_factory=dict)
    audit_events: Dict[str, Any] = field(default_factory=dict)
    metrics_dashboard: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    mongo_audit_count: Optional[int] = None
    errors: List[str] = field(default_factory=list)

    @property
    def audit_event_count(self) -> int:
        for key in ("audit_events", "audit_replay"):
            payload = getattr(self, key, {}) or {}
            if isinstance(payload.get("count"), int):
                return int(payload["count"])
        events = (self.audit_events or {}).get("events") or (self.audit_replay or {}).get("events") or []
        return len(events) if isinstance(events, list) else 0

    @property
    def latest_correlation_id(self) -> Optional[str]:
        replay = self.audit_replay or {}
        cid = replay.get("correlation_id")
        if cid:
            return str(cid)
        events = replay.get("events") or []
        if events and isinstance(events[0], dict):
            return str(events[0].get("correlation_id") or "") or None
        return None


def _extract_correlation(headers: httpx.Headers) -> Optional[str]:
    for key in ("x-correlation-id", "X-Correlation-ID"):
        value = headers.get(key)
        if value:
            return str(value).strip()
    return None


def _extract_policy_scope(headers: httpx.Headers) -> Optional[str]:
    for key in ("x-policy-scope", "X-Policy-Scope"):
        value = headers.get(key)
        if value:
            return str(value).strip()
    return None


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    *,
    params: Optional[Dict[str, Any]] = None,
) -> tuple[int, Dict[str, Any], httpx.Headers, Optional[str]]:
    try:
        response = await client.get(url, headers=headers, params=params)
        body: Dict[str, Any] = {}
        try:
            body = response.json() if response.content else {}
        except Exception:
            body = {"raw": response.text[:500]}
        return response.status_code, body, response.headers, None
    except Exception as exc:
        return 0, {}, httpx.Headers(), str(exc)


async def capture_state(
    client: httpx.AsyncClient,
    config: E2EConfig,
    *,
    label: str,
    auth_headers: Dict[str, str],
    correlation_filter: Optional[str] = None,
) -> SystemState:
    """Snapshot Control Center reads (mirrors frontend api.ts contracts)."""
    state = SystemState(label=label, captured_at=time.time())
    gw = config.gateway_url

    endpoints = [
        ("candidate_stats", f"{gw}/v1/candidates/stats", None),
        ("dashboard_aggregates", f"{gw}/v1/control-center/dashboard-aggregates", None),
        (
            "audit_replay",
            f"{gw}/v1/control-center/audit-replay",
            {"correlation_id": correlation_filter} if correlation_filter else None,
        ),
        ("audit_events", f"{gw}/v1/control-center/audit-events", {"limit": 50}),
        ("metrics_dashboard", f"{gw}/metrics/dashboard", None),
    ]

    last_headers: httpx.Headers = httpx.Headers()
    for attr, url, params in endpoints:
        status, body, hdrs, err = await _get_json(client, url, auth_headers, params=params)
        last_headers = hdrs
        if err:
            state.errors.append(f"{attr}: {err}")
            continue
        if status != 200:
            state.errors.append(f"{attr}: http_{status}")
            continue
        setattr(state, attr, body)

    state.headers = {
        "correlation_id": _extract_correlation(last_headers) or "",
        "policy_scope": _extract_policy_scope(last_headers) or "",
    }

    state.mongo_audit_count = await count_audit_logs_mongo(config)
    return state


async def count_audit_logs_mongo(config: E2EConfig) -> Optional[int]:
    if not config.mongodb_uri:
        return None
    try:
        from pymongo import MongoClient

        client = MongoClient(config.mongodb_uri, serverSelectionTimeoutMS=3000)
        db = client.get_default_database()
        if db is None:
            name = config.mongodb_uri.rsplit("/", 1)[-1].split("?")[0]
            db = client[name or "bhiv"]
        count = db.audit_logs.count_documents({"event_type": "control_center"})
        client.close()
        return int(count)
    except Exception:
        return None
