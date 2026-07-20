from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import hmac
import hashlib
import json
import httpx
import time
import asyncio

from .mongo_store import MongoSetuStore

TELEMETRY_TYPES = [
    "execution_started",
    "execution_failed",
    "execution_completed",
    "execution_blocked",
    "governance_rejection",
    "dependency_blocked",
    "tenant_rejection"
]


async def _send_telemetry_to_pravah(event: Dict[str, Any]):
    """Format, sign, and post telemetry to Pravah decision API out-of-band."""
    try:
        event_type = event.get("event_type", "info")
        state = "running"
        if event_type in ["execution_failed", "execution_blocked"]:
            state = "crashed"
        elif event_type in ["execution_started"]:
            state = "running"
        else:
            state = "degraded"
            
        payload = {
            "app": "ai-crm-setu",
            "env": "dev",
            "state": state,
            "latency_ms": 50,
            "errors_last_min": 0 if state == "running" else 1,
            "workers": 1
        }
        
        # Sort and serialize canonically
        sorted_keys = sorted(payload.keys())
        sorted_obj = {k: payload[k] for k in sorted_keys}
        canonical = json.dumps(sorted_obj, separators=(',', ':'))
        
        body_hash = hashlib.sha256(canonical.encode()).hexdigest()
        trace_id = event.get("trace_id", "trace-default")
        timestamp = str(int(time.time()))
        secret_key = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
        
        trace_payload = f"{trace_id}:{timestamp}:{body_hash}"
        signature = hmac.new(secret_key.encode(), trace_payload.encode(), hashlib.sha256).hexdigest()
        
        headers = {
            "X-Trace-Id": trace_id,
            "X-Timestamp": timestamp,
            "X-Trace-Signature": signature,
            "Content-Type": "application/json"
        }
        
        # Dispatch request asynchronously
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post("http://localhost:7000/api/runtime", json=payload, headers=headers)
    except Exception as e:
        print(f"[Pravah Telemetry Hook] Failed to send telemetry out-of-band: {e}")


class TelemetryLayer:
    def __init__(self, store: MongoSetuStore):
        self.store = store

    async def emit(self, event: Dict[str, Any]) -> Dict[str, Any]:
        missing = [
            field for field in ["execution_id", "trace_id", "tenant_id", "timestamp", "event_type"]
            if event.get(field) is None
        ]
        if missing:
            raise ValueError("Telemetry missing required fields: " + ", ".join(missing))
        if event.get("event_type") not in TELEMETRY_TYPES:
            raise ValueError("Unsupported telemetry type: " + str(event.get("event_type")))
        stored = await self.store.append_telemetry(event)
        
        # Forward event to Pravah Bhiv decision control plane (observe, don't own)
        try:
            asyncio.create_task(_send_telemetry_to_pravah(stored))
        except Exception:
            pass

        try:
            from .sampada_dispatcher import dispatch_to_sampada
            subsystem = (event.get("details") or {}).get("subsystem")
            await dispatch_to_sampada(stored, subsystem=subsystem)
        except Exception:
            pass  # additive side-effect; never block CRM telemetry
        return stored

    def _build_event(self, event_type: str, execution: Dict[str, Any], details: Dict[str, Any],
                     overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        overrides = overrides or {}
        return {
            "event_type": event_type,
            "execution_id": execution.get("execution_id"),
            "trace_id": execution.get("trace_id"),
            "tenant_id": execution.get("tenant_id"),
            "timestamp": overrides.get("timestamp") or execution.get("timestamp") or datetime.utcnow().isoformat(),
            "details": details or {},
            "source_system": execution.get("source_system") or "setu"
        }

    async def emit_execution_started(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                    overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("execution_started", execution, details or {}, overrides))

    async def emit_execution_failed(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                   overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("execution_failed", execution, details or {}, overrides))

    async def emit_execution_completed(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                      overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("execution_completed", execution, details or {}, overrides))

    async def emit_execution_blocked(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                    overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("execution_blocked", execution, details or {}, overrides))

    async def emit_governance_rejection(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                       overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("governance_rejection", execution, details or {}, overrides))

    async def emit_dependency_blocked(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                     overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("dependency_blocked", execution, details or {}, overrides))

    async def emit_tenant_rejection(self, execution: Dict[str, Any], details: Optional[Dict[str, Any]] = None,
                                   overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self.emit(self._build_event("tenant_rejection", execution, details or {}, overrides))

    async def list_events(self, trace_id: str, limit: int = 200):
        return await self.store.list_telemetry_events(trace_id, limit)
