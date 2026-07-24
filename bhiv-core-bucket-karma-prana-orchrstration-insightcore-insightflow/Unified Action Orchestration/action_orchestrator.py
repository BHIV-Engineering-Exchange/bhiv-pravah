import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Integration clients
from integration.bucket_client import bucket_client
from integration.karma_client import karma_client

# Configure logging
logging.basicConfig(filename='lifecycle.log', level=logging.INFO, format='%(asctime)s - %(message)s')

app = FastAPI()

try:
    from observability.pravah_adapter import start_heartbeat, emit_pravah_signal
    start_heartbeat(60)
except Exception as e:
    logging.warning(f"Failed to start Pravah heartbeat: {e}")

# In-memory storage for actions (in production, use a database)
actions: Dict[str, Dict[str, Any]] = {}

class ActionRequest(BaseModel):
    action_id: str
    action_type: str
    payload: Dict[str, Any]

class ExecutionResult(BaseModel):
    action_id: str
    success: bool
    error: Optional[str] = None

def log_state_change(action_id: str, state: str, details: str = ""):
    logging.info(f"STATE={state}: {action_id} {details}")

def emit_command(command: Dict[str, Any]):
    # In a real implementation, this would send to a message queue or external service
    logging.info(f"COMMAND_EMITTED: {json.dumps(command)}")
    print(f"Emitted command: {json.dumps(command)}")  # For demo purposes

@app.get("/health")
def health():
    return {"status": "ok", "service": "bhiv-uao", "version": "1.0.0"}

@app.post("/api/assistant")
async def receive_action(action: ActionRequest):
    start_time = datetime.utcnow()
    if action.action_id in actions:
        raise HTTPException(status_code=400, detail="Action ID already exists")

    # Safety checks (placeholder - implement actual checks)
    if not is_safe(action):
        raise HTTPException(status_code=403, detail="Action failed safety checks")

    # Create action record
    now = datetime.utcnow().isoformat()
    actions[action.action_id] = {
        "action_id": action.action_id,
        "action_type": action.action_type,
        "state": "requested",
        "payload": action.payload,
        "created_at": now,
        "updated_at": now,
        "error": None
    }

    logging.info(f"ACTION_RECEIVED: {action.action_id}")
    log_state_change(action.action_id, "requested")

    # Fire-and-forget: Log to Bucket and Karma
    try:
        await bucket_client.log_orchestration_event(
            action_id=action.action_id,
            action_type=action.action_type,
            state="requested",
            payload=action.payload
        )
        await karma_client.log_orchestration_behavior(
            action_id=action.action_id,
            action_type=action.action_type,
            state="requested",
            metadata=action.payload
        )
    except Exception:
        pass  # Non-blocking

    # Transition to executing
    actions[action.action_id]["state"] = "executing"
    actions[action.action_id]["updated_at"] = datetime.utcnow().isoformat()
    log_state_change(action.action_id, "executing")

    # Fire-and-forget: Log executing state
    try:
        await bucket_client.log_orchestration_event(
            action_id=action.action_id,
            action_type=action.action_type,
            state="executing",
            payload=action.payload
        )
        await karma_client.log_orchestration_behavior(
            action_id=action.action_id,
            action_type=action.action_type,
            state="executing",
            metadata=action.payload
        )
    except Exception:
        pass  # Non-blocking

    # Emit command based on action type
    command = {
        "command": action.action_type,
        "action_id": action.action_id,
        "payload": action.payload
    }
    emit_command(command)

    try:
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        emit_pravah_signal(state="running", latency_ms=latency_ms)
    except Exception:
        pass

    return {"status": "accepted", "action_id": action.action_id}

@app.post("/api/execution_result")
async def receive_execution_result(result: ExecutionResult):
    if result.action_id not in actions:
        raise HTTPException(status_code=404, detail="Action not found")

    action = actions[result.action_id]
    if action["state"] != "executing":
        raise HTTPException(status_code=400, detail="Action not in executing state")

    # Update state
    new_state = "completed" if result.success else "failed"
    action["state"] = new_state
    action["updated_at"] = datetime.utcnow().isoformat()
    if not result.success:
        action["error"] = result.error

    log_state_change(result.action_id, new_state, f"Error: {result.error}" if result.error else "")

    # Fire-and-forget: Log completion state
    try:
        await bucket_client.log_orchestration_event(
            action_id=result.action_id,
            action_type=action["action_type"],
            state=new_state,
            payload=action["payload"],
            error=result.error
        )
        await karma_client.log_orchestration_behavior(
            action_id=result.action_id,
            action_type=action["action_type"],
            state=new_state,
            metadata={"error": result.error} if result.error else {}
        )
    except Exception:
        pass  # Non-blocking

    return {"status": "updated"}

def is_safe(action: ActionRequest) -> bool:
    # Placeholder for safety checks - implement actual logic
    # For example, check payload for malicious content, rate limiting, etc.
    return True

if __name__ == "__main__":
    import uvicorn
    # Port 8004 (Karma=8000, Bucket=8001, Core=8002, Workflow=8003, UAO=8004)
    uvicorn.run(app, host="0.0.0.0", port=8004)