from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agents.agent_registry import AgentRegistry
from agents.agent_runner import AgentRunner
from baskets.basket_manager import AgentBasket
from communication.event_bus import EventBus
from database.mongo_db import MongoDBClient
from utils.redis_service import RedisService
from utils.logger import get_logger, get_execution_logger
from governance.config import get_bucket_info, validate_artifact_class, BUCKET_VERSION
from governance.snapshot import get_snapshot_info, validate_mongodb_schema, validate_redis_key
from governance.integration import (
    validate_integration_pattern,
    validate_data_flow,
    get_integration_requirements,
    get_boundary_definition,
    validate_integration_checklist
)
from governance.artifacts import (
    get_artifact_admission_policy,
    get_artifact_details,
    validate_artifact_admission,
    get_decision_criteria
)
from governance.provenance import (
    get_provenance_guarantees,
    get_provenance_gaps,
    get_guarantee_details,
    get_risk_matrix,
    get_phase_2_roadmap,
    get_compliance_status,
    get_trust_recommendations
)
from governance.retention import (
    get_retention_config,
    get_artifact_retention_rules,
    get_data_lifecycle,
    get_deletion_strategy,
    get_gdpr_process,
    get_legal_hold_process,
    get_storage_impact,
    get_cleanup_procedures,
    get_compliance_checklist,
    calculate_retention_date,
    get_dsar_process
)
from governance.integration_gate import (
    get_integration_requirements,
    get_approval_checklist,
    get_blocking_criteria,
    get_approval_timeline,
    get_approval_likelihood,
    validate_integration_request,
    validate_checklist_section,
    check_blocking_criteria,
    generate_approval_decision,
    generate_rejection_feedback,
    calculate_approval_deadline,
    get_conditional_approval_examples
)
from governance.executor_lane import (
    get_executor_role,
    get_can_execute_changes,
    get_requires_approval_changes,
    get_forbidden_actions,
    get_code_review_checkpoints,
    get_success_metrics,
    categorize_change,
    get_escalation_path,
    get_default_rule,
    validate_change_request
)
from governance.escalation_protocol import (
    get_advisor_role,
    get_escalation_triggers,
    get_response_timeline,
    get_response_format,
    get_decision_authority,
    get_disagreement_protocol,
    get_success_metrics as get_advisor_success_metrics,
    create_escalation,
    validate_escalation_response,
    assess_conflict_of_interest,
    get_escalation_process
)
from governance.owner_principles import (
    get_document_metadata,
    get_core_principles,
    get_principle_details,
    get_responsibility_checklist,
    get_owner_confirmation,
    validate_principle_adherence,
    get_closing_thought,
    check_confirmation_status
)
from governance.governance_gate import governance_gate, GovernanceDecision
from middleware.audit_middleware import AuditMiddleware
from middleware.constitutional.core_boundary_enforcer import core_boundary_enforcer, CoreCapability, ProhibitedAction
from validators.core_api_contract import core_api_contract, InputChannel, OutputChannel
from handlers.core_violation_handler import core_violation_handler, ViolationSeverity

logger = get_logger(__name__)
execution_logger = get_execution_logger()
import socketio
import os
import asyncio
import importlib
import json
import redis
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone
import uvicorn

load_dotenv()

# Get the directory where main.py is located
script_dir = Path(__file__).parent
agents_dir = script_dir / "agents"
config_file = script_dir / "agents_and_baskets.yaml"

registry = AgentRegistry(str(agents_dir))
registry.load_baskets(str(config_file))  # Load baskets from config
event_bus = EventBus()
mongo_client = MongoDBClient()
redis_service = RedisService()
sio = socketio.AsyncClient()

# Initialize audit middleware
audit_middleware = AuditMiddleware(mongo_client.db if mongo_client is not None and mongo_client.db is not None else None)

# Redis client setup
redis_client = None
try:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD", None)
    redis_username = os.getenv("REDIS_USERNAME", None)
    
    redis_config = {
        "host": redis_host,
        "port": redis_port,
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5
    }
    
    if redis_password:
        redis_config["password"] = redis_password
    if redis_username:
        redis_config["username"] = redis_username
    
    redis_client = redis.Redis(**redis_config)
    redis_client.ping()
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
except (redis.ConnectionError, redis.RedisError) as e:
    logger.warning(f"Redis connection failed: {e}. Redis features will be disabled")
    redis_client = None

