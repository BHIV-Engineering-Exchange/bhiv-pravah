#!/usr/bin/env python3
"""
Runtime Observability — Execution tracking, event emission for InsightFlow.
Produces structured events for every platform execution.
"""

import os
import time
import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import APIRouter, Request
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

SCHEMA_VERSION = os.getenv("PLATFORM_SCHEMA_VERSION", "1.0.0")

# ─── Execution Event Model ─────────────────────────────────────────────

@dataclass
class ExecutionEvent:
    trace_id: str
    execution_id: str
    module: str
    action: str
    status: str
    timestamp: str
    duration_ms: float
    event_type: str = "execution_completed"
    user_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# ─── Runtime Event Store ───────────────────────────────────────────────

class RuntimeEventStore:
    """In-memory event store with file persistence for InsightFlow."""

    def __init__(self):
        self.events: List[ExecutionEvent] = []
        self.max_events = 10000
        self.module_stats = defaultdict(lambda: {"count": 0, "success": 0, "error": 0, "total_duration_ms": 0})
        self._event_log_dir = "logs"

    def record(self, event: ExecutionEvent):
        """Record an execution event."""
        self.events.append(event)

        # Trim old events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        # Update module stats
        stats = self.module_stats[event.module]
        stats["count"] += 1
        stats["total_duration_ms"] += event.duration_ms
        if event.status == "success":
            stats["success"] += 1
        elif event.status == "error":
            stats["error"] += 1

        # Persist to file
        self._persist_event(event)

    def get_events(self, module: Optional[str] = None, status: Optional[str] = None,
                   limit: int = 50) -> List[Dict]:
        """Get recent events with optional filtering."""
        filtered = self.events
        if module:
            filtered = [e for e in filtered if e.module == module]
        if status:
            filtered = [e for e in filtered if e.status == status]
        return [asdict(e) for e in filtered[-limit:]]

    def get_module_stats(self) -> Dict[str, Any]:
        """Get aggregated module statistics."""
        result = {}
        for module, stats in self.module_stats.items():
            avg_duration = stats["total_duration_ms"] / stats["count"] if stats["count"] > 0 else 0
            result[module] = {
                "total_executions": stats["count"],
                "success_count": stats["success"],
                "error_count": stats["error"],
                "success_rate": round(stats["success"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0,
                "avg_duration_ms": round(avg_duration, 2)
            }
        return result

    def get_recent_trace(self, trace_id: str) -> List[Dict]:
        """Get all events for a specific trace (end-to-end flow)."""
        return [asdict(e) for e in self.events if e.trace_id == trace_id]

    def _persist_event(self, event: ExecutionEvent):
        """Persist event to daily log file for InsightFlow."""
        try:
            from core import bhiv_bucket

            log_date = datetime.now().strftime("%Y%m%d")
            log_filename = f"runtime_events_{log_date}.log"

            event_dict = asdict(event)
            log_line = json.dumps(event_dict, default=str, ensure_ascii=False) + "\n"

            try:
                log_path = bhiv_bucket.get_bucket_path("logs", log_filename)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                bhiv_bucket.save_log(log_line.strip(), log_filename)

        except Exception as e:
            logger.warning(f"Failed to persist runtime event: {e}")

# ─── Global Event Store ────────────────────────────────────────────────

event_store = RuntimeEventStore()

# ─── Observability Router ──────────────────────────────────────────────

observability_router = APIRouter(prefix="/observability", tags=["Runtime Observability"])

@observability_router.get("/events")
async def get_events(module: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    """Get recent execution events (InsightFlow compatible)."""
    return {
        "trace_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "status": "success",
        "module": "observability",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "events": event_store.get_events(module=module, status=status, limit=limit),
            "total_count": len(event_store.events),
            "filters": {"module": module, "status": status}
        }
    }

@observability_router.get("/events/trace/{trace_id}")
async def get_trace_events(trace_id: str):
    """Get all events for a specific trace (end-to-end flow visualization)."""
    events = event_store.get_recent_trace(trace_id)
    return {
        "trace_id": trace_id,
        "schema_version": SCHEMA_VERSION,
        "status": "success",
        "module": "observability",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "trace_id": trace_id,
            "events": events,
            "event_count": len(events)
        }
    }

@observability_router.get("/stats/modules")
async def get_module_stats():
    """Get per-module execution statistics."""
    return {
        "trace_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "status": "success",
        "module": "observability",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "modules": event_store.get_module_stats(),
            "total_modules": len(event_store.module_stats)
        }
    }

@observability_router.get("/health")
async def observability_health():
    """Check observability system health."""
    return {
        "trace_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "status": "success",
        "module": "observability",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "event_store": {
                "status": "healthy",
                "total_events": len(event_store.events),
                "max_events": event_store.max_events
            },
            "sentry": {
                "configured": bool(os.getenv("SENTRY_DSN"))
            },
            "posthog": {
                "configured": bool(os.getenv("POSTHOG_API_KEY"))
            }
        }
    }

# ─── Helper: Record Event ─────────────────────────────────────────────

def send_telemetry_to_pravah(trace_id: str, status: str, duration_ms: float, error: str = None):
    """Asynchronously send telemetry to Pravah control plane."""
    import threading
    import requests
    import hmac
    import hashlib
    import json
    import time
    
    def _send():
        try:
            # Map status
            state = "running"
            if status == "error" or error:
                state = "degraded"
                
            payload = {
                "app": "artha-fastapi",
                "env": os.getenv("ENVIRONMENT", "dev"),
                "state": state,
                "latency_ms": round(duration_ms, 2),
                "errors_last_min": 1 if error else 0,
                "workers": 1
            }
            
            # Canonical serialization
            canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            body_hash = hashlib.sha256(canonical.encode()).hexdigest()
            timestamp = str(int(time.time()))
            
            # Build trace signature
            secret_key = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
            trace_payload = f"{trace_id}:{timestamp}:{body_hash}"
            signature = hmac.new(
                secret_key.encode(),
                trace_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                "X-Trace-Id": trace_id,
                "X-Timestamp": timestamp,
                "X-Trace-Signature": signature,
                "Content-Type": "application/json"
            }
            
            requests.post(
                "http://localhost:7000/api/runtime",
                json=payload,
                headers=headers,
                timeout=2.0
            )
        except Exception:
            pass  # Do not block runtime on telemetry issues
            
    threading.Thread(target=_send, daemon=True).start()


def record_platform_event(trace_id: str, execution_id: str, module: str, action: str,
                          status: str, duration_ms: float, user_id: str = None,
                          error: str = None, metadata: Dict = None):
    """Convenience function to record a platform execution event."""
    event = ExecutionEvent(
        trace_id=trace_id,
        execution_id=execution_id,
        module=module,
        action=action,
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        duration_ms=round(duration_ms, 2),
        event_type=f"platform_{status}",
        user_id=user_id,
        error=error,
        metadata=metadata or {}
    )
    event_store.record(event)
    
    # Observe execution via Pravah control plane
    try:
        send_telemetry_to_pravah(trace_id, status, duration_ms, error)
    except Exception:
        pass
