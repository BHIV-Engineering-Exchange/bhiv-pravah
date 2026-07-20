"""
TANTRA Integration Bridge
=========================
Enforces system boundaries and routes TTG/TTV through the BHIV pipeline.

TANTRA PRINCIPLES:
1. Core is the ONLY execution authority
2. NO direct execution from Creator Core
3. NO bypass of pipeline
4. Adapters are THIN layers only
5. System isolation enforced

Pipeline Flow:
TTG/TTV Input → Normalizer → Prompt Runner → Creator Core → BHIV Core → Adapter → TTG/TTV Output
"""

import requests
from typing import Dict, Any
from datetime import datetime, timezone

from .ttg_input_normalizer import TTGInputNormalizer
from .ttv_input_normalizer import TTVInputNormalizer
from .ttg_output_adapter import TTGOutputAdapter
from .ttv_output_adapter import TTVOutputAdapter


class TANTRAIntegrationBridge:
    """
    TANTRA-compliant integration bridge for TTG/TTV systems.
    
    Enforces:
    - All requests go through Prompt Runner → Creator Core → BHIV Core
    - NO direct execution
    - NO bypass
    - System boundary isolation
    """
    
    def __init__(self):
        # Component URLs
        self.prompt_runner_url = "http://127.0.0.1:8003"
        self.bhiv_core_url = "http://127.0.0.1:8001"     # Main Core (main.py)
        self.bucket_url = "http://127.0.0.1:8005"
        
        # Input normalizers
        self.ttg_normalizer = TTGInputNormalizer()
        self.ttv_normalizer = TTVInputNormalizer()
        
        # Output adapters
        self.ttg_adapter = TTGOutputAdapter()
        self.ttv_adapter = TTVOutputAdapter()
    
    def process_ttg_request(self, ttg_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process TTG request through full pipeline
        
        Flow: TTG Input → Normalizer → Pipeline → Adapter → TTG Output
        """
        trace_id = f"ttg_trace_{datetime.now(timezone.utc).timestamp()}"
        
        try:
            # PHASE 1: Input Normalization
            if not self.ttg_normalizer.validate_ttg_input(ttg_input):
                return self._error_response("Invalid TTG input format", trace_id)
            
            unified_prompt = self.ttg_normalizer.normalize(ttg_input)
            
            # PHASE 2: Pipeline Execution (MANDATORY - NO BYPASS)
            pipeline_result = self._execute_pipeline(unified_prompt, "ttg", trace_id)
            
            if pipeline_result["status"] != "success":
                return pipeline_result
            
            # PHASE 3: Output Adaptation (OUTSIDE Core)
            core_output = pipeline_result["core_output"]
            ttg_output = self.ttg_adapter.transform(core_output)
            
            # PHASE 4: Artifact Trace Validation
            artifact_chain = pipeline_result.get("artifact_chain", {})
            
            return {
                "status": "success",
                "product": "ttg",
                "trace_id": trace_id,
                "ttg_output": ttg_output,
                "artifact_chain": artifact_chain,
                "pipeline_metadata": {
                    "original_input": ttg_input,
                    "unified_prompt": unified_prompt,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            return self._error_response(str(e), trace_id)
    
    def process_ttv_request(self, ttv_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process TTV request through full pipeline
        
        Flow: TTV Input → Normalizer → Pipeline → Adapter → TTV Output
        """
        trace_id = f"ttv_trace_{datetime.now(timezone.utc).timestamp()}"
        
        try:
            # PHASE 1: Input Normalization
            if not self.ttv_normalizer.validate_ttv_input(ttv_input):
                return self._error_response("Invalid TTV input format", trace_id)
            
            unified_prompt = self.ttv_normalizer.normalize(ttv_input)
            
            # PHASE 2: Pipeline Execution (MANDATORY - NO BYPASS)
            pipeline_result = self._execute_pipeline(unified_prompt, "ttv", trace_id)
            
            if pipeline_result["status"] != "success":
                return pipeline_result
            
            # PHASE 3: Output Adaptation (OUTSIDE Core)
            core_output = pipeline_result["core_output"]
            ttv_output = self.ttv_adapter.transform(core_output)
            
            # PHASE 4: Artifact Trace Validation
            artifact_chain = pipeline_result.get("artifact_chain", {})
            
            return {
                "status": "success",
                "product": "ttv",
                "trace_id": trace_id,
                "ttv_output": ttv_output,
                "artifact_chain": artifact_chain,
                "pipeline_metadata": {
                    "original_input": ttv_input,
                    "unified_prompt": unified_prompt,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            return self._error_response(str(e), trace_id)
    
    def _execute_pipeline(self, prompt: str, product: str, trace_id: str) -> Dict[str, Any]:
        """
        Execute full BHIV pipeline (MANDATORY - NO BYPASS ALLOWED)
        
        Flow: Prompt Runner → BHIV Core (with instruction)
        """
        try:
            # Step 1: Prompt Runner (structured instruction)
            instruction = self._call_prompt_runner(prompt)
            
            # Step 2: BHIV Core (execution authority) - Core handles blueprint internally
            core_output = self._call_bhiv_core_with_instruction(instruction, product, trace_id)
            
            # Step 3: Extract artifact chain
            artifact_chain = self._extract_artifact_chain(core_output)
            
            return {
                "status": "success",
                "core_output": core_output,
                "artifact_chain": artifact_chain,
                "instruction": instruction
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Pipeline execution failed: {str(e)}",
                "trace_id": trace_id
            }
    
    def _call_prompt_runner(self, prompt: str) -> Dict[str, Any]:
        """Call Prompt Runner for structured instruction"""
        response = requests.post(
            f"{self.prompt_runner_url}/generate",
            json={"prompt": prompt},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    

    def _call_bhiv_core_with_instruction(self, instruction: Dict[str, Any], product: str, trace_id: str) -> Dict[str, Any]:
        """Call BHIV Core with instruction (Core handles blueprint internally)"""
        # Map TTG/TTV to creator module with product metadata
        core_request = {
            "module": "creator",  # TTG/TTV use creator module
            "intent": instruction.get("intent", "generate"),
            "user_id": f"{product}_user_{trace_id}",
            "data": {
                "product_type": product,  # "ttg" or "ttv"
                "instruction": instruction,
                "trace_id": trace_id,
                "topic": instruction.get("topic", ""),
                "tasks": instruction.get("tasks", []),
                "output_format": instruction.get("output_format", "json")
            }
        }
        
        response = requests.post(
            f"{self.bhiv_core_url}/core",
            json=core_request,
            timeout=60  # Increased timeout for full pipeline
        )
        response.raise_for_status()
        return response.json()
    
    def _extract_artifact_chain(self, core_output: Dict[str, Any]) -> Dict[str, Any]:
        """Extract artifact chain from Core output"""
        # Try multiple possible locations for execution envelope
        execution_envelope = core_output.get("execution_envelope", {})
        
        # Fallback: check if result contains envelope
        if not execution_envelope and "result" in core_output:
            result = core_output["result"]
            if isinstance(result, dict):
                execution_envelope = result.get("execution_envelope", {})
        
        return {
            "execution_id": execution_envelope.get("execution_id", "unknown"),
            "input_hash": execution_envelope.get("input_hash", "unknown"),
            "output_hash": execution_envelope.get("output_hash", "unknown"),
            "semantic_hash": execution_envelope.get("semantic_hash", "unknown"),
            "timestamp": execution_envelope.get("timestamp", datetime.now(timezone.utc).isoformat())
        }
    
    def _error_response(self, error: str, trace_id: str) -> Dict[str, Any]:
        """Standard error response"""
        return {
            "status": "error",
            "error": error,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def validate_system_boundaries(self) -> Dict[str, Any]:
        """
        Validate TANTRA system boundaries
        
        Ensures:
        - TTG cannot execute without Core
        - TTV cannot execute without Core
        - Prompt Runner is accessible
        """
        checks = {
            "prompt_runner_accessible": self._check_component(f"{self.prompt_runner_url}/health"),
            "bhiv_core_accessible": self._check_component(f"{self.bhiv_core_url}/system/health"),
            "bucket_accessible": self._check_component(f"{self.bucket_url}/bucket/stats") if self.bucket_url else False
        }
        
        all_accessible = all(checks.values())
        
        return {
            "tantra_compliant": all_accessible,
            "system_boundaries": "enforced" if all_accessible else "degraded",
            "component_checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _check_component(self, url: str) -> bool:
        """Check if component is accessible"""
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
