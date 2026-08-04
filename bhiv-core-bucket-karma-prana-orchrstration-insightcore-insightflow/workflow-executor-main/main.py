from fastapi import FastAPI, HTTPException, Request

# ... existing imports ...
import traceback
import asyncio
from datetime import datetime
import uuid
import time

from contracts.workflow_request import WorkflowExecuteRequest
from execution_engine.guard import should_execute
from execution_engine.engine import execute_engine
from utils.logger import get_logger
from config.settings import settings
from integration.bucket_client import bucket_client
from integration.karma_client import karma_client

logger = get_logger()

app = FastAPI(
    title="Workflow Executor",
    description="Deterministic execution layer for assistant workflows",
    version="1.0.0",
)

from observability.pravah_adapter import emit_pravah_signal

@app.middleware("http")
async def tantra_trace_middleware(request: Request, call_next):
    # Extract trace ID or generate a new one
    trace_id = request.headers.get("X-Trace-Id") or request.headers.get("x-trace-id")
    if not trace_id:
        trace_id = f"tantra-{uuid.uuid4().hex[:12]}"
        
    start_time = time.time()
    response = await call_next(request)
    latency = (time.time() - start_time) * 1000
    
    # Emit telemetry to Pravah
    try:
        status = "running" if response.status_code < 400 else "degraded"
        errors = 1 if response.status_code >= 400 else 0
        emit_pravah_signal(
            state=status,
            latency_ms=latency,
            errors_last_min=errors,
            extra={
                "signal_type": "truth",
                "source": "workflow-executor",
                "context": {"path": request.url.path, "method": request.method}
            },
            trace_id=trace_id
        )
    except Exception as e:
        logger.warning(f"Failed to emit Pravah signal: {e}")
        
    # Inject trace ID into response headers
    response.headers["X-Trace-Id"] = trace_id
    return response

# Port Configuration: 8003 (Karma=8000, Bucket=8001, Core=8002)
WORKFLOW_EXECUTOR_PORT = 8003

# -------------------------------------------------
# Startup
# -------------------------------------------------

@app.on_event("startup")
def startup_event():
    logger.info(
        f"SERVICE_STARTUP | service={settings.service_name} | env={settings.environment}"
    )
    try:
        from observability.pravah_adapter import start_heartbeat, emit_pravah_signal
        start_heartbeat(60)
    except Exception as e:
        logger.warning(f"Failed to start Pravah heartbeat: {e}")

# -------------------------------------------------
# Health Check (MANDATORY FOR RENDER)
# -------------------------------------------------

@app.get("/healthz")
def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

# -------------------------------------------------
# Workflow Execution Endpoint
# -------------------------------------------------

@app.post("/api/workflow/execute")
async def execute_workflow(request: WorkflowExecuteRequest):
    start_time = datetime.now()
    trace_id = request.trace_id
    decision = request.decision

    logger.info(
        f"REQUEST_RECEIVED | trace_id={trace_id} | decision={decision}"
    )

    try:
        # -------------------------------------------------
        # Guard: execute ONLY when decision == "workflow"
        # -------------------------------------------------
        if not should_execute(decision):
            logger.info(
                f"EXECUTION_SKIPPED | trace_id={trace_id} | reason=decision_not_workflow"
            )
            return {
                "trace_id": trace_id,
                "status": "skipped",
                "reason": "decision_not_workflow",
            }

        # -------------------------------------------------
        # Validate workflow payload
        # -------------------------------------------------
        if not request.data or not request.data.payload:
            logger.error(
                f"EXECUTION_FAILED | trace_id={trace_id} | error_code=missing_workflow_payload"
            )
            raise HTTPException(
                status_code=400,
                detail="missing_workflow_payload",
            )

        payload = request.data.payload
        action_type = payload.get("action_type")

        logger.info(
            f"EXECUTION_STARTED | trace_id={trace_id} | action_type={action_type}"
        )

        # -------------------------------------------------
        # Execute deterministically
        # -------------------------------------------------
        result = execute_engine(payload)

        # -------------------------------------------------
        # Normalize response
        # -------------------------------------------------
        if result.get("success") is True:
            logger.info(
                f"EXECUTION_SUCCESS | trace_id={trace_id} | action_type={action_type}"
            )
            status = "success"
        else:
            logger.error(
                f"EXECUTION_FAILED | trace_id={trace_id} | action_type={action_type} "
                f"| error_code={result.get('error_code')}"
            )
            status = "failed"

        # -------------------------------------------------
        # Fire-and-forget integration logging
        # -------------------------------------------------
        # Log to Bucket (audit trail)
        try:
            bucket_logged = await bucket_client.log_workflow_execution(
                trace_id=trace_id,
                action_type=action_type,
                status=status,
                execution_result=result,
                metadata=payload
            )
            if bucket_logged:
                logger.info(f"✅ Bucket logging successful: {trace_id}")
            else:
                logger.warning(f"⚠️ Bucket logging failed: {trace_id}")
        except Exception as bucket_error:
            logger.error(f"❌ Bucket logging exception: {bucket_error}")
        
        # Log to Karma (behavioral tracking)
        try:
            user_id = payload.get("user_id", "system")
            karma_logged = await karma_client.log_workflow_behavior(
                trace_id=trace_id,
                user_id=user_id,
                action_type=action_type,
                status=status,
                metadata={"result": result}
            )
            if karma_logged:
                logger.info(f"✅ Karma logging successful: {trace_id}")
            else:
                logger.warning(f"⚠️ Karma logging failed: {trace_id}")
        except Exception as karma_error:
            logger.error(f"❌ Karma logging exception: {karma_error}")

        try:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            emit_pravah_signal(state="running", latency_ms=latency_ms)
        except Exception:
            pass

        return {
            "trace_id": trace_id,
            "status": status,
            "execution_result": result,
        }

    except HTTPException:
        # Explicit contract failure
        raise

    except Exception as e:
        # -------------------------------------------------
        # HARD SAFETY BOUNDARY — NEVER CRASH OUTWARD
        # -------------------------------------------------
        logger.error(
            f"EXECUTION_CRASH | trace_id={trace_id} | exception={str(e)}"
        )
        logger.debug(traceback.format_exc())

        try:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            emit_pravah_signal(state="degraded", latency_ms=latency_ms, errors_last_min=1)
        except Exception:
            pass

        return {
            "trace_id": trace_id,
            "status": "failed",
            "execution_result": {
                "success": False,
                "error_code": "internal_execution_error",
                "message": "Execution failed due to internal error",
            },
        }

# -------------------------------------------------
# Run on port 8003 when executed directly
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=WORKFLOW_EXECUTOR_PORT)
