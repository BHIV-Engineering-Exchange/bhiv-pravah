import logging
import json
import sys
import os
from datetime import datetime
from app.core.context import get_trace_id

class JsonFormatter(logging.Formatter):
    """
    Standard JSON Formatter for Gurukul Runtime.
    Converts log records to structured JSON for Pravah consumption.
    """
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
            "trace_id": get_trace_id(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry)

def setup_logging(level=logging.INFO):
    """
    Initialize global logging with JSON formatting.
    Writes to stdout for Docker/Vercel/Render compatibility.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clean existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Stdout handler with JSON formatter
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(stdout_handler)

    # Optional: File handler for persistence
    log_dir = os.path.join(os.getcwd(), "runtime_logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except:
            pass
    
    if os.path.exists(log_dir):
        file_handler = logging.FileHandler(os.path.join(log_dir, "runtime.log.json"))
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)

    logging.info("Structured logging initialized in JSON format.")
