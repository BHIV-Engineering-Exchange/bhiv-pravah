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
from src.core.cet_contract_compiler import CETContractCompiler
from src.core.creator_core_parser import RoutingDecision
from src.utils.insightflow import make_lineage_event
from src.utils.telemetry_writer import emit_insightflow_event

app = FastAPI(
    title="CET Contract Compiler Service",
    description="Compiles blueprints into deterministic execution contracts",
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

compiler = CETContractCompiler()

class CompileRequest(BaseModel):
    instruction: dict
    routing_decision: dict

@app.get("/health")
def health():
    return {"status": "ok", "service": "cet"}

@app.post("/contract/compile", dependencies=[Depends(verify_api_key)])
def compile_contract(req: CompileRequest):
    try:
        rd = req.routing_decision
        decision = RoutingDecision(
            blueprint_type=rd.get("blueprint_type", ""),
            target_product=rd.get("target_product", ""),
            execution_intent=rd.get("execution_intent", ""),
            module_path=rd.get("module_path", ""),
            adapter_name=rd.get("adapter_name", ""),
            execution_data=rd.get("execution_data", {})
        )
        contract = compiler.compile_contract(req.instruction, decision)
        payload = compiler.contract_to_dict(contract)
        trace_id = payload.get("trace_id") or req.instruction.get("trace_id", "unknown")
        emit_insightflow_event(
            make_lineage_event(
                "contract.compiled",
                trace_id,
                trace_id,
                artifact_hash=payload.get("contract_hash"),
                component="cet",
                details={"contract_id": payload.get("contract_id")},
            )
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CET_PORT", "8006"))
    uvicorn.run(app, host="0.0.0.0", port=port)
