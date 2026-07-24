from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("telemetry")


def emit_execution_event(
    *,
    trace_id: str,
    action_type: str,
    adapter: str,
    status: str,
    product: str,
    error_code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """
    Non-blocking execution telemetry emitter.

    GUARANTEES:
    - Append-only
    - Immutable event shape
    - No retries
    - No dependency on downstream storage
    - NEVER raises
    """

    event = {
        "trace_id": trace_id,
        "action_type": action_type,
        "adapter": adapter,
        "status": status,
        "product": product,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if error_code:
        event["error_code"] = error_code

    # Guard against unsafe extras
    if isinstance(extra, dict) and extra:
        event["extra"] = extra  # must be non-sensitive, flat, JSON-safe

    try:
        # Phase-1: log-based emission (InsightFlow / Bucket consumers)
        logger.info(f"EXECUTION_EVENT | {event}")

        # Phase-2 (future): push to Kafka / HTTP / InsightFlow API

    except Exception:
        # Telemetry must NEVER affect execution correctness
        logger.error("TELEMETRY_EMIT_FAILED", exc_info=True)
