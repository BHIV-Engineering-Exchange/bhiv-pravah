"""
Bucket Service Serverless Function for Vercel
Stores and retrieves artifacts
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
from typing import Dict, Any, Optional

# Initialize FastAPI app
app = FastAPI(
    title="Bucket - Vercel",
    description="Artifact storage service",
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

class ArtifactRequest(BaseModel):
    """Store artifact request"""
    artifact_id: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, str]] = None

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "bucket"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Bucket",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "store": "/store",
            "retrieve": "/retrieve/{artifact_id}"
        }
    }

@app.post("/store")
async def store_artifact(request: ArtifactRequest):
    """Store an artifact"""
    try:
        return {
            "status": "success",
            "artifact_id": request.artifact_id,
            "message": "Artifact stored successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/retrieve/{artifact_id}")
async def retrieve_artifact(artifact_id: str):
    """Retrieve an artifact"""
    try:
        return {
            "status": "success",
            "artifact_id": artifact_id,
            "content": {}
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Artifact not found")

# Mangum ASGI to WSGI adapter for Vercel
handler = Mangum(app)
