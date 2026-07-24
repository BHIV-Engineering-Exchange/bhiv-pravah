"""
Prompt Runner - FastAPI Service
================================
Converts any user prompt into a structured JSON instruction using the Groq API.

Required environment variable:
    GROQ_API_KEY=gsk_...   (get yours at console.groq.com)

Start:
    uvicorn api:app --host 0.0.0.0 --port 8001

Endpoints:
    POST /generate   — prompt  structured JSON instruction
    GET  /health     — Groq availability check
    GET  /schema     — JSON Schema for the instruction format
    GET  /models     — list available Groq models
"""

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_adapter import LLMAdapter, DEFAULT_MODEL
from observability.pravah_adapter import emit_pravah_signal, start_heartbeat

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Prompt Runner API",
    description="Converts any user prompt into a deterministic JSON instruction via Groq API.",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    start_heartbeat(interval_seconds=60)

# ---------------------------------------------------------------------------
# JSON Schema (served at /schema)
# ---------------------------------------------------------------------------

INSTRUCTION_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Prompt Runner Instruction",
    "type": "object",
    "properties": {
        "prompt":          {"type": "string"},
        "module":          {"type": "string"},
        "intent":          {"type": "string"},
        "topic":           {"type": "string"},
        "tasks":           {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "output_format":   {"type": "string"},
        "product_context": {"type": "string", "enum": ["creator_core"]},
    },
    "required": ["prompt", "module", "intent", "topic", "tasks", "output_format", "product_context"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Singleton adapter
# ---------------------------------------------------------------------------

_llm: Optional[LLMAdapter] = None


def _get_llm() -> LLMAdapter:
    global _llm
    if _llm is None:
        _llm = LLMAdapter()   # reads GROQ_API_KEY from environment / .env.local
    return _llm


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class PromptRequest(BaseModel):
    prompt: str           = Field(..., min_length=1, description="User prompt to interpret")
    model:  Optional[str] = Field(None, description="Groq model override")


class InstructionResponse(BaseModel):
    prompt:          str
    module:          str
    intent:          str
    topic:           str
    tasks:           List[str]
    output_format:   str
    product_context: str = "creator_core"


class HealthResponse(BaseModel):
    status:         str
    groq_available: bool
    models:         List[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check():
    """Check Groq API availability."""
    llm = _get_llm()
    llm.reset_availability_cache()
    return HealthResponse(
        status         = "healthy",
        groq_available = llm.available,
        models         = llm.client.list_models() if llm.available else [],
    )


@app.post("/generate", response_model=InstructionResponse, tags=["core"])
def generate_instruction(request: PromptRequest):
    """
    Convert a user prompt into a structured JSON instruction via Groq API.

    Output always contains exactly these 6 keys:
    {
        "prompt": "...",
        "module": "...",
        "intent": "...",
        "topic": "...",
        "tasks": ["...", "..."],
        "output_format": "..."
    }
    """
    llm = _get_llm()

    start_time = time.time()

    if not llm.available:
        emit_pravah_signal(state="error", latency_ms=0.0, errors_last_min=1)
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured. Set it as an environment variable.",
        )

    if request.model:
        llm.client.model = request.model
        llm.reset_availability_cache()

    try:
        instruction = llm.generate_instruction(request.prompt)
        duration_ms = (time.time() - start_time) * 1000
        emit_pravah_signal(state="running", latency_ms=duration_ms)
        return InstructionResponse(**instruction)
    except Exception as exc:
        emit_pravah_signal(state="error", latency_ms=0.0, errors_last_min=1)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/schema", tags=["system"])
def get_schema():
    """Return the JSON Schema for the instruction output format."""
    return INSTRUCTION_SCHEMA


@app.get("/models", tags=["system"])
def list_models():
    """List available Groq models."""
    llm = _get_llm()
    llm.reset_availability_cache()
    return {
        "groq_available": llm.available,
        "models":         llm.client.list_models() if llm.available else [],
        "default_model":  DEFAULT_MODEL,
    }
    
    
    
    
    