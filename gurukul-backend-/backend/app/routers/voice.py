"""
voice.py — Gurukul Speech Interface Layer (STT Router)
=======================================================

Exposes the /voice namespace for Speech-to-Text endpoints.

Endpoints:
  POST /voice/listen        — transcribe uploaded audio file
  POST /voice/converse      — full voice conversation loop (STT → LLM → TTS)
  GET  /voice/stt/status    — provider health and stats
  GET  /voice/languages     — list all supported STT languages
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.speech_provider import speech_provider
from app.services.system_metrics import record_ai_latency, record_voice_latency
from app.services.pravah_adapter import pravah_adapter
from app.services.bucket_adapter import bucket_adapter

logger = logging.getLogger("VoiceRouter")

router = APIRouter(prefix="/voice", tags=["Speech Interface (STT)"])

# Permitted audio MIME types
ALLOWED_MIME_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp3",
    "audio/mp4", "audio/m4a", "audio/x-m4a",
    "audio/ogg", "audio/webm",
    "audio/flac",
    "application/octet-stream",   # generic fallback
}


# ---------------------------------------------------------------------------
# POST /voice/listen
# ---------------------------------------------------------------------------

@router.post("/listen")
async def listen(
    audio: UploadFile = File(..., description="Audio file to transcribe (WAV, MP3, OGG, WebM, M4A)"),
    language: Optional[str] = Form(default="auto",
        description="Language code: 'en', 'hi', 'ar', 'es', 'fr', 'ja', or 'auto'"),
):
    """
    Transcribe an audio file to text.

    Accepts any standard audio format. Returns transcribed text along
    with detected language and confidence score.

    - **language**: Pass a BCP-47 code (e.g. 'hi' for Hindi) or 'auto' for auto-detection.
    - **audio**: Upload as multipart form data.
    """
    # ── Validation ────────────────────────────────────────────────────
    if audio.content_type and audio.content_type not in ALLOWED_MIME_TYPES:
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported media type: '{audio.content_type}'. "
                       f"Please upload an audio file (WAV, MP3, OGG, WebM, M4A).",
            )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty")

    filename = audio.filename or "audio.wav"

    # ── Transcribe ────────────────────────────────────────────────────
    try:
        # Emit Signal: STT Started
        pravah_adapter.emit_signal(
            event_type="stt_action",
            action="stt_request_started",
            payload={"lang": language or "auto"}
        )

        result = await speech_provider.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language=language or "auto",
        )
        record_ai_latency(result.duration_ms)   # Track in telemetry

        # Emit Signal: STT Success
        pravah_adapter.emit_signal(
            event_type="stt_action",
            action="stt_request_success",
            status="success",
            payload={"engine": result.engine, "lang": result.language}
        )
        
        # Emit Memory
        bucket_adapter.emit_memory(
            user_id="anonymous",
            session_id="stt_session",
            action="speech_to_text",
            outcome="success",
            payload={"engine": result.engine, "duration_ms": result.duration_ms}
        )
    except Exception as e:
        # Emit Failure Signal
        pravah_adapter.emit_signal(
            event_type="stt_action",
            action="stt_request_failed",
            status="failure",
            payload={"error": str(e)}
        )
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        if isinstance(e, TimeoutError):
            raise HTTPException(status_code=504, detail=str(e))
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "success": True,
        "transcript": result.text,
        "language": result.language,
        "language_name": result.language_name,
        "confidence": result.confidence,
        "engine": result.engine,
        "transcription_time_ms": round(result.duration_ms, 2),
        "word_count": result.word_count,
    }


# ---------------------------------------------------------------------------
# POST /voice/converse  — Full Voice Conversation Loop
# ---------------------------------------------------------------------------

@router.post("/converse")
async def converse(
    audio: UploadFile = File(..., description="Student's spoken question as audio"),
    language: Optional[str] = Form(default="auto",
        description="Language code or 'auto' for auto-detection"),
    return_audio: bool = Form(default=True,
        description="If true, also return a TTS voice response"),
):
    """
    Full voice conversation loop:

    1. Transcribe student's audio (STT)
    2. Pass transcript to the AI reasoning engine (LLM)
    3. Optionally synthesize the AI response to audio (TTS via Vaani)

    Returns both the transcript, LLM response text, and (optionally) audio bytes.
    """
    import time

    # Step 1 ── STT ────────────────────────────────────────────────────
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    try:
        stt_result = await speech_provider.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
            language=language or "auto",
        )
        record_ai_latency(stt_result.duration_ms)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"STT failed: {e}")

    user_text = stt_result.text
    if not user_text:
        raise HTTPException(status_code=422, detail="Could not recognise any speech in the audio")

    # Step 2 ── LLM ───────────────────────────────────────────────────
    ai_text = ""
    t_llm = time.perf_counter()
    try:
        import os
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Gurukul, an expert multilingual AI tutor. "
                        "Answer concisely and clearly. "
                        f"Respond in the same language as the user ({stt_result.language_name})."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            max_tokens=500,
        )
        ai_text = resp.choices[0].message.content.strip()
        record_ai_latency((time.perf_counter() - t_llm) * 1000)
    except Exception as e:
        # Emit Signal: LLM Failure
        pravah_adapter.emit_signal(
            event_type="converse_action",
            action="llm_failed",
            status="failure",
            payload={"error": str(e)}
        )
        logger.error(f"[Converse] LLM failed: {e}")
        ai_text = f"I received your message: '{user_text}', but my reasoning engine is currently unavailable."

    # Emit Memory & Final Signal
    bucket_adapter.emit_memory(
        user_id="anonymous",
        session_id="converse_session",
        action="voice_conversation",
        outcome="success",
        payload={"user_text_len": len(user_text), "ai_text_len": len(ai_text)}
    )
    pravah_adapter.emit_signal(
        event_type="converse_action",
        action="conversation_loop_complete",
        status="success"
    )

    response_payload = {
        "success": True,
        "stt": {
            "transcript": user_text,
            "language": stt_result.language,
            "language_name": stt_result.language_name,
            "confidence": stt_result.confidence,
            "engine": stt_result.engine,
        },
        "ai_response": ai_text,
        "audio_response": None,
    }

    return response_payload


# ---------------------------------------------------------------------------
# POST /voice/respond  — AI Response + TTS
# ---------------------------------------------------------------------------

@router.post("/respond")
async def respond(
    text: str = Form(..., description="Text to synthesize to speech"),
    language: Optional[str] = Form(default="en", description="Language code"),
    return_audio: bool = Form(default=True, description="If true, return TTS audio"),
):
    """
    Generate an AI voice response for given text.
    Strictly uses the unified Vaani pipeline.
    """
    import base64
    import time
    from app.services.voice_provider import provider as voice_provider

    response_payload = {
        "success": True,
        "text": text,
        "audio_response": None,
    }

    if return_audio:
        t_tts = time.perf_counter()
        try:
            audio_data = await voice_provider.generate_audio(text, language)
            record_voice_latency((time.perf_counter() - t_tts) * 1000)
            response_payload["audio_response"] = base64.b64encode(audio_data).decode("utf-8")
            response_payload["audio_format"] = "wav"
        except Exception as e:
            logger.warning(f"[Respond] TTS failed: {e}")
            raise HTTPException(status_code=503, detail=f"TTS failed: {e}")

    return response_payload


# ---------------------------------------------------------------------------
# GET /voice/stt/status
# ---------------------------------------------------------------------------

@router.get("/stt/status")
async def stt_status():
    """Return STT provider health and stats."""
    return speech_provider.get_status()


# ---------------------------------------------------------------------------
# GET /voice/languages
# ---------------------------------------------------------------------------

@router.get("/languages")
async def supported_languages():
    """Return all languages supported by the STT engine."""
    from app.services.stt_service import SUPPORTED_LANGUAGES
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "auto_detection": True,
        "engine": "groq/whisper-large-v3 (primary), faster-whisper (fallback)",
    }
