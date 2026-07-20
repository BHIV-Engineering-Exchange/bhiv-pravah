from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from ai_agent import AIAgent, MultiAgentSystem
import os
from dotenv import load_dotenv
from database.mongo_db import MongoDBClient
from utils.logger import logger
from datetime import datetime
from bson import ObjectId
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import traceback

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_client = MongoDBClient()
db = mongo_client.db

# Initialize Multi-Agent System
multi_agent_system = MultiAgentSystem()
try:
    departments = [dept["name"] for dept in db.departments.find()]
    if not departments:
        raise ValueError("No departments found")
    multi_agent_system.initialize_agents(departments)
except ValueError as e:
    logger.warning(f"Failed to initialize agents: {str(e)}")

class OptimizeRequest(BaseModel):
    department: str

class EscalateRequest(BaseModel):
    task_id: str

class DependencyRequest(BaseModel):
    task_id: str

@app.get("/health")
async def health_check():
    try:
        mongo_client.client.admin.command("ping")
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"failed: {str(e)}"
    agent_count = len(multi_agent_system.agents)
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "agents_initialized": agent_count,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/optimize")
async def optimize_tasks(request: OptimizeRequest):
    try:
        try:
            dept_id = ObjectId(request.department)
            dept = db.departments.find_one({"_id": dept_id})
            if not dept:
                raise HTTPException(status_code=404, detail=f"Department with ID {request.department} not found")
            department_name = dept["name"]
        except ValueError:
            department_name = request.department
            dept = db.departments.find_one({"name": department_name})
            if not dept:
                raise HTTPException(status_code=404, detail=f"Department {department_name} not found")

        agent = multi_agent_system.agents.get(department_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent for department {department_name} not initialized")
        
        recommendations = await agent.optimize_tasks()
        await agent.notify(recommendations)
        return {"status": "Optimization completed", "recommendations": recommendations}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Optimization error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@app.post("/escalate")
async def escalate_task(request: EscalateRequest):
    try:
        recommendation = await multi_agent_system.handle_escalation(request.task_id)
        if "error" in recommendation:
            raise HTTPException(status_code=500, detail=recommendation["error"])
        return {
            "status": "Escalation initiated",
            "task_id": request.task_id,
            "recommendations": recommendation
        }
    except Exception as e:
        logger.error(f"Escalation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Escalation failed: {str(e)}")

@app.post("/negotiate-dependencies")
async def negotiate_dependencies(request: DependencyRequest):
    try:
        recommendations = await multi_agent_system.negotiate_dependencies(request.task_id)
        return {
            "status": "Dependency negotiation initiated",
            "task_id": request.task_id,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Dependency negotiation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Dependency negotiation failed: {str(e)}")

@app.on_event("shutdown")
def shutdown_event():
    mongo_client.client.close()

if __name__ == "__main__":
    port = int(os.getenv("FASTAPI_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)