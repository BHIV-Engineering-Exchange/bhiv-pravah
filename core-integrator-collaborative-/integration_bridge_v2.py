"""
BHIV Integration Bridge - Full Pipeline Orchestrator
====================================================
Connects: Prompt Runner → Creator Core → BHIV Core → Bucket

DEPLOYMENT READY:
- All service URLs configurable via environment variables
- Can be deployed independently
- Supports remote services

MANDATORY FLOW:
User Prompt → Prompt Runner → Creator Core → BHIV Core → Bucket
"""

import json
import uuid
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import os

# Import service URLs from configuration
from config.service_urls import get_service_url


class ArtifactGraph:
    """Manages the artifact chain: A1 → A2 → A3 → A4"""
    
    def __init__(self, bucket_url: str = None):
        self.artifacts = {}
        self.bucket_url = bucket_url or get_service_url("bucket")
        
    def create_chain(self, trace_id: str, instruction: Dict[str, Any]) -> Dict[str, str]:
        """Create full artifact chain for a request"""
        chain = {
            "trace_id": trace_id,
            "A1_instruction": self._store_artifact("instruction", instruction, trace_id),
            "A2_blueprint": None,
            "A3_execution": None,
            "A4_result": None
        }
        self.artifacts[trace_id] = chain
        return chain
        
    def update_artifact(self, trace_id: str, artifact_type: str, data: Dict[str, Any]) -> str:
        """Update artifact in chain"""
        artifact_id = self._store_artifact(artifact_type, data, trace_id)
        if trace_id in self.artifacts:
            self.artifacts[trace_id][f"A{self._get_artifact_number(artifact_type)}_{artifact_type}"] = artifact_id
        return artifact_id
        
    def _store_artifact(self, artifact_type: str, data: Dict[str, Any], trace_id: str) -> str:
        """Store individual artifact to bucket"""
        artifact_id = f"{artifact_type}_{uuid.uuid4().hex[:8]}"
        
        try:
            response = requests.post(
                f"{self.bucket_url}/bucket/store",
                json={
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "data": data,
                    "trace_id": trace_id
                },
                timeout=10
            )
            if response.status_code != 200:
                print(f"Warning: Failed to store artifact {artifact_id} to bucket")
        except Exception as e:
            print(f"Warning: Bucket storage failed for {artifact_id}: {str(e)}")
            
        return artifact_id
        
    def _get_artifact_number(self, artifact_type: str) -> int:
        mapping = {"instruction": 1, "blueprint": 2, "execution": 3, "result": 4}
        return mapping.get(artifact_type, 0)


