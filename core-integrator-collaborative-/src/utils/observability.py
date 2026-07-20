"""
Observability middleware — assigns trace_id and request_id to every request.

Every request gets:
  trace_id   — propagated from X-Trace-Id header or auto-generated
  request_id — always auto-generated (unique per request)

Both are:
  - stored on request.state
  - added to response headers
  - available to all log formatters via contextvars
"""

import uuid
import time
import logging
from contextvars import ContextVar
from fastapi import Request
from fastapi.responses import JSONResponse

# Context variables accessible from anywhere in the call stack
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
_workflow_id_var: ContextVar[str] = ContextVar("workflow_id", default="")
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_workflow_id() -> str:
    return "wf_" + uuid.uuid4().hex[:12]


def get_trace_id() -> str:
    return _trace_id_var.get()


def get_workflow_id() -> str:
    return _workflow_id_var.get()


def get_request_id() -> str:
    return _request_id_var.get()


async def observability_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or request.headers.get("x-trace-id") or new_trace_id()
    workflow_id = request.headers.get("X-Workflow-Id") or request.headers.get("x-workflow-id") or new_workflow_id()
    request_id = new_trace_id()

    _trace_id_var.set(trace_id)
    _workflow_id_var.set(workflow_id)
    _request_id_var.set(request_id)

    request.state.trace_id = trace_id
    request.state.workflow_id = workflow_id
    request.state.request_id = request_id

    start = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.getLogger("observability").error(
            "Unhandled exception",
            extra={"trace_id": trace_id, "workflow_id": workflow_id, "request_id": request_id, "error": str(exc)},
        )
        response = JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "trace_id": trace_id, "workflow_id": workflow_id, "request_id": request_id},
        )

    duration_ms = round((time.time() - start) * 1000, 2)
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Workflow-Id"] = workflow_id
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response