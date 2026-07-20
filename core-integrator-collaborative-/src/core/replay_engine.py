"""
Replay Engine
Reconstructs and re-executes instructions deterministically from stored artifacts
"""

import json
import time
from typing import Dict, Any, Optional, List
from .lineage_manager import LineageManager
from .routing_engine import RoutingEngine
from .creator_core_parser import CreatorCoreParser
from ..utils.logger import setup_logger

class ReplayEngine:
    """Handles deterministic replay of instructions from stored artifacts"""
    
    def __init__(self, lineage_manager: LineageManager, routing_engine: RoutingEngine, memory):
        self.lineage_manager = lineage_manager
        self.routing_engine = routing_engine
        self.memory = memory
        self.logger = setup_logger(__name__)
        self.parser = CreatorCoreParser()
    
    def replay_instruction(self, instruction_id: str) -> Dict[str, Any]:
        """
        Replay an instruction deterministically
        
        Args:
            instruction_id: Creator Core instruction ID to replay
            
        Returns:
            Replay result with comparison to original execution
        """
        try:
            # Step 1: Fetch artifacts from Bucket
            lineage = self.lineage_manager.get_instruction_lineage(instruction_id)
            
            if lineage["status"] == "not_found":
                return {
                    "replay_status": "failed",
                    "error": "instruction_not_found",
                    "instruction_id": instruction_id,
                    "message": f"No artifacts found for instruction {instruction_id}"
                }
            
            # Step 2: Reconstruct original instruction
            blueprint_artifact = self._get_artifact_by_type(lineage["artifacts"], "blueprint")
            if not blueprint_artifact:
                return {
                    "replay_status": "failed",
                    "error": "missing_blueprint",
                    "instruction_id": instruction_id,
                    "message": "Blueprint artifact not found"
                }
            
            original_instruction = blueprint_artifact["payload"]["instruction"]
            original_execution_artifact = self._get_artifact_by_type(lineage["artifacts"], "execution")
            original_result_artifact = self._get_artifact_by_type(lineage["artifacts"], "result")
            
            # Step 3: Re-run execution deterministically
            self.logger.info(
                f"Starting replay for instruction {instruction_id}",
                extra={
                    "event_type": "replay.started",
                    "instruction_id": instruction_id,
                    "original_execution_id": lineage["execution_id"],
                    "telemetry_target": "insightflow"
                }
            )
            
            start_time = time.time()
            
            # Parse instruction again
            routing_decision = self.parser.parse_instruction(original_instruction)
            
            # Execute through routing engine (this will create new artifacts)
            replayed_result = self.routing_engine.execute_instruction(
                instruction=original_instruction,
                routing_decision=routing_decision,
                start_time=start_time
            )
            
            # Step 4: Compare results
            comparison_result = self._compare_execution_results(
                original_result=original_result_artifact["payload"] if original_result_artifact else {},
                replayed_result=replayed_result,
                original_execution=original_execution_artifact["payload"] if original_execution_artifact else {}
            )
            
            # Step 5: Generate replay report
            replay_report = {
                "replay_status": "completed",
                "instruction_id": instruction_id,
                "original_execution_id": lineage["execution_id"],
                "replayed_execution_id": replayed_result.get("execution_envelope", {}).get("execution_id"),
                "original_output": original_result_artifact["payload"] if original_result_artifact else {},
                "replayed_output": replayed_result,
                "hash_match": comparison_result["hash_match"],
                "determinism_score": comparison_result["determinism_score"],
                "differences": comparison_result["differences"],
                "replay_duration_ms": (time.time() - start_time) * 1000,
                "artifacts_used": len(lineage["artifacts"]),
                "lineage_chain_length": len(lineage["lineage_chain"])
            }
            
            self.logger.info(
                f"Replay completed for instruction {instruction_id}",
                extra={
                    "event_type": "replay.completed",
                    "instruction_id": instruction_id,
                    "replay_status": "completed",
                    "hash_match": comparison_result["hash_match"],
                    "determinism_score": comparison_result["determinism_score"],
                    "telemetry_target": "insightflow"
                }
            )
            
            return replay_report
            
        except Exception as e:
            error_report = {
                "replay_status": "failed",
                "error": "replay_exception",
                "instruction_id": instruction_id,
                "message": str(e),
                "error_type": type(e).__name__
            }
            
            self.logger.error(
                f"Replay failed for instruction {instruction_id}: {e}",
                extra={
                    "event_type": "replay.failed",
                    "instruction_id": instruction_id,
                    "error": str(e),
                    "telemetry_target": "insightflow"
                }
            )
            
            return error_report
    
    def batch_replay(self, instruction_ids: List[str]) -> Dict[str, Any]:
        """
        Replay multiple instructions in batch
        
        Args:
            instruction_ids: List of instruction IDs to replay
            
        Returns:
            Batch replay results
        """
        results = {}
        successful_replays = 0
        failed_replays = 0
        
        for instruction_id in instruction_ids:
            result = self.replay_instruction(instruction_id)
            results[instruction_id] = result
            
            if result["replay_status"] == "completed":
                successful_replays += 1
            else:
                failed_replays += 1
        
        return {
            "batch_replay_status": "completed",
            "total_instructions": len(instruction_ids),
            "successful_replays": successful_replays,
            "failed_replays": failed_replays,
            "success_rate": successful_replays / len(instruction_ids) if instruction_ids else 0,
            "results": results
        }
    
    def validate_replay_capability(self, instruction_id: str) -> Dict[str, Any]:
        """
        Validate if an instruction can be replayed
        
        Args:
            instruction_id: Instruction ID to validate
            
        Returns:
            Validation result
        """
        lineage = self.lineage_manager.get_instruction_lineage(instruction_id)
        
        if lineage["status"] == "not_found":
            return {
                "can_replay": False,
                "reason": "instruction_not_found",
                "instruction_id": instruction_id
            }
        
        # Check for required artifacts
        artifacts = lineage["artifacts"]
        required_types = ["blueprint", "execution", "result"]
        missing_types = []
        
        for required_type in required_types:
            if not self._get_artifact_by_type(artifacts, required_type):
                missing_types.append(required_type)
        
        # Validate lineage integrity
        integrity_check = self.lineage_manager.validate_lineage_integrity(instruction_id)
        
        can_replay = len(missing_types) == 0 and integrity_check["valid"]
        
        return {
            "can_replay": can_replay,
            "instruction_id": instruction_id,
            "missing_artifact_types": missing_types,
            "lineage_valid": integrity_check["valid"],
            "lineage_issues": integrity_check["issues"],
            "artifact_count": len(artifacts),
            "reason": "ready" if can_replay else "missing_artifacts_or_invalid_lineage"
        }
    
    def get_replay_statistics(self) -> Dict[str, Any]:
        """Get overall replay system statistics"""
        lineage_stats = self.lineage_manager.get_lineage_statistics()
        
        # Count replayable instructions
        replayable_count = 0
        total_instructions = lineage_stats["total_instructions"]
        
        for instruction_id in self.lineage_manager.lineage_store.keys():
            validation = self.validate_replay_capability(instruction_id)
            if validation["can_replay"]:
                replayable_count += 1
        
        return {
            "total_instructions": total_instructions,
            "replayable_instructions": replayable_count,
            "replay_readiness_rate": replayable_count / total_instructions if total_instructions > 0 else 0,
            "total_artifacts": lineage_stats["total_artifacts"],
            "max_lineage_depth": lineage_stats["max_lineage_depth"],
            "artifact_type_distribution": lineage_stats["artifact_type_counts"]
        }
    
    def _get_artifact_by_type(self, artifacts: List[Dict[str, Any]], artifact_type: str) -> Optional[Dict[str, Any]]:
        """Get artifact of specific type from list"""
        for artifact in artifacts:
            if artifact["artifact_type"] == artifact_type:
                return artifact
        return None
    
    def _compare_execution_results(
        self,
        original_result: Dict[str, Any],
        replayed_result: Dict[str, Any],
        original_execution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare original and replayed execution results
        
        Returns:
            Comparison analysis
        """
        # Extract result portions for comparison
        original_output = original_result.get("result", original_result)
        replayed_output = replayed_result.get("result", replayed_result)
        
        # Compare hashes
        original_hash = original_execution.get("output_hash", "")
        replayed_hash = replayed_result.get("execution_envelope", {}).get("output_hash", "")
        hash_match = original_hash == replayed_hash and original_hash != ""
        
        # Compare status
        original_status = original_result.get("status", "unknown")
        replayed_status = replayed_result.get("status", "unknown")
        status_match = original_status == replayed_status
        
        # Find differences
        differences = []
        
        if not hash_match:
            differences.append({
                "type": "hash_mismatch",
                "original_hash": original_hash,
                "replayed_hash": replayed_hash
            })
        
        if not status_match:
            differences.append({
                "type": "status_mismatch",
                "original_status": original_status,
                "replayed_status": replayed_status
            })
        
        # Calculate determinism score
        determinism_factors = [hash_match, status_match]
        determinism_score = sum(determinism_factors) / len(determinism_factors)
        
        return {
            "hash_match": hash_match,
            "status_match": status_match,
            "determinism_score": determinism_score,
            "differences": differences,
            "comparison_summary": {
                "total_checks": len(determinism_factors),
                "passed_checks": sum(determinism_factors),
                "is_deterministic": determinism_score == 1.0
            }
        }