class AgentInput(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to run")
    input_data: Dict = Field(..., description="Input data for the agent")
    stateful: bool = Field(False, description="Whether to run agent with state")

class BasketInput(BaseModel):
    basket_name: Optional[str] = Field(None, description="Name of predefined basket")
    config: Optional[Dict] = Field(None, description="Custom basket configuration")
    input_data: Optional[Dict] = Field(None, description="Input data for the basket execution")

async def connect_socketio():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            socketio_url = os.getenv("SOCKETIO_URL", "http://localhost:5000")
            await sio.connect(socketio_url)
            logger.info("Socket.IO client connected")
            return True
        except Exception as e:
            logger.error(f"Socket.IO connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    logger.error("Socket.IO connection failed after all retries")
    return False

async def forward_event_to_socketio(event_type: str, message: Dict):
    if sio.connected:
        try:
            await sio.emit(event_type, message)
            logger.debug(f"Forwarded event {event_type} to Socket.IO server")
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
    else:
        logger.warning(f"Socket.IO not connected, could not forward event {event_type}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Disable Socket.IO connection for now
    socketio_connected = False
    # socketio_connected = await connect_socketio()
    if not socketio_connected:
        logger.info("Socket.IO disabled - continuing with core functionality")
        # We'll continue without Socket.IO instead of raising an error
    
    # Set up event forwarding only if Socket.IO is connected
    if socketio_connected:
        event_bus.subscribe('agent-recommendation', lambda msg: forward_event_to_socketio('agent-recommendation', msg))
        event_bus.subscribe('escalation', lambda msg: forward_event_to_socketio('escalation', msg))
        event_bus.subscribe('dependency-update', lambda msg: forward_event_to_socketio('dependency-update', msg))
        logger.info("Event forwarding setup complete")
    else:
        logger.warning("Event forwarding to Socket.IO disabled due to connection failure")
    
    yield
    if mongo_client:
        mongo_client.close()
    if sio.connected:
        await sio.disconnect()
    if redis_client:
        try:
            redis_client.close()
            logger.info("Closed Redis connection")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    logger.info("Disconnected from Socket.IO, MongoDB, and Redis")

app = FastAPI(lifespan=lifespan)

try:
    from observability.pravah_adapter import start_heartbeat, emit_pravah_signal
    start_heartbeat(60)
except Exception as e:
    logger.warning(f"Failed to start Pravah heartbeat: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8080", "http://localhost:5000", "http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "bucket_version": BUCKET_VERSION,
        "core_integration": {
            "status": "active",
            "events_received": core_stats["events_received"],
            "agents_tracked": len(core_stats["agents_tracked"])
        },
        "prana_telemetry": {
            "status": "active",
            "packets_received": prana_stats["packets_received"],
            "users_tracked": len(prana_stats["users_tracked"]),
            "systems": prana_stats["systems"]
        },
        "governance": {
            "gate_active": True,
            "approved_integrations": len(governance_gate.approved_integrations),
            "certification": "enterprise_ready",
            "certification_date": "2026-01-19",
            "constitutional_governance": "active"
        },
        "services": {
            "mongodb": "connected" if mongo_client and mongo_client.db is not None else "disconnected",
            "socketio": "disabled",
            "redis": "connected" if redis_service.is_connected() else "disconnected",
            "audit_middleware": "active" if audit_middleware.audit_collection is not None else "inactive",
            "constitutional_enforcement": "active"
        }
    }

    # Check legacy Redis client if it exists
    if redis_client:
        try:
            redis_client.ping()
            health_status["services"]["redis_legacy"] = "connected"
        except (redis.ConnectionError, redis.RedisError):
            health_status["services"]["redis_legacy"] = "disconnected"

    # Determine overall status
    connected_services = [status for status in health_status["services"].values() if status == "connected"]
    if len(connected_services) >= 2:  # MongoDB + Redis is sufficient
        health_status["status"] = "healthy"
    elif health_status["services"]["mongodb"] == "connected":
        health_status["status"] = "degraded"
    else:
        health_status["status"] = "unhealthy"

    return health_status

@app.get("/agents")
async def get_agents(domain: str = Query(None)):
    logger.debug(f"Fetching agents with domain: {domain}")
    try:
        if domain:
            return registry.get_agents_by_domain(domain)
        return list(registry.agents.values())
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch agents: {str(e)}")

@app.get("/baskets")
async def get_baskets():
    logger.debug("Fetching available baskets")
    try:
        # Get baskets from registry
        baskets_from_registry = registry.baskets

        # Also scan the baskets directory for JSON files
        baskets_dir = Path("baskets")
        file_baskets = []

        if baskets_dir.exists():
            for basket_file in baskets_dir.glob("*.json"):
                try:
                    with basket_file.open("r") as f:
                        basket_data = json.load(f)
                        basket_data["source"] = "file"
                        basket_data["filename"] = basket_file.name
                        file_baskets.append(basket_data)
                except Exception as e:
                    logger.warning(f"Failed to load basket file {basket_file}: {e}")

        # Combine both sources
        all_baskets = baskets_from_registry + file_baskets

        return {
            "baskets": all_baskets,
            "count": len(all_baskets)
        }
    except Exception as e:
        logger.error(f"Error fetching baskets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch baskets: {str(e)}")

@app.post("/run-agent")
async def run_agent(agent_input: AgentInput):
    logger.debug(f"Running agent: {agent_input.agent_name}")
    try:
        if not registry.validate_compatibility(agent_input.agent_name, agent_input.input_data):
            raise HTTPException(status_code=400, detail="Input data incompatible with agent")
        
        agent_spec = registry.get_agent(agent_input.agent_name)
        if not agent_spec:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        module_path = agent_spec.get("module_path", f"agents.{agent_input.agent_name}.{agent_input.agent_name}")
        try:
            # Reload module to get latest changes (hot reload for development)
            import sys
            if module_path in sys.modules:
                importlib.reload(sys.modules[module_path])
                agent_module = sys.modules[module_path]
            else:
                agent_module = importlib.import_module(module_path)
        except ImportError as e:
            logger.error(f"Failed to import agent module {module_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Agent module import failed: {str(e)}")
        
        runner = AgentRunner(agent_input.agent_name, stateful=agent_input.stateful)
        result = await runner.run(agent_module, agent_input.input_data)
        runner.close()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        mongo_client.store_log(agent_input.agent_name, f"Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@app.post("/run-basket")
async def execute_basket(basket_input: BasketInput):
    """Execute a basket with enhanced logging and error handling"""
    logger.info(f"Executing basket: {basket_input}")

    try:
        # Load basket configuration
        if basket_input.basket_name:
            basket_path = Path("baskets") / f"{basket_input.basket_name}.json"
            if not basket_path.exists():
                raise HTTPException(status_code=404, detail=f"Basket {basket_input.basket_name} not found")
            with basket_path.open("r") as f:
                basket_spec = json.load(f)
        elif basket_input.config:
            basket_spec = basket_input.config
        else:
            raise HTTPException(status_code=400, detail="Must provide basket_name or config")

        # Validate basket specification
        if not basket_spec.get("agents"):
            raise HTTPException(status_code=400, detail="Basket must contain at least one agent")

        # Create and execute basket with Redis integration
        basket = AgentBasket(basket_spec, registry, event_bus, redis_service)

        # Execute with provided input data or agent-specific default
        if basket_input.input_data:
            input_data = basket_input.input_data
        else:
            # Get default input based on the first agent in the basket
            first_agent_name = basket_spec.get("agents", [])[0] if basket_spec.get("agents") else None
            if first_agent_name:
                agent_spec = registry.get_agent(first_agent_name)
                if agent_spec and "sample_input" in agent_spec:
                    input_data = agent_spec["sample_input"]
                    logger.info(f"Using sample input from {first_agent_name}: {input_data}")
                else:
                    input_data = {"input": "start"}
            else:
                input_data = {"input": "start"}

        logger.info(f"Starting basket execution: {basket_spec.get('basket_name', 'unnamed')} (ID: {basket.execution_id})")
        result = await basket.execute(input_data)

        # Add execution metadata to result
        if "error" not in result:
            result["execution_metadata"] = {
                "execution_id": basket.execution_id,
                "basket_name": basket_spec.get("basket_name", "unnamed"),
                "agents_executed": basket_spec.get("agents", []),
                "strategy": basket_spec.get("execution_strategy", "sequential")
            }

        logger.info(f"Basket execution completed: {basket.execution_id}")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = f"Basket execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Store error in Redis if service is available
        if redis_service.is_connected():
            try:
                redis_service.store_execution_log(
                    "unknown",
                    "basket_manager",
                    "execution_error",
                    {"error": error_msg, "basket_input": basket_input.model_dump()},
                    "error"
                )
            except Exception as redis_error:
                logger.warning(f"Failed to store error in Redis: {redis_error}")

        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/create-basket")
async def create_basket(basket_data: Dict):
    logger.debug(f"Creating basket: {basket_data}")
    try:
        basket_name = basket_data.get("name")
        if not basket_name:
            raise HTTPException(status_code=400, detail="Basket name is required")

        # Validate agents exist
        agents = basket_data.get("agents", [])
        for agent_name in agents:
            if not registry.get_agent(agent_name):
                raise HTTPException(status_code=400, detail=f"Agent {agent_name} not found")

        # Create basket configuration
        basket_config = {
            "basket_name": basket_name,
            "agents": agents,
            "execution_strategy": basket_data.get("execution_strategy", "sequential"),
            "description": basket_data.get("description", "")
        }

        # Save to file
        basket_path = Path("baskets") / f"{basket_name}.json"
        with basket_path.open("w") as f:
            json.dump(basket_config, f, indent=2)

        logger.info(f"Created basket: {basket_name}")
        return {"success": True, "message": f"Basket {basket_name} created successfully", "basket": basket_config}
    except Exception as e:
        logger.error(f"Basket creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Basket creation failed: {str(e)}")

@app.get("/logs")
async def get_logs(agent: str = Query(None)):
    logger.debug(f"Fetching logs for agent: {agent}")
    try:
        return {"logs": mongo_client.get_logs(agent)}
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")

@app.get("/redis/status")
async def redis_status():
    """Check Redis connection and get statistics"""
    if not redis_service.is_connected():
        raise HTTPException(status_code=503, detail="Redis service not connected")

    try:
        stats = redis_service.get_stats()
        return {
            "status": "healthy" if stats["connected"] else "unhealthy",
            "message": "Redis service is working correctly",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Redis status check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Redis status check failed: {str(e)}")

@app.get("/execution-logs/{execution_id}")
async def get_execution_logs(execution_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get execution logs for a specific execution ID"""
    try:
        logs = redis_service.get_execution_logs(execution_id, limit)
        return {
            "execution_id": execution_id,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get execution logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution logs: {str(e)}")

@app.get("/agent-logs/{agent_name}")
async def get_agent_logs(agent_name: str, limit: int = Query(100, ge=1, le=1000)):
    """Get logs for a specific agent"""
    try:
        logs = redis_service.get_agent_logs(agent_name, limit)
        return {
            "agent_name": agent_name,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get agent logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent logs: {str(e)}")

@app.post("/redis/cleanup")
async def cleanup_redis_data(days: int = Query(7, ge=1, le=30)):
    """Clean up old Redis data"""
    try:
        redis_service.cleanup_old_data(days)
        return {
            "success": True,
            "message": f"Cleaned up Redis data older than {days} days"
        }
    except Exception as e:
        logger.error(f"Redis cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Redis cleanup failed: {str(e)}")

@app.delete("/baskets/{basket_name}")
async def delete_basket(basket_name: str):
    """Delete a basket and clean up all related data"""
    logger.info(f"Deleting basket: {basket_name}")

    try:
        # Check if basket exists
        basket_path = Path("baskets") / f"{basket_name}.json"
        if not basket_path.exists():
            raise HTTPException(status_code=404, detail=f"Basket '{basket_name}' not found")

        # Load basket configuration to get execution history
        with basket_path.open("r") as f:
            basket_config = json.load(f)

        cleanup_summary = {
            "basket_name": basket_name,
            "files_deleted": [],
            "redis_data_cleaned": [],
            "mongo_data_cleaned": [],
            "errors": []
        }

        # 1. Clean up Redis data
        if redis_service.is_connected():
            try:
                # Get all execution IDs for this basket
                execution_ids = redis_service.get_basket_executions(basket_name)

                for execution_id in execution_ids:
                    # Clean execution logs
                    redis_service.client.delete(f"execution:{execution_id}:logs")

                    # Clean agent outputs for this execution
                    for agent_name in basket_config.get("agents", []):
                        redis_service.client.delete(f"execution:{execution_id}:outputs:{agent_name}")
                        redis_service.client.delete(f"agent:{agent_name}:state:{execution_id}")

                    cleanup_summary["redis_data_cleaned"].append(f"execution:{execution_id}")

                # Clean basket metadata
                redis_service.client.delete(f"basket:{basket_name}:executions")

                # Clean basket execution metadata
                basket_keys = redis_service.client.keys(f"basket:{basket_name}:execution:*")
                if basket_keys:
                    redis_service.client.delete(*basket_keys)
                    cleanup_summary["redis_data_cleaned"].extend([key.decode() for key in basket_keys])

                logger.info(f"Cleaned Redis data for basket: {basket_name}")

            except Exception as e:
                error_msg = f"Redis cleanup error: {str(e)}"
                cleanup_summary["errors"].append(error_msg)
                logger.error(error_msg)

        # 2. Clean up MongoDB data (if connected)
        if mongo_client and mongo_client.db is not None:
            try:
                # Clean basket execution logs from MongoDB
                result = mongo_client.db.logs.delete_many({"basket_name": basket_name})
                if result.deleted_count > 0:
                    cleanup_summary["mongo_data_cleaned"].append(f"Deleted {result.deleted_count} log entries")

                # Clean basket metadata from MongoDB
                result = mongo_client.db.baskets.delete_many({"basket_name": basket_name})
                if result.deleted_count > 0:
                    cleanup_summary["mongo_data_cleaned"].append(f"Deleted {result.deleted_count} basket records")

                logger.info(f"Cleaned MongoDB data for basket: {basket_name}")

            except Exception as e:
                error_msg = f"MongoDB cleanup error: {str(e)}"
                cleanup_summary["errors"].append(error_msg)
                logger.error(error_msg)

        # 3. Clean up log files
        try:
            logs_dir = Path("logs/basket_runs")
            if logs_dir.exists():
                # Find and delete log files for this basket
                log_files = list(logs_dir.glob(f"{basket_name}_*.log"))
                for log_file in log_files:
                    log_file.unlink()
                    cleanup_summary["files_deleted"].append(str(log_file))

                logger.info(f"Deleted {len(log_files)} log files for basket: {basket_name}")

        except Exception as e:
            error_msg = f"Log file cleanup error: {str(e)}"
            cleanup_summary["errors"].append(error_msg)
            logger.error(error_msg)

        # 4. Delete the basket configuration file
        try:
            basket_path.unlink()
            cleanup_summary["files_deleted"].append(str(basket_path))
            logger.info(f"Deleted basket configuration file: {basket_path}")

        except Exception as e:
            error_msg = f"Basket file deletion error: {str(e)}"
            cleanup_summary["errors"].append(error_msg)
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # 5. Reload registry to remove basket from memory
        try:
            config_file = Path("agents_and_baskets.yaml")
            if config_file.exists():
                registry.load_baskets(str(config_file))
            logger.info("Reloaded basket registry")

        except Exception as e:
            error_msg = f"Registry reload error: {str(e)}"
            cleanup_summary["errors"].append(error_msg)
            logger.warning(error_msg)

        # 6. Log the deletion event in Redis (if available)
        if redis_service.is_connected():
            try:
                deletion_log = {
                    "event": "basket_deleted",
                    "basket_name": basket_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cleanup_summary": cleanup_summary
                }
                redis_service.client.lpush("system:basket_deletions", json.dumps(deletion_log))
                redis_service.client.expire("system:basket_deletions", 86400 * 30)  # Keep for 30 days

            except Exception as e:
                logger.warning(f"Failed to log deletion event: {e}")

        # Prepare response
        success_message = f"Basket '{basket_name}' deleted successfully"
        if cleanup_summary["errors"]:
            success_message += f" with {len(cleanup_summary['errors'])} warnings"

        logger.info(f"Basket deletion completed: {basket_name}")

        return {
            "success": True,
            "message": success_message,
            "cleanup_summary": cleanup_summary
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = f"Failed to delete basket '{basket_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# Law Agent Request Models
class BasicLegalQueryRequest(BaseModel):
    user_input: str
    feedback: Optional[str] = None
    session_id: Optional[str] = None

class AdaptiveLegalQueryRequest(BaseModel):
    user_input: str
    enable_learning: bool = True
    feedback: Optional[str] = None
    session_id: Optional[str] = None

class EnhancedLegalQueryRequest(BaseModel):
    user_input: str
    location: Optional[str] = None
    feedback: Optional[str] = None
    session_id: Optional[str] = None

# ============================================================================
# CORE INTEGRATION ENDPOINTS (Core-Bucket Communication)
# ============================================================================

# In-memory storage for Core events
core_events_store = []
core_stats = {"events_received": 0, "agents_tracked": set()}

# In-memory storage for PRANA telemetry
prana_packets_store = []
prana_stats = {"packets_received": 0, "users_tracked": set(), "systems": {"gurukul": 0, "ems": 0}}

class CoreEventRequest(BaseModel):
    requester_id: str
    event_data: Dict

class PranaPacket(BaseModel):
    user_id: str
    session_id: str
    lesson_id: Optional[str] = None
    task_id: Optional[str] = None
    system_type: str  # "gurukul" | "ems"
    role: str  # "student" | "employee"
    timestamp: str
    cognitive_state: str
    active_seconds: float
    idle_seconds: float
    away_seconds: float
    focus_score: int
    raw_signals: Dict

@app.post("/core/write-event")
async def write_core_event(request: CoreEventRequest):
    """Receive events from Core, Workflow Executor, and UAO (fire-and-forget) and forward to Karma"""
    try:
        # Accept events from Core, Workflow Executor, and Unified Action Orchestrator
        if request.requester_id not in ["bhiv_core", "workflow_executor", "unified_action_orchestrator"]:
            raise HTTPException(status_code=403, detail="Unauthorized requester")
        
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requester_id": request.requester_id,
            **request.event_data
        }
        
        core_events_store.append(event)
        core_stats["events_received"] += 1
        
        if "agent_id" in request.event_data:
            core_stats["agents_tracked"].add(request.event_data["agent_id"])
        
        # Forward to Karma (fire-and-forget)
        try:
            from integration.karma_forwarder import karma_forwarder
            asyncio.create_task(karma_forwarder.forward_agent_event(request.event_data))
        except Exception as karma_error:
            logger.debug(f"Karma forward failed (non-blocking): {karma_error}")
        
        logger.info(f"Core event received: {request.event_data.get('event_type')}")
        return {"success": True, "message": "Event received"}
    except Exception as e:
        logger.error(f"Core event write failed: {e}")
        return {"success": False, "message": str(e)}

@app.get("/core/events")
async def get_core_events(limit: int = Query(100, ge=1, le=1000)):
    """Get Core events stored in Bucket"""
    return {
        "events": core_events_store[-limit:],
        "count": len(core_events_store),
        "showing": min(limit, len(core_events_store))
    }

@app.get("/core/stats")
async def get_core_stats():
    """Get Core integration statistics"""
    return {
        "stats": {
            "total_events": core_stats["events_received"],
            "agents_with_context": len(core_stats["agents_tracked"]),
            "tracked_agents": list(core_stats["agents_tracked"])
        },
        "integration_status": "active"
    }

@app.get("/core/read-context")
async def read_core_context(
    agent_id: str = Query(..., description="Agent ID"),
    requester_id: str = Query(..., description="Requester ID")
):
    """Read historical context for an agent"""
    if requester_id != "bhiv_core":
        raise HTTPException(status_code=403, detail="Unauthorized requester")
    
    agent_events = [e for e in core_events_store if e.get("agent_id") == agent_id]
    
    if agent_events:
        return {
            "success": True,
            "context": {
                "agent_id": agent_id,
                "event_count": len(agent_events),
                "last_updated": agent_events[-1].get("timestamp"),
                "recent_event_types": list(set(e.get("event_type") for e in agent_events[-10:]))
            }
        }
    else:
        return {"success": True, "context": None}

# ============================================================================
# PRANA TELEMETRY ENDPOINTS (User Behavior Tracking)
# ============================================================================

@app.post("/bucket/prana/ingest")
async def ingest_prana_packet(packet: PranaPacket):
    """Receive PRANA telemetry packets (fire-and-forget)"""
    try:
        # Convert to dict and ensure JSON serializable
        packet_dict = packet.model_dump()
        
        # Store packet with metadata
        stored_packet = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            **packet_dict
        }
        
        # Store in MongoDB FIRST (before adding to in-memory store)
        if mongo_client and mongo_client.db is not None:
            try:
                mongo_packet = stored_packet.copy()
                mongo_client.db.prana_telemetry.insert_one(mongo_packet)
            except Exception as mongo_error:
                logger.debug(f"MongoDB storage failed (non-blocking): {mongo_error}")
        
        # Add to in-memory store (clean dict without _id)
        prana_packets_store.append(stored_packet)
        prana_stats["packets_received"] += 1
        prana_stats["users_tracked"].add(packet.user_id)
        prana_stats["systems"][packet.system_type] = prana_stats["systems"].get(packet.system_type, 0) + 1
        
        # Forward to Karma (fire-and-forget)
        try:
            from integration.karma_forwarder import karma_forwarder
            karma_event = {
                "user_id": packet.user_id,
                "action": f"cognitive_state_{packet.cognitive_state.lower()}",
                "role": packet.role,
                "note": f"Focus: {packet.focus_score}%, Active: {packet.active_seconds}s, System: {packet.system_type}",
                "metadata": {
                    "cognitive_state": packet.cognitive_state,
                    "focus_score": packet.focus_score,
                    "active_seconds": packet.active_seconds,
                    "idle_seconds": packet.idle_seconds,
                    "away_seconds": packet.away_seconds,
                    "system_type": packet.system_type,
                    "session_id": packet.session_id,
                    "lesson_id": packet.lesson_id,
                    "task_id": packet.task_id
                }
            }
            asyncio.create_task(karma_forwarder.forward_prana_event(karma_event))
        except Exception as karma_error:
            logger.debug(f"Karma forward failed (non-blocking): {karma_error}")
        
        logger.info(f"PRANA packet received: user={packet.user_id}, state={packet.cognitive_state}, focus={packet.focus_score}")
        try:
            emit_pravah_signal(state="running", extra={"user_id": packet.user_id, "cognitive_state": packet.cognitive_state})
        except Exception:
            pass
        return {"success": True, "message": "Packet received"}
    except Exception as e:
        logger.error(f"PRANA packet ingestion failed: {e}")
        try:
            emit_pravah_signal(state="degraded", errors_last_min=1, extra={"error": str(e)})
        except Exception:
            pass
        return {"success": False, "message": str(e)}

@app.get("/bucket/prana/packets")
async def get_prana_packets(
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    system_type: Optional[str] = Query(None, description="Filter by system type")
):
    """Get PRANA packets stored in Bucket"""
    try:
        packets = prana_packets_store[:]
        
        if user_id:
            packets = [p for p in packets if p.get("user_id") == user_id]
        if system_type:
            packets = [p for p in packets if p.get("system_type") == system_type]
        
        result_packets = packets[-limit:]
        
        # Ensure clean JSON serialization by removing any _id fields
        clean_packets = []
        for p in result_packets:
            clean_p = {k: v for k, v in p.items() if k != "_id"}
            clean_packets.append(clean_p)
        
        return {
            "packets": clean_packets,
            "count": len(packets),
            "showing": len(clean_packets)
        }
    except Exception as e:
        logger.error(f"PRANA packets error: {e}", exc_info=True)
        return {"packets": [], "count": 0, "showing": 0, "error": str(e)}

@app.get("/bucket/prana/stats")
async def get_prana_stats():
    """Get PRANA telemetry statistics"""
    return {
        "stats": {
            "total_packets": prana_stats["packets_received"],
            "unique_users": len(prana_stats["users_tracked"]),
            "systems": prana_stats["systems"],
            "tracked_users": list(prana_stats["users_tracked"])
        },
        "telemetry_status": "active"
    }

@app.get("/bucket/prana/user/{user_id}")
async def get_user_prana_history(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get PRANA history for a specific user"""
    try:
        user_packets = [p for p in prana_packets_store if p.get("user_id") == user_id]
        
        if not user_packets:
            return {
                "user_id": user_id,
                "packets": [],
                "count": 0,
                "analytics": {
                    "average_focus_score": 0,
                    "state_distribution": {},
                    "most_common_state": None
                }
            }
        
        total_focus = sum(p.get("focus_score", 0) for p in user_packets)
        avg_focus = total_focus / len(user_packets)
        
        states = {}
        for p in user_packets:
            state = p.get("cognitive_state", "UNKNOWN")
            states[state] = states.get(state, 0) + 1
        
        result_packets = user_packets[-limit:]
        
        # Ensure clean JSON serialization by removing any _id fields
        clean_packets = []
        for p in result_packets:
            clean_p = {k: v for k, v in p.items() if k != "_id"}
            clean_packets.append(clean_p)
        
        return {
            "user_id": user_id,
            "packets": clean_packets,
            "count": len(user_packets),
            "analytics": {
                "average_focus_score": round(avg_focus, 2),
                "state_distribution": states,
                "most_common_state": max(states, key=states.get) if states else None
            }
        }
    except Exception as e:
        logger.error(f"User PRANA history error: {e}", exc_info=True)
        return {
            "user_id": user_id,
            "packets": [],
            "count": 0,
            "analytics": {"average_focus_score": 0, "state_distribution": {}, "most_common_state": None},
            "error": str(e)
        }

# Governance Endpoints
@app.get("/governance/info")
async def get_governance_info():
    """Get BHIV Bucket v1 governance information"""
    return get_bucket_info()

@app.get("/governance/snapshot")
async def get_schema_snapshot():
    """Get Bucket v1 schema snapshot (baseline state)"""
    return get_snapshot_info()

@app.get("/governance/integration-requirements")
async def get_integration_reqs():
    """Get mandatory integration requirements"""
    return get_integration_requirements()

@app.get("/governance/boundary")
async def get_integration_boundary():
    """Get Bucket boundary definition (what Bucket accepts/returns)"""
    return get_boundary_definition()

@app.get("/governance/artifact-policy")
async def get_artifact_policy():
    """Get artifact admission policy (approved/rejected classes)"""
    return get_artifact_admission_policy()

@app.get("/governance/artifact-details/{artifact_class}")
async def get_artifact_info(artifact_class: str):
    """Get detailed information about an artifact class"""
    return get_artifact_details(artifact_class)

@app.get("/governance/decision-criteria")
async def get_criteria():
    """Get artifact admission decision criteria"""
    return get_decision_criteria()

@app.post("/governance/validate-artifact")
async def validate_artifact(artifact_class: str = Query(..., description="Artifact class to validate")):
    """Validate if an artifact class is approved for storage"""
    return validate_artifact_class(artifact_class)

@app.post("/governance/validate-artifact-admission")
async def validate_admission(artifact_class: str = Query(...), data: Dict = None):
    """Validate if artifact can be admitted to Bucket"""
    return validate_artifact_admission(artifact_class, data)

@app.post("/governance/validate-schema")
async def validate_schema(collection: str = Query(...), document: Dict = None):
    """Validate MongoDB document against snapshot schema"""
    if not document:
        raise HTTPException(status_code=400, detail="Document required for validation")
    return validate_mongodb_schema(collection, document)

@app.post("/governance/validate-integration-pattern")
async def validate_pattern(pattern: str = Query(..., description="Integration pattern to validate")):
    """Validate if integration pattern is allowed"""
    return validate_integration_pattern(pattern)

@app.post("/governance/validate-data-flow")
async def validate_flow(direction: str = Query(..., description="Data flow direction")):
    """Validate data flow direction"""
    return validate_data_flow(direction)

@app.post("/governance/validate-integration-checklist")
async def validate_checklist(checklist: Dict):
    """Validate integration approval checklist"""
    return validate_integration_checklist(checklist)

@app.get("/governance/provenance/guarantees")
async def get_guarantees():
    """Get what IS guaranteed in provenance tracking"""
    return get_provenance_guarantees()

@app.get("/governance/provenance/gaps")
async def get_gaps():
    """Get what is NOT guaranteed (honest gaps)"""
    return get_provenance_gaps()

@app.get("/governance/provenance/details/{item_name}")
async def get_provenance_detail(item_name: str):
    """Get details about a specific guarantee or gap"""
    return get_guarantee_details(item_name)

@app.get("/governance/provenance/risk-matrix")
async def get_risks():
    """Get risk assessment for all gaps"""
    return get_risk_matrix()

@app.get("/governance/provenance/roadmap")
async def get_roadmap():
    """Get Phase 2 improvement roadmap"""
    return get_phase_2_roadmap()

@app.get("/governance/provenance/compliance")
async def get_compliance():
    """Get compliance implications (GDPR, HIPAA, SOC2, PCI-DSS)"""
    return get_compliance_status()

@app.get("/governance/provenance/trust-recommendations")
async def get_recommendations():
    """Get what teams can and cannot trust"""
    return get_trust_recommendations()

# Retention Endpoints (Document 06)
@app.get("/governance/retention/config")
async def get_retention_configuration():
    """Get retention configuration and tunable parameters"""
    return get_retention_config()

@app.get("/governance/retention/rules")
async def get_retention_rules():
    """Get per-artifact retention rules"""
    return get_artifact_retention_rules()

@app.get("/governance/retention/lifecycle")
async def get_lifecycle():
    """Get data lifecycle stages"""
    return get_data_lifecycle()

@app.get("/governance/retention/deletion-strategy")
async def get_deletion():
    """Get deletion strategy (tombstoning + TTL)"""
    return get_deletion_strategy()

@app.get("/governance/retention/gdpr")
async def get_gdpr():
    """Get GDPR right-to-be-forgotten process"""
    return get_gdpr_process()

@app.get("/governance/retention/legal-hold")
async def get_legal_hold():
    """Get legal hold process"""
    return get_legal_hold_process()

@app.get("/governance/retention/storage-impact")
async def get_storage():
    """Get storage impact analysis"""
    return get_storage_impact()

@app.get("/governance/retention/cleanup-procedures")
async def get_cleanup():
    """Get cleanup procedures (automated and manual)"""
    return get_cleanup_procedures()

@app.get("/governance/retention/compliance-checklist")
async def get_retention_compliance():
    """Get retention compliance checklist"""
    return get_compliance_checklist()

@app.get("/governance/retention/dsar")
async def get_dsar():
    """Get Data Subject Access Request process"""
    return get_dsar_process()

@app.post("/governance/retention/calculate")
async def calculate_retention(
    artifact_type: str = Query(..., description="Artifact type to calculate retention for"),
    created_date: Optional[str] = Query(None, description="ISO format date (defaults to now)")
):
    """Calculate when data should be deleted based on artifact type"""
    from datetime import datetime
    
    if created_date:
        try:
            created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
    else:
        created = None
    
    return calculate_retention_date(artifact_type, created)

# Integration Gate Endpoints (Document 07)
@app.get("/governance/integration-gate/requirements")
async def get_integration_reqs():
    """Get integration request requirements"""
    return get_integration_requirements()

@app.get("/governance/integration-gate/checklist")
async def get_gate_checklist():
    """Get 50-item approval checklist"""
    return get_approval_checklist()

@app.get("/governance/integration-gate/blocking-criteria")
async def get_blocking():
    """Get automatic rejection criteria"""
    return get_blocking_criteria()

@app.get("/governance/integration-gate/timeline")
async def get_timeline():
    """Get approval timeline (7 days max)"""
    return get_approval_timeline()

@app.get("/governance/integration-gate/approval-likelihood")
async def get_likelihood():
    """Get quick reference for approval likelihood"""
    return get_approval_likelihood()

@app.get("/governance/integration-gate/conditional-examples")
async def get_conditional_examples():
    """Get examples of conditional approvals"""
    return get_conditional_approval_examples()

@app.post("/governance/integration-gate/validate-request")
async def validate_request(request_data: Dict):
    """Validate integration request completeness"""
    return validate_integration_request(request_data)

@app.post("/governance/integration-gate/validate-section")
async def validate_section(
    section_name: str = Query(..., description="Checklist section to validate"),
    checklist_data: Dict = None
):
    """Validate a specific checklist section"""
    if not checklist_data:
        raise HTTPException(status_code=400, detail="Checklist data required")
    return validate_checklist_section(section_name, checklist_data)

@app.post("/governance/integration-gate/check-blocking")
async def check_blocking(integration_data: Dict):
    """Check if integration meets any blocking criteria"""
    return check_blocking_criteria(integration_data)

@app.post("/governance/integration-gate/generate-approval")
async def generate_approval(
    system_name: str = Query(..., description="System name"),
    status: str = Query(..., description="approved/rejected/conditional"),
    rationale: str = Query(..., description="Approval rationale"),
    conditions: Optional[List[str]] = Query(None, description="Conditions if conditional"),
    owner_contact: Optional[str] = Query(None, description="Owner contact")
):
    """Generate approval decision document"""
    return generate_approval_decision(system_name, status, rationale, conditions, owner_contact)

@app.post("/governance/integration-gate/generate-rejection")
async def generate_rejection(rejection_data: Dict):
    """Generate rejection feedback document"""
    system_name = rejection_data.get("system_name")
    issues = rejection_data.get("issues", [])
    path_forward = rejection_data.get("path_forward", [])
    
    if not system_name:
        raise HTTPException(status_code=400, detail="system_name required")
    
    return generate_rejection_feedback(system_name, issues, path_forward)

@app.post("/governance/integration-gate/calculate-deadline")
async def calculate_deadline(submission_date: Optional[str] = Query(None, description="ISO format date")):
    """Calculate approval timeline deadlines"""
    from datetime import datetime
    
    if submission_date:
        try:
            submission = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        submission = None
    
    return calculate_approval_deadline(submission)

# Executor Lane Endpoints (Document 08)
@app.get("/governance/executor/role")
async def get_executor():
    """Get executor role definition (Akanksha)"""
    return get_executor_role()

@app.get("/governance/executor/can-execute")
async def get_can_execute():
    """Get changes that can be executed without approval"""
    return get_can_execute_changes()

@app.get("/governance/executor/requires-approval")
async def get_requires_approval():
    """Get changes that require Ashmit's approval"""
    return get_requires_approval_changes()

@app.get("/governance/executor/forbidden")
async def get_forbidden():
    """Get forbidden actions"""
    return get_forbidden_actions()

@app.get("/governance/executor/checkpoints")
async def get_checkpoints():
    """Get code review checkpoints"""
    return get_code_review_checkpoints()

@app.get("/governance/executor/success-metrics")
async def get_metrics():
    """Get success metrics for executor role"""
    return get_success_metrics()

@app.get("/governance/executor/escalation-path")
async def get_escalation():
    """Get escalation path for disagreements or blocks"""
    return get_escalation_path()

@app.get("/governance/executor/default-rule")
async def get_default():
    """Get default rule: IF UNSURE, ASK"""
    return get_default_rule()

@app.post("/governance/executor/categorize-change")
async def categorize(change_description: str = Query(..., description="Description of the change")):
    """Categorize a change as can_execute, requires_approval, or forbidden"""
    return categorize_change(change_description)

@app.post("/governance/executor/validate-change")
async def validate_change(change_data: Dict):
    """Validate if a change request is properly categorized"""
    return validate_change_request(change_data)

# Escalation Protocol Endpoints (Document 09)
@app.get("/governance/escalation/advisor-role")
async def get_advisor():
    """Get advisor role definition (Vijay Dhawan)"""
    return get_advisor_role()

@app.get("/governance/escalation/triggers")
async def get_triggers():
    """Get escalation triggers (when Ashmit escalates to Vijay)"""
    return get_escalation_triggers()

@app.get("/governance/escalation/response-timeline")
async def get_timeline():
    """Get response timeline expectations"""
    return get_response_timeline()

@app.get("/governance/escalation/response-format")
async def get_format():
    """Get response format template"""
    return get_response_format()

@app.get("/governance/escalation/decision-authority")
async def get_authority():
    """Get decision authority boundaries"""
    return get_decision_authority()

@app.get("/governance/escalation/disagreement-protocol")
async def get_disagreement():
    """Get disagreement protocol"""
    return get_disagreement_protocol()

@app.get("/governance/escalation/advisor-success-metrics")
async def get_advisor_metrics():
    """Get success metrics for advisor role"""
    return get_advisor_success_metrics()

@app.get("/governance/escalation/process")
async def get_process():
    """Get escalation process flow"""
    return get_escalation_process()

@app.post("/governance/escalation/create")
async def create_escalation_request(
    trigger_type: str = Query(..., description="Escalation trigger type"),
    context: str = Query(..., description="Context of the escalation"),
    options: List[str] = Query(..., description="Options being considered"),
    urgency: str = Query(..., description="critical/high/medium/low"),
    timeline: Optional[str] = Query(None, description="Decision timeline")
):
    """Create an escalation to Vijay"""
    return create_escalation(trigger_type, context, options, urgency, timeline)

@app.post("/governance/escalation/validate-response")
async def validate_response(response_data: Dict):
    """Validate if escalation response has all required components"""
    return validate_escalation_response(response_data)

@app.post("/governance/escalation/assess-conflict")
async def assess_conflict(advisor_data: Dict):
    """Assess if advisor has conflict of interest"""
    return assess_conflict_of_interest(advisor_data)

# Owner Principles Endpoints (Document 10)
@app.get("/governance/owner/metadata")
async def get_metadata():
    """Get document metadata"""
    return get_document_metadata()

@app.get("/governance/owner/principles")
async def get_principles():
    """Get all 10 core principles"""
    return get_core_principles()

@app.get("/governance/owner/principle/{principle_number}")
async def get_principle(principle_number: int):
    """Get details of a specific principle (1-10)"""
    return get_principle_details(principle_number)

@app.get("/governance/owner/checklist")
async def get_checklist():
    """Get final responsibility checklist"""
    return get_responsibility_checklist()

@app.get("/governance/owner/confirmation")
async def get_confirmation():
    """Get owner confirmation details"""
    return get_owner_confirmation()

@app.get("/governance/owner/closing-thought")
async def get_closing():
    """Get closing thought"""
    return get_closing_thought()

@app.post("/governance/owner/validate-principle")
async def validate_principle(
    principle_number: int = Query(..., description="Principle number (1-10)"),
    scenario: str = Query(..., description="Scenario to validate")
):
    """Validate if a scenario adheres to a specific principle"""
    return validate_principle_adherence(principle_number, scenario)

@app.post("/governance/owner/check-confirmation")
async def check_confirmation(checklist_responses: Dict):
    """Check if all checklist items are confirmed"""
    return check_confirmation_status(checklist_responses)

# Governance Gate Endpoints (Enterprise Production Lock)
@app.post("/governance/gate/validate-integration")
async def validate_integration_request(
    integration_id: str = Query(..., description="Unique integration identifier"),
    integration_type: str = Query(..., description="Type of integration"),
    artifact_classes: List[str] = Query(..., description="Artifact classes to use"),
    product_name: str = Query(..., description="Product name"),
    data_schema: Dict = None
):
    """Validate integration request through governance gate"""
    if not data_schema:
        raise HTTPException(status_code=400, detail="data_schema required")
    
    result = await governance_gate.validate_integration(
        integration_id=integration_id,
        integration_type=integration_type,
        artifact_classes=artifact_classes,
        data_schema=data_schema,
        product_name=product_name
    )
    
    if result["decision"] == GovernanceDecision.REJECTED.value:
        raise HTTPException(status_code=403, detail={
            "message": "Integration rejected by governance gate",
            "reasons": result["reasons"],
            "threats": result.get("threats_found", [])
        })
    
    return result

@app.post("/governance/gate/validate-operation")
async def validate_operation_request(
    operation_type: str = Query(..., description="Operation type (CREATE/READ/UPDATE/DELETE)"),
    artifact_class: str = Query(..., description="Artifact class"),
    data_size: int = Query(..., description="Data size in bytes"),
    integration_id: str = Query(..., description="Integration ID")
):
    """Validate operation through governance gate"""
    
    result = governance_gate.validate_operation(
        operation_type=operation_type,
        artifact_class=artifact_class,
        data_size=data_size,
        integration_id=integration_id
    )
    
    if not result["allowed"]:
        raise HTTPException(status_code=403, detail={
            "message": "Operation not allowed",
            "reason": result["reason"]
        })
    
    return {"allowed": True, "message": "Operation validated"}

@app.get("/governance/gate/scale-limits")
async def get_scale_limits():
    """Get current scale limits (doc 15)"""
    from governance.governance_gate import SCALE_LIMITS
    return {
        "limits": SCALE_LIMITS,
        "description": "Scale limits enforced by governance gate",
        "reference": "docs/15_scale_readiness.md"
    }

@app.get("/governance/gate/product-rules")
async def get_product_rules():
    """Get product safety rules (doc 16)"""
    from governance.governance_gate import PRODUCT_RULES
    return {
        "rules": PRODUCT_RULES,
        "description": "Product-specific artifact class rules",
        "reference": "docs/16_multi_product_compatibility.md"
    }

@app.get("/governance/gate/operation-rules")
async def get_operation_rules():
    """Get operation rules for artifact classes (doc 04)"""
    from governance.governance_gate import OPERATION_RULES
    return {
        "rules": OPERATION_RULES,
        "description": "Allowed operations per artifact class",
        "reference": "docs/04_artifact_admission.md"
    }

@app.get("/governance/gate/status")
async def get_governance_gate_status():
    """Get governance gate status and statistics"""
    return {
        "status": "active",
        "approved_integrations": len(governance_gate.approved_integrations),
        "enforcement_level": "production",
        "certification": "enterprise_ready",
        "reference": "docs/18_bucket_enterprise_certification.md"
    }

# Threat Model Endpoints
@app.get("/governance/threats")
async def get_all_threats():
    """Get all threats from threat model (doc 14)"""
    from utils.threat_validator import BucketThreatModel
    return {
        "threats": BucketThreatModel.get_all_threats(),
        "total_threats": len(BucketThreatModel.THREATS),
        "reference": "docs/14_bucket_threat_model.md"
    }

@app.get("/governance/threats/{threat_id}")
async def get_threat_details(threat_id: str):
    """Get details for a specific threat"""
    from utils.threat_validator import BucketThreatModel
    
    threat = BucketThreatModel.get_threat(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail=f"Threat {threat_id} not found")
    
    return threat

@app.post("/governance/threats/scan")
async def scan_for_threats(data: Dict):
    """Scan data for threat patterns"""
    from utils.threat_validator import BucketThreatModel
    
    detected_threats = BucketThreatModel.scan_for_threats(data)
    has_critical = BucketThreatModel.has_critical_threats(detected_threats)
    
    return {
        "threats_detected": len(detected_threats),
        "has_critical_threats": has_critical,
        "threats": detected_threats,
        "recommendation": "BLOCK" if has_critical else "ALLOW"
    }

@app.get("/governance/threats/pattern/{pattern}")
async def find_threats_by_pattern(pattern: str):
    """Find threats matching a detection pattern"""
    from utils.threat_validator import BucketThreatModel
    
    matching_threats = BucketThreatModel.detect_threat_pattern(pattern)
    
    return {
        "pattern": pattern,
        "matching_threats": matching_threats,
        "count": len(matching_threats)
    }

# Scale Limits Endpoints
@app.get("/governance/scale/limits")
async def get_detailed_scale_limits():
    """Get detailed scale limits and performance targets (doc 15)"""
    from config.scale_limits import get_scale_limits_dict, get_performance_targets_dict
    
    return {
        "scale_limits": get_scale_limits_dict(),
        "performance_targets": get_performance_targets_dict(),
        "reference": "docs/15_scale_readiness.md",
        "enforcement": "hard_limits",
        "status": "production_active"
    }

@app.post("/governance/scale/validate")
async def validate_scale_operation(
    operation_type: str = Query(..., description="Operation type (read/write)"),
    data_size: int = Query(..., description="Data size in bytes"),
    frequency: int = Query(1, description="Operations per second")
):
    """Validate if operation is within scale limits"""
    from config.scale_limits import validate_operation_scale
    
    is_valid, error_message = validate_operation_scale(operation_type, data_size, frequency)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail={
            "message": "Operation exceeds scale limits",
            "error": error_message,
            "operation_type": operation_type,
            "data_size": data_size,
            "frequency": frequency
        })
    
    return {
        "valid": True,
        "message": "Operation within scale limits",
        "operation_type": operation_type,
        "data_size": data_size,
        "frequency": frequency
    }

@app.get("/governance/scale/proximity/{limit_name}")
async def check_limit_proximity(
    limit_name: str,
    current_value: int = Query(..., description="Current metric value")
):
    """Check how close current value is to scale limit"""
    from config.scale_limits import check_scale_limit_proximity
    
    result = check_scale_limit_proximity(current_value, limit_name)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/governance/scale/what-scales")
async def get_what_scales():
    """Get information about what scales safely and what doesn't"""
    from config.scale_limits import ScaleLimits
    
    limits = ScaleLimits()
    
    return {
        "scales_safely": limits.SCALES_SAFELY,
        "does_not_scale": limits.DOES_NOT_SCALE,
        "never_assume": limits.NEVER_ASSUME,
        "reference": "docs/15_scale_readiness.md"
    }

# Scale Monitoring Dashboard Endpoints (Document 15 - Real-time Monitoring)
@app.get("/metrics/scale-status")
async def get_scale_status_dashboard():
    """Real-time scale monitoring dashboard with all metrics"""
    from utils.scale_monitor import scale_monitor
    
    status = await scale_monitor.get_full_status()
    return status

@app.get("/metrics/concurrent-writes")
async def get_concurrent_writes_metric():
    """Get current concurrent writes status"""
    from utils.scale_monitor import scale_monitor
    
    return await scale_monitor.get_concurrent_writes_status()

@app.get("/metrics/storage-capacity")
async def get_storage_capacity_metric(
    used_gb: Optional[float] = Query(None, description="Current storage usage in GB")
):
    """Get storage capacity status with escalation paths"""
    from utils.scale_monitor import scale_monitor
    
    return await scale_monitor.get_storage_status(used_gb)

@app.get("/metrics/write-throughput")
async def get_write_throughput_metric():
    """Get write throughput status"""
    from utils.scale_monitor import scale_monitor
    
    return await scale_monitor.get_write_throughput_status()

@app.get("/metrics/query-performance")
async def get_query_performance_metric():
    """Get query performance metrics (p50, p99, p999)"""
    from utils.scale_monitor import scale_monitor
    
    return await scale_monitor.get_query_performance_status()

@app.get("/metrics/alerts")
async def get_active_alerts():
    """Get active scale alerts"""
    from utils.scale_monitor import scale_monitor
    
    alerts = await scale_monitor.check_and_alert()
    return {
        "active_alerts": alerts,
        "count": len(alerts),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/metrics/alert-history")
async def get_alert_history(
    limit: int = Query(50, ge=1, le=100, description="Number of alerts to retrieve")
):
    """Get alert history"""
    from utils.scale_monitor import scale_monitor
    
    history = scale_monitor.alert_history[-limit:]
    return {
        "alerts": history,
        "count": len(history),
        "total_in_history": len(scale_monitor.alert_history)
    }

@app.post("/metrics/record-query-latency")
async def record_query_latency(
    latency_ms: float = Query(..., description="Query latency in milliseconds")
):
    """Record a query latency measurement"""
    from utils.scale_monitor import scale_monitor
    
    await scale_monitor.record_query_latency(latency_ms)
    return {
        "success": True,
        "latency_ms": latency_ms,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }

@app.get("/governance/scale/certification")
async def get_scale_certification():
    """Get scale readiness certification status"""
    return {
        "certification": "ENTERPRISE_SCALE_READY",
        "certification_date": "2026-01-19",
        "certified_limits": {
            "artifact_size": "500 MB",
            "total_storage": "1000 GB (1 TB)",
            "concurrent_writes": "100 writers",
            "write_throughput": "1000 writes/sec",
            "artifact_count": "100,000 artifacts",
            "query_response": "<5 seconds",
            "audit_retention": "7 years (unlimited entries)"
        },
        "proof": {
            "artifact_size": "Tested 2026-01-19",
            "concurrent_writes": "Load tested 2026-01-19",
            "total_storage": "Supabase tier spec",
            "write_throughput": "Calculated limit",
            "artifact_count": "DB capacity estimate",
            "query_response": "SLA target"
        },
        "monitoring": {
            "real_time_dashboard": "/metrics/scale-status",
            "automated_alerts": "enabled",
            "graceful_degradation": "enabled",
            "escalation_paths": "defined"
        },
        "status": "PRODUCTION_ACTIVE",
        "review_cycle": "6 months",
        "next_review": "2026-07-19",
        "owner": "Ashmit_Pandey",
        "reference": "docs/15_scale_readiness.md"
    }

@app.get("/governance/scale/what-scales-safely")
async def get_what_scales_safely():
    """Get detailed information about what scales safely"""
    return {
        "scales_safely": [
            {
                "metric": "Concurrent Writes",
                "safe_limit": 100,
                "proof": "Load tested 2026-01-19",
                "status": "CERTIFIED",
                "monitoring": "/metrics/concurrent-writes"
            },
            {
                "metric": "Artifact Size",
                "safe_limit": "500 MB",
                "proof": "HTTP + DB limits tested",
                "status": "CERTIFIED",
                "validation": "Enforced at API layer"
            },
            {
                "metric": "Total Storage",
                "safe_limit": "1000 GB",
                "proof": "Supabase PostgreSQL tier",
                "status": "CERTIFIED",
                "monitoring": "/metrics/storage-capacity"
            },
            {
                "metric": "Write Throughput",
                "safe_limit": "1000 writes/sec",
                "proof": "DB connection pool calculation",
                "status": "CERTIFIED (theoretical)",
                "monitoring": "/metrics/write-throughput"
            },
            {
                "metric": "Audit Trail",
                "safe_limit": "Unlimited (7 year retention)",
                "proof": "Append-only design",
                "status": "CERTIFIED",
                "growth": "~350 MB over 7 years"
            },
            {
                "metric": "Multi-Product Isolation",
                "safe_limit": "4 products certified",
                "proof": "Product certification matrix",
                "status": "CERTIFIED",
                "products": ["AI_ASSISTANT", "AI_AVATAR", "GURUKUL", "ENFORCEMENT"]
            },
            {
                "metric": "Query Performance",
                "safe_limit": "<5 seconds",
                "proof": "Database query optimization",
                "status": "CERTIFIED",
                "monitoring": "/metrics/query-performance"
            }
        ],
        "reference": "docs/15_scale_readiness.md"
    }

@app.get("/governance/scale/what-does-not-scale")
async def get_what_does_not_scale():
    """Get information about what does NOT scale yet"""
    return {
        "does_not_scale": [
            {
                "operation": "Real-time queries across all products",
                "reason": "Would require full-table scan",
                "workaround": "Query by product_id, aggregate in application",
                "future_plan": "Materialized views per product (Phase 2)"
            },
            {
                "operation": "Distributed read-heavy operations",
                "reason": "Bucket designed as write-only sink",
                "workaround": "Copy artifacts to read-optimized storage",
                "future_plan": "Read replica for analytics (Phase 2)"
            },
            {
                "operation": "Multi-region replication",
                "reason": "Single region (India), legal hold on data",
                "workaround": "Single-region with daily backups",
                "future_plan": "Evaluate after legal review (Phase 3)"
            },
            {
                "operation": "Schema migrations",
                "reason": "Schema is immutable by constitutional design",
                "workaround": "Create new artifact type",
                "status": "PERMANENTLY_BLOCKED"
            },
            {
                "operation": "Conditional writes",
                "reason": "Append-only semantics",
                "workaround": "Create new artifact, keep old in audit",
                "status": "NOT_SUPPORTED"
            }
        ],
        "reference": "docs/15_scale_readiness.md"
    }

@app.get("/governance/scale/never-assume")
async def get_never_assume():
    """Get critical assumptions that must NEVER be made"""
    return {
        "never_assume": [
            {
                "assumption": "Eventual consistency without bounds",
                "reality": "All writes are immediately consistent",
                "guarantee": "Synchronous writes with immediate visibility",
                "status": "ENFORCED"
            },
            {
                "assumption": "Automatic schema migrations",
                "reality": "Schema is immutable",
                "requirement": "Manual review + governance approval",
                "status": "ENFORCED"
            },
            {
                "assumption": "Backfill on failure",
                "reality": "Client must retry failed writes",
                "guarantee": "Exactly-once semantics",
                "status": "ENFORCED"
            },
            {
                "assumption": "Performance improvement without limits",
                "reality": "All optimizations must be load-tested",
                "requirement": "Test at 2x max expected load",
                "status": "ENFORCED"
            },
            {
                "assumption": "Governance relaxation for emergency",
                "reality": "Zero governance exceptions",
                "override": "CEO-only with post-review",
                "status": "CONSTITUTIONAL"
            }
        ],
        "reference": "docs/15_scale_readiness.md"
    }

@app.get("/governance/scale/thresholds")
async def get_scale_thresholds():
    """Get scale thresholds and alert levels"""
    return {
        "concurrent_writes": {
            "GREEN": "0-50 writers (safe)",
            "YELLOW": "51-75 writers (monitor)",
            "ORANGE": "76-99 writers (alert)",
            "RED": "100+ writers (pause new writes)"
        },
        "storage_capacity": {
            "GREEN": "0-70% (safe)",
            "YELLOW": "70-90% (plan expansion)",
            "ORANGE": "90-99% (critical - 6 hour response)",
            "RED": "99-100% (halt writes - immediate response)"
        },
        "write_throughput": {
            "GREEN": "0-500 writes/sec (safe)",
            "YELLOW": "501-800 writes/sec (monitor)",
            "ORANGE": "801-1000 writes/sec (alert)",
            "RED": "1000+ writes/sec (throttle)"
        },
        "query_latency": {
            "GREEN": "p99 < 100ms (excellent)",
            "YELLOW": "p99 100-200ms (acceptable)",
            "ORANGE": "p99 200-500ms (degraded)",
            "RED": "p99 > 500ms (SLA breach)"
        },
        "escalation_paths": {
            "storage_90_percent": "Ops_Team (6 hours)",
            "storage_99_percent": "Ashmit_Pandey (1 hour)",
            "storage_100_percent": "Ashmit_Pandey + Ops (IMMEDIATE)",
            "concurrent_writes_100": "Ops_Team (IMMEDIATE)",
            "query_sla_breach": "Ops_Team (1 hour)"
        },
        "reference": "docs/15_scale_readiness.md"
    }

# Audit Middleware Endpoints
@app.get("/audit/artifact/{artifact_id}")
async def get_artifact_audit_history(
    artifact_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """Get complete audit history for an artifact"""
    history = await audit_middleware.get_artifact_history(artifact_id, limit)
    return {
        "artifact_id": artifact_id,
        "history": history,
        "count": len(history)
    }

@app.get("/audit/user/{requester_id}")
async def get_user_audit_activities(
    requester_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """Get all operations performed by a user"""
    activities = await audit_middleware.get_user_activities(requester_id, limit)
    return {
        "requester_id": requester_id,
        "activities": activities,
        "count": len(activities)
    }

@app.get("/audit/recent")
async def get_recent_audit_operations(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type")
):
    """Get recent operations across all artifacts"""
    operations = await audit_middleware.get_recent_operations(limit, operation_type)
    return {
        "operations": operations,
        "count": len(operations),
        "filter": {"operation_type": operation_type} if operation_type else None
    }

@app.get("/audit/failed")
async def get_failed_audit_operations(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """Get recent failed operations for incident response"""
    operations = await audit_middleware.get_failed_operations(limit)
    return {
        "failed_operations": operations,
        "count": len(operations),
        "severity": "high" if len(operations) > 10 else "normal"
    }

@app.post("/audit/validate-immutability/{artifact_id}")
async def validate_artifact_immutability(artifact_id: str):
    """Verify that artifact has not been modified since creation"""
    is_immutable = await audit_middleware.validate_immutability(artifact_id)
    return {
        "artifact_id": artifact_id,
        "is_immutable": is_immutable,
        "status": "valid" if is_immutable else "violation_detected"
    }

@app.post("/audit/log")
async def create_audit_log(
    operation_type: str = Query(..., description="Operation type (CREATE/READ/UPDATE/DELETE)"),
    artifact_id: str = Query(..., description="Artifact ID"),
    requester_id: str = Query(..., description="User/system performing operation"),
    integration_id: str = Query(..., description="Integration ID"),
    data_before: Optional[Dict] = None,
    data_after: Optional[Dict] = None,
    status: str = Query("success", description="Operation status"),
    error_message: Optional[str] = Query(None, description="Error message if failed")
):
    """Manually create an audit log entry"""
    audit_id = await audit_middleware.log_operation(
        operation_type=operation_type,
        artifact_id=artifact_id,
        requester_id=requester_id,
        integration_id=integration_id,
        data_before=data_before,
        data_after=data_after,
        status=status,
        error_message=error_message
    )
    
    if audit_id:
        return {
            "success": True,
            "audit_id": audit_id,
            "message": "Audit entry created successfully"
        }
    else:
        raise HTTPException(status_code=503, detail="Audit service unavailable")

# Comprehensive Threat Handling Endpoints (Document 14 - Full Implementation)
@app.post("/governance/threats/scan-with-context")
async def scan_threats_with_context(
    data: Dict,
    actor: Optional[str] = Query(None, description="Actor performing operation"),
    operation_type: Optional[str] = Query(None, description="Operation type"),
    target_type: Optional[str] = Query(None, description="Target type (e.g., audit_log)"),
    override_attempted: bool = Query(False, description="Whether override was attempted")
):
    """Scan for threats with full context and escalation paths"""
    from utils.threat_validator import BucketThreatModel
    
    context = {
        "actor": actor,
        "operation_type": operation_type,
        "target_type": target_type,
        "override_attempted": override_attempted
    }
    
    detected_threats = BucketThreatModel.scan_for_threats(data, context)
    has_critical = BucketThreatModel.has_critical_threats(detected_threats)
    
    # Determine action based on threat level
    if has_critical:
        action = "HALT_OPERATIONS"
        status_code = 403
    else:
        action = "ALLOW_WITH_MONITORING"
        status_code = 200
    
    response = {
        "threats_detected": len(detected_threats),
        "has_critical_threats": has_critical,
        "threats": detected_threats,
        "action": action,
        "escalation_required": has_critical,
        "context": context
    }
    
    if has_critical:
        # Log critical threat detection
        logger.critical(f"Critical threats detected: {detected_threats}")
        await audit_middleware.log_operation(
            operation_type="THREAT_DETECTED",
            artifact_id="system",
            requester_id=actor or "unknown",
            integration_id="threat_scanner",
            data_after={"threats": detected_threats},
            status="blocked",
            error_message="Critical threats detected"
        )
    
    if has_critical:
        raise HTTPException(status_code=status_code, detail=response)
    
    return response

@app.post("/governance/threats/check-storage-exhaustion")
async def check_storage_exhaustion(
    used_gb: float = Query(..., description="Current storage usage in GB"),
    total_gb: Optional[float] = Query(None, description="Total capacity in GB")
):
    """Check for storage exhaustion threat (T1)"""
    from config.scale_limits import ScaleLimits
    
    capacity_status = ScaleLimits.check_storage_capacity(used_gb, total_gb)
    
    if capacity_status["status"] == "CRITICAL":
        logger.critical(f"Storage exhaustion detected: {capacity_status}")
        await audit_middleware.log_operation(
            operation_type="STORAGE_ALERT",
            artifact_id="system",
            requester_id="system",
            integration_id="storage_monitor",
            data_after=capacity_status,
            status="critical"
        )
    
    return {
        "threat_id": "T1_STORAGE_EXHAUSTION",
        "capacity_status": capacity_status,
        "escalation_required": capacity_status["status"] in ["CRITICAL", "WARNING"],
        "escalation_path": capacity_status.get("escalation_path"),
        "response_timeline": capacity_status.get("response_timeline")
    }

@app.post("/governance/threats/check-executor-override")
async def check_executor_override(
    actor: str = Query(..., description="Actor attempting operation"),
    requested_action: str = Query(..., description="Action being requested"),
    governance_scope: bool = Query(False, description="Is this within governance scope?")
):
    """Check for executor authority violation (T5)"""
    
    # Check if executor is attempting unauthorized action
    is_executor = actor == "akanksha_parab"
    is_violation = is_executor and not governance_scope
    
    if is_violation:
        threat = {
            "threat_id": "T5_EXECUTOR_OVERRIDE",
            "name": "Executor Authority Violation",
            "level": "critical",
            "description": f"Executor attempted action outside defined scope: {requested_action}",
            "escalation": "Vijay_Dhawan",
            "action": "BLOCK_AND_ESCALATE"
        }
        
        logger.critical(f"Executor override detected: {threat}")
        await audit_middleware.log_operation(
            operation_type="EXECUTOR_OVERRIDE_ATTEMPT",
            artifact_id="system",
            requester_id=actor,
            integration_id="governance_gate",
            data_after={"requested_action": requested_action},
            status="blocked",
            error_message="Executor authority violation"
        )
        
        raise HTTPException(status_code=403, detail={
            "threat": threat,
            "message": "Operation blocked - executor authority violation",
            "escalation_required": True
        })
    
    return {
        "allowed": True,
        "actor": actor,
        "is_executor": is_executor,
        "within_scope": governance_scope
    }

@app.post("/governance/threats/check-ai-escalation")
async def check_ai_escalation(
    actor: str = Query(..., description="Actor requesting operation"),
    requested_operation: str = Query(..., description="Operation being requested")
):
    """Check for AI authority escalation (T6)"""
    
    is_ai_actor = actor.startswith("ai_")
    allowed_operations = ["WRITE", "APPEND_AUDIT"]
    is_escalation = is_ai_actor and requested_operation not in allowed_operations
    
    if is_escalation:
        threat = {
            "threat_id": "T6_AI_ESCALATION",
            "name": "AI Authority Escalation",
            "level": "critical",
            "description": f"AI actor {actor} requested unauthorized operation: {requested_operation}",
            "escalation": "Vijay_Dhawan",
            "action": "REJECT_AND_ALERT"
        }
        
        logger.critical(f"AI escalation detected: {threat}")
        await audit_middleware.log_operation(
            operation_type="AI_ESCALATION_ATTEMPT",
            artifact_id="system",
            requester_id=actor,
            integration_id="governance_gate",
            data_after={"requested_operation": requested_operation},
            status="blocked",
            error_message="AI authority escalation attempt"
        )
        
        raise HTTPException(status_code=403, detail={
            "threat": threat,
            "message": "Operation blocked - AI escalation attempt",
            "escalation_required": True
        })
    
    return {
        "allowed": True,
        "actor": actor,
        "is_ai_actor": is_ai_actor,
        "operation": requested_operation
    }

@app.post("/governance/threats/check-audit-tampering")
async def check_audit_tampering(
    operation_type: str = Query(..., description="Operation type"),
    target_type: str = Query(..., description="Target type"),
    actor: str = Query(..., description="Actor attempting operation")
):
    """Check for audit trail tampering attempt (T8)"""
    
    is_tampering = operation_type in ["DELETE", "UPDATE"] and target_type == "audit_log"
    
    if is_tampering:
        threat = {
            "threat_id": "T8_AUDIT_TAMPERING",
            "name": "Audit Trail Tampering Attempt",
            "level": "critical",
            "description": f"Attempt to {operation_type} audit logs by {actor}",
            "escalation": "CEO",
            "action": "HALT_AND_INVESTIGATE"
        }
        
        logger.critical(f"AUDIT TAMPERING DETECTED: {threat}")
        # Log to separate system logs (not the audit trail being tampered with)
        
        raise HTTPException(status_code=403, detail={
            "threat": threat,
            "message": "CRITICAL: Audit tampering attempt detected",
            "escalation_required": True,
            "severity": "MAXIMUM"
        })
    
    return {
        "allowed": True,
        "operation_type": operation_type,
        "target_type": target_type
    }

@app.post("/governance/threats/check-cross-product-leak")
async def check_cross_product_leak(
    product_id: str = Query(..., description="Product making request"),
    requested_product_data: str = Query(..., description="Product data being accessed"),
    artifact_type: str = Query(..., description="Artifact type")
):
    """Check for cross-product data leakage (T9)"""
    
    is_cross_product = product_id != requested_product_data
    
    if is_cross_product:
        threat = {
            "threat_id": "T9_CROSS_PRODUCT_LEAK",
            "name": "Cross-Product Access Attempt",
            "level": "critical",
            "description": f"Product {product_id} attempted to access {requested_product_data} data",
            "escalation": "Security_Team",
            "action": "REJECT_OPERATION"
        }
        
        logger.critical(f"Cross-product leak detected: {threat}")
        await audit_middleware.log_operation(
            operation_type="CROSS_PRODUCT_ACCESS",
            artifact_id="system",
            requester_id=product_id,
            integration_id="governance_gate",
            data_after={
                "product_id": product_id,
                "requested_product": requested_product_data,
                "artifact_type": artifact_type
            },
            status="blocked",
            error_message="Cross-product access violation"
        )
        
        raise HTTPException(status_code=403, detail={
            "threat": threat,
            "message": "Operation blocked - cross-product isolation violation",
            "escalation_required": True
        })
    
    return {
        "allowed": True,
        "product_id": product_id,
        "isolation_maintained": True
    }

@app.get("/governance/threats/escalation-matrix")
async def get_threat_escalation_matrix():
    """Get complete threat escalation matrix with response timelines"""
    return {
        "escalation_matrix": [
            {
                "threat_id": "T1_STORAGE_EXHAUSTION",
                "severity": "HIGH",
                "escalation_path": "Ops_Team -> Ashmit_Pandey",
                "response_timeline": "90%: 6 hours, 99%: 1 hour, 100%: IMMEDIATE",
                "automated_action": "HALT_WRITES at 100%"
            },
            {
                "threat_id": "T2_METADATA_POISONING",
                "severity": "CRITICAL",
                "escalation_path": "CEO",
                "response_timeline": "IMMEDIATE",
                "automated_action": "REJECT_OPERATION"
            },
            {
                "threat_id": "T3_SCHEMA_EVOLUTION",
                "severity": "HIGH",
                "escalation_path": "Vijay_Dhawan",
                "response_timeline": "24 hours",
                "automated_action": "REQUIRE_REVIEW"
            },
            {
                "threat_id": "T5_EXECUTOR_OVERRIDE",
                "severity": "CRITICAL",
                "escalation_path": "Vijay_Dhawan",
                "response_timeline": "IMMEDIATE",
                "automated_action": "BLOCK_AND_ESCALATE"
            },
            {
                "threat_id": "T6_AI_ESCALATION",
                "severity": "CRITICAL",
                "escalation_path": "Vijay_Dhawan",
                "response_timeline": "IMMEDIATE",
                "automated_action": "REJECT_AND_ALERT"
            },
            {
                "threat_id": "T7_CROSS_PRODUCT_CONTAMINATION",
                "severity": "HIGH",
                "escalation_path": "Security_Team",
                "response_timeline": "1 hour",
                "automated_action": "REJECT_OPERATION"
            },
            {
                "threat_id": "T8_AUDIT_TAMPERING",
                "severity": "CRITICAL",
                "escalation_path": "CEO",
                "response_timeline": "IMMEDIATE",
                "automated_action": "HALT_AND_INVESTIGATE"
            },
            {
                "threat_id": "T9_OWNERSHIP_CHALLENGE",
                "severity": "HIGH",
                "escalation_path": "CEO + Legal",
                "response_timeline": "As required by legal process",
                "automated_action": "PRESERVE_EVIDENCE"
            },
            {
                "threat_id": "T10_PROVENANCE_OVERTRUST",
                "severity": "MEDIUM",
                "escalation_path": "Vijay_Dhawan",
                "response_timeline": "48 hours",
                "automated_action": "VERIFY_METADATA"
            }
        ],
        "certification": "All threats have automated detection and escalation paths",
        "reference": "docs/14_bucket_threat_model.md"
    }

@app.get("/governance/threats/certification-status")
async def get_threat_certification_status():
    """Get threat model certification status"""
    return {
        "certification": "PRODUCTION_READY",
        "total_threats_identified": 10,
        "threats_mitigated": 7,
        "threats_partially_mitigated": 2,
        "threats_requiring_process_change": 1,
        "automated_detection": "ALL_THREATS",
        "automated_escalation": "ALL_THREATS",
        "zero_acceptable_risks": True,
        "governance_violations_halt_operations": True,
        "certification_date": "2026-01-19",
        "review_cycle": "6_months",
        "next_review": "2026-07-19",
        "bucket_owner": "Ashmit_Pandey",
        "status": "CERTIFIED_FOR_PRODUCTION",
        "reference": "docs/14_bucket_threat_model.md"
    }

# ============================================================================
# CONSTITUTIONAL GOVERNANCE ENDPOINTS (Core-Bucket Boundaries)
# ============================================================================

@app.post("/constitutional/core/validate-request")
async def validate_core_request(
    requester_id: str = Query(..., description="ID of requesting system (must be bhiv_core)"),
    operation_type: str = Query(..., description="Operation type (READ/WRITE/QUERY/etc)"),
    target_resource: str = Query(..., description="Resource being accessed"),
    request_data: Dict = None,
    context: Optional[Dict] = None
):
    """
    Validate Core request against constitutional boundaries
    Enforces sovereignty and prevents unauthorized operations
    """
    if not request_data:
        raise HTTPException(status_code=400, detail="request_data required")
    
    validation_result = core_boundary_enforcer.validate_request(
        requester_id=requester_id,
        operation_type=operation_type,
        target_resource=target_resource,
        request_data=request_data,
        context=context or {}
    )
    
    if not validation_result["allowed"]:
        for violation in validation_result["violations"]:
            core_violation_handler.handle_violation(
                violation_type=violation["type"],
                severity=violation["severity"],
                details=violation,
                requester_id=requester_id,
                context={"operation": operation_type, "resource": target_resource}
            )
        
        raise HTTPException(status_code=403, detail={
            "message": "Request violates constitutional boundaries",
            "violations": validation_result["violations"],
            "allowed": False
        })
    
    return {
        "allowed": True,
        "message": "Request validated successfully",
        "validation_result": validation_result
    }

@app.post("/constitutional/core/validate-input")
async def validate_core_input(
    channel: str = Query(..., description="Input channel (artifact_write/metadata_query/etc)"),
    requester_id: str = Query(..., description="ID of requesting system"),
    data: Dict = None
):
    """
    Validate Core input against API contract
    Ensures data format compliance
    """
    if not data:
        raise HTTPException(status_code=400, detail="data required")
    
    validation_result = core_api_contract.validate_input(
        channel=channel,
        data=data,
        requester_id=requester_id
    )
    
    if not validation_result["valid"]:
        raise HTTPException(status_code=400, detail={
            "message": "Input validation failed",
            "violations": validation_result["violations"]
        })
    
    return {
        "valid": True,
        "message": "Input validated successfully",
        "channel": channel
    }

@app.post("/constitutional/core/validate-output")
async def validate_core_output(
    channel: str = Query(..., description="Output channel (artifact_read/query_result/etc)"),
    data: Dict = None
):
    """
    Validate Bucket output to Core against API contract
    Ensures response format compliance
    """
    if not data:
        raise HTTPException(status_code=400, detail="data required")
    
    validation_result = core_api_contract.validate_output(
        channel=channel,
        data=data
    )
    
    if not validation_result["valid"]:
        raise HTTPException(status_code=400, detail={
            "message": "Output validation failed",
            "violations": validation_result["violations"]
        })
    
    return {
        "valid": True,
        "message": "Output validated successfully",
        "channel": channel
    }

@app.get("/constitutional/core/capabilities")
async def get_core_capabilities():
    """
    Get allowed Core capabilities
    Returns list of operations Core is authorized to perform
    """
    return {
        "allowed_capabilities": [cap.value for cap in CoreCapability],
        "prohibited_actions": [action.value for action in ProhibitedAction],
        "description": "Constitutional boundaries between Core and Bucket",
        "enforcement": "automatic",
        "reference": "docs/constitutional/BHIV_CORE_BUCKET_BOUNDARIES.md"
    }

@app.get("/constitutional/core/contract")
async def get_core_contract():
    """
    Get complete Core-Bucket API contract
    Returns input/output channels and schemas
    """
    return core_api_contract.get_contract_documentation()

@app.get("/constitutional/violations/summary")
async def get_violations_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """
    Get summary of boundary violations
    Returns violation statistics and trends
    """
    boundary_summary = core_boundary_enforcer.get_violation_summary(hours)
    handler_report = core_violation_handler.get_violation_report(hours)
    
    return {
        "period_hours": hours,
        "boundary_violations": boundary_summary,
        "detailed_report": handler_report,
        "status": "critical" if boundary_summary["critical_count"] > 0 else "normal"
    }

@app.get("/constitutional/violations/report")
async def get_violations_report(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """
    Get detailed violation report
    Includes escalations, responses, and trends
    """
    return core_violation_handler.get_violation_report(hours)

@app.post("/constitutional/violations/handle")
async def handle_violation_manually(
    violation_type: str = Query(..., description="Type of violation"),
    severity: str = Query(..., description="Severity (low/medium/high/critical)"),
    requester_id: str = Query(..., description="ID of violating system"),
    details: Dict = None,
    context: Optional[Dict] = None
):
    """
    Manually report and handle a boundary violation
    Used for violations detected outside automated checks
    """
    if not details:
        raise HTTPException(status_code=400, detail="details required")
    
    response = core_violation_handler.handle_violation(
        violation_type=violation_type,
        severity=severity,
        details=details,
        requester_id=requester_id,
        context=context or {}
    )
    
    return {
        "success": True,
        "violation_handled": response,
        "message": "Violation logged and escalated as appropriate"
    }

@app.get("/constitutional/status")
async def get_constitutional_status():
    """
    Get overall constitutional governance status
    Returns health of boundary enforcement system
    """
    recent_violations = core_boundary_enforcer.get_violation_summary(24)
    
    return {
        "status": "active",
        "enforcement": "enabled",
        "boundaries_locked": True,
        "recent_violations_24h": recent_violations["total_violations"],
        "critical_violations_24h": recent_violations["critical_count"],
        "allowed_capabilities": len([cap for cap in CoreCapability]),
        "prohibited_actions": len([action for action in ProhibitedAction]),
        "input_channels": len([ch for ch in InputChannel]),
        "output_channels": len([ch for ch in OutputChannel]),
        "certification": "constitutional_governance_active",
        "reference": "docs/constitutional/"
    }

# Law Agent Endpoints
@app.post("/basic-query")
async def process_basic_query(request: BasicLegalQueryRequest):
    """Process a legal query using the basic agent"""
    try:
        # Use the existing run-agent endpoint internally
        agent_input = AgentInput(
            agent_name="law_agent",
            input_data={
                "query": request.user_input,
                "agent_type": "basic",
                "feedback": request.feedback
            },
            stateful=False
        )
        return await run_agent(agent_input)
    except Exception as e:
        logger.error(f"Basic query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/adaptive-query")
async def process_adaptive_query(request: AdaptiveLegalQueryRequest):
    """Process a legal query using the adaptive agent"""
    try:
        agent_input = AgentInput(
            agent_name="law_agent",
            input_data={
                "query": request.user_input,
                "agent_type": "adaptive",
                "feedback": request.feedback
            },
            stateful=False
        )
        return await run_agent(agent_input)
    except Exception as e:
        logger.error(f"Adaptive query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enhanced-query")
async def process_enhanced_query(request: EnhancedLegalQueryRequest):
    """Process a legal query using the enhanced agent"""
    try:
        agent_input = AgentInput(
            agent_name="law_agent",
            input_data={
                "query": request.user_input,
                "agent_type": "enhanced",
                "location": request.location,
                "feedback": request.feedback
            },
            stateful=False
        )
        return await run_agent(agent_input)
    except Exception as e:
        logger.error(f"Enhanced query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("FASTAPI_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
