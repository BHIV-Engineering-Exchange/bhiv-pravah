"""
BHIV Integration Bridge - Full Pipeline Orchestrator
====================================================
Connects: Prompt Runner → Creator Core → BHIV Core → Bucket

Enforces strict trace_id and workflow_id propagation across all endpoints,
secured with API key middleware.
"""

import json
import importlib
import os
import sys
import uuid
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from src.adapters.ttg_input_normalizer import TTGInputNormalizer
from src.adapters.ttg_output_adapter import TTGOutputAdapter
from src.adapters.ttv_input_normalizer import TTVInputNormalizer
from src.adapters.ttv_output_adapter import TTVOutputAdapter
from src.adapters.gurukul_input_normalizer import GurukulInputNormalizer
from src.adapters.gurukul_output_adapter import GurukulOutputAdapter
from src.adapters.simulation_runtime_input_normalizer import SimulationRuntimeInputNormalizer
from src.adapters.simulation_runtime_output_adapter import SimulationRuntimeOutputAdapter
from config import ConfigManager
from src.utils.insightflow import make_event, make_lineage_event
from src.utils.determinism import compute_pipeline_deterministic_hash

REPO_ROOT = Path(__file__).resolve().parent
SPRINT_DIR = REPO_ROOT / "SHAKTI Production Convergence Sprint (Energy Intelligence Platform Production Transition)"
if str(SPRINT_DIR) not in sys.path:
    sys.path.insert(0, str(SPRINT_DIR))

_metrics_module = importlib.import_module("runtime_manager.metrics_middleware")
request_metrics_middleware = _metrics_module.request_metrics_middleware
get_local_metrics_snapshot = _metrics_module.get_local_metrics_snapshot

# Load environment variables
load_dotenv()


