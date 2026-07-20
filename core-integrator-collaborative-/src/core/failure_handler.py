"""
Failure Handler
Comprehensive error handling for lineage and replay system failures
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from ..utils.logger import setup_logger

class FailureType(Enum):
    """Types of system failures"""
    MISSING_ARTIFACT = "missing_artifact"
    BROKEN_LINEAGE = "broken_lineage"
    EXECUTION_MISMATCH = "execution_mismatch"
    REPLAY_FAILURE = "replay_failure"
    HASH_MISMATCH = "hash_mismatch"
    INSTRUCTION_NOT_FOUND = "instruction_not_found"
    STORAGE_ERROR = "storage_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"

class FailureHandler:
    """Handles all failure scenarios in the lineage and replay system"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def handle_missing_artifact(
        self,
        instruction_id: str,
        artifact_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle missing artifact scenario"""
        error_details = {
            "status": "error",
            "error_type": FailureType.MISSING_ARTIFACT.value,
            "instruction_id": instruction_id,
            "message": f"Required artifact of type '{artifact_type}' not found for instruction {instruction_id}",
            "missing_artifact_type": artifact_type,
            "context": context or {},
            "recovery_suggestions": [
                "Check if the instruction was executed completely",
                "Verify artifact storage system is functioning",
                "Re-execute the instruction if possible"
            ]
        }
        
        self.logger.error(
            f"Missing artifact: {artifact_type} for instruction {instruction_id}",
            extra={
                "event_type": "failure.missing_artifact",
                "instruction_id": instruction_id,
                "artifact_type": artifact_type,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_broken_lineage(
        self,
        instruction_id: str,
        lineage_issues: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle broken lineage chain scenario"""
        error_details = {
            "status": "error",
            "error_type": FailureType.BROKEN_LINEAGE.value,
            "instruction_id": instruction_id,
            "message": f"Lineage chain is broken for instruction {instruction_id}",
            "lineage_issues": lineage_issues,
            "context": context or {},
            "recovery_suggestions": [
                "Check artifact parent-child relationships",
                "Verify hash integrity of artifacts",
                "Rebuild lineage if possible"
            ]
        }
        
        self.logger.error(
            f"Broken lineage for instruction {instruction_id}: {lineage_issues}",
            extra={
                "event_type": "failure.broken_lineage",
                "instruction_id": instruction_id,
                "issues": lineage_issues,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_execution_mismatch(
        self,
        instruction_id: str,
        original_result: Dict[str, Any],
        replayed_result: Dict[str, Any],
        differences: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle execution result mismatch scenario"""
        error_details = {
            "status": "error",
            "error_type": FailureType.EXECUTION_MISMATCH.value,
            "instruction_id": instruction_id,
            "message": f"Execution results do not match for instruction {instruction_id}",
            "differences": differences,
            "original_status": original_result.get("status"),
            "replayed_status": replayed_result.get("status"),
            "context": context or {},
            "recovery_suggestions": [
                "Check for non-deterministic behavior in modules",
                "Verify input data consistency",
                "Review execution environment differences"
            ]
        }
        
        self.logger.error(
            f"Execution mismatch for instruction {instruction_id}: {len(differences)} differences found",
            extra={
                "event_type": "failure.execution_mismatch",
                "instruction_id": instruction_id,
                "difference_count": len(differences),
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_replay_failure(
        self,
        instruction_id: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle general replay failure scenario"""
        error_details = {
            "status": "error",
            "error_type": FailureType.REPLAY_FAILURE.value,
            "instruction_id": instruction_id,
            "message": f"Replay failed for instruction {instruction_id}: {str(error)}",
            "error_class": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "recovery_suggestions": [
                "Check system resources and dependencies",
                "Verify instruction and artifact integrity",
                "Review system logs for detailed error information"
            ]
        }
        
        self.logger.error(
            f"Replay failure for instruction {instruction_id}: {error}",
            extra={
                "event_type": "failure.replay_failure",
                "instruction_id": instruction_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_hash_mismatch(
        self,
        instruction_id: str,
        artifact_id: str,
        expected_hash: str,
        actual_hash: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle hash mismatch scenario"""
        error_details = {
            "status": "error",
            "error_type": FailureType.HASH_MISMATCH.value,
            "instruction_id": instruction_id,
            "artifact_id": artifact_id,
            "message": f"Hash mismatch detected for artifact {artifact_id}",
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "context": context or {},
            "recovery_suggestions": [
                "Check for data corruption",
                "Verify artifact storage integrity",
                "Re-compute hash if artifact is valid"
            ]
        }
        
        self.logger.error(
            f"Hash mismatch for artifact {artifact_id}: expected {expected_hash[:16]}..., got {actual_hash[:16]}...",
            extra={
                "event_type": "failure.hash_mismatch",
                "instruction_id": instruction_id,
                "artifact_id": artifact_id,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_instruction_not_found(
        self,
        instruction_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle instruction not found scenario"""
        error_details = {
            "status": "error",
            "error_type": FailureType.INSTRUCTION_NOT_FOUND.value,
            "instruction_id": instruction_id,
            "message": f"Instruction {instruction_id} not found in system",
            "context": context or {},
            "recovery_suggestions": [
                "Verify instruction ID is correct",
                "Check if instruction was successfully processed",
                "Review system logs for instruction processing"
            ]
        }
        
        self.logger.error(
            f"Instruction not found: {instruction_id}",
            extra={
                "event_type": "failure.instruction_not_found",
                "instruction_id": instruction_id,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_storage_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle storage system errors"""
        error_details = {
            "status": "error",
            "error_type": FailureType.STORAGE_ERROR.value,
            "operation": operation,
            "message": f"Storage operation '{operation}' failed: {str(error)}",
            "error_class": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "recovery_suggestions": [
                "Check storage system connectivity",
                "Verify storage permissions",
                "Review storage system logs"
            ]
        }
        
        self.logger.error(
            f"Storage error during {operation}: {error}",
            extra={
                "event_type": "failure.storage_error",
                "operation": operation,
                "error": str(error),
                "error_type": type(error).__name__,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_validation_error(
        self,
        validation_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle validation errors"""
        error_details = {
            "status": "error",
            "error_type": FailureType.VALIDATION_ERROR.value,
            "validation_type": validation_type,
            "message": f"Validation failed for {validation_type}: {error_message}",
            "context": context or {},
            "recovery_suggestions": [
                "Check input data format",
                "Verify schema compliance",
                "Review validation rules"
            ]
        }
        
        self.logger.error(
            f"Validation error for {validation_type}: {error_message}",
            extra={
                "event_type": "failure.validation_error",
                "validation_type": validation_type,
                "error_message": error_message,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def handle_system_error(
        self,
        component: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle general system errors"""
        error_details = {
            "status": "error",
            "error_type": FailureType.SYSTEM_ERROR.value,
            "component": component,
            "message": f"System error in {component}: {str(error)}",
            "error_class": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "recovery_suggestions": [
                "Check system resources",
                "Review component configuration",
                "Restart component if necessary"
            ]
        }
        
        self.logger.error(
            f"System error in {component}: {error}",
            extra={
                "event_type": "failure.system_error",
                "component": component,
                "error": str(error),
                "error_type": type(error).__name__,
                "telemetry_target": "insightflow"
            }
        )
        
        return error_details
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get failure statistics (would need to track failures over time)"""
        # This would typically connect to a metrics system
        return {
            "failure_types": [ft.value for ft in FailureType],
            "total_failure_types": len(FailureType),
            "recovery_available": True,
            "monitoring_active": True
        }