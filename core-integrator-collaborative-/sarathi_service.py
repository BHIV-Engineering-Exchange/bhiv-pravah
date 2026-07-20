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
from src.core.authority_engine import SarathiAuthorityEngine
from src.utils.insightflow import make_lineage_event
from src.utils.telemetry_writer import emit_insightflow_event

app = FastAPI(
    title="Sarathi Authority Service",
    description="Validates execution contracts and issues authorization decisions",
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

engine = SarathiAuthorityEngine()

class ValidateRequest(BaseModel):
    contract: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "sarathi"}

@app.post("/authority/validate", dependencies=[Depends(verify_api_key)])
def validate_contract(req: ValidateRequest):
    try:
        decision = engine.validate_contract(req.contract)
        payload = engine._decision_to_dict(decision)
        trace_id = payload.get("trace_id") or req.contract.get("trace_id", "unknown")
        emit_insightflow_event(
            make_lineage_event(
                "authority.validated",
                trace_id,
                trace_id,
                component="sarathi",
                status="success" if payload.get("allowed") else "rejected",
                details={"reason": payload.get("reason"), "decision_id": payload.get("decision_id")},
            )
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SARATHI_PORT", "8007"))
    uvicorn.run(app, host="0.0.0.0", port=port)
