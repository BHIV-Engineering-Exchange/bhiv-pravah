"""
Insight Core Bridge - Standalone Security Service
Port: 8005
Purpose: JWT validation and replay attack prevention for Core-Bucket communication
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import jwt
import time
import json
import os
from pathlib import Path

# Configuration
BRIDGE_VERSION = "4.2.0"
SERVICE_NAME = "InsightBridge"
FAIL_CLOSED = True
SECRET_KEY = os.getenv("INSIGHT_SECRET_KEY", "demo-secret")
ALGORITHM = "HS256"

# Storage for replay protection
STORE_FILE = Path(__file__).parent / "replay_store.json"

app = FastAPI(title="Insight Core Bridge", version=BRIDGE_VERSION)

try:
    from observability.pravah_adapter import start_heartbeat, emit_pravah_signal
    start_heartbeat(60)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to start Pravah heartbeat: {e}")

class InboundRequest(BaseModel):
    token: str
    nonce: str
    payload: Dict[str, Any]

class DecisionResponse(BaseModel):
    decision: str
    reason: str
    version: str

def _load_nonces() -> set:
    """Load seen nonces from storage"""
    if not STORE_FILE.exists():
        return set()
    try:
        with open(STORE_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def _save_nonces(seen: set) -> None:
    """Save seen nonces to storage"""
    try:
        with open(STORE_FILE, "w") as f:
            json.dump(list(seen), f)
    except Exception:
        pass

def validate_jwt(token: str) -> bool:
    """Validate JWT token"""
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = decoded.get("exp")
        if exp is None:
            return False
        if exp <= time.time():
            return False
        return True
    except jwt.PyJWTError:
        return False

def check_and_store_nonce(nonce: str) -> bool:
    """Check if nonce was seen before and store it"""
    seen = _load_nonces()
    if nonce in seen:
        return False
    seen.add(nonce)
    _save_nonces(seen)
    return True

def emit_telemetry(decision: str, reason: str):
    """Emit telemetry event"""
    event = {
        "service": SERVICE_NAME,
        "version": BRIDGE_VERSION,
        "timestamp": int(time.time()),
        "decision": decision,
        "reason": reason
    }
    print(json.dumps(event))
    try:
        state = "running" if decision == "ALLOW" else "degraded"
        errors = 0 if decision == "ALLOW" else 1
        emit_pravah_signal(state=state, errors_last_min=errors, extra={"decision": decision, "reason": reason})
    except Exception:
        pass

@app.post("/ingest")
def ingest(req: InboundRequest):
    """Validate inbound request with JWT and replay protection"""
    try:
        # Validate JWT
        if not validate_jwt(req.token):
            emit_telemetry("DENY", "INVALID_OR_EXPIRED_JWT")
            return JSONResponse(
                status_code=403,
                content={
                    "decision": "DENY",
                    "reason": "INVALID_OR_EXPIRED_JWT",
                    "version": BRIDGE_VERSION
                }
            )
        
        # Check replay attack
        if not check_and_store_nonce(req.nonce):
            emit_telemetry("DENY", "REPLAY_DETECTED")
            return JSONResponse(
                status_code=403,
                content={
                    "decision": "DENY",
                    "reason": "REPLAY_DETECTED",
                    "version": BRIDGE_VERSION
                }
            )
        
        # All checks passed
        emit_telemetry("ALLOW", "OK")
        return {
            "decision": "ALLOW",
            "reason": "OK",
            "version": BRIDGE_VERSION
        }
    
    except Exception as e:
        emit_telemetry("DENY", "INTERNAL_ERROR")
        return JSONResponse(
            status_code=403,
            content={
                "decision": "DENY",
                "reason": "INTERNAL_ERROR",
                "version": BRIDGE_VERSION
            }
        )

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": SERVICE_NAME, "version": BRIDGE_VERSION}

@app.get("/metrics")
def metrics():
    """Metrics endpoint"""
    return {
        "bridge_version": BRIDGE_VERSION,
        "service": SERVICE_NAME,
        "fail_closed": FAIL_CLOSED
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
