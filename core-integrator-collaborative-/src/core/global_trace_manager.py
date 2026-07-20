"""
Global Trace Manager
Enforces BHIV-wide trace_id and execution_id standards for cross-system tracking
"""

import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..utils.logger import setup_logger

class GlobalTraceManager:
    """Manages global trace identifiers for BHIV ecosystem alignment"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.active_traces = {}  # trace_id -> trace_context
    
    def generate_trace_id(self) -> str:
        """Generate global trace ID for cross-system tracking"""
        return f"trace_{uuid.uuid4().hex[:16]}"
    
    def generate_execution_id(self) -> str:
        """Generate global execution ID"""
        return f"exec_{uuid.uuid4().hex[:16]}"
    
    def start_trace(
        self,
        instruction_id: str,
        origin: str = "core_integrator",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Start a new global trace
        
        Args:
            instruction_id: Creator Core instruction ID
            origin: System that initiated the trace
            context: Additional trace context
            
        Returns:
            Trace identifiers (trace_id, execution_id)
        """
        trace_id = self.generate_trace_id()
        execution_id = self.generate_execution_id()
        
        trace_context = {
            "trace_id": trace_id,
            "execution_id": execution_id,
            "instruction_id": instruction_id,
            "origin": origin,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "context": context or {},
            "status": "active"
        }
        
        self.active_traces[trace_id] = trace_context
        
        self.logger.info(
            "Global trace started",
            extra={
                "event_type": "trace.started",
                "trace_id": trace_id,
                "execution_id": execution_id,
                "instruction_id": instruction_id,
                "origin": origin,
                "telemetry_target": "insightflow"
            }
        )
        
        return {
            "trace_id": trace_id,
            "execution_id": execution_id
        }
    
    def get_trace_context(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace context by trace_id"""
        return self.active_traces.get(trace_id)
    
    def update_trace_status(self, trace_id: str, status: str, metadata: Optional[Dict[str, Any]] = None):
        """Update trace status and metadata"""
        if trace_id in self.active_traces:
            self.active_traces[trace_id]["status"] = status
            self.active_traces[trace_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            if metadata:
                self.active_traces[trace_id]["context"].update(metadata)
            
            self.logger.info(
                f"Trace status updated: {status}",
                extra={
                    "event_type": "trace.status_updated",
                    "trace_id": trace_id,
                    "status": status,
                    "metadata": metadata,
                    "telemetry_target": "insightflow"
                }
            )
    
    def complete_trace(self, trace_id: str, result: Optional[Dict[str, Any]] = None):
        """Complete a trace"""
        if trace_id in self.active_traces:
            self.active_traces[trace_id]["status"] = "completed"
            self.active_traces[trace_id]["end_time"] = datetime.now(timezone.utc).isoformat()
            
            if result:
                self.active_traces[trace_id]["result"] = result
            
            self.logger.info(
                "Global trace completed",
                extra={
                    "event_type": "trace.completed",
                    "trace_id": trace_id,
                    "execution_id": self.active_traces[trace_id]["execution_id"],
                    "instruction_id": self.active_traces[trace_id]["instruction_id"],
                    "telemetry_target": "insightflow"
                }
            )
    
    def validate_trace_identifiers(self, trace_id: str, execution_id: str) -> Dict[str, Any]:
        """
        Validate trace identifiers conform to BHIV standards
        
        Returns:
            Validation result
        """
        issues = []
        
        # Validate trace_id format
        if not trace_id.startswith("trace_") or len(trace_id) != 22:
            issues.append("Invalid trace_id format - must be 'trace_' + 16 hex chars")
        
        # Validate execution_id format  
        if not execution_id.startswith("exec_") or len(execution_id) != 21:
            issues.append("Invalid execution_id format - must be 'exec_' + 16 hex chars")
        
        # Check if trace exists
        if trace_id not in self.active_traces:
            issues.append(f"Trace {trace_id} not found in active traces")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "trace_id": trace_id,
            "execution_id": execution_id
        }
    
    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get global trace statistics"""
        total_traces = len(self.active_traces)
        
        status_counts = {}
        for trace in self.active_traces.values():
            status = trace["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_traces": total_traces,
            "status_distribution": status_counts,
            "active_traces": status_counts.get("active", 0),
            "completed_traces": status_counts.get("completed", 0)
        }
    
    def enforce_global_identifiers(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce global identifier standards on artifact
        
        Args:
            artifact: Artifact to validate and enhance
            
        Returns:
            Enhanced artifact with global identifiers
        """
        # Ensure trace_id is present
        if "trace_id" not in artifact:
            # Try to derive from instruction_id
            instruction_id = artifact.get("instruction_id")
            if instruction_id:
                # Look for existing trace for this instruction
                for trace_id, trace_context in self.active_traces.items():
                    if trace_context["instruction_id"] == instruction_id:
                        artifact["trace_id"] = trace_id
                        break
                else:
                    # Create new trace if none exists
                    trace_ids = self.start_trace(instruction_id, "artifact_creation")
                    artifact["trace_id"] = trace_ids["trace_id"]
        
        # Validate execution_id format
        execution_id = artifact.get("execution_id")
        if execution_id and not execution_id.startswith("exec_"):
            self.logger.warning(f"Non-standard execution_id format: {execution_id}")
        
        return artifact