"""
Execution Gate
==============
STRICT enforcement: NO execution without authority approval.

CRITICAL RULES:
- ONLY executes if authority.allowed == True
- NO bypasses
- NO shortcuts
- Logs all gate decisions
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ..utils.logger import setup_logger


class ExecutionGate:
    """Gated execution - enforces authority decisions"""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.logger = setup_logger(__name__)
        self.gate_log = []
    
    def execute_if_authorized(self, contract: Dict[str, Any], authority_decision: Dict[str, Any], execute: bool = True) -> Dict[str, Any]:
        """
        Execute ONLY if authority allows
        
        Args:
            contract: Execution contract
            authority_decision: Authority decision from Sarathi
            
        Returns:
            Execution result or rejection
        """
        contract_id = contract.get('contract_id', 'unknown')
        trace_id = contract.get('trace_id', 'unknown')
        
        # GATE CHECK: Authority must allow
        if not authority_decision.get('allowed', False):
            rejection = self._reject_execution(contract, authority_decision)
            self._log_gate_decision(contract_id, trace_id, "REJECTED", authority_decision.get('reason'))
            return rejection
        
        # Authority allowed - proceed with execution or return allow-only decision
        self._log_gate_decision(contract_id, trace_id, "ALLOWED", authority_decision.get('reason'))
        if not execute:
            return {
                "status": "allowed",
                "message": "Execution approved by gate",
                "result": {},
                "contract_id": contract.get("contract_id"),
                "trace_id": trace_id,
                "gate_status": "ALLOWED",
                "authority_decision": authority_decision,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            execution_result = self._execute_contract(contract)
            self._log_gate_decision(contract_id, trace_id, "EXECUTED", "execution_completed")
            return execution_result
        except Exception as e:
            error_result = self._handle_execution_error(contract, str(e))
            self._log_gate_decision(contract_id, trace_id, "FAILED", str(e))
            return error_result
    
    def _reject_execution(self, contract: Dict[str, Any], authority_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Reject execution - authority denied"""
        return {
            "status": "rejected",
            "message": f"Execution rejected by authority: {authority_decision.get('reason')}",
            "result": {},
            "contract_id": contract.get('contract_id'),
            "trace_id": contract.get('trace_id'),
            "authority_decision": authority_decision,
            "gate_status": "REJECTED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _execute_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Execute contract through module"""
        execution_plan = contract.get('execution_plan', {})
        
        module_name = execution_plan.get('target_module')
        intent = execution_plan.get('execution_intent')
        data = execution_plan.get('execution_data', {})
        
        if module_name not in self.agents:
            raise ValueError(f"Module {module_name} not found")
        
        agent = self.agents[module_name]
        if agent is None:
            raise ValueError(f"Module {module_name} is invalid or failed to load")
        
        # Execute through agent
        context = []  # Empty context for contract-based execution
        
        if hasattr(agent, 'process'):
            response = agent.process(data, context)
        elif hasattr(agent, 'handle_request'):
            response = agent.handle_request(intent, data, context)
        else:
            raise ValueError(f"Module {module_name} has invalid interface")
        
        # Normalize response
        normalized = {
            'status': 'success',
            'message': '',
            'result': {},
            'contract_id': contract.get('contract_id'),
            'trace_id': contract.get('trace_id'),
            'gate_status': 'EXECUTED'
        }
        
        if isinstance(response, dict):
            normalized['status'] = response.get('status', 'success')
            normalized['message'] = response.get('message', '')
            if 'result' in response:
                normalized['result'] = response.get('result', {})
            else:
                raw = {k: v for k, v in response.items() if k not in ('status', 'message', 'result')}
                normalized['result'] = raw
        
        return normalized
    
    def _handle_execution_error(self, contract: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Handle execution error"""
        return {
            "status": "error",
            "message": f"Execution failed: {error}",
            "result": {},
            "contract_id": contract.get('contract_id'),
            "trace_id": contract.get('trace_id'),
            "gate_status": "FAILED",
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _log_gate_decision(self, contract_id: str, trace_id: str, gate_status: str, reason: str):
        """Log gate decision"""
        log_entry = {
            "contract_id": contract_id,
            "trace_id": trace_id,
            "gate_status": gate_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.gate_log.append(log_entry)
        
        self.logger.info(
            f"Execution gate decision: {gate_status}",
            extra={
                "event_type": "execution_gate.decision",
                "gate_decision": log_entry,
                "telemetry_target": "insightflow"
            }
        )
    
    def get_gate_log(self) -> list:
        """Get all gate decisions"""
        return self.gate_log
