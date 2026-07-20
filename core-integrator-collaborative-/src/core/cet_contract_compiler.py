"""
CET Contract Compiler
=====================
Converts decision + blueprint into deterministic execution contract.

STRICT RULES:
- NO execution
- NO module calls
- ONLY contract generation
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ExecutionContract:
    """Deterministic execution contract"""
    contract_id: str
    instruction_id: str
    trace_id: str
    target_module: str
    execution_intent: str
    execution_data: Dict[str, Any]
    constraints: Dict[str, Any]
    contract_hash: str
    timestamp: str
    schema_version: str = "1.0.0"


class CETContractCompiler:
    """Contract compiler - converts decisions to execution contracts"""
    
    def __init__(self):
        self.schema_version = "1.0.0"
    
    def compile_contract(self, instruction: Dict[str, Any], routing_decision: Any) -> ExecutionContract:
        """
        Compile execution contract from instruction + routing decision
        
        Args:
            instruction: Creator Core instruction
            routing_decision: Parsed routing decision
            
        Returns:
            ExecutionContract with deterministic hash
        """
        contract_id = f"contract_{uuid.uuid4().hex[:12]}"
        trace_id = instruction.get('instruction_id', f"trace_{uuid.uuid4().hex[:12]}")
        
        # Build execution plan
        execution_plan = {
            "target_module": routing_decision.module_path,
            "execution_intent": routing_decision.execution_intent,
            "execution_data": routing_decision.execution_data,
            "target_product": routing_decision.target_product
        }
        
        # Build constraints
        constraints = {
            "schema_version": instruction.get('schema_version', '1.0.0'),
            "origin": instruction.get('origin', 'creator_core'),
            "intent_type": instruction.get('intent_type'),
            "deterministic": True,
            "replay_safe": True
        }
        
        # Generate deterministic contract hash
        contract_hash = self._generate_contract_hash(
            instruction_id=trace_id,
            execution_plan=execution_plan,
            constraints=constraints
        )
        
        return ExecutionContract(
            contract_id=contract_id,
            instruction_id=trace_id,
            trace_id=trace_id,
            target_module=routing_decision.module_path,
            execution_intent=routing_decision.execution_intent,
            execution_data=routing_decision.execution_data,
            constraints=constraints,
            contract_hash=contract_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            schema_version=self.schema_version
        )
    
    def _generate_contract_hash(self, instruction_id: str, execution_plan: Dict[str, Any], 
                               constraints: Dict[str, Any]) -> str:
        """Generate deterministic hash for contract"""
        contract_data = {
            "instruction_id": instruction_id,
            "execution_plan": execution_plan,
            "constraints": constraints
        }
        
        canonical = json.dumps(contract_data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def contract_to_dict(self, contract: ExecutionContract) -> Dict[str, Any]:
        """Convert contract to dictionary"""
        return {
            "contract_id": contract.contract_id,
            "instruction_id": contract.instruction_id,
            "trace_id": contract.trace_id,
            "execution_plan": {
                "target_module": contract.target_module,
                "execution_intent": contract.execution_intent,
                "execution_data": contract.execution_data
            },
            "constraints": contract.constraints,
            "contract_hash": contract.contract_hash,
            "timestamp": contract.timestamp,
            "schema_version": contract.schema_version
        }
