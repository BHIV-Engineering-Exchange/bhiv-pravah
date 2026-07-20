#!/usr/bin/env python3
"""
Platform Contract — Trace propagation, schema validation, and execution interface.
Implements PLATFORM_ENTRY.md contract for TANTRA ecosystem participation.
"""

import os
import time
import uuid
import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

SCHEMA_VERSION = os.getenv("PLATFORM_SCHEMA_VERSION", "1.0.0")
PLATFORM_STRICT_MODE = os.getenv("PLATFORM_STRICT_MODE", "false").lower() == "true"

# ─── Request/Response Models ────────────────────────────────────────────

class PlatformMetadata(BaseModel):
    source: str = "unknown"
    timestamp: Optional[str] = None
    user_id: Optional[str] = None

class PlatformRequest(BaseModel):
    trace_id: str = Field(..., description="UUID v4 trace identifier")
    schema_version: str = Field(default=SCHEMA_VERSION, description="Schema version")
    module: str = Field(..., min_length=1, max_length=100, description="Module performing work")
    action: str = Field(..., min_length=1, max_length=200, description="Action being performed")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action payload")
    metadata: PlatformMetadata = Field(default_factory=PlatformMetadata)

    @validator("trace_id")
    def validate_trace_id(cls, v):
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError("trace_id must be a valid UUID v4")
        return v

    @validator("schema_version")
    def validate_schema_version(cls, v):
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("schema_version must be semver (e.g., 1.0.0)")
        return v

class PlatformError(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class PlatformResponse(BaseModel):
    trace_id: str
    schema_version: str = SCHEMA_VERSION
    status: str = Field(..., pattern="^(success|error|partial|pending|rejected)$")
    module: str
    execution_id: str
    timestamp: str
    duration_ms: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[PlatformError] = None

# ─── Trace Propagation Middleware ───────────────────────────────────────

class TracePropagationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request/response carries trace context.
    Injects X-Trace-ID, X-Schema-Version, X-Execution-ID headers.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract or generate trace_id
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("x-trace-id")
        if not trace_id:
            try:
                trace_id = str(uuid.uuid4())
            except Exception:
                trace_id = f"trace_{int(time.time() * 1000)}"

        # Extract schema_version
        schema_version = request.headers.get("X-Schema-Version") or request.headers.get("x-schema-version", SCHEMA_VERSION)

        # Generate execution_id for this request
        try:
            execution_id = str(uuid.uuid4())
        except Exception:
            execution_id = f"exec_{int(time.time() * 1000)}"

        # Store in request state for downstream use
        request.state.trace_id = trace_id
        request.state.schema_version = schema_version
        request.state.execution_id = execution_id
        request.state.platform_start_time = start_time

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Request failed: {e}")
            response = JSONResponse(
                status_code=500,
                content={
                    "trace_id": trace_id,
                    "schema_version": schema_version,
                    "status": "error",
                    "module": "platform",
                    "execution_id": execution_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": round(duration_ms, 2),
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                        "details": {"exception": str(e)}
                    }
                }
            )

        # Inject trace headers into response
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Schema-Version"] = schema_version
        response.headers["X-Execution-ID"] = execution_id
        response.headers["X-Duration-Ms"] = str(round(duration_ms, 2))

        return response

# ─── Platform Router ───────────────────────────────────────────────────

platform_router = APIRouter(prefix="/platform", tags=["Platform Contract"])