class ArtifactGraph:
    """Manages the artifact chain: A1 → A2 → A2b → A2c → A2d → A3 → A4"""
    
    def __init__(self, bucket_url: str = "http://127.0.0.1:8005"):
        self.artifacts = {}
        self.bucket_url = bucket_url
        
    def create_chain(self, trace_id: str, workflow_id: str, instruction: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        """Create full artifact chain for a request"""
        chain = {
            "trace_id": trace_id,
            "workflow_id": workflow_id,
            "A1_instruction": self._store_artifact("instruction", instruction, trace_id, workflow_id, headers),
            "A2_blueprint": None,  # Set after Creator Core
            "A2b_contract": None,
            "A2c_authority": None,
            "A2d_gate": None,
            "A3_execution": None,
            "A4_result": None
        }
        self.artifacts[trace_id] = chain
        return chain
        
    def update_artifact(self, trace_id: str, workflow_id: str, artifact_type: str, data: Dict[str, Any], headers: Dict[str, str]) -> str:
        """Update artifact in chain"""
        artifact_id = self._store_artifact(artifact_type, data, trace_id, workflow_id, headers)
        if trace_id in self.artifacts:
            self.artifacts[trace_id][f"A{self._get_artifact_number(artifact_type)}_{artifact_type}"] = artifact_id
        return artifact_id
        
    def _store_artifact(self, artifact_type: str, data: Dict[str, Any], trace_id: str, workflow_id: str, headers: Dict[str, str]) -> str:
        """Store individual artifact to bucket"""
        artifact_id = f"{artifact_type}_{uuid.uuid4().hex[:8]}"
        
        # Inject workflow_id into data for storage correlation
        data_to_store = data.copy() if isinstance(data, dict) else {"raw": data}
        data_to_store["workflow_id"] = workflow_id
        data_to_store["trace_id"] = trace_id
        
        try:
            # Store to BHIV Bucket
            response = requests.post(
                f"{self.bucket_url}/bucket/store",
                json={
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "data": data_to_store,
                    "trace_id": trace_id
                },
                headers=headers,
                timeout=10
            )
            if response.status_code != 200:
                print(f"Warning: Failed to store artifact {artifact_id} to bucket: {response.text}")
        except Exception as e:
            print(f"Warning: Bucket storage failed for {artifact_id}: {str(e)}")
            
        return artifact_id
        
    def _get_artifact_number(self, artifact_type: str) -> int:
        mapping = {"telemetry": 0, "instruction": 1, "blueprint": 2, "contract": "2b", "authority": "2c", "gate": "2d", "alert": 5, "execution": 3, "result": 4}
        return mapping.get(artifact_type, 0)


class BHIVIntegrationBridge:
    """Main integration orchestrator"""
    
    def __init__(self):
        self.prompt_runner_url = ConfigManager.get_service_url("prompt_runner")
        self.creator_core_url = ConfigManager.get_service_url("creator_core")
        self.bhiv_core_url = ConfigManager.get_service_url("bhiv_core")
        self.cet_url = ConfigManager.get_service_url("cet")
        self.sarathi_url = ConfigManager.get_service_url("sarathi")
        self.gate_url = ConfigManager.get_service_url("gate")
        self.bucket_url = ConfigManager.get_service_url("bucket")
        self.artifact_graph = ArtifactGraph(self.bucket_url)
        self.telemetry_path = Path("bhiv_bucket") / "insightflow_events.jsonl"
        self.input_adapters = {
            "ttg": TTGInputNormalizer(),
            "ttv": TTVInputNormalizer(),
            "gurukul": GurukulInputNormalizer(),
            "simulation_runtime": SimulationRuntimeInputNormalizer(),
        }
        self.output_adapters = {
            "ttg": TTGOutputAdapter(),
            "ttv": TTVOutputAdapter(),
            "gurukul": GurukulOutputAdapter(),
            "simulation_runtime": SimulationRuntimeOutputAdapter(),
        }

    def _emit_telemetry(self, event: Dict[str, Any]) -> None:
        self.telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.telemetry_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
        
    def _report_to_pravah(self, trace_id: str, status: str, duration_ms: float, error: str = None) -> None:
        """Report pipeline execution to Pravah control plane."""
        import threading
        import requests
        import hmac
        import hashlib
        import json
        import time
        
        def _send():
            try:
                state = "running"
                if status == "error" or error:
                    state = "degraded"
                    
                payload = {
                    "app": "bhiv-integrator",
                    "env": "dev",
                    "state": state,
                    "latency_ms": round(duration_ms, 2),
                    "errors_last_min": 1 if error else 0,
                    "workers": 1
                }
                
                # Canonical serialization
                canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
                body_hash = hashlib.sha256(canonical.encode()).hexdigest()
                timestamp = str(int(time.time()))
                
                secret_key = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
                trace_payload = f"{trace_id}:{timestamp}:{body_hash}"
                signature = hmac.new(
                    secret_key.encode(),
                    trace_payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                headers = {
                    "X-Trace-Id": trace_id,
                    "X-Timestamp": timestamp,
                    "X-Trace-Signature": signature,
                    "Content-Type": "application/json"
                }
                
                requests.post(
                    "http://localhost:7000/api/runtime",
                    json=payload,
                    headers=headers,
                    timeout=5.0
                )
            except Exception:
                pass
                
        threading.Thread(target=_send, daemon=True).start()

    def process_full_pipeline(self, user_prompt: str, trace_id: Optional[str] = None, workflow_id: Optional[str] = None, product_context: str = "creator") -> Dict[str, Any]:
        """
        Execute complete pipeline: Prompt → Instruction → Blueprint → Execution → Result
        
        Returns full trace with artifact chain
        """
        import time
        start_time = time.time()
        trace_id = trace_id or f"trace_{uuid.uuid4().hex[:12]}"
        workflow_id = workflow_id or f"wf_{uuid.uuid4().hex[:12]}"
        
        # Build authentication headers
        api_key = os.getenv("AUTH_API_KEY", "")
        headers = {
            "X-Trace-Id": trace_id,
            "X-Workflow-Id": workflow_id
        }
        if api_key:
            headers["X-API-Key"] = api_key
            
        try:
            normalized_prompt = self._normalize_prompt(user_prompt, product_context)
            instruction = self._call_prompt_runner(normalized_prompt, headers, product_context)
            instruction["trace_id"] = trace_id
            instruction["workflow_id"] = workflow_id
            instruction["instruction_id"] = trace_id
            self._emit_telemetry(make_lineage_event("instruction.received", trace_id, trace_id, component="integration_bridge", details={"workflow_id": workflow_id, "product_context": product_context}))
            
            # Create artifact chain
            chain = self.artifact_graph.create_chain(trace_id, workflow_id, instruction, headers)
            
            # PHASE 2: Creator Core → Blueprint Generation  
            blueprint = self._call_creator_core(instruction, headers)
            blueprint["trace_id"] = trace_id
            blueprint["workflow_id"] = workflow_id
            self.artifact_graph.update_artifact(trace_id, workflow_id, "blueprint", blueprint, headers)
            routing_decision = self._derive_routing_decision_from_blueprint(blueprint, product_context)
            contract = self._call_cet(instruction, routing_decision, headers)
            self.artifact_graph.update_artifact(trace_id, workflow_id, "contract", contract, headers)
 
            authority_decision = self._call_sarathi(contract, headers)
            self.artifact_graph.update_artifact(trace_id, workflow_id, "authority", authority_decision, headers)
            if not authority_decision.get("allowed", False):
                duration_ms = (time.time() - start_time) * 1000
                self._report_to_pravah(trace_id, "error", duration_ms, error="authority_rejected")
                return {
                    "status": "rejected",
                    "trace_id": trace_id,
                    "workflow_id": workflow_id,
                    "artifact_chain": self.artifact_graph.artifacts[trace_id],
                    "pipeline_result": {"reason": authority_decision.get("reason", "authority_rejected")},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
 
            gate_decision = self._call_gate(contract, authority_decision, headers)
            self.artifact_graph.update_artifact(trace_id, workflow_id, "gate", gate_decision, headers)
            if gate_decision.get("gate_status") not in ("ALLOWED", "EXECUTED"):
                duration_ms = (time.time() - start_time) * 1000
                self._report_to_pravah(trace_id, "error", duration_ms, error="gate_rejected")
                return {
                    "status": "rejected",
                    "trace_id": trace_id,
                    "workflow_id": workflow_id,
                    "artifact_chain": self.artifact_graph.artifacts[trace_id],
                    "pipeline_result": {"reason": gate_decision.get("message", "gate_rejected")},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # PHASE 3: BHIV Core → Execution
            execution_result = self._call_bhiv_core(blueprint, trace_id, workflow_id, headers)
            execution_result["trace_id"] = trace_id
            execution_result["workflow_id"] = workflow_id
            self.artifact_graph.update_artifact(trace_id, workflow_id, "execution", execution_result, headers)
            
            # PHASE 4: Final Result Assembly
            final_result = self._assemble_final_result(instruction, blueprint, contract, authority_decision, gate_decision, execution_result)
            final_result["product_output"] = self._adapt_output(product_context, execution_result)
            final_result["trace_id"] = trace_id
            final_result["workflow_id"] = workflow_id
            self.artifact_graph.update_artifact(trace_id, workflow_id, "result", final_result, headers)
            
            duration_ms = (time.time() - start_time) * 1000
            self._report_to_pravah(trace_id, "success", duration_ms)
            return {
                "status": "success",
                "trace_id": trace_id,
                "workflow_id": workflow_id,
                "artifact_chain": self.artifact_graph.artifacts[trace_id],
                "pipeline_result": final_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._report_to_pravah(trace_id, "error", duration_ms, error=str(e))
            return {
                "status": "error", 
                "trace_id": trace_id,
                "workflow_id": workflow_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _call_prompt_runner(self, prompt: str, headers: Dict[str, str], product_context: str) -> Dict[str, Any]:
        """Phase 1: Convert prompt to structured instruction"""
        response = requests.post(
            f"{self.prompt_runner_url}/generate",
            json={"prompt": prompt, "origin": product_context},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def _call_creator_core(self, instruction: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Phase 2: Generate blueprint from instruction"""
        # Filter out extra keys that are forbidden by creator-core PromptRunnerInstruction model
        allowed_keys = {"prompt", "module", "intent", "topic", "tasks", "output_format", "product_context"}
        clean_instruction = {k: v for k, v in instruction.items() if k in allowed_keys}
        
        response = requests.post(
            f"{self.creator_core_url}/creator-core/generate-blueprint", 
            json=clean_instruction,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def _call_bhiv_core(self, blueprint: Dict[str, Any], trace_id: str, workflow_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Phase 3: Execute blueprint through BHIV Core"""
        blueprint_data = blueprint.get("blueprint", blueprint)
        
        # Convert to Core request format
        core_request = {
            "module": "creator",
            "intent": "generate", 
            "user_id": f"bhiv_user_{uuid.uuid4().hex[:8]}",
            "data": {
                "blueprint": blueprint_data.get("payload", blueprint_data),
                "target_product": blueprint_data.get("target_product", "creator"),
                "trace_id": trace_id,
                "workflow_id": workflow_id
            }
        }
        
        response = requests.post(
            f"{self.bhiv_core_url}/core",
            json=core_request,
            headers=headers,
            timeout=45
        )
        response.raise_for_status()
        return response.json()

    def _call_cet(self, instruction: Dict[str, Any], routing_decision: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.cet_url}/contract/compile",
            json={"instruction": instruction, "routing_decision": routing_decision},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _derive_routing_decision_from_blueprint(self, blueprint: Dict[str, Any], product_context: str) -> Dict[str, Any]:
        envelope = blueprint.get("blueprint", blueprint)
        payload = envelope.get("payload", {})
        target_product = envelope.get("target_product", product_context or "creator")
        module_mapping = {
            "content": "creator",
            "creator": "creator",
            "finance": "finance",
            "education": "education",
            "ttv": "video",
            "ttg": "creator",
            "gurukul": "education",
            "simulation_runtime": "creator",
        }
        module_path = module_mapping.get(target_product, "creator")
        intent_type = envelope.get("intent_type", "generate")
        return {
            "blueprint_type": payload.get("blueprint_type", "general_processing"),
            "target_product": target_product,
            "execution_intent": intent_type,
            "module_path": module_path,
            "adapter_name": f"{target_product}_adapter",
            "execution_data": payload,
        }

    def _call_sarathi(self, contract: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.sarathi_url}/authority/validate",
            json={"contract": contract},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _call_gate(self, contract: Dict[str, Any], authority_decision: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.gate_url}/gate/evaluate",
            json={"contract": contract, "authority_decision": authority_decision, "execute": False},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def _assemble_final_result(self, instruction: Dict[str, Any], blueprint: Dict[str, Any], contract: Dict[str, Any],
                               authority: Dict[str, Any], gate: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Assemble final result"""
        return {
            "original_prompt": instruction.get("prompt"),
            "generated_instruction": instruction,
            "blueprint_envelope": blueprint,
            "contract": contract,
            "authority_decision": authority,
            "gate_decision": gate,
            "execution_result": execution,
            "pipeline_status": "completed",
            "deterministic_hash": self._compute_hash(instruction, blueprint, contract, execution)
        }
    
    def _compute_hash(self, instruction, blueprint, contract, execution) -> str:
        """Compute deterministic hash for replay validation (volatile fields stripped)."""
        return compute_pipeline_deterministic_hash(instruction, blueprint, contract, execution)
    
    def replay_from_trace(self, trace_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Replay pipeline from stored trace"""
        try:
            response = requests.get(f"{self.bucket_url}/bucket/trace/{trace_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                bucket_data = response.json()
                return {
                    "status": "success",
                    "trace_id": trace_id,
                    "artifact_chain": bucket_data.get("artifacts", []),
                    "replay_timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "bucket"
                }
        except Exception as e:
            print(f"Bucket replay failed: {str(e)}")
            
        if trace_id not in self.artifact_graph.artifacts:
            return {"status": "error", "message": "Trace not found"}
            
        chain = self.artifact_graph.artifacts[trace_id]
        return {
            "status": "success",
            "trace_id": trace_id,
            "artifact_chain": chain,
            "replay_timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "local"
        }
    
    def health_check(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check all pipeline components"""
        components = {
            "prompt_runner": self._check_component(f"{self.prompt_runner_url}/health", headers),
            "creator_core": self._check_component(f"{self.creator_core_url}/", headers),
            "cet": self._check_component(f"{self.cet_url}/health", headers),
            "sarathi": self._check_component(f"{self.sarathi_url}/health", headers),
            "gate": self._check_component(f"{self.gate_url}/health", headers),
            "bhiv_core": self._check_component(f"{self.bhiv_core_url}/", headers),
            "bucket": self._check_component(f"{self.bucket_url}/bucket/stats", headers)
        }
        all_healthy = all(comp["status"] == "healthy" for comp in components.values())
        return {
            "pipeline_status": "healthy" if all_healthy else "degraded",
            "components": components,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _normalize_prompt(self, user_prompt: str, product_context: str) -> str:
        adapter = self.input_adapters.get(product_context)
        if adapter and isinstance(user_prompt, str) and user_prompt.strip().startswith("{") and user_prompt.strip().endswith("}"):
            try:
                return adapter.normalize(json.loads(user_prompt))
            except Exception:
                return user_prompt
        return user_prompt

    def _adapt_output(self, product_context: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        adapter = self.output_adapters.get(product_context)
        if adapter:
            try:
                return adapter.transform(execution_result)
            except Exception:
                return {"status": "adapter_error", "raw": execution_result}
        return execution_result
    
    def _check_component(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check individual component health"""
        try:
            response = requests.get(url, headers=headers, timeout=5)
            return {"status": "healthy", "code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Integration API endpoints
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from src.utils.security_hardening import security_middleware
from src.utils.auth import auth_middleware, require_auth
from src.utils.observability import observability_middleware

app = FastAPI(
    title="BHIV Integration Bridge",
    description="Full pipeline orchestrator: Prompt Runner → Creator Core → BHIV Core → Bucket",
    version="1.0.0"
)

# Apply global security, auth, and observability middleware
# Middleware order: execution order: observability → auth → security
app.middleware("http")(security_middleware)
app.middleware("http")(auth_middleware)
app.middleware("http")(observability_middleware)
app.middleware("http")(request_metrics_middleware)

bridge = BHIVIntegrationBridge()

class PipelineRequest(BaseModel):
    prompt: str
    trace_id: Optional[str] = None
    workflow_id: Optional[str] = None
    product_context: Optional[str] = "creator"

@app.post("/pipeline/execute", dependencies=[Depends(require_auth)])
async def execute_pipeline(request: PipelineRequest, http_req: Request):
    """Execute full BHIV pipeline"""
    # Extract IDs from headers or request state if available
    trace_id = request.trace_id or http_req.state.trace_id
    workflow_id = request.workflow_id or http_req.state.workflow_id
    
    result = bridge.process_full_pipeline(request.prompt, trace_id, workflow_id, request.product_context or "creator")
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/pipeline/health")
async def pipeline_health(http_req: Request):
    """Check pipeline component health"""
    api_key = os.getenv("AUTH_API_KEY", "")
    headers = {"X-API-Key": api_key} if api_key else {}
    return bridge.health_check(headers)

@app.get("/health")
async def health(http_req: Request):
    """Alias for pipeline health check used by orchestrator"""
    return await pipeline_health(http_req)


@app.get("/internal/metrics-snapshot")
async def internal_metrics_snapshot():
    """Expose runtime request metrics snapshot for control plane aggregation."""
    return get_local_metrics_snapshot()

@app.get("/pipeline/replay/{trace_id}", dependencies=[Depends(require_auth)])
async def replay_pipeline(trace_id: str):
    """Replay pipeline from trace ID"""
    api_key = os.getenv("AUTH_API_KEY", "")
    headers = {"X-API-Key": api_key} if api_key else {}
    result = bridge.replay_from_trace(trace_id, headers)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)