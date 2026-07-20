"""
Bucket Read Contract
Interface for passive artifact retrieval - NO transformation logic in Bucket
Bucket provides ONLY raw artifact storage and retrieval
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from ..utils.logger import setup_logger

class BucketReadContract(ABC):
    """Abstract contract for Bucket read operations - passive storage only"""
    
    @abstractmethod
    def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get single artifact by ID - raw retrieval only
        
        Args:
            artifact_id: Unique artifact identifier
            
        Returns:
            Raw artifact data or None if not found
        """
        pass
    
    @abstractmethod
    def get_artifacts_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get all artifacts for a trace - raw retrieval only
        
        Args:
            trace_id: Global trace identifier
            
        Returns:
            List of raw artifacts for the trace
        """
        pass
    
    @abstractmethod
    def get_artifacts_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all artifacts for a session - raw retrieval only
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of raw artifacts for the session
        """
        pass
    
    @abstractmethod
    def get_full_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get complete artifact chain for trace - raw artifacts only
        
        Args:
            trace_id: Global trace identifier
            
        Returns:
            Raw artifacts in storage order (NO ordering logic in Bucket)
        """
        pass

class BucketClient(BucketReadContract):
    """
    Bucket client implementation - passive storage interface
    CRITICAL: NO transformation or reconstruction logic here
    """
    
    def __init__(self, memory):
        self.memory = memory
        self.logger = setup_logger(__name__)
    
    def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Raw artifact retrieval by ID"""
        try:
            context_data = self.memory.get_context(f"artifact_{artifact_id}")
            
            if context_data and "context" in context_data:
                artifact = context_data["context"]
                
                self.logger.debug(
                    f"Artifact retrieved from Bucket: {artifact_id}",
                    extra={
                        "event_type": "bucket.artifact_retrieved",
                        "artifact_id": artifact_id,
                        "artifact_type": artifact.get("artifact_type"),
                        "telemetry_target": "insightflow"
                    }
                )
                
                return artifact
            
            return None
            
        except Exception as e:
            self.logger.error(f"Bucket retrieval failed for artifact {artifact_id}: {e}")
            return None
    
    def get_artifacts_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Raw artifact retrieval by trace_id"""
        try:
            # Search through memory for artifacts with matching trace_id
            artifacts = []
            
            # This is a simplified implementation - in production, Bucket would have proper indexing
            # For now, we'll search through stored contexts
            all_contexts = self._get_all_artifact_contexts()
            
            for context_data in all_contexts:
                if context_data and "context" in context_data:
                    artifact = context_data["context"]
                    if artifact.get("trace_id") == trace_id:
                        artifacts.append(artifact)
            
            self.logger.debug(
                f"Retrieved {len(artifacts)} artifacts for trace {trace_id}",
                extra={
                    "event_type": "bucket.trace_artifacts_retrieved",
                    "trace_id": trace_id,
                    "artifact_count": len(artifacts),
                    "telemetry_target": "insightflow"
                }
            )
            
            return artifacts
            
        except Exception as e:
            self.logger.error(f"Bucket retrieval failed for trace {trace_id}: {e}")
            return []
    
    def get_artifacts_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Raw artifact retrieval by session_id"""
        try:
            artifacts = []
            all_contexts = self._get_all_artifact_contexts()
            
            for context_data in all_contexts:
                if context_data and "context" in context_data:
                    artifact = context_data["context"]
                    if artifact.get("session_id") == session_id:
                        artifacts.append(artifact)
            
            self.logger.debug(
                f"Retrieved {len(artifacts)} artifacts for session {session_id}",
                extra={
                    "event_type": "bucket.session_artifacts_retrieved",
                    "session_id": session_id,
                    "artifact_count": len(artifacts),
                    "telemetry_target": "insightflow"
                }
            )
            
            return artifacts
            
        except Exception as e:
            self.logger.error(f"Bucket retrieval failed for session {session_id}: {e}")
            return []
    
    def get_full_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get complete artifact chain - raw artifacts only
        NO ordering or transformation logic in Bucket
        """
        return self.get_artifacts_by_trace(trace_id)
    
    def _get_all_artifact_contexts(self) -> List[Dict[str, Any]]:
        """
        Get all artifact contexts from memory
        This is a simplified implementation for the prototype
        """
        try:
            # In a real implementation, Bucket would have proper indexing
            # For now, we'll use a simple approach
            contexts = []
            
            # This would be replaced with proper Bucket indexing in production
            # For prototype, we'll search through memory adapter
            if hasattr(self.memory, 'get_all_contexts'):
                all_contexts = self.memory.get_all_contexts()
                for context in all_contexts:
                    metadata = context.get("metadata", {})
                    if metadata.get("type") == "artifact_graph":
                        contexts.append(context)
            
            return contexts
            
        except Exception as e:
            self.logger.error(f"Failed to get all artifact contexts: {e}")
            return []
    
    def store_artifact(self, artifact: Dict[str, Any]) -> bool:
        """
        Store artifact in Bucket - passive storage only
        NO validation or transformation logic here
        """
        try:
            artifact_id = artifact.get("artifact_id")
            if not artifact_id:
                return False
            
            self.memory.store_context(
                user_id=f"artifact_{artifact_id}",
                context=artifact,
                metadata={
                    "type": "artifact_graph",
                    "artifact_type": artifact.get("artifact_type"),
                    "trace_id": artifact.get("trace_id"),
                    "session_id": artifact.get("session_id")
                }
            )
            
            self.logger.debug(
                f"Artifact stored in Bucket: {artifact_id}",
                extra={
                    "event_type": "bucket.artifact_stored",
                    "artifact_id": artifact_id,
                    "artifact_type": artifact.get("artifact_type"),
                    "telemetry_target": "insightflow"
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Bucket storage failed for artifact: {e}")
            return False