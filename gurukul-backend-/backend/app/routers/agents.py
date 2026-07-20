from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Any
from app.services.llm import call_groq_api, call_ollama_api
from app.core.config import settings
import io
import logging
from app.services.pravah_adapter import pravah_adapter
from app.services.bucket_adapter import bucket_adapter

logger = logging.getLogger("AgentsRouter")

router = APIRouter()

# --- Schemas ---

class EduMentorRequest(BaseModel):
    subject: str
    topic: str
    include_wikipedia: bool = False
    use_knowledge_store: bool = False
    use_orchestration: bool = False

class ExpenseCategory(BaseModel):
    name: str
    amount: float

class FinancialRequest(BaseModel):
    name: str
    monthly_income: float
    monthly_expenses: float
    expense_categories: List[ExpenseCategory]
    financial_goal: str
    financial_type: str
    risk_level: str

class WellnessRequest(BaseModel):
    emotional_wellness_score: int
    financial_wellness_score: int
    current_mood_score: int
    stress_level: int
    concerns: Optional[str] = None

class TTSAgentRequest(BaseModel):
    text: str
    language: str = "en"

# --- TTS Fallback Helpers ---

def _tts_via_vaani(text: str, language: str) -> bytes:
    """Attempt to generate audio via the local Vaani engine."""
    import requests as req
    vaani_url = getattr(settings, "VAANI_API_URL", "http://localhost:8008")
    resp = req.post(
        f"{vaani_url}/voice/speak",
        json={"text": text, "language": language, "voice_profile": "vaani_teacher"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.content


def _tts_via_openai(text: str, language: str) -> bytes:
    """Generate audio via OpenAI TTS API (cloud, no local engine needed)."""
    import openai
    api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",       # clear, neutral voice
        input=text[:4096],  # OpenAI TTS limit
    )
    buf = io.BytesIO()
    for chunk in response.iter_bytes():
        buf.write(chunk)
    return buf.getvalue()


def _tts_via_gtts(text: str, language: str) -> bytes:
    """Free fallback: Google Text-to-Speech (no API key required)."""
    from gtts import gTTS
    lang_map = {"en": "en", "hi": "hi", "ar": "ar", "es": "es", "fr": "fr", "ja": "ja"}
    lang = lang_map.get(language, "en")
    tts = gTTS(text=text[:500], lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def _generate_audio(text: str, language: str) -> tuple[bytes, str]:
    """
    3-tier TTS with automatic fallback.
    Returns (audio_bytes, engine_used).
    """
    # Tier 1: Vaani local engine
    try:
        audio = _tts_via_vaani(text, language)
        logger.info("[TTS] Generated via Vaani")
        return audio, "vaani"
    except Exception as e:
        logger.warning(f"[TTS] Vaani unavailable ({e}), trying OpenAI...")

    # Tier 2: OpenAI TTS
    try:
        audio = _tts_via_openai(text, language)
        logger.info("[TTS] Generated via OpenAI")
        return audio, "openai"
    except Exception as e:
        logger.warning(f"[TTS] OpenAI TTS failed ({e}), trying gTTS...")

    # Tier 3: gTTS (free, no key)
    try:
        audio = _tts_via_gtts(text, language)
        logger.info("[TTS] Generated via gTTS")
        return audio, "gtts"
    except Exception as e:
        raise RuntimeError(f"All TTS engines failed. Last error: {e}")


# --- Endpoints ---

@router.post("/tts")
async def agent_generate_tts(request: TTSAgentRequest):
    """
    Unified Vaani TTS Generation endpoint for agents.

    Tier 1 — Vaani local engine (sovereign, on-premise)
    Tier 2 — OpenAI TTS cloud API
    Tier 3 — gTTS (Google, free, no key)
    """
    import hashlib, asyncio

    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    # Optional cache lookup — non-fatal if MongoDB is unavailable
    text_hash = hashlib.sha256(f"{text}|{request.language}".encode()).hexdigest()
    try:
        from app.core.karma_database import get_db
        db = get_db()
        cached = db.tts_cache.find_one({"text_hash": text_hash})
        if cached and cached.get("audio_data"):
            logger.info(f"[TTS] Cache hit for {text_hash[:8]}")
            return {
                "status": "success",
                "audio_id": text_hash,
                "audio_url": f"/api/v1/agent/download-audio?audio_id={text_hash}"
            }
    except Exception as cache_err:
        logger.warning(f"[TTS] Cache lookup skipped: {cache_err}")

    # Generate audio
    try:
        # Emit Signal: Agent TTS Started
        pravah_adapter.emit_signal(
            event_type="agent_action",
            action="agent_tts_started",
            payload={"lang": request.language, "text_len": len(text)}
        )

        audio_bytes, engine = await asyncio.to_thread(_generate_audio, text, request.language)

        # Emit Signal: Agent TTS Success
        pravah_adapter.emit_signal(
            event_type="agent_action",
            action="agent_tts_success",
            status="success",
            payload={"engine": engine, "lang": request.language}
        )

        # Emit Memory
        bucket_adapter.emit_memory(
            user_id="agent_user",
            session_id=f"agent_tts_{text_hash[:8]}",
            action="agent_voice_generation",
            outcome="success",
            payload={"engine": engine, "lang": request.language, "text_hash": text_hash}
        )
    except RuntimeError as e:
        # Emit Failure Signal
        pravah_adapter.emit_signal(
            event_type="agent_action",
            action="agent_tts_failed",
            status="failure",
            payload={"error": str(e)}
        )
        raise HTTPException(status_code=503, detail=str(e))

    # Optional cache store — non-fatal if MongoDB is unavailable
    try:
        from app.core.karma_database import get_db
        import datetime
        db = get_db()
        db.tts_cache.insert_one({
            "text_hash": text_hash,
            "text": text,
            "language": request.language,
            "audio_data": audio_bytes,
            "engine": engine,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        })
    except Exception as store_err:
        logger.warning(f"[TTS] Cache store skipped: {store_err}")

    return {
        "status": "success",
        "audio_id": text_hash,
        "audio_url": f"/api/v1/agent/download-audio?audio_id={text_hash}"
    }

@router.get("/download-audio")
async def download_agent_audio(audio_id: str):
    """Retrieve audio from tts_cache by hash."""
    try:
        from app.core.karma_database import get_db
        db = get_db()
        cached = db.tts_cache.find_one({"text_hash": audio_id})
        if not cached:
            raise HTTPException(status_code=404, detail="Audio not found")
        return Response(
            content=cached["audio_data"],
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"attachment; filename={audio_id}.mp3"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
