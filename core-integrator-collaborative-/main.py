from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
import os
import sqlite3
import logging
from pathlib import Path
from src.core.models import CoreRequest, CoreResponse
from src.core.feedback_models import FeedbackRequest
from src.core.gateway import Gateway
from src.db.memory import ContextMemory
from config.config import DB_PATH, validate_config, get_config_summary
from src.utils.security_hardening import security_middleware, validate_user_request, security
from src.utils.auth import auth_middleware, require_auth
from src.utils.observability import new_trace_id, observability_middleware
import asyncio

# Validate configuration on startup
validate_config()

# Log startup summary
config_summary = get_config_summary()
logging.info("Core Integrator startup", extra={"config_summary": config_summary})

# Optional SSPL - can be disabled for testing
SSPL_ENABLED = os.getenv("SSPL_ENABLED", "false").lower() in ("true", "1", "yes")

if SSPL_ENABLED:
    from src.utils.sspl_dependency import require_sspl
else:
    async def require_sspl():
        return True

app = FastAPI(
    title="Unified Backend Bridge",
    description="Central orchestration layer for Finance, Education, and Creator agents",
    version="1.0.0"
)

# Middleware order: last-added runs first in FastAPI (LIFO).
# Execution order: observability → auth → security
app.middleware("http")(security_middleware)
app.middleware("http")(auth_middleware)
app.middleware("http")(observability_middleware)

# Initialize gateway and memory
gateway = Gateway()
memory = ContextMemory(DB_PATH)

@app.post("/core", response_model=CoreResponse)
async def core_endpoint(request: CoreRequest, http_request: Request, _auth=Depends(require_auth), _sspl=Depends(require_sspl)) -> CoreResponse:
    """Main gateway endpoint for processing agent requests"""
    try:
        # Security validation
        validated_user_id = validate_user_request(request.user_id, http_request)
        
        response = gateway.process_request(
            module=request.module,
            intent=request.intent, 
            user_id=validated_user_id,
            data=request.data
        )
        
        # Validate response structure
        if not isinstance(response, dict) or 'status' not in response:
            raise HTTPException(status_code=500, detail="Processing failed")
        
        # Sanitize response
        sanitized_response = security.sanitize_response(response)
        sanitized_response.setdefault('message', 'Request processed')
        sanitized_response.setdefault('result', {})
        
        return CoreResponse(**sanitized_response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Processing failed")

@app.get("/get-history")
async def get_history(user_id: str, request: Request, _auth=Depends(require_auth)) -> List[Dict[str, Any]]:
    """Get full interaction history for a user"""
    try:
        # Security validation
        validated_user_id = validate_user_request(user_id, request)
        
        history = memory.get_user_history(validated_user_id)
        
        # Limit and sanitize history
        limited_history = history[:10]  # Limit to 10 most recent
        sanitized_history = []
        
        for item in limited_history:
            sanitized_item = {
                "module": item.get("module"),
                "timestamp": item.get("timestamp"),
                "response": security.sanitize_response(item.get("response", {}))
            }
            sanitized_history.append(sanitized_item)
            
        return sanitized_history
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="History retrieval failed")

