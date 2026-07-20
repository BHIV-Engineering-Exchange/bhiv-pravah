"""
Lineage Manager
Tracks instruction → execution → artifact relationships with BHIV global trace alignment
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from .global_trace_manager import GlobalTraceManager
from .artifact_schema_validator import ArtifactSchemaValidator
from ..utils.logger import setup_logger

class LineageManager:
    """Manages instruction lineage and artifact relationships"""
    
    def __init__(self, memory):
        self.memory = memory
        self.logger = setup_logger(__name__)
        self.lineage_store = {}  # In-memory lineage tracking
        self.trace_manager = GlobalTraceManager()
        self.schema_validator = ArtifactSchemaValidator()
    
    def generate_artifact_id(self) -> str:
        """Generate unique artifact ID"""
        return f"artifact_{uuid.uuid4().hex[:16]}"
    
    def compute_artifact_hash(self, payload: Dict[str, Any]) -> str:
        """Compute deterministic hash of artifact payload"""
        normalized_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized_payload.encode('utf-8')).hexdigest()
    
    def create_artifact(
        self,
        artifact_type: str,
        instruction_id: str,
        execution_id: str,
        source_module_id: str,
        payload: Dict[str, Any],
        parent_instruction_id: Optional[str] = None,
        parent_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a structured artifact with BHIV global trace alignment
        
        Args:
            artifact_type: Type of artifact (blueprint, execution, result)
            instruction_id: Creator Core instruction ID
            execution_id: Global execution ID
            source_module_id: Module that generated this artifact
            payload: Artifact payload data
            parent_instruction_id: Parent instruction ID for chaining
            parent_hash: Hash of parent artifact for lineage
            metadata: Additional metadata
            trace_id: Global trace ID for cross-system tracking
            
        Returns:
            Complete artifact dictionary
        """
        artifact_id = self.generate_artifact_id()
        artifact_hash = self.compute_artifact_hash(payload)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Ensure trace_id is present (BHIV requirement)
        if not trace_id:
            # Try to get from existing trace or create new one
            trace_context = None
            for tid, ctx in self.trace_manager.active_traces.items():
                if ctx["instruction_id"] == instruction_id:
                    trace_id = tid
                    trace_context = ctx
                    break
            
            if not trace_id:
                trace_ids = self.trace_manager.start_trace(instruction_id, "lineage_manager")
                trace_id = trace_ids["trace_id"]
        
        # Determine lineage depth
        lineage_depth = 0
        if parent_hash:
            parent_artifact = self._find_artifact_by_hash(parent_hash)
            if parent_artifact:
                lineage_depth = parent_artifact.get('lineage_depth', 0) + 1
        
        artifact = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "instruction_id": instruction_id,
            "parent_instruction_id": parent_instruction_id,
            "execution_id": execution_id,
            "trace_id": trace_id,  # BHIV global trace requirement
            "source_module_id": source_module_id,
            "payload": payload,
            "artifact_hash": artifact_hash,
            "parent_hash": parent_hash,
            "timestamp": timestamp,
            "lineage_depth": lineage_depth,
            "metadata": metadata or {}
        }
        
        # BHIV Schema Validation (STRICT)
        validation_result = self.schema_validator.validate_artifact(artifact)
        if not validation_result["valid"]:
            error_msg = f"Artifact schema validation failed: {validation_result['issues']}"
            self.logger.error(error_msg)
            raise ValueError(f"Schema validation failed for {artifact_type}: {validation_result['issues']}")
        
        # Store artifact (Bucket contract: append-only, immutable)
        self._store_artifact(artifact)
        
        # Update lineage tracking
        self._update_lineage_tracking(instruction_id, execution_id, artifact_id, artifact_type)
        
        self.logger.info(
            f"Artifact created: {artifact_type}",
            extra={
                "event_type": "lineage.artifact_created",
                "artifact_id": artifact_id,
                "instruction_id": instruction_id,
                "execution_id": execution_id,
                "trace_id": trace_id,  # BHIV trace linking
                "artifact_type": artifact_type,
                "artifact_hash": artifact_hash,  # BHIV trace linking
                "lineage_depth": lineage_depth,
                "telemetry_target": "insightflow"
            }
        )
        
        return artifact
    
    def get_instruction_lineage(self, instruction_id: str) -> Dict[str, Any]:
        """
        Get complete lineage for an instruction
        
        Args:
            instruction_id: Creator Core instruction ID
            
        Returns:
            Lineage information with artifacts and chain
        """
        if instruction_id not in self.lineage_store:
            return {
                "instruction_id": instruction_id,
                "execution_id": None,
                "artifacts": [],
                "lineage_chain": [],
                "status": "not_found"
            }
        
        lineage_data = self.lineage_store[instruction_id]
        
        # Get all artifacts for this instruction
        artifacts = []
        for artifact_id in lineage_data["artifacts"]:
            artifact = self._get_artifact_by_id(artifact_id)
            if artifact:
                artifacts.append(artifact)
        
        # Build lineage chain
        lineage_chain = self._build_lineage_chain(instruction_id)
        
        return {
            "instruction_id": instruction_id,
            "execution_id": lineage_data["execution_id"],
            "artifacts": artifacts,
            "lineage_chain": lineage_chain,
            "status": "found"
        }
    
    def get_execution_artifacts(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get all artifacts for a specific execution"""
        artifacts = []
        
        # Search through lineage store
        for instruction_id, lineage_data in self.lineage_store.items():
            if lineage_data["execution_id"] == execution_id:
                for artifact_id in lineage_data["artifacts"]:
                    artifact = self._get_artifact_by_id(artifact_id)
                    if artifact:
                        artifacts.append(artifact)
        
        return artifacts
    
    def validate_lineage_integrity(self, instruction_id: str) -> Dict[str, Any]:
        """
        Validate lineage integrity for an instruction
        
        Returns:
            Validation result with any issues found
        """
        lineage = self.get_instruction_lineage(instruction_id)
        
        if lineage["status"] == "not_found":
            return {
                "instruction_id": instruction_id,
                "valid": False,
                "issues": ["Instruction not found in lineage store"]
            }
        
        issues = []
        artifacts = lineage["artifacts"]
        
        # Check for required artifact types
        artifact_types = [a["artifact_type"] for a in artifacts]
        required_types = ["blueprint", "execution", "result"]
        
        for required_type in required_types:
            if required_type not in artifact_types:
                issues.append(f"Missing required artifact type: {required_type}")
        
        # Check hash integrity
        for artifact in artifacts:
            expected_hash = self.compute_artifact_hash(artifact["payload"])
            if artifact["artifact_hash"] != expected_hash:
                issues.append(f"Hash mismatch for artifact {artifact['artifact_id']}")
        
        # Check parent-child relationships
        for artifact in artifacts:
            if artifact["parent_hash"]:
                parent_found = any(
                    a["artifact_hash"] == artifact["parent_hash"] 
                    for a in artifacts
                )
                if not parent_found:
                    issues.append(f"Parent artifact not found for {artifact['artifact_id']}")
        
        return {
            "instruction_id": instruction_id,
            "valid": len(issues) == 0,
            "issues": issues,
            "artifact_count": len(artifacts),
            "lineage_depth": max([a["lineage_depth"] for a in artifacts]) if artifacts else 0
        }
    
    def _store_artifact(self, artifact: Dict[str, Any]):
        """Store artifact in memory system"""
        try:
            # Store in memory system
            self.memory.store_context(
                user_id=f"artifact_{artifact['artifact_id']}",
                context=artifact,
                metadata={
                    "type": "artifact",
                    "instruction_id": artifact["instruction_id"],
                    "execution_id": artifact["execution_id"],
                    "artifact_type": artifact["artifact_type"]
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to store artifact {artifact['artifact_id']}: {e}")
    
    def _get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve artifact by ID"""
        try:
            context_data = self.memory.get_context(f"artifact_{artifact_id}")
            return context_data.get("context") if context_data else None
        except Exception as e:
            self.logger.error(f"Failed to retrieve artifact {artifact_id}: {e}")
            return None
    
    def _find_artifact_by_hash(self, artifact_hash: str) -> Optional[Dict[str, Any]]:
        """Find artifact by hash (linear search through lineage store)"""
        for instruction_id, lineage_data in self.lineage_store.items():
            for artifact_id in lineage_data["artifacts"]:
                artifact = self._get_artifact_by_id(artifact_id)
                if artifact and artifact["artifact_hash"] == artifact_hash:
                    return artifact
        return None
    
    def _update_lineage_tracking(self, instruction_id: str, execution_id: str, artifact_id: str, artifact_type: str):
        """Update in-memory lineage tracking"""
        if instruction_id not in self.lineage_store:
            self.lineage_store[instruction_id] = {
                "execution_id": execution_id,
                "artifacts": [],
                "artifact_types": {}
            }
        
        self.lineage_store[instruction_id]["artifacts"].append(artifact_id)
        self.lineage_store[instruction_id]["artifact_types"][artifact_type] = artifact_id
    
    def _build_lineage_chain(self, instruction_id: str) -> List[Dict[str, Any]]:
        """Build complete lineage chain for instruction"""
        chain = []
        
        if instruction_id not in self.lineage_store:
            return chain
        
        lineage_data = self.lineage_store[instruction_id]
        
        # Sort artifacts by lineage depth
        artifacts = []
        for artifact_id in lineage_data["artifacts"]:
            artifact = self._get_artifact_by_id(artifact_id)
            if artifact:
                artifacts.append(artifact)
        
        artifacts.sort(key=lambda x: x["lineage_depth"])
        
        # Build chain representation
        for artifact in artifacts:
            chain_entry = {
                "artifact_id": artifact["artifact_id"],
                "artifact_type": artifact["artifact_type"],
                "artifact_hash": artifact["artifact_hash"],
                "parent_hash": artifact["parent_hash"],
                "lineage_depth": artifact["lineage_depth"],
                "timestamp": artifact["timestamp"]
            }
            chain.append(chain_entry)
        
        return chain
    
    def get_lineage_statistics(self) -> Dict[str, Any]:
        """Get overall lineage statistics"""
        total_instructions = len(self.lineage_store)
        total_artifacts = sum(len(data["artifacts"]) for data in self.lineage_store.values())
        
        artifact_type_counts = {}
        max_depth = 0
        
        for lineage_data in self.lineage_store.values():
            for artifact_id in lineage_data["artifacts"]:
                artifact = self._get_artifact_by_id(artifact_id)
                if artifact:
                    artifact_type = artifact["artifact_type"]
                    artifact_type_counts[artifact_type] = artifact_type_counts.get(artifact_type, 0) + 1
                    max_depth = max(max_depth, artifact["lineage_depth"])
        
        return {
            "total_instructions": total_instructions,
            "total_artifacts": total_artifacts,
            "artifact_type_counts": artifact_type_counts,
            "max_lineage_depth": max_depth,
            "average_artifacts_per_instruction": total_artifacts / total_instructions if total_instructions > 0 else 0
        }