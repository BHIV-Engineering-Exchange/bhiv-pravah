"""
Core Reconstruction Engine
Fetches artifacts from Bucket and reconstructs full execution state
CRITICAL: Bucket is passive storage ONLY - Core performs ALL reconstruction logic
"""

import json
from typing import Dict, Any, List, Optional
from .artifact_graph_manager import ArtifactGraphManager
from ..utils.logger import setup_logger

class CoreReconstructionEngine:
    """Core-driven state reconstruction from artifact graph"""
    
    def __init__(self, artifact_graph_manager: ArtifactGraphManager, bucket_client):
        self.artifact_graph = artifact_graph_manager
        self.bucket_client = bucket_client  # Passive storage interface
        self.logger = setup_logger(__name__)
    
    def reconstruct_from_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Reconstruct complete execution state from trace_id
        
        Args:
            trace_id: Global trace identifier
            
        Returns:
            Reconstructed execution state
        """
        self.logger.info(
            f"Starting state reconstruction for trace {trace_id}",
            extra={
                "event_type": "reconstruction.started",
                "trace_id": trace_id,
                "reconstruction_mode": "trace_based",
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # Step 1: Fetch raw artifacts from Bucket (passive retrieval)
            raw_artifacts = self._fetch_artifacts_by_trace(trace_id)
            
            if not raw_artifacts:
                return {
                    "reconstruction_status": "failed",
                    "error": "no_artifacts_found",
                    "trace_id": trace_id
                }
            
            # Step 2: Core validates and orders artifacts
            ordered_chain = self._validate_and_order_artifacts(raw_artifacts)
            
            if not ordered_chain["valid"]:
                return {
                    "reconstruction_status": "failed",
                    "error": "invalid_artifact_chain",
                    "trace_id": trace_id,
                    "issues": ordered_chain["issues"]
                }
            
            # Step 3: Core reconstructs execution state
            reconstructed_state = self._reconstruct_execution_state(ordered_chain["artifacts"])
            
            # Step 4: Core validates hash integrity
            integrity_check = self._validate_reconstruction_integrity(reconstructed_state)
            
            reconstruction_result = {
                "reconstruction_status": "completed",
                "trace_id": trace_id,
                "session_id": reconstructed_state["session_id"],
                "instruction_id": reconstructed_state["instruction_id"],
                "reconstructed_state": reconstructed_state,
                "integrity_valid": integrity_check["valid"],
                "artifacts_used": len(raw_artifacts),
                "reconstruction_timestamp": reconstructed_state["completion_timestamp"]
            }
            
            self.logger.info(
                f"State reconstruction completed for trace {trace_id}",
                extra={
                    "event_type": "reconstruction.completed",
                    "trace_id": trace_id,
                    "reconstruction_status": "completed",
                    "integrity_valid": integrity_check["valid"],
                    "artifacts_used": len(raw_artifacts),
                    "telemetry_target": "insightflow"
                }
            )
            
            return reconstruction_result
            
        except Exception as e:
            error_result = {
                "reconstruction_status": "failed",
                "error": "reconstruction_exception",
                "trace_id": trace_id,
                "message": str(e),
                "error_type": type(e).__name__
            }
            
            self.logger.error(
                f"State reconstruction failed for trace {trace_id}: {e}",
                extra={
                    "event_type": "reconstruction.failed",
                    "trace_id": trace_id,
                    "error": str(e),
                    "telemetry_target": "insightflow"
                }
            )
            
            return error_result
    
    def reconstruct_from_session(self, session_id: str) -> Dict[str, Any]:
        """
        Reconstruct complete session state from multiple instruction chains
        
        Args:
            session_id: Session identifier
            
        Returns:
            Reconstructed session state with all instruction chains
        """
        self.logger.info(
            f"Starting session reconstruction for session {session_id}",
            extra={
                "event_type": "reconstruction.session_started",
                "session_id": session_id,
                "reconstruction_mode": "session_based",
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # Step 1: Fetch all artifacts for session (passive retrieval)
            session_artifacts = self._fetch_artifacts_by_session(session_id)
            
            if not session_artifacts:
                return {
                    "reconstruction_status": "failed",
                    "error": "no_session_artifacts_found",
                    "session_id": session_id
                }
            
            # Step 2: Core groups artifacts by trace_id
            trace_groups = self._group_artifacts_by_trace(session_artifacts)
            
            # Step 3: Core reconstructs each instruction chain
            reconstructed_chains = {}
            for trace_id, artifacts in trace_groups.items():
                chain_reconstruction = self.reconstruct_from_trace(trace_id)
                reconstructed_chains[trace_id] = chain_reconstruction
            
            # Step 4: Core orders chains by instruction sequence
            ordered_session = self._order_instruction_chains(reconstructed_chains, session_artifacts)
            
            session_result = {
                "reconstruction_status": "completed",
                "session_id": session_id,
                "instruction_chains": ordered_session["chains"],
                "chain_count": len(reconstructed_chains),
                "session_integrity": ordered_session["integrity"],
                "reconstruction_timestamp": ordered_session["completion_timestamp"]
            }
            
            self.logger.info(
                f"Session reconstruction completed for session {session_id}",
                extra={
                    "event_type": "reconstruction.session_completed",
                    "session_id": session_id,
                    "chain_count": len(reconstructed_chains),
                    "session_integrity": ordered_session["integrity"],
                    "telemetry_target": "insightflow"
                }
            )
            
            return session_result
            
        except Exception as e:
            return {
                "reconstruction_status": "failed",
                "error": "session_reconstruction_exception",
                "session_id": session_id,
                "message": str(e)
            }
    
    def reconstruct_from_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """
        Reconstruct state starting from any artifact in chain
        
        Args:
            artifact_id: Any artifact ID in the chain
            
        Returns:
            Reconstructed state from complete chain
        """
        try:
            # Step 1: Fetch starting artifact (passive retrieval)
            starting_artifact = self._fetch_artifact_by_id(artifact_id)
            
            if not starting_artifact:
                return {
                    "reconstruction_status": "failed",
                    "error": "artifact_not_found",
                    "artifact_id": artifact_id
                }
            
            # Step 2: Core determines trace_id and reconstructs full chain
            trace_id = starting_artifact["trace_id"]
            return self.reconstruct_from_trace(trace_id)
            
        except Exception as e:
            return {
                "reconstruction_status": "failed",
                "error": "artifact_reconstruction_exception",
                "artifact_id": artifact_id,
                "message": str(e)
            }
    
    def _fetch_artifacts_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Fetch raw artifacts from Bucket by trace_id (passive retrieval)"""
        try:
            # Bucket provides ONLY raw artifact retrieval - no transformation
            return self.bucket_client.get_artifacts_by_trace(trace_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch artifacts for trace {trace_id}: {e}")
            return []
    
    def _fetch_artifacts_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch raw artifacts from Bucket by session_id (passive retrieval)"""
        try:
            return self.bucket_client.get_artifacts_by_session(session_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch artifacts for session {session_id}: {e}")
            return []
    
    def _fetch_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single artifact from Bucket by ID (passive retrieval)"""
        try:
            return self.bucket_client.get_artifact_by_id(artifact_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch artifact {artifact_id}: {e}")
            return None
    
    def _validate_and_order_artifacts(self, raw_artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Core validates and orders artifacts into proper chain sequence"""
        artifacts_by_type = {}
        issues = []
        
        # Group by artifact type
        for artifact in raw_artifacts:
            artifact_type = artifact.get("artifact_type")
            if artifact_type:
                artifacts_by_type[artifact_type] = artifact
        
        # Validate required types
        required_types = ["instruction", "blueprint", "execution", "result"]
        for required_type in required_types:
            if required_type not in artifacts_by_type:
                issues.append(f"Missing required artifact type: {required_type}")
        
        # Validate chain linking
        if len(issues) == 0:
            linking_issues = self._validate_chain_linking(artifacts_by_type)
            issues.extend(linking_issues)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "artifacts": artifacts_by_type
        }
    
    def _validate_chain_linking(self, artifacts_by_type: Dict[str, Dict[str, Any]]) -> List[str]:
        """Validate artifact chain linking integrity"""
        issues = []
        
        # Check instruction → blueprint link
        if "instruction" in artifacts_by_type and "blueprint" in artifacts_by_type:
            instruction = artifacts_by_type["instruction"]
            blueprint = artifacts_by_type["blueprint"]
            if blueprint.get("input_ref") != instruction.get("artifact_id"):
                issues.append("Blueprint input_ref does not link to instruction artifact_id")
        
        # Check blueprint → execution link
        if "blueprint" in artifacts_by_type and "execution" in artifacts_by_type:
            blueprint = artifacts_by_type["blueprint"]
            execution = artifacts_by_type["execution"]
            if execution.get("blueprint_ref") != blueprint.get("artifact_id"):
                issues.append("Execution blueprint_ref does not link to blueprint artifact_id")
        
        # Check execution → result link
        if "execution" in artifacts_by_type and "result" in artifacts_by_type:
            execution = artifacts_by_type["execution"]
            result = artifacts_by_type["result"]
            if result.get("execution_ref") != execution.get("artifact_id"):
                issues.append("Result execution_ref does not link to execution artifact_id")
        
        return issues
    
    def _reconstruct_execution_state(self, artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Core reconstructs complete execution state from ordered artifacts"""
        instruction = artifacts["instruction"]
        blueprint = artifacts["blueprint"]
        execution = artifacts["execution"]
        result = artifacts["result"]
        
        # Reconstruct complete state
        reconstructed_state = {
            "session_id": instruction["session_id"],
            "trace_id": instruction["trace_id"],
            "instruction_id": instruction["instruction_id"],
            "original_instruction": instruction["payload"],
            "execution_plan": blueprint["payload"]["execution_plan"],
            "routing_decision": blueprint["payload"]["routing_decision"],
            "execution_envelope": execution["payload"]["execution_envelope"],
            "runtime_state": execution["payload"]["runtime_state"],
            "final_result": result["payload"]["result"],
            "execution_status": result["payload"]["status"],
            "completion_timestamp": result["timestamp"],
            "artifact_chain": {
                "instruction_id": instruction["artifact_id"],
                "blueprint_id": blueprint["artifact_id"],
                "execution_id": execution["artifact_id"],
                "result_id": result["artifact_id"]
            }
        }
        
        return reconstructed_state
    
    def _validate_reconstruction_integrity(self, reconstructed_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate integrity of reconstructed state"""
        issues = []
        
        # Check required fields
        required_fields = ["session_id", "trace_id", "instruction_id", "original_instruction", "final_result"]
        for field in required_fields:
            if field not in reconstructed_state:
                issues.append(f"Missing required field in reconstructed state: {field}")
        
        # Check artifact chain completeness
        artifact_chain = reconstructed_state.get("artifact_chain", {})
        required_artifacts = ["instruction_id", "blueprint_id", "execution_id", "result_id"]
        for artifact in required_artifacts:
            if artifact not in artifact_chain:
                issues.append(f"Missing artifact in chain: {artifact}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _group_artifacts_by_trace(self, session_artifacts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group session artifacts by trace_id"""
        trace_groups = {}
        
        for artifact in session_artifacts:
            trace_id = artifact.get("trace_id")
            if trace_id:
                if trace_id not in trace_groups:
                    trace_groups[trace_id] = []
                trace_groups[trace_id].append(artifact)
        
        return trace_groups
    
    def _order_instruction_chains(self, reconstructed_chains: Dict[str, Dict[str, Any]], session_artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Order instruction chains within session using prev_hash"""
        # Find instruction artifacts and their prev_hash relationships
        instruction_artifacts = [a for a in session_artifacts if a.get("artifact_type") == "instruction"]
        
        # Build ordering based on prev_hash
        ordered_chains = []
        chain_map = {chain["trace_id"]: chain for chain in reconstructed_chains.values()}
        
        # Simple ordering by timestamp for now (can be enhanced with prev_hash logic)
        sorted_instructions = sorted(instruction_artifacts, key=lambda x: x.get("timestamp", ""))
        
        for instruction in sorted_instructions:
            trace_id = instruction["trace_id"]
            if trace_id in chain_map:
                ordered_chains.append(chain_map[trace_id])
        
        return {
            "chains": ordered_chains,
            "integrity": len(ordered_chains) == len(reconstructed_chains),
            "completion_timestamp": datetime.now().isoformat()
        }