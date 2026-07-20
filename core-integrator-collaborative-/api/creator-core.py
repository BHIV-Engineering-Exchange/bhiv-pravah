"""
Creator Core Serverless Function for Vercel
Converts Prompt Runner instructions to Blueprint Envelopes
"""

import os
import sys
from pathlib import Path

# Add project root and necessary subdirectories to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, str(Path(project_root) / "creator-core" / "Core-Integrator-Sprint-1.1"))
sys.path.insert(0, str(Path(project_root) / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from creator_core_engine import CreatorCoreService, create_creator_core_router

# Initialize FastAPI app
app = FastAPI(
    title="Creator Core - Vercel",
    description="Blueprint generation service",
    version="1.0.0"
)

# Enable CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
try:
    creator_core_service = CreatorCoreService()
    app.include_router(create_creator_core_router(creator_core_service))
except Exception as e:
    print(f"Error initializing Creator Core: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "creator-core"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Creator Core",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_blueprint": "/creator-core/generate-blueprint"
        }
    }

# Mangum ASGI to WSGI adapter for Vercel
handler = Mangum(app)
