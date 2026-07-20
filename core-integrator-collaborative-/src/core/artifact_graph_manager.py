"""
Artifact Graph Manager
Manages 4-artifact chain linking for sovereign memory system: instruction → blueprint → execution → result
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from ..utils.logger import setup_logger

class ArtifactGraphManager:
    """Manages artifact graph for deterministic state reconstruction"""
    
    def __init__(self, memory):
        self.memory = memory
        self.logger = setup_logger(__name__)
        self.active_sessions = {}  # session_id -> session_context
        self.artifact_chains = {}  # trace_id -> artifact_chain
    
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{uuid.uuid4().hex[:16]}"
    
    def generate_artifact_id(self, artifact_type: str) -> str:
        """Generate typed artifact ID"""
        return f"artifact_{artifact_type}_{uuid.uuid4().hex[:16]}"
    
    def compute_artifact_hash(self, payload: Dict[str, Any]) -> str:
        """Compute deterministic hash of artifact payload"""
        normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized_payload.encode('utf-8')).hexdigest()
    
    def start_artifact_chain(
        self,
        instruction_id: str,
        trace_id: str,
        session_id: Optional[str] = None,
        prev_instruction_hash: Optional[str] = None
    ) -> str:
        """
        Start new artifact chain with instruction artifact
        
        Args:
            instruction_id: Original instruction identifier
            trace_id: Global trace identifier
            session_id: Session identifier (generated if None)
            prev_instruction_hash: Previous instruction in session
            
        Returns:
            session_id for chain tracking
        """
        if not session_id:
            session_id = self.generate_session_id()
        
        # Initialize chain tracking
        self.artifact_chains[trace_id] = {
            "session_id": session_id,
            "instruction_id": instruction_id,
            "artifacts": {},
            "chain_status": "started",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info(
            f"Artifact chain started for trace {trace_id}",
            extra={
                "event_type": "artifact_graph.chain_started",
                "trace_id": trace_id,
                "session_id": session_id,
                "instruction_id": instruction_id,
                "telemetry_target": "insightflow"
            }
        )
        
        return session_id
    
    def create_instruction_artifact(
        self,
        instruction_id: str,
        trace_id: str,
        session_id: str,
        payload: Dict[str, Any],
        prev_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create instruction artifact (A1 in chain)
        
        Returns:
            Complete instruction artifact
        """
        artifact_id = self.generate_artifact_id("instruction")
        artifact_hash = self.compute_artifact_hash(payload)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        instruction_artifact = {
            "artifact_id": artifact_id,
            "artifact_type": "instruction",
            "trace_id": trace_id,
            "session_id": session_id,
            "instruction_id": instruction_id,
            "payload": payload,
            "artifact_hash": artifact_hash,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
            "schema_version": "3.0.0"
        }
        
        # Store and track
        self._store_artifact(instruction_artifact)
        self._update_chain_tracking(trace_id, "instruction", instruction_artifact)
        
        self.logger.info(
            "Instruction artifact created",
            extra={
                "event_type": "artifact_graph.instruction_created",
                "artifact_id": artifact_id,
                "trace_id": trace_id,
                "session_id": session_id,
                "artifact_hash": artifact_hash,
                "telemetry_target": "insightflow"
            }
        )
        
        return instruction_artifact
    
    def create_blueprint_artifact(
        self,
        instruction_artifact: Dict[str, Any],
        routing_decision: Dict[str, Any],
        execution_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create blueprint artifact (A2 in chain) - linked to instruction
        
        Returns:
            Complete blueprint artifact
        """
        artifact_id = self.generate_artifact_id("blueprint")
        trace_id = instruction_artifact["trace_id"]
        session_id = instruction_artifact["session_id"]
        
        payload = {
            "routing_decision": routing_decision,
            "execution_plan": execution_plan,
            "derived_from": instruction_artifact["instruction_id"]
        }
        
        artifact_hash = self.compute_artifact_hash(payload)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        blueprint_artifact = {
            "artifact_id": artifact_id,
            "artifact_type": "blueprint",
            "trace_id": trace_id,
            "session_id": session_id,
            "instruction_id": instruction_artifact["instruction_id"],
            "input_ref": instruction_artifact["artifact_id"],  # Chain linking
            "payload": payload,
            "artifact_hash": artifact_hash,
            "timestamp": timestamp,
            "schema_version": "3.0.0"
        }
        
        # Store and track
        self._store_artifact(blueprint_artifact)
        self._update_chain_tracking(trace_id, "blueprint", blueprint_artifact)
        
        self.logger.info(
            "Blueprint artifact created",
            extra={
                "event_type": "artifact_graph.blueprint_created",
                "artifact_id": artifact_id,
                "trace_id": trace_id,
                "input_ref": instruction_artifact["artifact_id"],
                "artifact_hash": artifact_hash,
                "telemetry_target": "insightflow"
            }
        )
        
        return blueprint_artifact
    
    def create_execution_artifact(
        self,
        blueprint_artifact: Dict[str, Any],
        execution_id: str,
        execution_envelope: Dict[str, Any],
        runtime_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create execution artifact (A3 in chain) - linked to blueprint
        
        Returns:
            Complete execution artifact
        """
        artifact_id = self.generate_artifact_id("execution")
        trace_id = blueprint_artifact["trace_id"]
        session_id = blueprint_artifact["session_id"]
        
        payload = {
            "execution_envelope": execution_envelope,
            "runtime_state": runtime_state,
            "blueprint_hash": blueprint_artifact["artifact_hash"]
        }
        
        artifact_hash = self.compute_artifact_hash(payload)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        execution_artifact = {
            "artifact_id": artifact_id,
            "artifact_type": "execution",
            "trace_id": trace_id,
            "session_id": session_id,
            "instruction_id": blueprint_artifact["instruction_id"],
            "blueprint_ref": blueprint_artifact["artifact_id"],  # Chain linking
            "execution_id": execution_id,
            "payload": payload,
            "artifact_hash": artifact_hash,
            "timestamp": timestamp,
            "schema_version": "3.0.0"
        }
        
        # Store and track
        self._store_artifact(execution_artifact)
        self._update_chain_tracking(trace_id, "execution", execution_artifact)
        
        self.logger.info(
            "Execution artifact created",
            extra={
                "event_type": "artifact_graph.execution_created",
                "artifact_id": artifact_id,
                "trace_id": trace_id,
                "execution_id": execution_id,
                "blueprint_ref": blueprint_artifact["artifact_id"],
                "artifact_hash": artifact_hash,
                "telemetry_target": "insightflow"
            }
        )
        
        return execution_artifact
    
    def create_result_artifact(
        self,
        execution_artifact: Dict[str, Any],
        result_data: Dict[str, Any],
        status: str,
        output_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create result artifact (A4 in chain) - linked to execution
        
        Returns:
            Complete result artifact
        """
        artifact_id = self.generate_artifact_id("result")
        trace_id = execution_artifact["trace_id"]
        session_id = execution_artifact["session_id"]
        
        payload = {
            "status": status,
            "result": result_data,
            "output_metadata": output_metadata,
            "execution_hash": execution_artifact["artifact_hash"]
        }
        
        artifact_hash = self.compute_artifact_hash(payload)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        result_artifact = {
            "artifact_id": artifact_id,
            "artifact_type": "result",
            "trace_id": trace_id,
            "session_id": session_id,
            "instruction_id": execution_artifact["instruction_id"],
            "execution_ref": execution_artifact["artifact_id"],  # Chain linking
            "payload": payload,
            "artifact_hash": artifact_hash,
            "timestamp": timestamp,
            "schema_version": "3.0.0"
        }
        
        # Store and track
        self._store_artifact(result_artifact)
        self._update_chain_tracking(trace_id, "result", result_artifact)
        
        # Mark chain as complete
        self.artifact_chains[trace_id]["chain_status"] = "complete"
        
        self.logger.info(
            "Result artifact created - chain complete",
            extra={
                "event_type": "artifact_graph.result_created",
                "artifact_id": artifact_id,
                "trace_id": trace_id,
                "execution_ref": execution_artifact["artifact_id"],
                "artifact_hash": artifact_hash,
                "chain_status": "complete",
                "telemetry_target": "insightflow"
            }
        )
        
        return result_artifact
    
    def get_artifact_chain(self, trace_id: str) -> Dict[str, Any]:
        """
        Get complete artifact chain for trace
        
        Returns:
            Complete chain: instruction → blueprint → execution → result
        """
        if trace_id not in self.artifact_chains:
            return {
                "trace_id": trace_id,
                "chain_status": "not_found",
                "artifacts": {}
            }
        
        chain_data = self.artifact_chains[trace_id]
        
        return {
            "trace_id": trace_id,
            "session_id": chain_data["session_id"],
            "instruction_id": chain_data["instruction_id"],
            "chain_status": chain_data["chain_status"],
            "artifacts": chain_data["artifacts"],
            "chain_sequence": ["instruction", "blueprint", "execution", "result"],
            "created_at": chain_data["created_at"]
        }
    
    def validate_chain_integrity(self, trace_id: str) -> Dict[str, Any]:
        """
        Validate artifact chain integrity
        
        Returns:
            Validation result with any issues
        """
        chain = self.get_artifact_chain(trace_id)
        
        if chain["chain_status"] == "not_found":
            return {
                "valid": False,
                "issues": ["Chain not found"],
                "trace_id": trace_id
            }
        
        issues = []
        artifacts = chain["artifacts"]
        
        # Check all 4 artifact types present
        required_types = ["instruction", "blueprint", "execution", "result"]
        for artifact_type in required_types:
            if artifact_type not in artifacts:
                issues.append(f"Missing artifact type: {artifact_type}")
        
        # Validate chain linking
        if "instruction" in artifacts and "blueprint" in artifacts:
            blueprint = artifacts["blueprint"]
            instruction = artifacts["instruction"]
            if blueprint.get("input_ref") != instruction.get("artifact_id"):
                issues.append("Blueprint input_ref does not link to instruction")
        
        if "blueprint" in artifacts and "execution" in artifacts:
            execution = artifacts["execution"]
            blueprint = artifacts["blueprint"]
            if execution.get("blueprint_ref") != blueprint.get("artifact_id"):
                issues.append("Execution blueprint_ref does not link to blueprint")
        
        if "execution" in artifacts and "result" in artifacts:
            result = artifacts["result"]
            execution = artifacts["execution"]
            if result.get("execution_ref") != execution.get("artifact_id"):
                issues.append("Result execution_ref does not link to execution")
        
        # Validate hash integrity
        for artifact_type, artifact in artifacts.items():
            expected_hash = self.compute_artifact_hash(artifact["payload"])
            if artifact["artifact_hash"] != expected_hash:
                issues.append(f"Hash mismatch for {artifact_type} artifact")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "trace_id": trace_id,
            "chain_complete": len(artifacts) == 4,
            "chain_linked": len(issues) == 0
        }
    
    def _store_artifact(self, artifact: Dict[str, Any]):
        """Store artifact in memory system"""
        try:
            self.memory.store_context(
                user_id=f"artifact_{artifact['artifact_id']}",
                context=artifact,
                metadata={
                    "type": "artifact_graph",
                    "artifact_type": artifact["artifact_type"],
                    "trace_id": artifact["trace_id"],
                    "session_id": artifact["session_id"]
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to store artifact {artifact['artifact_id']}: {e}")
    
    def _update_chain_tracking(self, trace_id: str, artifact_type: str, artifact: Dict[str, Any]):
        """Update chain tracking with new artifact"""
        if trace_id in self.artifact_chains:
            self.artifact_chains[trace_id]["artifacts"][artifact_type] = artifact