"""InsightFlow telemetry payload generator

Produces deterministic, structured events suitable for InsightFlow ingestion and offline testing.
Enhanced with deep linking for instruction → execution → artifact traceability.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

INSIGHTFLOW_VERSION = "1.0.0"


def timestamp_iso(ts: Optional[datetime] = None) -> str:
    return (ts or datetime.now(timezone.utc)).isoformat()


def make_event(event_type: str, component: str, status: str, details: Dict[str, Any] = None,
               integration_score: Optional[float] = None, failing_components: Optional[List[str]] = None,
               timestamp: Optional[datetime] = None) -> Dict[str, Any]:
    payload = {
        "insightflow_version": INSIGHTFLOW_VERSION,
        "event_type": event_type,
        "component": component,
        "status": status,
        "details": details or {},
        "timestamp": timestamp_iso(timestamp)
    }
    if integration_score is not None:
        payload["integration_score"] = float(integration_score)
    if failing_components is not None:
        payload["failing_components"] = list(failing_components)
    return payload


def make_lineage_event(
    event_type: str,
    instruction_id: str,
    execution_id: str,
    artifact_hash: Optional[str] = None,
    component: str = "core_integrator",
    status: str = "success",
    details: Dict[str, Any] = None,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create InsightFlow event with deep linking for lineage traceability
    
    Args:
        event_type: Type of event (instruction.received, execution.started, etc.)
        instruction_id: Creator Core instruction ID
        execution_id: Execution ID from routing engine
        artifact_hash: Hash of associated artifact
        component: Component generating the event
        status: Event status
        details: Additional event details
        timestamp: Event timestamp
        
    Returns:
        InsightFlow event with lineage linking
    """
    event_details = details or {}
    
    # Add mandatory lineage fields
    event_details.update({
        "instruction_id": instruction_id,
        "execution_id": execution_id
    })
    
    # Add artifact hash if provided
    if artifact_hash:
        event_details["artifact_hash"] = artifact_hash
    
    # Add trace context for full lineage
    event_details["trace_context"] = {
        "instruction_id": instruction_id,
        "execution_id": execution_id,
        "artifact_hash": artifact_hash,
        "event_sequence": event_type
    }
    
    return make_event(
        event_type=event_type,
        component=component,
        status=status,
        details=event_details,
        timestamp=timestamp
    )


def make_artifact_graph_event(
    stage: str,
    trace_id: str,
    artifact_id: str,
    parent_artifact_id: Optional[str] = None,
    session_id: Optional[str] = None,
    instruction_id: Optional[str] = None,
    component: str = "artifact_graph",
    status: str = "success",
    details: Dict[str, Any] = None,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create InsightFlow event for artifact graph operations with full trace context
    
    Args:
        stage: Artifact stage (instruction/blueprint/execution/result)
        trace_id: Global trace identifier
        artifact_id: Current artifact identifier
        parent_artifact_id: Parent artifact identifier for linking
        session_id: Session identifier
        instruction_id: Original instruction identifier
        component: Component generating the event
        status: Event status
        details: Additional event details
        timestamp: Event timestamp
        
    Returns:
        InsightFlow event with complete artifact graph context
    """
    event_details = details or {}
    
    # Add mandatory artifact graph fields
    event_details.update({
        "stage": stage,
        "trace_id": trace_id,
        "artifact_id": artifact_id,
        "session_id": session_id,
        "instruction_id": instruction_id
    })
    
    # Add parent linking if provided
    if parent_artifact_id:
        event_details["parent_artifact_id"] = parent_artifact_id
    
    # Add artifact graph context for sovereign memory tracing
    event_details["artifact_graph_context"] = {
        "trace_id": trace_id,
        "artifact_id": artifact_id,
        "parent_artifact_id": parent_artifact_id,
        "stage": stage,
        "session_id": session_id,
        "reconstruction_ready": True
    }
    
    return make_event(
        event_type=f"artifact_graph.{stage}",
        component=component,
        status=status,
        details=event_details,
        timestamp=timestamp
    )


def make_reconstruction_event(
    reconstruction_type: str,
    trace_id: str,
    session_id: Optional[str] = None,
    artifacts_used: int = 0,
    reconstruction_status: str = "completed",
    component: str = "core_reconstruction",
    details: Dict[str, Any] = None,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create InsightFlow event for state reconstruction operations
    
    Args:
        reconstruction_type: Type of reconstruction (trace/session/artifact)
        trace_id: Global trace identifier
        session_id: Session identifier (if applicable)
        artifacts_used: Number of artifacts used in reconstruction
        reconstruction_status: Status of reconstruction
        component: Component performing reconstruction
        details: Additional reconstruction details
        timestamp: Event timestamp
        
    Returns:
        InsightFlow event for reconstruction tracking
    """
    event_details = details or {}
    
    # Add reconstruction context
    event_details.update({
        "reconstruction_type": reconstruction_type,
        "trace_id": trace_id,
        "artifacts_used": artifacts_used,
        "reconstruction_status": reconstruction_status
    })
    
    if session_id:
        event_details["session_id"] = session_id
    
    # Add sovereign memory context
    event_details["sovereign_memory_context"] = {
        "reconstruction_type": reconstruction_type,
        "trace_id": trace_id,
        "session_id": session_id,
        "artifacts_used": artifacts_used,
        "memory_system": "sovereign"
    }
    
    return make_event(
        event_type=f"reconstruction.{reconstruction_type}",
        component=component,
        status=reconstruction_status,
        details=event_details,
        timestamp=timestamp
    )
