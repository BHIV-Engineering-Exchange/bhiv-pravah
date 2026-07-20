"""
Routing Engine
Executes Creator Core instructions through deterministic routing
"""

import time
from typing import Dict, Any
from .creator_core_parser import RoutingDecision
from .execution_envelope import ExecutionEnvelopeManager
from .hash_generation import ExecutionHashGenerator
from .lineage_manager import LineageManager
from .global_trace_manager import GlobalTraceManager
from .cet_contract_compiler import CETContractCompiler
from .authority_engine import SarathiAuthorityEngine
from .execution_gate import ExecutionGate
from ..utils.logger import setup_logger

class RoutingEngine:
    """Executes instructions through deterministic routing"""
    
    def __init__(self, agents: Dict[str, Any], memory):
        self.agents = agents
        self.memory = memory
        self.logger = setup_logger(__name__)
        self.envelope_manager = ExecutionEnvelopeManager()
        self.hash_generator = ExecutionHashGenerator()
        self.lineage_manager = LineageManager(memory)
        self.trace_manager = GlobalTraceManager()
        
        # TANTRA LAYERS
        self.cet_compiler = CETContractCompiler()
        self.authority_engine = SarathiAuthorityEngine()
        self.execution_gate = ExecutionGate(agents)
    
    def execute_instruction(self, instruction: Dict[str, Any], routing_decision: RoutingDecision, start_time: float) -> Dict[str, Any]:
        """
        Execute instruction through routing decision
        
        Args:
            instruction: Original Creator Core instruction
            routing_decision: Parsed routing decision
            start_time: Execution start time
            
        Returns:
            Execution result with envelope
        """
        instruction_id = instruction.get('instruction_id')
        
        # Log execution started
        self.logger.info(
            "Instruction execution started",
            extra={
                "event_type": "execution.started",
                "instruction_id": instruction_id,
                "target_product": routing_decision.target_product,
                "module_path": routing_decision.module_path,
                "telemetry_target": "insightflow"
            }
        )
        
        try:
            # TANTRA FLOW: Core → CET → Sarathi → Gate → Execution (via microservice APIs)
            import os
            import requests
            from src.utils.observability import get_trace_id, get_workflow_id
            
            # API Key authorization
            api_key = os.getenv("AUTH_API_KEY", "")
            headers = {"X-API-Key": api_key} if api_key else {}
            
            ctx_trace_id = get_trace_id() or instruction.get('trace_id') or instruction.get('instruction_id')
            ctx_workflow_id = get_workflow_id() or instruction.get('workflow_id') or "wf_unknown"
            
            # Propagate trace and workflow identifiers
            instruction['trace_id'] = ctx_trace_id
            instruction['workflow_id'] = ctx_workflow_id
            instruction['instruction_id'] = ctx_trace_id

            # PHASE 1: CET - Compile execution contract
            cet_url = "http://127.0.0.1:8006"
            try:
                from config import ConfigManager
                cet_url = ConfigManager.get_service_url('cet')
            except ImportError:
                pass
            
            cet_req = {
                "instruction": instruction,
                "routing_decision": {
                    "blueprint_type": routing_decision.blueprint_type,
                    "target_product": routing_decision.target_product,
                    "execution_intent": routing_decision.execution_intent,
                    "module_path": routing_decision.module_path,
                    "adapter_name": routing_decision.adapter_name,
                    "execution_data": routing_decision.execution_data
                }
            }
            cet_res = requests.post(f"{cet_url}/contract/compile", json=cet_req, headers=headers, timeout=10)
            cet_res.raise_for_status()
            contract_dict = cet_res.json()
            
            self.logger.info(
                "Contract compiled via CET Service",
                extra={
                    "event_type": "cet.contract_compiled",
                    "contract_id": contract_dict.get("contract_id"),
                    "instruction_id": instruction_id,
                    "trace_id": ctx_trace_id,
                    "workflow_id": ctx_workflow_id,
                    "contract_hash": contract_dict.get("contract_hash"),
                    "telemetry_target": "insightflow"
                }
            )
            
            # PHASE 2: Sarathi - Validate contract
            sarathi_url = "http://127.0.0.1:8007"
            try:
                from config import ConfigManager
                sarathi_url = ConfigManager.get_service_url('sarathi')
            except ImportError:
                pass
                
            sarathi_res = requests.post(f"{sarathi_url}/authority/validate", json={"contract": contract_dict}, headers=headers, timeout=10)
            sarathi_res.raise_for_status()
            authority_dict = sarathi_res.json()
            
            self.logger.info(
                "Authority decision via Sarathi Service",
                extra={
                    "event_type": "sarathi.authority_decision",
                    "contract_id": contract_dict.get("contract_id"),
                    "trace_id": ctx_trace_id,
                    "workflow_id": ctx_workflow_id,
                    "allowed": authority_dict.get("allowed"),
                    "reason": authority_dict.get("reason"),
                    "telemetry_target": "insightflow"
                }
            )
            
            # PHASE 3: Gate - Execute if authorized
            gate_url = "http://127.0.0.1:8008"
            try:
                from config import ConfigManager
                gate_url = ConfigManager.get_service_url('gate')
            except ImportError:
                pass
                
            gate_res = requests.post(f"{gate_url}/gate/evaluate", json={
                "contract": contract_dict,
                "authority_decision": authority_dict
            }, headers=headers, timeout=30)
            gate_res.raise_for_status()
            execution_result = gate_res.json()
            
            # Calculate execution duration
            execution_duration_ms = (time.time() - start_time) * 1000
            
            # Generate execution envelope
            envelope = self._generate_instruction_envelope(
                instruction=instruction,
                routing_decision=routing_decision,
                execution_result=execution_result,
                execution_duration_ms=execution_duration_ms
            )
            
            # Add envelope to result
            execution_result['execution_envelope'] = self.envelope_manager.generator.envelope_to_dict(envelope)
            
            # Generate hashes
            hash_fingerprint = self.hash_generator.generate_execution_fingerprint(
                module_id=routing_decision.module_path,
                intent=routing_decision.execution_intent,
                user_id=instruction_id,  # Use instruction_id as user_id for tracing
                input_data=routing_decision.execution_data,
                output_data=execution_result
            )
            
            # Add TANTRA metadata to envelope
            execution_result['execution_envelope'].update(hash_fingerprint)
            execution_result['tantra_flow'] = {
                "contract_id": contract_dict.get("contract_id"),
                "contract_hash": contract_dict.get("contract_hash"),
                "authority_allowed": authority_dict.get("allowed"),
                "authority_reason": authority_dict.get("reason"),
                "gate_status": execution_result.get('gate_status'),
                "flow_complete": True,
                "workflow_id": ctx_workflow_id
            }
            
            # Log execution completed
            self.logger.info(
                "Instruction execution completed",
                extra={
                    "event_type": "execution.completed",
                    "instruction_id": instruction_id,
                    "execution_id": envelope.execution_id,
                    "trace_id": ctx_trace_id,
                    "workflow_id": ctx_workflow_id,
                    "status": execution_result.get('status'),
                    "execution_duration_ms": execution_duration_ms,
                    "telemetry_target": "insightflow"
                }
            )
            
            # Emit to Bucket
            self._emit_to_bucket(instruction, execution_result, envelope)
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Instruction execution failed: {e}")
            return {
                "status": "error",
                "message": f"Execution failed: {str(e)}",
                "result": {},
                "instruction_id": instruction_id
            }
    

    
    def _generate_instruction_envelope(self, instruction: Dict[str, Any], routing_decision: RoutingDecision, 
                                     execution_result: Dict[str, Any], execution_duration_ms: float):
        """Generate execution envelope for instruction"""
        
        return self.envelope_manager.create_immediate_envelope(
            module_id=routing_decision.module_path,
            intent=routing_decision.execution_intent,
            user_id=instruction.get('instruction_id'),
            input_data=routing_decision.execution_data,
            output_data=execution_result,
            schema_version=instruction.get('schema_version', '1.0.0'),
            truth_classification_level='unclassified',  # Default for Creator Core instructions
            parent_execution_id=instruction.get('parent_instruction_id'),
            execution_duration_ms=execution_duration_ms,
            instruction_id=instruction.get('instruction_id'),
            parent_instruction_id=instruction.get('parent_instruction_id')
        )
    
    def _emit_to_bucket(self, instruction: Dict[str, Any], execution_result: Dict[str, Any], envelope):
        """Emit structured artifacts to Bucket with lineage including contract and authority"""
        try:
            instruction_id = instruction.get('instruction_id')
            execution_id = envelope.execution_id
            parent_instruction_id = instruction.get('parent_instruction_id')
            contract_id = execution_result.get('contract_id', 'unknown')
            
            # Create blueprint artifact (instruction)
            blueprint_artifact = self.lineage_manager.create_artifact(
                artifact_type="blueprint",
                instruction_id=instruction_id,
                execution_id=execution_id,
                source_module_id="creator_core",
                payload={
                    "instruction": instruction,
                    "routing_decision": {
                        "target_product": instruction.get('target_product'),
                        "intent_type": instruction.get('intent_type')
                    }
                },
                parent_instruction_id=parent_instruction_id,
                metadata={
                    "target_product": instruction.get('target_product'),
                    "intent_type": instruction.get('intent_type'),
                    "schema_version": instruction.get('schema_version', '1.0.0')
                }
            )
            
            # Create contract artifact (CET output)
            contract_artifact = self.lineage_manager.create_artifact(
                artifact_type="contract",
                instruction_id=instruction_id,
                execution_id=execution_id,
                source_module_id="cet_compiler",
                payload={
                    "contract_id": contract_id,
                    "trace_id": execution_result.get('trace_id'),
                    "contract_hash": execution_result.get('contract_hash', 'unknown')
                },
                parent_instruction_id=parent_instruction_id,
                parent_hash=blueprint_artifact["artifact_hash"],
                metadata={
                    "contract_id": contract_id,
                    "gate_status": execution_result.get('gate_status', 'unknown')
                }
            )
            
            # Create execution artifact (envelope)
            execution_artifact = self.lineage_manager.create_artifact(
                artifact_type="execution",
                instruction_id=instruction_id,
                execution_id=execution_id,
                source_module_id=envelope.module_id,
                payload={
                    "execution_envelope": execution_result.get('execution_envelope', {}),
                    "input_hash": envelope.input_hash,
                    "output_hash": envelope.output_hash,
                    "contract_id": contract_id,
                    "gate_status": execution_result.get('gate_status')
                },
                parent_instruction_id=parent_instruction_id,
                parent_hash=contract_artifact["artifact_hash"],
                metadata={
                    "execution_duration_ms": envelope.execution_duration_ms,
                    "status": envelope.status,
                    "module_id": envelope.module_id
                }
            )
            
            # Create result artifact (output)
            result_artifact = self.lineage_manager.create_artifact(
                artifact_type="result",
                instruction_id=instruction_id,
                execution_id=execution_id,
                source_module_id=envelope.module_id,
                payload=execution_result,
                parent_instruction_id=parent_instruction_id,
                parent_hash=execution_artifact["artifact_hash"],
                metadata={
                    "target_product": instruction.get('target_product'),
                    "final_status": execution_result.get('status'),
                    "result_type": "execution_output"
                }
            )
            
            # Log structured bucket emission
            self.logger.info(
                "Structured artifacts emitted to Bucket",
                extra={
                    "event_type": "bucket.lineage_artifacts_stored",
                    "instruction_id": instruction_id,
                    "execution_id": execution_id,
                    "artifacts": {
                        "blueprint": blueprint_artifact["artifact_id"],
                        "contract": contract_artifact["artifact_id"],
                        "execution": execution_artifact["artifact_id"],
                        "result": result_artifact["artifact_id"]
                    },
                    "lineage_chain_length": 4,
                    "telemetry_target": "bucket"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Structured bucket emission failed: {e}")