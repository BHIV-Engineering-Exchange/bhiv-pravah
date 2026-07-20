"""
Execution Envelope System
Generates standardized execution envelopes for replay-ready traceability
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ExecutionEnvelope:
    """Standardized execution envelope for replay-ready traceability"""
    execution_id: str
    module_id: str
    product_id: str
    schema_version: str
    input_hash: str
    output_hash: str
    truth_classification_level: str
    parent_execution_id: Optional[str]
    timestamp_utc: str
    intent: str
    user_id: str
    semantic_hash: str
    execution_duration_ms: float
    status: str
    # NEW: Global trace metadata for BHIV alignment
    trace_id: Optional[str] = None
    global_execution_id: Optional[str] = None

class ExecutionEnvelopeGenerator:
    """Generates execution envelopes for module executions"""
    
    def __init__(self, product_id: str = "core_integrator"):
        self.product_id = product_id
    
    def generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        return f"exec_{uuid.uuid4().hex[:16]}"
    
    def compute_input_hash(self, data: Dict[str, Any]) -> str:
        """Compute deterministic hash of input data"""
        # Sort keys for deterministic hashing
        normalized_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized_data.encode('utf-8')).hexdigest()
    
    def compute_output_hash(self, response: Dict[str, Any]) -> str:
        """Compute deterministic hash of output data"""
        # Extract only the result portion for hashing to avoid metadata noise
        result_data = response.get('result', response)
        normalized_data = json.dumps(result_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized_data.encode('utf-8')).hexdigest()
    
    def compute_semantic_hash(self, module_id: str, intent: str, input_hash: str, output_hash: str) -> str:
        """Compute semantic hash for execution replay validation"""
        semantic_content = f"{module_id}:{intent}:{input_hash}:{output_hash}"
        return hashlib.sha256(semantic_content.encode('utf-8')).hexdigest()
    
    def create_envelope(
        self,
        module_id: str,
        intent: str,
        user_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        schema_version: str = "1.0.0",
        truth_classification_level: str = "unclassified",
        parent_execution_id: Optional[str] = None,
        execution_duration_ms: float = 0.0,
        instruction_id: Optional[str] = None,
        parent_instruction_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        global_execution_id: Optional[str] = None
    ) -> ExecutionEnvelope:
        """
        Create execution envelope for a module execution
        
        Args:
            module_id: Module identifier
            intent: Execution intent
            user_id: User identifier
            input_data: Input data
            output_data: Output data
            schema_version: Schema version
            truth_classification_level: Classification level
            parent_execution_id: Parent execution ID for chaining
            execution_duration_ms: Execution duration in milliseconds
            
        Returns:
            ExecutionEnvelope instance
        """
        execution_id = global_execution_id or self.generate_execution_id()
        timestamp_utc = datetime.now(timezone.utc).isoformat()
        
        input_hash = self.compute_input_hash(input_data)
        output_hash = self.compute_output_hash(output_data)
        semantic_hash = self.compute_semantic_hash(module_id, intent, input_hash, output_hash)
        
        status = output_data.get('status', 'unknown')
        
        return ExecutionEnvelope(
            execution_id=execution_id,
            module_id=module_id,
            product_id=self.product_id,
            schema_version=schema_version,
            input_hash=input_hash,
            output_hash=output_hash,
            truth_classification_level=truth_classification_level,
            parent_execution_id=parent_execution_id,
            timestamp_utc=timestamp_utc,
            intent=intent,
            user_id=user_id,
            semantic_hash=semantic_hash,
            execution_duration_ms=execution_duration_ms,
            status=status,
            instruction_id=instruction_id,
            parent_instruction_id=parent_instruction_id,
            trace_id=trace_id,
            global_execution_id=global_execution_id
        )
    
    def envelope_to_dict(self, envelope: ExecutionEnvelope) -> Dict[str, Any]:
        """Convert envelope to dictionary for serialization"""
        return asdict(envelope)
    
    def envelope_to_json(self, envelope: ExecutionEnvelope) -> str:
        """Convert envelope to JSON string"""
        return json.dumps(self.envelope_to_dict(envelope), indent=2)

class ExecutionEnvelopeManager:
    """Manages execution envelope generation and emission"""
    
    def __init__(self, product_id: str = "core_integrator"):
        self.generator = ExecutionEnvelopeGenerator(product_id)
        self.active_executions: Dict[str, ExecutionEnvelope] = {}
    
    def start_execution(
        self,
        module_id: str,
        intent: str,
        user_id: str,
        input_data: Dict[str, Any],
        schema_version: str = "1.0.0",
        truth_classification_level: str = "unclassified",
        parent_execution_id: Optional[str] = None
    ) -> str:
        """
        Start execution tracking and return execution ID
        
        Returns:
            execution_id for tracking
        """
        execution_id = self.generator.generate_execution_id()
        
        # Create partial envelope for tracking
        envelope = ExecutionEnvelope(
            execution_id=execution_id,
            module_id=module_id,
            product_id=self.generator.product_id,
            schema_version=schema_version,
            input_hash=self.generator.compute_input_hash(input_data),
            output_hash="",  # Will be filled on completion
            truth_classification_level=truth_classification_level,
            parent_execution_id=parent_execution_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            intent=intent,
            user_id=user_id,
            semantic_hash="",  # Will be filled on completion
            execution_duration_ms=0.0,
            status="in_progress"
        )
        
        self.active_executions[execution_id] = envelope
        return execution_id
    
    def complete_execution(
        self,
        execution_id: str,
        output_data: Dict[str, Any],
        execution_duration_ms: float
    ) -> ExecutionEnvelope:
        """
        Complete execution and generate final envelope
        
        Args:
            execution_id: Execution ID from start_execution
            output_data: Output data
            execution_duration_ms: Execution duration
            
        Returns:
            Complete ExecutionEnvelope
        """
        if execution_id not in self.active_executions:
            raise ValueError(f"Execution ID {execution_id} not found in active executions")
        
        envelope = self.active_executions[execution_id]
        
        # Complete the envelope
        envelope.output_hash = self.generator.compute_output_hash(output_data)
        envelope.semantic_hash = self.generator.compute_semantic_hash(
            envelope.module_id, envelope.intent, envelope.input_hash, envelope.output_hash
        )
        envelope.execution_duration_ms = execution_duration_ms
        envelope.status = output_data.get('status', 'completed')
        
        # Remove from active tracking
        del self.active_executions[execution_id]
        
        return envelope
    
    def create_immediate_envelope(
        self,
        module_id: str,
        intent: str,
        user_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        schema_version: str = "1.0.0",
        truth_classification_level: str = "unclassified",
        parent_execution_id: Optional[str] = None,
        execution_duration_ms: float = 0.0,
        instruction_id: Optional[str] = None,
        parent_instruction_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        global_execution_id: Optional[str] = None
    ) -> ExecutionEnvelope:
        """
        Create complete envelope immediately (for simple cases)
        
        Returns:
            Complete ExecutionEnvelope
        """
        return self.generator.create_envelope(
            module_id=module_id,
            intent=intent,
            user_id=user_id,
            input_data=input_data,
            output_data=output_data,
            schema_version=schema_version,
            truth_classification_level=truth_classification_level,
            parent_execution_id=parent_execution_id,
            execution_duration_ms=execution_duration_ms,
            instruction_id=instruction_id,
            parent_instruction_id=parent_instruction_id,
            trace_id=trace_id,
            global_execution_id=global_execution_id
        )
    
    def get_active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active executions for monitoring"""
        return {
            exec_id: self.generator.envelope_to_dict(envelope)
            for exec_id, envelope in self.active_executions.items()
        }