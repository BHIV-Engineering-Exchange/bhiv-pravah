from typing import Dict, Any
from ..agents.finance import FinanceAgent
from ..agents.education import EducationAgent
from ..agents.creator import CreatorAgent
from ..agents.video import VideoAgent
from ..modules.base import BaseModule
from .module_loader import load_modules
from .feedback_models import CanonicalFeedbackSchema
from .registry_validation_logic import RegistryValidator, RegistryValidationError
from .execution_envelope import ExecutionEnvelopeManager
from .hash_generation import ExecutionHashGenerator
from .lineage_manager import LineageManager
from .replay_engine import ReplayEngine
from .bucket_reader import BucketReader
from ..db.memory import ContextMemory
from ..db.memory_adapter import SQLiteAdapter, RemoteNoopurAdapter, MONGODB_AVAILABLE
from ..utils.logger import setup_logger
from ..utils.bridge_client import BridgeClient
from ..utils.video_bridge_client import VideoBridgeClient
from ..utils.insightflow import make_lineage_event
from ..utils.telemetry_writer import emit_insightflow_event
from config.config import DB_PATH, INTEGRATOR_USE_NOOPUR, USE_MONGODB, MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME
from pydantic import ValidationError
import time

if MONGODB_AVAILABLE:
    from ..db.mongodb_adapter import MongoDBAdapter
try:
    from creator_routing import CreatorRouter
except ImportError:
    # Fallback if creator_routing not available
    CreatorRouter = None
import json
import os

