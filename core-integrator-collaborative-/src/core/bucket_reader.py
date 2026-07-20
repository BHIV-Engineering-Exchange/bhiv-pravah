"""
Bucket Reader
Provides queryable access to stored artifacts and lineage information
"""

from typing import Dict, Any, List, Optional, Tuple
from .lineage_manager import LineageManager
from ..utils.logger import setup_logger

class BucketReader:
    """Provides read access to the Bucket artifact storage system"""
    
    def __init__(self, lineage_manager: LineageManager):
        self.lineage_manager = lineage_manager
        self.logger = setup_logger(__name__)
    
    def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve artifact by its unique ID
        
        Args:
            artifact_id: Unique artifact identifier
            
        Returns:
            Artifact data or None if not found
        """
        try:
            artifact = self.lineage_manager._get_artifact_by_id(artifact_id)
            
            if artifact:
                self.logger.debug(
                    f"Artifact retrieved: {artifact_id}",
                    extra={
                        "event_type": "bucket.artifact_retrieved",
                        "artifact_id": artifact_id,
                        "artifact_type": artifact.get("artifact_type"),
                        "telemetry_target": "insightflow"
                    }
                )
            
            return artifact
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve artifact {artifact_id}: {e}")
            return None
    
    def get_artifacts_by_instruction(self, instruction_id: str) -> List[Dict[str, Any]]:
        """
        Get all artifacts associated with an instruction
        
        Args:
            instruction_id: Creator Core instruction ID
            
        Returns:
            List of artifacts for the instruction
        """
        try:
            lineage = self.lineage_manager.get_instruction_lineage(instruction_id)
            
            if lineage["status"] == "not_found":
                return []
            
            artifacts = lineage["artifacts"]
            
            self.logger.debug(
                f"Retrieved {len(artifacts)} artifacts for instruction {instruction_id}",
                extra={
                    "event_type": "bucket.instruction_artifacts_retrieved",
                    "instruction_id": instruction_id,
                    "artifact_count": len(artifacts),
                    "telemetry_target": "insightflow"
                }
            )
            
            return artifacts
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve artifacts for instruction {instruction_id}: {e}")
            return []
    
    def get_artifacts_by_execution(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Get all artifacts for a specific execution
        
        Args:
            execution_id: Execution ID from routing engine
            
        Returns:
            List of artifacts for the execution
        """
        try:
            artifacts = self.lineage_manager.get_execution_artifacts(execution_id)
            
            self.logger.debug(
                f"Retrieved {len(artifacts)} artifacts for execution {execution_id}",
                extra={
                    "event_type": "bucket.execution_artifacts_retrieved",
                    "execution_id": execution_id,
                    "artifact_count": len(artifacts),
                    "telemetry_target": "insightflow"
                }
            )
            
            return artifacts
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve artifacts for execution {execution_id}: {e}")
            return []
    
    def get_lineage_chain(self, instruction_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete lineage chain for an instruction
        
        Args:
            instruction_id: Creator Core instruction ID
            
        Returns:
            Ordered lineage chain from root to leaf
        """
        try:
            lineage = self.lineage_manager.get_instruction_lineage(instruction_id)
            
            if lineage["status"] == "not_found":
                return []
            
            lineage_chain = lineage["lineage_chain"]
            
            self.logger.debug(
                f"Retrieved lineage chain for instruction {instruction_id}",
                extra={
                    "event_type": "bucket.lineage_chain_retrieved",
                    "instruction_id": instruction_id,
                    "chain_length": len(lineage_chain),
                    "telemetry_target": "insightflow"
                }
            )
            
            return lineage_chain
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve lineage chain for instruction {instruction_id}: {e}")
            return []
    
    def get_artifacts_by_type(self, artifact_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get artifacts by type across all instructions
        
        Args:
            artifact_type: Type of artifact (blueprint, execution, result)
            limit: Maximum number of artifacts to return
            
        Returns:
            List of artifacts of the specified type
        """
        try:
            artifacts = []
            
            # Search through all instructions in lineage store
            for instruction_id in self.lineage_manager.lineage_store.keys():
                instruction_artifacts = self.get_artifacts_by_instruction(instruction_id)
                
                for artifact in instruction_artifacts:
                    if artifact["artifact_type"] == artifact_type:
                        artifacts.append(artifact)
                        
                        if limit and len(artifacts) >= limit:
                            break
                
                if limit and len(artifacts) >= limit:
                    break
            
            # Sort by timestamp (newest first)
            artifacts.sort(key=lambda x: x["timestamp"], reverse=True)
            
            self.logger.debug(
                f"Retrieved {len(artifacts)} artifacts of type {artifact_type}",
                extra={
                    "event_type": "bucket.artifacts_by_type_retrieved",
                    "artifact_type": artifact_type,
                    "artifact_count": len(artifacts),
                    "telemetry_target": "insightflow"
                }
            )
            
            return artifacts
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve artifacts by type {artifact_type}: {e}")
            return []
    
    def get_artifacts_by_hash(self, artifact_hash: str) -> Optional[Dict[str, Any]]:
        """
        Find artifact by its hash
        
        Args:
            artifact_hash: SHA256 hash of artifact payload
            
        Returns:
            Artifact with matching hash or None
        """
        try:
            artifact = self.lineage_manager._find_artifact_by_hash(artifact_hash)
            
            if artifact:
                self.logger.debug(
                    f"Artifact found by hash: {artifact_hash[:16]}...",
                    extra={
                        "event_type": "bucket.artifact_retrieved_by_hash",
                        "artifact_hash": artifact_hash,
                        "artifact_id": artifact["artifact_id"],
                        "telemetry_target": "insightflow"
                    }
                )
            
            return artifact
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve artifact by hash {artifact_hash}: {e}")
            return None
    
    def search_artifacts(
        self,
        instruction_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        artifact_type: Optional[str] = None,
        source_module_id: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> List[Dict[str, Any]]:
        """
        Search artifacts with multiple filter criteria
        
        Args:
            instruction_id: Filter by instruction ID
            execution_id: Filter by execution ID
            artifact_type: Filter by artifact type
            source_module_id: Filter by source module
            limit: Maximum results to return
            
        Returns:
            List of matching artifacts
        """
        try:
            results = []
            
            # If instruction_id is specified, start there
            if instruction_id:
                artifacts = self.get_artifacts_by_instruction(instruction_id)
            else:
                # Search all instructions
                artifacts = []
                for inst_id in self.lineage_manager.lineage_store.keys():
                    artifacts.extend(self.get_artifacts_by_instruction(inst_id))
            
            # Apply filters
            for artifact in artifacts:
                # Filter by execution_id
                if execution_id and artifact.get("execution_id") != execution_id:
                    continue
                
                # Filter by artifact_type
                if artifact_type and artifact.get("artifact_type") != artifact_type:
                    continue
                
                # Filter by source_module_id
                if source_module_id and artifact.get("source_module_id") != source_module_id:
                    continue
                
                results.append(artifact)
                
                # Apply limit
                if limit and len(results) >= limit:
                    break
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            
            self.logger.debug(
                f"Search returned {len(results)} artifacts",
                extra={
                    "event_type": "bucket.artifacts_searched",
                    "filters": {
                        "instruction_id": instruction_id,
                        "execution_id": execution_id,
                        "artifact_type": artifact_type,
                        "source_module_id": source_module_id
                    },
                    "result_count": len(results),
                    "telemetry_target": "insightflow"
                }
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Artifact search failed: {e}")
            return []
    
    def get_bucket_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive Bucket storage statistics
        
        Returns:
            Statistics about stored artifacts and lineage
        """
        try:
            lineage_stats = self.lineage_manager.get_lineage_statistics()
            
            # Get artifact type distribution
            artifact_types = {}
            total_size_estimate = 0
            
            for instruction_id in self.lineage_manager.lineage_store.keys():
                artifacts = self.get_artifacts_by_instruction(instruction_id)
                
                for artifact in artifacts:
                    artifact_type = artifact["artifact_type"]
                    artifact_types[artifact_type] = artifact_types.get(artifact_type, 0) + 1
                    
                    # Estimate size (rough)
                    payload_size = len(str(artifact["payload"]))
                    total_size_estimate += payload_size
            
            return {
                "total_instructions": lineage_stats["total_instructions"],
                "total_artifacts": lineage_stats["total_artifacts"],
                "artifact_type_distribution": artifact_types,
                "max_lineage_depth": lineage_stats["max_lineage_depth"],
                "average_artifacts_per_instruction": lineage_stats["average_artifacts_per_instruction"],
                "estimated_storage_size_bytes": total_size_estimate,
                "storage_efficiency": {
                    "artifacts_per_instruction": lineage_stats["average_artifacts_per_instruction"],
                    "lineage_completeness": self._calculate_lineage_completeness()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get bucket statistics: {e}")
            return {}
    
    def _calculate_lineage_completeness(self) -> float:
        """
        Calculate what percentage of instructions have complete lineage chains
        
        Returns:
            Completeness ratio (0.0 to 1.0)
        """
        total_instructions = len(self.lineage_manager.lineage_store)
        
        if total_instructions == 0:
            return 0.0
        
        complete_lineages = 0
        
        for instruction_id in self.lineage_manager.lineage_store.keys():
            integrity = self.lineage_manager.validate_lineage_integrity(instruction_id)
            if integrity["valid"]:
                complete_lineages += 1
        
        return complete_lineages / total_instructions