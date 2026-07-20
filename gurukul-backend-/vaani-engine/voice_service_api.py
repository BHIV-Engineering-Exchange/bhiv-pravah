"""
voice_service_api.py — Vaani Sovereign Voice Service API

FastAPI service that wraps the XTTS model with production guardrails:
  - 5000 character input validation
  - Model load state reporting in /health
  - Structured error handling
"""

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import os
import voice_engine_interface as vaani

app = FastAPI(title="Vaani Sentinel: Voice Service API")

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
MAX_INPUT_CHARS = 5000


# ──────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────
class VoiceRequest(BaseModel):
    text: str = Field(..., max_length=MAX_INPUT_CHARS, description="Text to synthesize (max 5000 chars)")
    language: str = Field(default="en", description="ISO 639-1 language code")
    voice_profile: str = Field(default="vaani_teacher", description="Voice profile to use")


# ──────────────────────────────────────────────────────────────
# Health Endpoint
# ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """
    Health endpoint with model load state for monitoring.
    """
    engine = vaani.get_engine()
    model_loaded = engine.model is not None

    return {
        "status": "healthy" if model_loaded else "initializing",
        "device": engine.device,
        "model_loaded": model_loaded,
        "model_name": engine.model_name,
        "max_input_chars": MAX_INPUT_CHARS,
    }


# ──────────────────────────────────────────────────────────────
# Voice Generation Endpoint
# ──────────────────────────────────────────────────────────────
@app.post("/voice/speak")
async def speak(request: VoiceRequest):
    """
    Standardized API endpoint for sovereign voice generation.

    Input guardrails:
      - Text must not be empty
      - Text must not exceed 5000 characters
    """
    # 1. Input length guard (belt-and-suspenders with Pydantic max_length)
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="Empty text provided")

    if len(request.text) > MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=422,
            detail=f"Text length {len(request.text)} exceeds maximum {MAX_INPUT_CHARS} characters"
        )

    # 2. Generate audio via Vaani engine
    output_path, error = vaani.generate_voice(
        text=request.text,
        language=request.language,
        voice_profile=request.voice_profile
    )

    if error:
        status_code = 422 if "Empty" in error else 500
        raise HTTPException(status_code=status_code, detail=error)

    # 3. Read and return audio data
    try:
        with open(output_path, "rb") as f:
            audio_data = f.read()

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(output_path)}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File read error: {e}")


if __name__ == "__main__":
    import uvicorn
    # Running on 8008 to maintain compatibility with backend proxy
    uvicorn.run(app, host="0.0.0.0", port=8008)
