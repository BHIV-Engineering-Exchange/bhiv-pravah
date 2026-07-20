import json
from datetime import datetime
from typing import Iterable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .trace_continuity import TraceContinuityError, extract_execution


class TraceContinuityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, validator, path_prefix: str = "/setu", methods: Optional[Iterable[str]] = None):
        super().__init__(app)
        self.validator = validator
        self.path_prefix = path_prefix
        self.methods = {method.upper() for method in (methods or ["POST", "PUT", "PATCH"])}

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self.path_prefix) or request.method.upper() not in self.methods:
            return await call_next(request)

        body_bytes = await request.body()
        if not body_bytes:
            payload = {
                "success": False,
                "error": "execution_missing",
                "message": "Execution contract is required",
                "details": {"received_type": "empty_body"}
            }
            return JSONResponse(status_code=400, content=payload)

        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError as error:
            payload = {
                "success": False,
                "error": "execution_parse_failed",
                "message": "Execution contract must be valid JSON",
                "details": {"error": str(error)}
            }
            return JSONResponse(status_code=400, content=payload)

        execution = extract_execution(payload)
        # Log trace received
        await self.validator.store.append_trace_log({
            "event": "TRACE_RECEIVED",
            "execution_id": execution.get("execution_id") if isinstance(execution, dict) else None,
            "trace_id": execution.get("trace_id") if isinstance(execution, dict) else None,
            "tenant_id": execution.get("tenant_id") if isinstance(execution, dict) else None,
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            record = await self.validator.validate(execution)
        except TraceContinuityError as error:
            # Log trace mismatch rejection
            await self.validator.store.append_trace_log({
                "event": "TRACE_MISMATCH_REJECTED",
                "execution_id": execution.get("execution_id") if isinstance(execution, dict) else None,
                "trace_id": execution.get("trace_id") if isinstance(execution, dict) else None,
                "tenant_id": execution.get("tenant_id") if isinstance(execution, dict) else None,
                "reason": error.code,
                "details": error.details,
                "timestamp": datetime.utcnow().isoformat()
            })
            return JSONResponse(status_code=error.status_code, content=error.payload())

        request.state.setu_execution = execution
        request.state.setu_trace = record

        # Log trace forwarded
        await self.validator.store.append_trace_log({
            "event": "TRACE_FORWARDED",
            "execution_id": record["execution_id"],
            "trace_id": record["trace_id"],
            "tenant_id": record["tenant_id"],
            "timestamp": datetime.utcnow().isoformat()
        })

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request = Request(request.scope, receive)
        response = await call_next(request)

        response.headers["X-SETU-Execution-Id"] = record["execution_id"]
        response.headers["X-SETU-Trace-Id"] = record["trace_id"]
        response.headers["X-SETU-Tenant-Id"] = record["tenant_id"]
        response.headers["X-SETU-Lineage-Hash"] = record["lineage_hash"]

        return response
