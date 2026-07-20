import os
import sys
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

# Add project root to PYTHONPATH
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from src.core.execution_gate import ExecutionGate
from src.utils.insightflow import make_lineage_event
from src.utils.telemetry_writer import emit_insightflow_event
from src.agents.finance import FinanceAgent
from src.agents.education import EducationAgent
from src.agents.creator import CreatorAgent
from src.agents.video import VideoAgent
from src.core.module_loader import load_modules
from src.modules.base import BaseModule

app = FastAPI(
    title="Execution Gate Service",
    description="Enforces authority decisions and executes modules if authorized",
    version="1.0.0"
)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    expected_api_key = os.getenv("AUTH_API_KEY", "")
    auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() in ("1", "true", "yes")
    if auth_enabled and expected_api_key:
        if not api_key or api_key != expected_api_key:
            raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

# Load agents exactly like the Gateway does
agents = {
    "finance": FinanceAgent(),
    "education": EducationAgent(),
    "creator": CreatorAgent(),
    "video": VideoAgent(),
}

loaded_modules, errors = load_modules()
for name, inst in loaded_modules.items():
    agents[name] = inst

for name, mod in list(agents.items()):
    if hasattr(mod, 'process'):
        if not isinstance(mod, BaseModule):
            agents[name] = None

gate = ExecutionGate(agents)

class EvaluateRequest(BaseModel):
    contract: dict
    authority_decision: dict
    execute: bool = False

@app.get("/health")
def health():
    return {"status": "ok", "service": "gate"}

@app.post("/gate/evaluate", dependencies=[Depends(verify_api_key)])
def evaluate_gate(req: EvaluateRequest):
    try:
        execution_result = gate.execute_if_authorized(req.contract, req.authority_decision, execute=req.execute)
        trace_id = req.contract.get("trace_id", "unknown")
        emit_insightflow_event(
            make_lineage_event(
                "gate.evaluated",
                trace_id,
                trace_id,
                component="gate",
                status="success" if execution_result.get("gate_status") in ("ALLOWED", "EXECUTED") else "rejected",
                details={"gate_status": execution_result.get("gate_status"), "message": execution_result.get("message")},
            )
        )
        return execution_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GATE_PORT", "8008"))
    uvicorn.run(app, host="0.0.0.0", port=port)