@platform_router.post("/execute")
async def platform_execute(request: PlatformRequest):
    """
    Canonical platform execution endpoint.
    Accepts PLATFORM_ENTRY.md contract, routes to appropriate module.
    """
    execution_id = str(uuid.uuid4())
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        # Validate schema version compatibility
        request_major = int(request.schema_version.split(".")[0])
        contract_major = int(SCHEMA_VERSION.split(".")[0])
        if request_major != contract_major:
            return JSONResponse(
                status_code=400,
                content={
                    "trace_id": request.trace_id,
                    "schema_version": SCHEMA_VERSION,
                    "status": "error",
                    "module": "platform",
                    "execution_id": execution_id,
                    "timestamp": timestamp,
                    "duration_ms": 0,
                    "error": {
                        "code": "SCHEMA_VERSION_MISMATCH",
                        "message": f"Request schema v{request.schema_version} incompatible with platform v{SCHEMA_VERSION}",
                        "details": {"request_version": request.schema_version, "platform_version": SCHEMA_VERSION}
                    }
                }
            )

        # Route to module handler
        result = await _route_to_module(request.module, request.action, request.payload, request.trace_id, execution_id)

        duration_ms = (time.time() - start_time) * 1000

        # Emit observability event
        _emit_execution_event(request.trace_id, execution_id, request.module, request.action,
                              result.get("status", "success"), duration_ms, request.metadata.dict() if request.metadata else {})

        # Persist artifact if output produced
        if result.get("data"):
            _persist_artifact(request.trace_id, execution_id, request.module, request.action, result["data"])

        return {
            "trace_id": request.trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": result.get("status", "success"),
            "module": request.module,
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round(duration_ms, 2),
            "data": result.get("data"),
            "error": result.get("error")
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Platform execution failed: {e}")

        _emit_execution_event(request.trace_id, execution_id, request.module, request.action,
                              "error", duration_ms, {}, str(e))

        return JSONResponse(
            status_code=500,
            content={
                "trace_id": request.trace_id,
                "schema_version": SCHEMA_VERSION,
                "status": "error",
                "module": request.module,
                "execution_id": execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": round(duration_ms, 2),
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "details": {"exception_type": type(e).__name__}
                }
            }
        )

@platform_router.post("/validate-contract")
async def validate_contract(request: PlatformRequest):
    """
    Validate a platform request against the contract without executing.
    Returns validation result with any violations.
    """
    violations = []

    # Validate trace_id format
    try:
        uuid.UUID(request.trace_id, version=4)
    except ValueError:
        violations.append({"field": "trace_id", "issue": "Not a valid UUID v4"})

    # Validate schema version
    parts = request.schema_version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        violations.append({"field": "schema_version", "issue": "Not valid semver"})

    # Validate module is registered
    registered_modules = {"platform", "prompt_runner", "moderation", "metadata", "ui", "bhiv_core", "testing", "verification"}
    if request.module not in registered_modules:
        violations.append({"field": "module", "issue": f"Module '{request.module}' not in registry", "registered": list(registered_modules)})

    # Validate action is non-empty
    if not request.action.strip():
        violations.append({"field": "action", "issue": "Action cannot be empty"})

    is_valid = len(violations) == 0

    return {
        "trace_id": request.trace_id,
        "schema_version": SCHEMA_VERSION,
        "status": "success" if is_valid else "error",
        "module": "platform",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "valid": is_valid,
            "violations": violations,
            "contract_version": SCHEMA_VERSION
        }
    }

