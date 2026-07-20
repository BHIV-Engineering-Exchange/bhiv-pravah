"""
Sarathi Authority Engine
========================
Validates execution contracts before allowing execution.

STRICT RULES:
- NO execution
- ONLY allow/deny decisions
- Deterministic validation
"""

from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AuthorityDecision:
    """Authority decision result"""
    allowed: bool
    reason: str
    contract_id: str
    trace_id: str
    decision_id: str
    timestamp: str
    validation_checks: Dict[str, bool]


class SarathiAuthorityEngine:
    """Authority engine - validates contracts before execution"""
    
    def __init__(self):
        self.decision_log = []
    
    def validate_contract(self, contract: Dict[str, Any]) -> AuthorityDecision:
        """
        Validate execution contract
        
        Args:
            contract: Execution contract from CET
            
        Returns:
            AuthorityDecision with allow/deny
        """
        contract_id = contract.get('contract_id', 'unknown')
        trace_id = contract.get('trace_id', 'unknown')
        
        # Run validation checks
        validation_checks = {
            "has_contract_id": self._check_contract_id(contract),
            "has_trace_id": self._check_trace_id(contract),
            "has_execution_plan": self._check_execution_plan(contract),
            "has_valid_module": self._check_valid_module(contract),
            "has_constraints": self._check_constraints(contract),
            "has_contract_hash": self._check_contract_hash(contract)
        }
        
        # Determine if allowed
        all_checks_passed = all(validation_checks.values())
        
        if all_checks_passed:
            reason = "valid_contract"
            allowed = True
        else:
            failed_checks = [k for k, v in validation_checks.items() if not v]
            reason = f"invalid_contract: {', '.join(failed_checks)}"
            allowed = False
        
        decision = AuthorityDecision(
            allowed=allowed,
            reason=reason,
            contract_id=contract_id,
            trace_id=trace_id,
            decision_id=f"decision_{contract_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            validation_checks=validation_checks
        )
        
        # Log decision
        self.decision_log.append(self._decision_to_dict(decision))
        
        return decision
    
    def _check_contract_id(self, contract: Dict[str, Any]) -> bool:
        """Check if contract has valid contract_id"""
        return 'contract_id' in contract and contract['contract_id']
    
    def _check_trace_id(self, contract: Dict[str, Any]) -> bool:
        """Check if contract has valid trace_id"""
        return 'trace_id' in contract and contract['trace_id']
    
    def _check_execution_plan(self, contract: Dict[str, Any]) -> bool:
        """Check if contract has execution plan"""
        return 'execution_plan' in contract and isinstance(contract['execution_plan'], dict)
    
    def _check_valid_module(self, contract: Dict[str, Any]) -> bool:
        """Check if contract specifies valid module"""
        execution_plan = contract.get('execution_plan', {})
        return 'target_module' in execution_plan and execution_plan['target_module']
    
    def _check_constraints(self, contract: Dict[str, Any]) -> bool:
        """Check if contract has constraints"""
        return 'constraints' in contract and isinstance(contract['constraints'], dict)
    
    def _check_contract_hash(self, contract: Dict[str, Any]) -> bool:
        """Check if contract has deterministic hash"""
        return 'contract_hash' in contract and contract['contract_hash']
    
    def _decision_to_dict(self, decision: AuthorityDecision) -> Dict[str, Any]:
        """Convert decision to dictionary"""
        return {
            "allowed": decision.allowed,
            "reason": decision.reason,
            "contract_id": decision.contract_id,
            "trace_id": decision.trace_id,
            "decision_id": decision.decision_id,
            "timestamp": decision.timestamp,
            "validation_checks": decision.validation_checks
        }
    
    def get_decision_log(self) -> list:
        """Get all authority decisions"""
        return self.decision_log