@app.get("/get-context") 
async def get_context(user_id: str, request: Request, _auth=Depends(require_auth)) -> List[Dict[str, Any]]:
    """Get recent context (last 3 interactions) for a user"""
    try:
        # Security validation
        validated_user_id = validate_user_request(user_id, request)
        
        context = memory.get_context(validated_user_id)
        
        # Sanitize context data
        sanitized_context = []
        for item in context:
            sanitized_item = {
                "module": item.get("module"),
                "timestamp": item.get("timestamp"),
                "response": security.sanitize_response(item.get("response", {}))
            }
            sanitized_context.append(sanitized_item)
            
        return sanitized_context
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Context retrieval failed")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Unified Backend Bridge API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/system/health")
async def system_health():
    """System health check - binary status with explicit dependency checks"""
    try:
        # Check database connectivity
        database_status = "up"
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT 1").fetchone()
        except Exception:
            database_status = "down"

        # Check gateway initialization
        gateway_status = "up" if gateway is not None else "down"

        # Check external services
        noopur_status = "disabled"
        if os.getenv("INTEGRATOR_USE_NOOPUR", "false").lower() in ("1", "true", "yes"):
            try:
                from src.utils.noopur_client import NoopurClient
                noopur_client = NoopurClient()
                noopur_status = await noopur_client.health_check()
            except Exception:
                noopur_status = "down"

        video_service_status = "disabled"
        if not os.getenv("DISABLE_VIDEO_SERVICE", "false").lower() in ("true", "1", "yes"):
            try:
                # Check video service health
                video_health = gateway.video_bridge_client.generate_video("test")
                video_service_status = "up" if not video_health.get("fallback_used", True) else "down"
            except Exception:
                video_service_status = "down"

        # Determine overall status
        dependencies = [database_status, gateway_status]
        if noopur_status != "disabled":
            dependencies.append(noopur_status)
        if video_service_status != "disabled":
            dependencies.append(video_service_status)

        overall_status = "ok" if all(dep in ["up", "disabled"] for dep in dependencies) else "down"

        return {
            "status": overall_status,
            "dependencies": {
                "database": database_status,
                "gateway": gateway_status,
                "noopur": noopur_status,
                "video_service": video_service_status
            },
            "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
            "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        }

@app.get("/system/diagnostics")
async def system_diagnostics(_auth=Depends(require_auth)):
    """System diagnostics - internal details for monitoring"""
    try:
        import time

        # Measure database latency
        db_latency = None
        db_status = "unknown"
        try:
            start_time = time.time()
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT 1").fetchone()
            db_latency = round((time.time() - start_time) * 1000, 2)  # ms
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

        # Get configuration summary
        config = get_config_summary()

        # Check agent/module status
        agent_status = {}
        for name, agent in gateway.agents.items():
            agent_status[name] = "loaded" if agent is not None else "failed"

        # Memory adapter info
        memory_adapter = type(gateway.memory).__name__

        return {
            "config": {
                "db_mode": config.get("db_mode"),
                "noopur_enabled": config.get("noopur_enabled"),
                "log_level": config.get("log_level"),
                "sspl_enabled": config.get("sspl_enabled")
            },
            "database": {
                "status": db_status,
                "latency_ms": db_latency
            },
            "agents": agent_status,
            "feature_flags": {
                "sspl_enabled": os.getenv("SSPL_ENABLED", "false").lower() in ("1", "true", "yes"),
                "noopur_integration": config["noopur_enabled"],
                "mongodb_enabled": config["db_mode"] == "mongodb"
            },
            "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        }

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest, http_request: Request, _auth=Depends(require_auth), _sspl=Depends(require_sspl)):
    """Submit feedback for generated content"""
    try:
        # Security validation
        user_id = request.user_id or "anonymous"
        if user_id != "anonymous":
            user_id = validate_user_request(user_id, http_request)
            
        response = gateway.process_request(
            module="creator",
            intent="feedback",
            user_id=user_id,
            data=request.dict()
        )
        
        # Sanitize response
        sanitized_response = security.sanitize_response(response)
        return sanitized_response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Feedback processing failed")

@app.get("/creator/history")
async def get_creator_history(user_id: str, request: Request, _auth=Depends(require_auth)):
    """Get creator generation history"""
    try:
        # Security validation - no "all" access allowed
        if user_id == "all":
            raise HTTPException(status_code=400, detail="Invalid user identifier")
            
        validated_user_id = validate_user_request(user_id, request)
        
        response = gateway.process_request(
            module="creator",
            intent="history",
            user_id=validated_user_id,
            data={}
        )
        
        # Sanitize response
        sanitized_response = security.sanitize_response(response)
        return sanitized_response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="History retrieval failed")

