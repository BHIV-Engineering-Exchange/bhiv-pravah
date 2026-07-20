import json
import logging
from datetime import datetime, UTC
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter with trace_id and request_id propagation."""

    def format(self, record: logging.LogRecord) -> str:
        from src.utils.observability import get_trace_id, get_request_id

        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "trace_id": get_trace_id() or getattr(record, "trace_id", ""),
            "request_id": get_request_id() or getattr(record, "request_id", ""),
        }

        # Propagate any extra fields attached by callers
        for field in ("user_id", "request_data", "response_data", "event_type",
                      "execution_trace", "telemetry_target", "instruction_id"):
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)

def setup_logger(name: str) -> logging.Logger:
    """Setup structured JSON logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger