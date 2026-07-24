"""
Insight Flow Bridge - Standalone Minimal Version
Port: 8006
Purpose: Provide basic routing without requiring full Insight Flow backend
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insight Flow Bridge (Standalone)", version="1.0.0")

# Configuration
CORE_URL = "http://localhost:8002"
BUCKET_URL = "http://localhost:8001"
KARMA_URL = "http://localhost:8000"

class RoutingRequest(BaseModel):
    input_data: Dict[str, Any]
    input_type: str
    strategy: str = "q_learning"
    context: Optional[Dict] = None

class AgentRouteRequest(BaseModel):
    agent_type: str
    context: Optional[Dict] = None
    confidence_threshold: float = 0.75

# Simple agent mapping
AGENT_MAP = {
    "text": "edumentor_agent",
    "nlp": "edumentor_agent",
    "pdf": "knowledge_agent",
    "image": "image_agent",
    "audio": "audio_agent",
    "default": "edumentor_agent"
}

@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "ok",
        "service": "Insight Flow Bridge (Standalone)",
        "version": "1.0.0",
        "mode": "standalone",
        "note": "Running without full backend - using simple routing"
    }

@app.post("/route")
async def route_request(request: RoutingRequest):
    """
    Simple routing without backend dependency
    Maps input types to appropriate agents
    """
    try:
        # Simple agent selection based on input type
        agent_name = AGENT_MAP.get(request.input_type, AGENT_MAP["default"])
        
        return {
            "routing": {
                "selected_agent": {
                    "name": agent_name,
                    "type": request.input_type
                },
                "confidence_score": 0.85,
                "routing_reason": f"Mapped {request.input_type} to {agent_name}",
                "strategy": "simple_mapping"
            },
            "status": "success",
            "mode": "standalone"
        }
            
    except Exception as e:
        logger.error(f"Routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route-agent")
async def route_agent(request: AgentRouteRequest):
    """Route to best agent based on type"""
    try:
        agent_name = AGENT_MAP.get(request.agent_type, AGENT_MAP["default"])
        
        return {
            "selected_agent": {
                "name": agent_name,
                "type": request.agent_type
            },
            "confidence_score": 0.85,
            "routing_reason": f"Mapped {request.agent_type} to {agent_name}",
            "alternatives": [],
            "mode": "standalone"
        }
            
    except Exception as e:
        logger.error(f"Agent routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get basic analytics"""
    return {
        "mode": "standalone",
        "message": "Full analytics require backend on port 8007",
        "basic_stats": {
            "total_routes": 0,
            "success_rate": 0.0
        }
    }

@app.get("/metrics")
def get_metrics():
    """Get bridge metrics"""
    return {
        "bridge_version": "1.0.0",
        "mode": "standalone",
        "core_url": CORE_URL,
        "status": "operational",
        "note": "Running without full backend - basic routing only"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Insight Flow Bridge in STANDALONE mode")
    logger.info("This provides basic routing without requiring the full backend")
    logger.info("For full features, start backend on port 8007")
    uvicorn.run(app, host="0.0.0.0", port=8006)
