import json
import time
from .config import BRIDGE_VERSION, SERVICE_NAME

def emit(decision: str, reason: str):
    event = {
        "service": SERVICE_NAME,
        "version": BRIDGE_VERSION,
        "timestamp": int(time.time()),
        "decision": decision,
        "reason": reason
    }
    print(json.dumps(event))  # demo-safe deterministic telemetry