@app.get("/system/logs/latest")
async def system_logs_latest(limit: int = 50, _auth=Depends(require_auth)):
    """Get latest log entries (authenticated, max 200 lines)"""
    limit = max(1, min(limit, 200))  # enforce hard cap""
    log_dir = Path("logs/bridge")
    if not log_dir.exists():
        return {"logs": [], "message": "No logs available"}
    
    log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not log_files:
        return {"logs": [], "message": "No log files found"}
    
    latest_log = log_files[0]
    try:
        with open(latest_log, 'r') as f:
            lines = f.readlines()[-limit:]
        return {
            "log_file": str(latest_log),
            "entries": [line.strip() for line in lines],
            "count": len(lines)
        }
    except Exception as e:
        return {"error": str(e)}

# NEW LINEAGE AND REPLAY ENDPOINTS

@app.get("/lineage/{instruction_id}")
async def get_instruction_lineage(instruction_id: str, request: Request, _auth=Depends(require_auth)):
    """Get complete lineage for an instruction"""
    try:
        lineage = gateway.lineage_manager.get_instruction_lineage(instruction_id)
        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lineage retrieval failed: {str(e)}")

@app.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str, request: Request, _auth=Depends(require_auth)):
    """Get artifact by ID"""
    try:
        artifact = gateway.bucket_reader.get_artifact_by_id(artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return artifact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Artifact retrieval failed: {str(e)}")

@app.get("/artifacts/instruction/{instruction_id}")
async def get_instruction_artifacts(instruction_id: str, request: Request, _auth=Depends(require_auth)):
    """Get all artifacts for an instruction"""
    try:
        artifacts = gateway.bucket_reader.get_artifacts_by_instruction(instruction_id)
        return {"instruction_id": instruction_id, "artifacts": artifacts, "count": len(artifacts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Artifacts retrieval failed: {str(e)}")

@app.post("/replay/{instruction_id}")
async def replay_instruction(instruction_id: str, request: Request, _auth=Depends(require_auth)):
    """Replay an instruction deterministically"""
    try:
        if gateway.replay_engine is None:
            from src.core.routing_engine import RoutingEngine
            from src.core.replay_engine import ReplayEngine
            routing_engine = RoutingEngine(gateway.agents, gateway.memory)
            gateway.replay_engine = ReplayEngine(gateway.lineage_manager, routing_engine, gateway.memory)
        
        replay_result = gateway.replay_engine.replay_instruction(instruction_id)
        return replay_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(e)}")

@app.get("/replay/validate/{instruction_id}")
async def validate_replay_capability(instruction_id: str, request: Request, _auth=Depends(require_auth)):
    """Check if an instruction can be replayed"""
    try:
        if gateway.replay_engine is None:
            from src.core.routing_engine import RoutingEngine
            routing_engine = RoutingEngine(gateway.agents, gateway.memory)
            from src.core.replay_engine import ReplayEngine
            gateway.replay_engine = ReplayEngine(gateway.lineage_manager, routing_engine, gateway.memory)
        
        validation = gateway.replay_engine.validate_replay_capability(instruction_id)
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/bucket/statistics")
async def get_bucket_statistics(request: Request, _auth=Depends(require_auth)):
    """Get Bucket storage statistics"""
    try:
        stats = gateway.bucket_reader.get_bucket_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@app.get("/replay/statistics")
async def get_replay_statistics(request: Request, _auth=Depends(require_auth)):
    """Get replay system statistics"""
    try:
        if gateway.replay_engine is None:
            from src.core.routing_engine import RoutingEngine
            routing_engine = RoutingEngine(gateway.agents, gateway.memory)
            from src.core.replay_engine import ReplayEngine
            gateway.replay_engine = ReplayEngine(gateway.lineage_manager, routing_engine, gateway.memory)
        
        stats = gateway.replay_engine.get_replay_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay statistics failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)