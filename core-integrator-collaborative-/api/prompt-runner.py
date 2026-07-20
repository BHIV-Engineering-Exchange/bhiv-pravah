"""
Prompt Runner Serverless Function for Vercel
Converts prompts to instructions
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
from typing import Optional

# Initialize FastAPI app
app = FastAPI(
    title="Prompt Runner - Vercel",
    description="Prompt to instruction conversion service",
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

class PromptRequest(BaseModel):
    """Prompt conversion request"""
    prompt: str
    module: str = "general"
    intent: str = "process"
    domain: Optional[str] = None

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "prompt-runner"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Prompt Runner",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "convert": "/convert",
            "generate": "/generate"
        }
    }

@app.post("/convert")
async def convert_prompt(request: PromptRequest):
    """Convert prompt to instruction"""
    try:
        return {
            "status": "success",
            "instruction": {
                "prompt": request.prompt,
                "module": request.module,
                "intent": request.intent,
                "domain": request.domain or "general"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_prompt(request: PromptRequest):
    """Compatibility alias for prompt generation"""
    return await convert_prompt(request)

# Mangum ASGI to WSGI adapter for Vercel
handler = Mangum(app)
