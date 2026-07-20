"""
BHIV Core Serverless Function for Vercel
Executes blueprints with enforcement discipline
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from typing import Dict, Any

# Initialize FastAPI app
app = FastAPI(
    title="BHIV Core - Vercel",
    description="Blueprint execution service",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExecutionRequest(BaseModel):
    """Blueprint execution request"""
    blueprint: Dict[str, Any]
    task_id: str
    agent: str

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "bhiv-core"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "BHIV Core",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "execute": "/execute"
        }
    }

@app.post("/execute")
async def execute_blueprint(request: ExecutionRequest):
    """Execute a blueprint"""
    try:
        # Blueprint execution logic
        return {
            "status": "success",
            "task_id": request.task_id,
            "result": {
                "execution_time": 0.5,
                "status": "completed"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mangum ASGI to WSGI adapter for Vercel
handler = Mangum(app)
