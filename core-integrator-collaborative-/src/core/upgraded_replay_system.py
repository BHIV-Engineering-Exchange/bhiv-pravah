"""
Upgraded Replay System
Supports 3 replay modes: from instruction, from blueprint, from execution
Includes session reconstruction and multi-step replay
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .core_reconstruction_engine import CoreReconstructionEngine
from .artifact_graph_manager import ArtifactGraphManager
from ..utils.logger import setup_logger

class UpgradedReplaySystem:
    """Enhanced replay system with multiple replay modes and session support"""
    
    def __init__(self, reconstruction_engine: CoreReconstructionEngine, artifact_graph: ArtifactGraphManager):
        self.reconstruction_engine = reconstruction_engine
        self.artifact_graph = artifact_graph
        self.logger = setup_logger(__name__)
    
    def replay_from_instruction(self, instruction_id: str) -> Dict[str, Any]:
        """
        Replay from instruction artifact (full chain replay)
        
        Args:
            instruction_id: Original instruction identifier
            
        Returns:
            Complete replay result with validation
        """
        self.logger.info(
            f"Starting instruction replay for {instruction_id}",
            extra={
                "event_type": "replay.instruction_started",
                "instruction_id": instruction_id,
                "replay_mode": "instruction_based",
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # Step 1: Find trace_id for instruction
            trace_id = self._find_trace_by_instruction(instruction_id)
            
            if not trace_id:
                return {
                    "replay_status": "failed",
                    "error": "instruction_not_found",
                    "instruction_id": instruction_id,
                    "message": f"No trace found for instruction {instruction_id}"
                }
            
            # Step 2: Reconstruct original state
            original_state = self.reconstruction_engine.reconstruct_from_trace(trace_id)
            
            if original_state["reconstruction_status"] != "completed":
                return {
                    "replay_status": "failed",
                    "error": "reconstruction_failed",
                    "instruction_id": instruction_id,
                    "reconstruction_error": original_state
                }
            
            # Step 3: Re-execute from instruction
            replay_result = self._execute_replay(
                original_state["reconstructed_state"]["original_instruction"],
                "instruction",
                original_state
            )
            
            # Step 4: Validate replay
            validation = self._validate_replay_result(original_state, replay_result)
            
            final_result = {
                "replay_status": "completed",
                "replay_mode": "instruction_based",
                "instruction_id": instruction_id,
                "trace_id": trace_id,
                "original_state": original_state,
                "replayed_result": replay_result,
                "validation": validation,
                "hash_match": validation["hash_match"],
                "determinism_score": validation["determinism_score"],
                "differences": validation["differences"]
            }
            
            self.logger.info(
                f"Instruction replay completed for {instruction_id}",
                extra={
                    "event_type": "replay.instruction_completed",
                    "instruction_id": instruction_id,
                    "hash_match": validation["hash_match"],
                    "determinism_score": validation["determinism_score"],
                    "telemetry_target": "insightflow"
                }
            )
            
            return final_result
            
        except Exception as e:
            return {
                "replay_status": "failed",
                "error": "instruction_replay_exception",
                "instruction_id": instruction_id,
                "message": str(e)
            }
    
    def replay_from_blueprint(self, blueprint_artifact_id: str) -> Dict[str, Any]:
        """
        Replay from blueprint artifact (skip instruction parsing)
        
        Args:
            blueprint_artifact_id: Blueprint artifact identifier
            
        Returns:
            Replay result starting from blueprint
        """
        self.logger.info(
            f"Starting blueprint replay for {blueprint_artifact_id}",
            extra={
                "event_type": "replay.blueprint_started",
                "blueprint_artifact_id": blueprint_artifact_id,
                "replay_mode": "blueprint_based",
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # Step 1: Reconstruct from blueprint artifact
            reconstruction = self.reconstruction_engine.reconstruct_from_artifact(blueprint_artifact_id)
            
            if reconstruction["reconstruction_status"] != "completed":
                return {
                    "replay_status": "failed",
                    "error": "blueprint_reconstruction_failed",
                    "blueprint_artifact_id": blueprint_artifact_id
                }
            
            # Step 2: Execute from blueprint (skip instruction parsing)\n            blueprint_data = reconstruction["reconstructed_state"]["execution_plan"]
            replay_result = self._execute_replay(blueprint_data, "blueprint", reconstruction)
            
            # Step 3: Validate replay
            validation = self._validate_replay_result(reconstruction, replay_result)
            
            return {
                "replay_status": "completed",
                "replay_mode": "blueprint_based",
                "blueprint_artifact_id": blueprint_artifact_id,
                "trace_id": reconstruction["trace_id"],
                "validation": validation,
                "hash_match": validation["hash_match"],
                "determinism_score": validation["determinism_score"]
            }
            
        except Exception as e:
            return {
                "replay_status": "failed",
                "error": "blueprint_replay_exception",
                "blueprint_artifact_id": blueprint_artifact_id,
                "message": str(e)
            }
    
    def replay_from_execution(self, execution_artifact_id: str) -> Dict[str, Any]:
        """
        Replay from execution artifact (validation only)
        
        Args:
            execution_artifact_id: Execution artifact identifier
            
        Returns:
            Replay validation result
        """
        self.logger.info(
            f"Starting execution replay for {execution_artifact_id}",
            extra={
                "event_type": "replay.execution_started",
                "execution_artifact_id": execution_artifact_id,
                "replay_mode": "execution_based",
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # Step 1: Reconstruct from execution artifact
            reconstruction = self.reconstruction_engine.reconstruct_from_artifact(execution_artifact_id)
            
            if reconstruction["reconstruction_status"] != "completed":
                return {
                    "replay_status": "failed",
                    "error": "execution_reconstruction_failed",
                    "execution_artifact_id": execution_artifact_id
                }
            
            # Step 2: Validate execution state consistency
            execution_validation = self._validate_execution_consistency(reconstruction)
            
            return {
                "replay_status": "completed",
                "replay_mode": "execution_based",
                "execution_artifact_id": execution_artifact_id,
                "trace_id": reconstruction["trace_id"],
                "execution_validation": execution_validation,
                "state_consistent": execution_validation["consistent"],
                "validation_score": execution_validation["score"]
            }
            
        except Exception as e:
            return {
                "replay_status": "failed",
                "error": "execution_replay_exception",
                "execution_artifact_id": execution_artifact_id,
                "message": str(e)
            }
    
    def replay_session(self, session_id: str) -> Dict[str, Any]:
        """
        Replay complete session with multiple instruction chains
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session replay results
        """
        self.logger.info(
            f"Starting session replay for {session_id}",
            extra={
                "event_type": "replay.session_started",
                "session_id": session_id,
                "replay_mode": "session_based",
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # Step 1: Reconstruct complete session
            session_reconstruction = self.reconstruction_engine.reconstruct_from_session(session_id)
            
            if session_reconstruction["reconstruction_status"] != "completed":
                return {
                    "replay_status": "failed",
                    "error": "session_reconstruction_failed",
                    "session_id": session_id
                }
            
            # Step 2: Replay each instruction chain in order
            chain_replays = {}
            successful_replays = 0
            failed_replays = 0
            
            for chain in session_reconstruction["instruction_chains"]:
                if chain["reconstruction_status"] == "completed":
                    instruction_id = chain["instruction_id"]
                    replay_result = self.replay_from_instruction(instruction_id)
                    chain_replays[instruction_id] = replay_result
                    
                    if replay_result["replay_status"] == "completed":
                        successful_replays += 1
                    else:
                        failed_replays += 1
            
            # Step 3: Validate session consistency
            session_validation = self._validate_session_consistency(chain_replays)
            
            session_result = {
                "replay_status": "completed",
                "replay_mode": "session_based",
                "session_id": session_id,
                "chain_count": len(chain_replays),
                "successful_replays": successful_replays,
                "failed_replays": failed_replays,
                "success_rate": successful_replays / len(chain_replays) if chain_replays else 0,
                "chain_replays": chain_replays,
                "session_validation": session_validation,
                "session_consistent": session_validation["consistent"]
            }
            
            self.logger.info(
                f"Session replay completed for {session_id}",
                extra={
                    "event_type": "replay.session_completed",
                    "session_id": session_id,
                    "successful_replays": successful_replays,
                    "failed_replays": failed_replays,
                    "session_consistent": session_validation["consistent"],
                    "telemetry_target": "insightflow"
                }
            )
            
            return session_result
            
        except Exception as e:
            return {
                "replay_status": "failed",
                "error": "session_replay_exception",
                "session_id": session_id,
                "message": str(e)
            }
    
    def _find_trace_by_instruction(self, instruction_id: str) -> Optional[str]:
        """Find trace_id for given instruction_id"""
        # Search through artifact chains
        for trace_id, chain_data in self.artifact_graph.artifact_chains.items():
            if chain_data["instruction_id"] == instruction_id:
                return trace_id
        return None
    
    def _execute_replay(self, replay_data: Dict[str, Any], replay_mode: str, original_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute replay based on mode and data"""
        # This would integrate with the actual execution system
        # For now, return a mock replay result
        return {
            "replay_execution_id": f"replay_{uuid.uuid4().hex[:16]}",
            "replay_mode": replay_mode,
            "replay_timestamp": datetime.now(timezone.utc).isoformat(),
            "replay_data": replay_data,
            "status": "success"
        }
    
    def _validate_replay_result(self, original_state: Dict[str, Any], replay_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate replay result against original state"""
        # Compare key aspects
        differences = []
        
        # Hash comparison (if available)
        original_hash = original_state.get("reconstructed_state", {}).get("execution_envelope", {}).get("output_hash")
        replay_hash = replay_result.get("output_hash")
        
        hash_match = original_hash == replay_hash if original_hash and replay_hash else False
        
        if not hash_match and original_hash and replay_hash:
            differences.append({
                "type": "hash_mismatch",
                "original_hash": original_hash,
                "replay_hash": replay_hash
            })
        
        # Status comparison
        original_status = original_state.get("reconstructed_state", {}).get("execution_status")
        replay_status = replay_result.get("status")
        
        status_match = original_status == replay_status
        
        if not status_match:
            differences.append({
                "type": "status_mismatch",
                "original_status": original_status,
                "replay_status": replay_status
            })
        
        # Calculate determinism score
        checks = [hash_match, status_match]
        determinism_score = sum(checks) / len(checks)
        
        return {
            "hash_match": hash_match,
            "status_match": status_match,
            "determinism_score": determinism_score,
            "differences": differences,
            "is_deterministic": determinism_score >= 0.9
        }
    
    def _validate_execution_consistency(self, reconstruction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution state consistency"""
        reconstructed_state = reconstruction.get("reconstructed_state", {})
        
        # Check state completeness
        required_fields = ["execution_envelope", "runtime_state", "final_result"]
        missing_fields = [f for f in required_fields if f not in reconstructed_state]
        
        # Check hash integrity
        execution_envelope = reconstructed_state.get("execution_envelope", {})
        hash_fields = ["input_hash", "output_hash", "semantic_hash"]
        missing_hashes = [h for h in hash_fields if h not in execution_envelope]
        
        consistent = len(missing_fields) == 0 and len(missing_hashes) == 0
        score = 1.0 if consistent else 0.5
        
        return {
            "consistent": consistent,
            "score": score,
            "missing_fields": missing_fields,
            "missing_hashes": missing_hashes
        }
    
    def _validate_session_consistency(self, chain_replays: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate consistency across session chain replays"""
        if not chain_replays:
            return {"consistent": False, "reason": "no_chains"}
        
        # Check if all chains replayed successfully
        successful_chains = [r for r in chain_replays.values() if r.get("replay_status") == "completed"]
        success_rate = len(successful_chains) / len(chain_replays)
        
        # Check determinism scores
        determinism_scores = [r.get("determinism_score", 0) for r in successful_chains]
        avg_determinism = sum(determinism_scores) / len(determinism_scores) if determinism_scores else 0
        
        consistent = success_rate >= 0.8 and avg_determinism >= 0.9
        
        return {
            "consistent": consistent,
            "success_rate": success_rate,
            "average_determinism": avg_determinism,
            "total_chains": len(chain_replays),
            "successful_chains": len(successful_chains)
        }