"""
trace_middleware.py — TANTRA Trace ID Middleware
=================================================

Rules (per TANTRA contract):
  - If x-trace-id is present in request headers → use it (immutable for request lifetime)
  - If x-trace-id is MISSING → generate a new UUID4 trace_id at entry point
  - Propagate trace_id back in response header for visibility
  - Once set, trace_id CANNOT be overwritten within the same request
"""

import uuid
import logging
from fastapi import Request
from app.core.context import set_trace_id

logger = logging.getLogger("TraceMiddleware")


async def trace_id_middleware(request: Request, call_next):
    """
    TANTRA Trace Lock Middleware.

    Ensures every request has an immutable trace_id:
      - Incoming x-trace-id header → use as-is
      - Missing header → generate uuid4 at entry (TANTRA PHASE 1 requirement)
    """
    incoming_trace = request.headers.get("x-trace-id")

    if incoming_trace:
        trace_id = incoming_trace
        logger.debug(f"[Trace] Accepted from header: {trace_id}")
    else:
        trace_id = f"gurukul-{uuid.uuid4().hex}"
        logger.debug(f"[Trace] Generated at entry: {trace_id}")

    # Lock trace_id into context — immutable for this request
    set_trace_id(trace_id)

    response = await call_next(request)

    # Echo back so clients and TANTRA can correlate
    response.headers["x-trace-id"] = trace_id

    return response
