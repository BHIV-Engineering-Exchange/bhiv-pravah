"""
KESHAV API — FastAPI wrapper for the full TANTRA pipeline

Endpoints:
    POST /analyze   — run full TANTRA chain, returns KESHAV output contract
    GET  /health    — liveness + readiness check

Run (development):
    uvicorn api:app --reload

Run (production):
    uvicorn api:app --workers 4 --host 0.0.0.0 --port 5000

Environment variables:
    PORT            — listening port (default: 5000)
    HOST            — bind address  (default: 127.0.0.1)
    DEBUG           — enable debug logging (default: false)
    MAX_CONTENT_MB  — max request body size in MB (default: 1)
"""

import logging
import os
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

import metrics
from tantra.pipeline import run_tantra_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("keshav.api")

_max_mb = int(os.environ.get("MAX_CONTENT_MB", 1))
MAX_CONTENT_LENGTH = _max_mb * 1024 * 1024

app = FastAPI(title="KESHAV API", description="FastAPI wrapper for the full TANTRA pipeline")

# Start Pravah heartbeat
try:
    from observability.pravah_adapter import start_heartbeat, emit_pravah_signal
    import time
    start_heartbeat()
except Exception as e:
    logger.error(f"Failed to start Pravah heartbeat: {e}")


class ContentSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_CONTENT_LENGTH:
                return JSONResponse(
                    {"status": "FAIL", "reason": "REQUEST_TOO_LARGE", "trace_id": ""},
                    status_code=413
                )
            
            # Starlette reads bodies incrementally, but we can also just rely on content-length
            # Since test client might not send content length sometimes, we'll also catch errors later.
        response = await call_next(request)
        return response

app.add_middleware(ContentSizeLimitMiddleware)


# ── error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse({"status": "FAIL", "reason": "NOT_FOUND", "trace_id": ""}, status_code=404)
    if exc.status_code == 405:
        return JSONResponse({"status": "FAIL", "reason": "METHOD_NOT_ALLOWED", "trace_id": ""}, status_code=405)
    return JSONResponse({"status": "FAIL", "reason": str(exc.detail), "trace_id": ""}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse({"status": "FAIL", "reason": "INVALID_JSON", "trace_id": ""}, status_code=400)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled internal error")
    return JSONResponse({"status": "FAIL", "reason": "INTERNAL_ERROR", "trace_id": ""}, status_code=500)


# ── routes ────────────────────────────────────────────────────────────────────

def check_content_type(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(status_code=415, detail="UNSUPPORTED_MEDIA_TYPE")

@app.post("/analyze", tags=["TANTRA"], dependencies=[Depends(check_content_type)])
async def analyze(request: Request, payload: Any = Body(
    ...,
    example={
        "trace_id": "rajya-trace-001",
        "execution_id": "exec-demo",
        "tasks": [{"task_id": "T1", "depends_on": []}],
        "constraint_results": [{"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []}],
        "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": 10}]
    }
)):
    """
    POST /analyze
    Content-Type: application/json
    Body: KESHAV input contract (trace_id + execution_id required)
    """
    start_time = metrics.record_request_start()
    start_ts = time.time()
    
    # Since FastAPI parses the JSON body into `payload` via the `Body` parameter,
    # and throws RequestValidationError (handled above) for invalid JSON, we can just use payload directly.
    try:
        # Check size explicitly for test client which might omit Content-Length
        raw_body = await request.body()
        if len(raw_body) > MAX_CONTENT_LENGTH:
            metrics.record_request_error(start_time)
            try:
                emit_pravah_signal(state="degraded", errors_last_min=1)
            except Exception:
                pass
            return JSONResponse({"status": "FAIL", "reason": "REQUEST_TOO_LARGE", "trace_id": ""}, status_code=413)

        input_data = payload
    except Exception:
        metrics.record_request_error(start_time)
        try:
            emit_pravah_signal(state="degraded", errors_last_min=1)
        except Exception:
            pass
        return JSONResponse({"status": "FAIL", "reason": "INVALID_JSON", "trace_id": ""}, status_code=400)

    if input_data is None:
        metrics.record_request_error(start_time)
        try:
            emit_pravah_signal(state="degraded", errors_last_min=1)
        except Exception:
            pass
        return JSONResponse({"status": "FAIL", "reason": "INVALID_JSON", "trace_id": ""}, status_code=400)

    trace_id = input_data.get("trace_id", "") if isinstance(input_data, dict) else ""
    logger.info("POST /analyze trace_id=%s", trace_id)

    result = run_tantra_pipeline(input_data)

    latency_ms = (time.time() - start_ts) * 1000

    if result["status"] == "FAIL":
        logger.warning("pipeline FAIL trace_id=%s error=%s", trace_id, result.get("error"))
        metrics.record_request_error(start_time)
        try:
            emit_pravah_signal(state="degraded", latency_ms=latency_ms, errors_last_min=1)
        except Exception:
            pass
        return JSONResponse(result["keshav_output"], status_code=400)

    logger.info("pipeline OK trace_id=%s", trace_id)
    severity = result["keshav_output"].get("severity", "UNKNOWN")
    metrics.record_request_success(start_time, severity, trace_id)
    try:
        emit_pravah_signal(state="running", latency_ms=latency_ms)
    except Exception:
        pass
    return JSONResponse(result["keshav_output"], status_code=200)



@app.get("/health", tags=["System"])
def health():
    """GET /health — liveness + readiness check."""
    return JSONResponse({"status": "OK", "service": "KESHAV"}, status_code=200)


@app.get("/metrics")
def metrics_endpoint():
    """GET /metrics — Prometheus-compatible metrics."""
    return Response(content=metrics.get_prometheus_metrics(), status_code=200, media_type="text/plain; charset=utf-8")


@app.get("/metrics/json")
def metrics_json():
    """GET /metrics/json — JSON metrics for debugging."""
    return JSONResponse(metrics.get_metrics(), status_code=200)


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    uvicorn.run("api:app", host=host, port=port, reload=debug)