class BHIVIntegrationBridge:
    """Main integration orchestrator - Deployment Ready"""
    
    def __init__(self):
        # Load service URLs from environment/config
        self.prompt_runner_url = get_service_url("prompt_runner")
        self.creator_core_url = get_service_url("creator_core")
        self.bhiv_core_url = get_service_url("bhiv_core")
        self.bucket_url = get_service_url("bucket")
        self.artifact_graph = ArtifactGraph(self.bucket_url)
        
        # Log configuration on startup
        print(f"\n{'='*70}")
        print("BHIV Integration Bridge - Service URLs")
        print(f"{'='*70}")
        print(f"  Prompt Runner:  {self.prompt_runner_url}")
        print(f"  Creator Core:   {self.creator_core_url}")
        print(f"  BHIV Core:      {self.bhiv_core_url}")
        print(f"  Bucket:         {self.bucket_url}")
        print(f"{'='*70}\n")
        
    def process_full_pipeline(self, user_prompt: str) -> Dict[str, Any]:
        """
        Execute complete pipeline: Prompt → Instruction → Blueprint → Execution → Result
        
        Returns full trace with artifact chain
        """
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        
        try:
            # PHASE 1: Prompt Runner → Structured Instruction
            print(f"[Phase 1] Calling Prompt Runner...")
            instruction = self._call_prompt_runner(user_prompt)
            
            # Create artifact chain
            chain = self.artifact_graph.create_chain(trace_id, instruction)
            
            # PHASE 2: Creator Core → Blueprint Generation
            print(f"[Phase 2] Calling Creator Core...")
            blueprint = self._call_creator_core(instruction)
            self.artifact_graph.update_artifact(trace_id, "blueprint", blueprint)
            
            # PHASE 3: BHIV Core → Execution
            print(f"[Phase 3] Calling BHIV Core...")
            execution_result = self._call_bhiv_core(blueprint)
            self.artifact_graph.update_artifact(trace_id, "execution", execution_result)
            
            # PHASE 4: Final Result Assembly
            print(f"[Phase 4] Assembling final result...")
            final_result = self._assemble_final_result(instruction, blueprint, execution_result)
            self.artifact_graph.update_artifact(trace_id, "result", final_result)
            
            return {
                "status": "success",
                "trace_id": trace_id,
                "artifact_chain": self.artifact_graph.artifacts[trace_id],
                "pipeline_result": final_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "trace_id": trace_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _call_prompt_runner(self, prompt: str) -> Dict[str, Any]:
        """Phase 1: Convert prompt to structured instruction"""
        try:
            response = requests.post(
                f"{self.prompt_runner_url}/generate",
                json={"prompt": prompt},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise Exception(f"Prompt Runner not reachable at {self.prompt_runner_url}")
        except requests.exceptions.Timeout:
            raise Exception(f"Prompt Runner timeout at {self.prompt_runner_url}")
    
    def _call_creator_core(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Generate blueprint from instruction"""
        try:
            response = requests.post(
                f"{self.creator_core_url}/creator-core/generate-blueprint", 
                json=instruction,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise Exception(f"Creator Core not reachable at {self.creator_core_url}")
        except requests.exceptions.Timeout:
            raise Exception(f"Creator Core timeout at {self.creator_core_url}")
    
    def _call_bhiv_core(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Execute blueprint through BHIV Core"""
        # Extract blueprint data for Core execution
        blueprint_data = blueprint.get("blueprint", blueprint)
        
        # Convert to Core request format
        core_request = {
            "module": "creator",
            "intent": "generate", 
            "user_id": f"bhiv_user_{uuid.uuid4().hex[:8]}",
            "data": {
                "blueprint": blueprint_data.get("payload", blueprint_data),
                "target_product": blueprint_data.get("target_product", "creator")
            }
        }
        
        try:
            response = requests.post(
                f"{self.bhiv_core_url}/core",
                json=core_request,
                timeout=45
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise Exception(f"BHIV Core not reachable at {self.bhiv_core_url}")
        except requests.exceptions.Timeout:
            raise Exception(f"BHIV Core timeout at {self.bhiv_core_url}")
    
    def _assemble_final_result(self, instruction: Dict[str, Any], blueprint: Dict[str, Any], 
                              execution: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Assemble final result"""
        return {
            "original_prompt": instruction.get("prompt"),
            "generated_instruction": instruction,
            "blueprint_envelope": blueprint,
            "execution_result": execution,
            "pipeline_status": "completed",
            "deterministic_hash": self._compute_hash(instruction, blueprint, execution)
        }
    
    def _compute_hash(self, *args) -> str:
        """Compute deterministic hash for replay validation"""
        combined = json.dumps(args, sort_keys=True)
        import hashlib
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def replay_from_trace(self, trace_id: str) -> Dict[str, Any]:
        """Replay pipeline from stored trace"""
        try:
            response = requests.get(f"{self.bucket_url}/bucket/trace/{trace_id}", timeout=10)
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
            
        # Fallback to local artifacts
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
    
    def health_check(self) -> Dict[str, Any]:
        """Check all pipeline components"""
        components = {
            "prompt_runner": self._check_component(f"{self.prompt_runner_url}/health"),
            "creator_core": self._check_component(f"{self.creator_core_url}/"),
            "bhiv_core": self._check_component(f"{self.bhiv_core_url}/"),
            "bucket": self._check_component(f"{self.bucket_url}/bucket/stats")
        }
        
        all_healthy = all(comp["status"] == "healthy" for comp in components.values())
        
        return {
            "pipeline_status": "healthy" if all_healthy else "degraded",
            "components": components,
            "service_urls": {
                "prompt_runner": self.prompt_runner_url,
                "creator_core": self.creator_core_url,
                "bhiv_core": self.bhiv_core_url,
                "bucket": self.bucket_url
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _check_component(self, url: str) -> Dict[str, Any]:
        """Check individual component health"""
        try:
            response = requests.get(url, timeout=5)
            return {"status": "healthy", "code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# FastAPI Application
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="BHIV Integration Bridge",
    description="Full pipeline orchestrator: Prompt Runner → Creator Core → BHIV Core → Bucket",
    version="2.0.0"
)

# Initialize bridge
bridge = None

@app.on_event("startup")
async def startup_event():
    global bridge
    bridge = BHIVIntegrationBridge()


class PipelineRequest(BaseModel):
    prompt: str


@app.post("/pipeline/execute")
async def execute_pipeline(request: PipelineRequest):
    """Execute full BHIV pipeline"""
    result = bridge.process_full_pipeline(request.prompt)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/pipeline/health")
async def pipeline_health():
    """Check pipeline component health"""
    return bridge.health_check()


@app.get("/pipeline/replay/{trace_id}")
async def replay_pipeline(trace_id: str):
    """Replay pipeline from trace ID"""
    result = bridge.replay_from_trace(trace_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "BHIV Integration Bridge",
        "version": "2.0.0",
        "status": "running",
        "configured_services": {
            "prompt_runner": bridge.prompt_runner_url if bridge else "not initialized",
            "creator_core": bridge.creator_core_url if bridge else "not initialized",
            "bhiv_core": bridge.bhiv_core_url if bridge else "not initialized",
            "bucket": bridge.bucket_url if bridge else "not initialized"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8004"))
    uvicorn.run(app, host="0.0.0.0", port=port)