class Gateway:
    """Central gateway for routing requests to appropriate agents"""
    
    def __init__(self):
        # Initialize logger first
        self.logger = setup_logger(__name__)
        
        # Memory adapter: MongoDB > Noopur > SQLite (priority order with fallback)
        if USE_MONGODB and MONGODB_AVAILABLE:
            try:
                self.memory = MongoDBAdapter(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)
                self.logger.info("Using MongoDB adapter")
            except Exception as e:
                self.logger.warning(f"MongoDB connection failed, falling back to SQLite: {e}")
                self.memory = SQLiteAdapter(DB_PATH)
        elif INTEGRATOR_USE_NOOPUR:
            self.memory = RemoteNoopurAdapter()
        else:
            self.memory = SQLiteAdapter(DB_PATH)
        
        # Initialize registry validator for strict execution discipline
        self.registry_validator = RegistryValidator()
        
        # Initialize execution envelope manager for traceability
        self.envelope_manager = ExecutionEnvelopeManager()
        
        # Initialize hash generator for replay validation
        self.hash_generator = ExecutionHashGenerator()
        
        # Initialize lineage manager for artifact tracking
        self.lineage_manager = LineageManager(self.memory)
        
        # Initialize bucket reader for artifact queries
        self.bucket_reader = BucketReader(self.lineage_manager)
        
        # Initialize BridgeClient as canonical external service interface
        self.bridge_client = BridgeClient()
        
        # Initialize VideoBridgeClient for text-to-video service
        self.video_bridge_client = VideoBridgeClient()
        
        # Built-in agents (non-module agents)
        self.agents = {
            "finance": FinanceAgent(),
            "education": EducationAgent(),
            "creator": CreatorAgent(),
            "video": VideoAgent(),
        }

        # Dynamically load modules from modules/ directory
        loaded_modules, errors = load_modules()
        for name, inst in loaded_modules.items():
            # register module instance under its name
            self.agents[name] = inst
        if errors:
            for e in errors:
                self.logger.warning(f"Module loader issue: {e}")
        
        self.creator_router = CreatorRouter(self.memory) if CreatorRouter else None
        
        # Initialize replay engine after routing engine is available
        self.replay_engine = None  # Will be initialized when needed
        # Validate module contracts for any module-like entries (modules under /modules should subclass BaseModule)
        for name, mod in list(self.agents.items()):
            # If the object exposes `process`, expect it to be a BaseModule
            if hasattr(mod, 'process'):
                if not isinstance(mod, BaseModule):
                    # replace with an error responder but do not crash
                    self.logger.error(f"Module '{name}' does not implement BaseModule contract. Marking as invalid.")
                    self.agents[name] = None

    def _load_module_metadata(self, module_name: str) -> Dict[str, Any]:
        """Try to load `modules/<module>/config.json` for metadata (optional)."""
        try:
            cfg_path = os.path.join('src', 'modules', module_name, 'config.json')
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def check_external_service_health(self) -> Dict[str, Any]:
        """Check external service health using BridgeClient"""
        try:
            health_result = self.bridge_client.health_check()
            if health_result.get('success') is not False:
                return {"status": "healthy", "details": health_result}
            else:
                return {
                    "status": "unhealthy", 
                    "error_type": health_result.get('error_type'),
                    "details": health_result
                }
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    def validate_feedback(self, data: Dict[str, Any]) -> CanonicalFeedbackSchema:
        """Validate feedback data against canonical schema"""
        try:
            return CanonicalFeedbackSchema(**data)
        except ValidationError as e:
            self.logger.error(f"Feedback validation failed: {e}")
            raise ValueError(f"Invalid feedback schema: {e}")
    def process_request(self, module: str, intent: str, user_id: str, 
                       data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request and route to appropriate agent"""
        
        start_time = time.time()
        
        # PHASE 1: Creator Core Instruction Detection
        is_creator_core_instruction = self._is_creator_core_instruction(data)
        
        if is_creator_core_instruction:
            return self._process_creator_core_instruction(data, start_time)
        else:
            return self._process_module_request(module, intent, user_id, data, start_time)
    
    def _is_creator_core_instruction(self, data: Dict[str, Any]) -> bool:
        """Check if request is a Creator Core instruction"""
        required_fields = ['instruction_id', 'origin', 'intent_type', 'target_product', 'payload', 'schema_version', 'timestamp']
        return (
            isinstance(data, dict) and
            all(field in data for field in required_fields) and
            data.get('origin') == 'creator_core'
        )
    
    def _process_creator_core_instruction(self, instruction: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Process Creator Core instruction"""
        
        # Validate instruction schema
        validation_result = self._validate_creator_core_instruction(instruction)
        if not validation_result['valid']:
            self.logger.error(f"Creator Core instruction validation failed: {validation_result['error']}")
            return {
                "status": "error",
                "message": f"Instruction validation failed: {validation_result['error']}",
                "result": {},
                "instruction_error": True
            }
        
        # Log instruction received
        self.logger.info(
            "Creator Core instruction received",
            extra={
                "event_type": "instruction.received",
                "instruction_id": instruction.get('instruction_id'),
                "target_product": instruction.get('target_product'),
                "intent_type": instruction.get('intent_type'),
                "telemetry_target": "insightflow"
            }
        )
        
        # Parse blueprint and route to execution
        try:
            from .creator_core_parser import CreatorCoreParser
            parser = CreatorCoreParser()
            
            routing_decision = parser.parse_blueprint(instruction)
            
            # Log instruction validated
            self.logger.info(
                "Creator Core instruction validated",
                extra={
                    "event_type": "instruction.validated",
                    "instruction_id": instruction.get('instruction_id'),
                    "routing_decision": {
                        "target_product": routing_decision.target_product,
                        "module_path": routing_decision.module_path,
                        "execution_intent": routing_decision.execution_intent
                    },
                    "telemetry_target": "insightflow"
                }
            )
            
            # Execute through routing engine
            from .routing_engine import RoutingEngine
            routing_engine = RoutingEngine(self.agents, self.memory)
            
            # Initialize replay engine if not already done
            if self.replay_engine is None:
                self.replay_engine = ReplayEngine(self.lineage_manager, routing_engine, self.memory)
            
            execution_result = routing_engine.execute_instruction(
                instruction=instruction,
                routing_decision=routing_decision,
                start_time=start_time
            )
            trace_id = instruction.get("trace_id") or instruction.get("instruction_id", "unknown")
            emit_insightflow_event(
                make_lineage_event(
                    "execution.completed",
                    trace_id,
                    trace_id,
                    component="bhiv_core",
                    status=execution_result.get("status", "unknown"),
                    details={"target_product": instruction.get("target_product")},
                )
            )
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Creator Core instruction processing failed: {e}")
            return {
                "status": "error",
                "message": f"Instruction processing failed: {str(e)}",
                "result": {},
                "instruction_error": True
            }
    
    def _validate_creator_core_instruction(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Creator Core instruction schema"""
        required_fields = {
            'instruction_id': str,
            'origin': str,
            'intent_type': str,
            'target_product': str,
            'payload': dict,
            'schema_version': str,
            'timestamp': str
        }
        
        # Check required fields and types
        for field, expected_type in required_fields.items():
            if field not in instruction:
                return {'valid': False, 'error': f'Missing required field: {field}'}
            if not isinstance(instruction[field], expected_type):
                return {'valid': False, 'error': f'Invalid type for {field}: expected {expected_type.__name__}'}
        
        # Check origin
        if instruction['origin'] != 'creator_core':
            return {'valid': False, 'error': f'Invalid origin: {instruction["origin"]}'}
        
        # Check schema version
        if instruction['schema_version'] != '1.0.0':
            return {'valid': False, 'error': f'Unsupported schema version: {instruction["schema_version"]}'}
        
        return {'valid': True}
    
    def _process_module_request(self, module: str, intent: str, user_id: str, 
                               data: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Process traditional module request (existing logic)"""
        
        # PART 1: Registry Validation - Enforce strict execution discipline
        try:
            validation_result = self.registry_validator.validate_execution_request(module, intent, data)
            if not validation_result["valid"]:
                # Reject execution immediately - no fallback permitted
                self.logger.error(f"Registry validation failed for module '{module}': {validation_result['error']}")
                return {
                    "status": "error",
                    "message": f"Registry validation failed: {validation_result['error']}",
                    "result": {},
                    "validation_error": True
                }
            
            registry_entry = validation_result["registry_entry"]
            truth_classification_level = registry_entry.truth_classification_level
            
        except Exception as e:
            self.logger.error(f"Registry validation system error: {e}")
            return {
                "status": "error",
                "message": "Registry validation system error",
                "result": {},
                "validation_error": True
            }
        
        # Special validation for feedback requests
        if module == "creator" and intent == "feedback":
            try:
                validated_feedback = self.validate_feedback(data)
                data = validated_feedback.dict()
                self.logger.info(f"Feedback validated successfully for user: {user_id}")
            except ValueError as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "result": {}
                }
        
        # Get user context (adapter provides get_context)
        context = self.memory.get_context(user_id) if user_id else []
        
        # Log request with execution tracing
        self.logger.info(
            f"Processing request for module: {module}, intent: {intent}",
            extra={
                "user_id": user_id, 
                "request_data": {"module": module, "intent": intent, "data": data},
                "registry_validation": "passed",
                "truth_classification_level": truth_classification_level
            }
        )
        
        # Special handling for creator flows: pre-warm with context from Noopur/local memory
        if module == "creator" and self.creator_router:
            try:
                data = self.creator_router.prewarm_and_prepare(request=user_id and data or {}, user_id=user_id, input_data=data)
            except Exception:
                # fallback to original data
                pass

        # Route to agent
        if module not in self.agents:
            response = {
                "status": "error",
                "message": f"Unknown module: {module}",
                "result": {}
            }
        elif self.agents[module] is None:
            response = {
                "status": "error",
                "message": f"Module {module} is invalid or failed to load",
                "result": {}
            }
        else:
            agent = self.agents[module]
            try:
                # Check if it's a BaseModule (has process method)
                if isinstance(agent, BaseModule):
                    response = agent.process(data, context)
                # Otherwise it's an agent (has handle_request method)
                elif hasattr(agent, 'handle_request'):
                    response = agent.handle_request(intent, data, context)
                else:
                    response = {
                        "status": "error",
                        "message": f"Module {module} has invalid interface",
                        "result": {}
                    }
            except Exception as e:
                self.logger.exception(f"Agent processing failed for {module}")
                response = {
                    "status": "error",
                    "message": f"Agent processing failed: {str(e)}",
                    "result": {}
                }
        
        # Calculate execution duration
        execution_duration_ms = (time.time() - start_time) * 1000
        
        # Normalize response into standardized CoreResponse shape (do not rely on module to emit full CoreResponse)
        normalized = {
            'status': 'success',
            'message': '',
            'result': {}
        }

        # If module returned a mapping, interpret intelligently
        if isinstance(response, dict):
            # If module returned keys 'status'/'message'/'result', use them; else treat whole dict as result
            normalized['status'] = response.get('status', 'success')
            normalized['message'] = response.get('message', '')
            if 'result' in response:
                normalized['result'] = response.get('result', {})
            else:
                # module returned raw payload -> put under result
                # avoid copying status/message keys into result
                raw = {k: v for k, v in response.items() if k not in ('status', 'message', 'result')}
                normalized['result'] = raw
        
        # PART 2: Generate Execution Envelope - Standardized execution tracing
        try:
            execution_envelope = self.envelope_manager.create_immediate_envelope(
                module_id=module,
                intent=intent,
                user_id=user_id,
                input_data=data,
                output_data=normalized,
                schema_version=registry_entry.schema_version,
                truth_classification_level=truth_classification_level,
                execution_duration_ms=execution_duration_ms
            )
            
            # Add envelope to response for traceability
            normalized['execution_envelope'] = self.envelope_manager.generator.envelope_to_dict(execution_envelope)
            
            # PART 3: Generate Replay Hashes - Deterministic hashing for replay validation
            hash_fingerprint = self.hash_generator.generate_execution_fingerprint(
                module_id=module,
                intent=intent,
                user_id=user_id,
                input_data=data,
                output_data=normalized
            )
            
            # Add hashes to envelope
            normalized['execution_envelope'].update(hash_fingerprint)
            
        except Exception as e:
            self.logger.error(f"Execution envelope generation failed: {e}")
            # Continue execution but log the failure

        # Store interaction
        if user_id:
            request_data = {"module": module, "intent": intent, "user_id": user_id, "data": data}
            try:
                self.memory.store_interaction(user_id, request_data, normalized)
            except Exception:
                self.logger.exception("Failed to store interaction")

        # PART 4: Execution Logging Alignment - Structured log event for telemetry
        try:
            execution_trace_log = {
                "execution_id": normalized.get('execution_envelope', {}).get('execution_id', 'unknown'),
                "module_id": module,
                "intent": intent,
                "user_id": user_id,
                "timestamp": normalized.get('execution_envelope', {}).get('timestamp_utc', ''),
                "input_hash": normalized.get('execution_envelope', {}).get('input_hash', ''),
                "output_hash": normalized.get('execution_envelope', {}).get('output_hash', ''),
                "semantic_hash": normalized.get('execution_envelope', {}).get('semantic_hash', ''),
                "status": normalized.get('status'),
                "execution_duration_ms": execution_duration_ms,
                "truth_classification_level": truth_classification_level
            }
            
            # Emit structured log through InsightFlow telemetry
            self.logger.info(
                "Execution trace event",
                extra={
                    "event_type": "execution_trace",
                    "execution_trace": execution_trace_log,
                    "telemetry_target": "insightflow"
                }
            )
            execution_id = execution_trace_log.get("execution_id", "unknown")
            emit_insightflow_event(
                make_lineage_event(
                    "execution.completed",
                    execution_id,
                    execution_id,
                    artifact_hash=execution_trace_log.get("output_hash"),
                    component="bhiv_core",
                    status=str(normalized.get("status", "unknown")),
                    details={"module_id": module, "intent": intent},
                )
            )
            
        except Exception as e:
            self.logger.error(f"Execution trace logging failed: {e}")

        # Log response with execution envelope metadata
        try:
            self.logger.info(
                f"Request processed with status: {normalized.get('status')}",
                extra={
                    "user_id": user_id, 
                    "response_data": normalized,
                    "execution_envelope_id": normalized.get('execution_envelope', {}).get('execution_id'),
                    "replay_ready": True
                }
            )
        except Exception:
            pass

        return normalized