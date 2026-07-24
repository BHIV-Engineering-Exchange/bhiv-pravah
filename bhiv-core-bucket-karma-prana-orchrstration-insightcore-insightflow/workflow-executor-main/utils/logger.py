# utils/logger.py

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any


def get_logger() -> logging.Logger:
    logger = logging.getLogger("workflow_executor")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def log_event(event: Dict[str, Any]) -> None:
    """
    Structured, append-only event log.
    This simulates Bucket ingestion.
    """

    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **event,
    }

    sys.stdout.write(json.dumps(record) + "\n")
    sys.stdout.flush()