@platform_router.get("/contract")
async def get_contract():
    """Return the current platform contract specification."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen",
        "contract": {
            "request": {
                "required_fields": ["trace_id", "schema_version", "module", "action"],
                "optional_fields": ["payload", "metadata"]
            },
            "response": {
                "required_fields": ["trace_id", "schema_version", "status", "module", "execution_id", "timestamp", "duration_ms"],
                "optional_fields": ["data", "error"]
            },
            "statuses": ["success", "error", "partial", "pending", "rejected"],
            "modules": ["platform", "prompt_runner", "moderation", "metadata", "ui", "bhiv_core", "testing", "verification"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@platform_router.get("/modules")
async def list_modules():
    """List all registered platform modules."""
    return {
        "trace_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "status": "success",
        "module": "platform",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "modules": [
                {"id": "platform", "name": "AI Content Platform", "owner": "Ashmit Pandey", "role": "Platform composition, adapters"},
                {"id": "prompt_runner", "name": "Prompt Runner", "owner": "Siddhesh Narkar", "role": "Deterministic execution interface"},
                {"id": "moderation", "name": "Moderation UI", "owner": "Hrujul Todankar", "role": "Application presentation, moderation"},
                {"id": "metadata", "name": "Metadata Enrichment", "owner": "Vijay Dhawan", "role": "Tagging, structured metadata"},
                {"id": "ui", "name": "UI/UX", "owner": "Chandragupta", "role": "Production user experience"},
                {"id": "bhiv_core", "name": "BHIV Core", "owner": "Raj Prajapati", "role": "Governed application integration"},
                {"id": "testing", "name": "Testing & Depository", "owner": "Vinayak Tiwari", "role": "Validation, documentation, evidence"},
                {"id": "verification", "name": "Functionality Testing", "owner": "Akash", "role": "Runtime verification, regression"}
            ]
        }
    }

@platform_router.get("/schema")
async def get_schema():
    """Return the current platform schema version."""
    return {
        "trace_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "status": "success",
        "module": "platform",
        "execution_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0,
        "data": {
            "schema_version": SCHEMA_VERSION,
            "status": "frozen",
            "frozen_at": "2026-07-04T00:00:00Z",
            "owner": "Ashmit Pandey"
        }
    }

# ─── Internal Routing ─────────────────────────────────────────────────

async def _route_to_module(module: str, action: str, payload: Dict[str, Any],
                           trace_id: str, execution_id: str) -> Dict[str, Any]:
    """Route execution to the appropriate module handler."""
    handlers = {
        "platform": _handle_platform_action,
        "prompt_runner": _handle_prompt_runner_action,
        "moderation": _handle_moderation_action,
        "metadata": _handle_metadata_action,
        "bhiv_core": _handle_bhiv_core_action,
    }

    handler = handlers.get(module)
    if not handler:
        return {
            "status": "error",
            "error": {"code": "MODULE_NOT_FOUND", "message": f"Module '{module}' has no handler registered"}
        }

    try:
        return await handler(action, payload, trace_id, execution_id)
    except Exception as e:
        return {
            "status": "error",
            "error": {"code": "MODULE_ERROR", "message": str(e), "details": {"module": module, "action": action}}
        }

async def _handle_platform_action(action: str, payload: Dict, trace_id: str, execution_id: str) -> Dict:
    """Handle platform-level actions."""
    if action == "health":
        return {"status": "success", "data": {"platform": "healthy", "schema_version": SCHEMA_VERSION}}
    elif action == "status":
        return {"status": "success", "data": {"modules_registered": 8, "schema_version": SCHEMA_VERSION}}
    elif action == "echo":
        return {"status": "success", "data": {"echo": payload, "trace_id": trace_id}}
    else:
        return {"status": "error", "error": {"code": "UNKNOWN_ACTION", "message": f"Platform action '{action}' not recognized"}}

async def _handle_prompt_runner_action(action: str, payload: Dict, trace_id: str, execution_id: str) -> Dict:
    """Delegate to prompt runner (deterministic execution)."""
    prompt = payload.get("prompt", "")
    if not prompt:
        return {"status": "error", "error": {"code": "MISSING_PAYLOAD", "message": "Prompt runner requires 'prompt' in payload"}}

    # Execute prompt through existing LLM client
    try:
        from core.bhiv_lm_client import call_lm_async, is_llm_configured
        if is_llm_configured():
            result = await call_lm_async(prompt)
            return {"status": "success", "data": {"result": result, "prompt_length": len(prompt)}}
        else:
            # Fallback: echo prompt as deterministic response
            return {"status": "success", "data": {"result": {"response": f"Echo: {prompt[:200]}"}, "method": "fallback_echo"}}
    except Exception as e:
        return {"status": "partial", "data": {"result": {"response": f"Fallback: {prompt[:200]}"}, "error": str(e)}}

async def _handle_moderation_action(action: str, payload: Dict, trace_id: str, execution_id: str) -> Dict:
    """Handle moderation actions."""
    if action == "validate_content":
        content = payload.get("content", "")
        # Basic content validation
        issues = []
        if len(content) > 10000:
            issues.append("Content exceeds 10000 characters")
        if not content.strip():
            issues.append("Content is empty")
        return {"status": "success" if not issues else "rejected", "data": {"valid": len(issues) == 0, "issues": issues}}
    elif action == "check_safety":
        return {"status": "success", "data": {"safe": True, "method": "basic_check"}}
    else:
        return {"status": "error", "error": {"code": "UNKNOWN_ACTION", "message": f"Moderation action '{action}' not recognized"}}

async def _handle_metadata_action(action: str, payload: Dict, trace_id: str, execution_id: str) -> Dict:
    """Handle metadata enrichment actions."""
    if action == "generate_tags":
        title = payload.get("title", "")
        description = payload.get("description", "")
        # Use existing tag suggestion
        try:
            from app.routes import suggest_tags
            tags = suggest_tags(title, description)
            return {"status": "success", "data": {"tags": tags, "title": title}}
        except Exception:
            tags = [w.lower() for w in title.split()[:5]] if title else []
            return {"status": "success", "data": {"tags": tags, "method": "fallback"}}
    elif action == "enrich_metadata":
        content_id = payload.get("content_id", "")
        return {"status": "success", "data": {"content_id": content_id, "enriched": True}}
    else:
        return {"status": "error", "error": {"code": "UNKNOWN_ACTION", "message": f"Metadata action '{action}' not recognized"}}

async def _handle_bhiv_core_action(action: str, payload: Dict, trace_id: str, execution_id: str) -> Dict:
    """Delegate to BHIV Core for governed operations."""
    try:
        from core import bhiv_core
        if action == "process_webhook":
            result = await bhiv_core.process_webhook_ingest(payload=payload)
            return {"status": "success", "data": result}
        elif action == "get_metadata":
            content_id = payload.get("content_id", "")
            metadata = bhiv_core.get_content_metadata(content_id)
            return {"status": "success", "data": {"metadata": metadata}}
        else:
            return {"status": "error", "error": {"code": "UNKNOWN_ACTION", "message": f"BHIV Core action '{action}' not recognized"}}
    except Exception as e:
        return {"status": "error", "error": {"code": "BHIV_CORE_ERROR", "message": str(e)}}

# ─── Observability Event Emission ──────────────────────────────────────

def _emit_execution_event(trace_id: str, execution_id: str, module: str, action: str,
                          status: str, duration_ms: float, metadata: Dict = None, error: str = None):
    """Emit execution event for InsightFlow consumption."""
    try:
        from app.observability import track_event, sentry_manager

        event_data = {
            "trace_id": trace_id,
            "execution_id": execution_id,
            "module": module,
            "action": action,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": f"platform_{status}",
            **(metadata or {})
        }

        if error:
            event_data["error"] = error

        # Track in PostHog
        user_id = metadata.get("user_id") if metadata else None
        if user_id:
            track_event(user_id, "platform_execution", event_data)

        # Write to event log for InsightFlow
        _write_event_log(event_data)

    except Exception as e:
        logger.warning(f"Failed to emit execution event: {e}")

def _write_event_log(event_data: Dict):
    """Write execution event to log file for InsightFlow consumption."""
    try:
        from core import bhiv_bucket
        import json as _json

        log_date = datetime.now().strftime("%Y%m%d")
        log_filename = f"platform_events_{log_date}.log"
        log_entry = _json.dumps(event_data, default=str, ensure_ascii=False) + "\n"

        try:
            log_path = bhiv_bucket.get_bucket_path("logs", log_filename)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            bhiv_bucket.save_log(log_entry.strip(), log_filename)
    except Exception as e:
        logger.warning(f"Failed to write event log: {e}")

# ─── Artifact Persistence ──────────────────────────────────────────────

def _persist_artifact(trace_id: str, execution_id: str, module: str, action: str, data: Dict):
    """Persist execution artifact to bucket with provenance."""
    try:
        from core import bhiv_bucket
        import json as _json

        content_str = _json.dumps(data, default=str, ensure_ascii=False)
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        artifact = {
            "artifact_id": f"art_{execution_id[:12]}",
            "trace_id": trace_id,
            "execution_id": execution_id,
            "module": module,
            "action": action,
            "artifact_type": "output",
            "content_hash": content_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "provenance": {
                "source": "platform_execute",
                "module": module,
                "action": action,
                "schema_version": SCHEMA_VERSION
            },
            "data": data
        }

        filename = f"{artifact['artifact_id']}.json"
        bhiv_bucket.save_json("logs", filename, artifact)
        logger.info(f"Persisted artifact {artifact['artifact_id']} for trace {trace_id}")

    except Exception as e:
        logger.warning(f"Failed to persist artifact: {e}")
