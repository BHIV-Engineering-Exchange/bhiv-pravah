from fastapi import APIRouter, HTTPException, Response
import time
from pydantic import BaseModel
from app.services.pravah_adapter import pravah_adapter
from app.services.bucket_adapter import bucket_adapter
from app.services.system_metrics import record_voice_latency

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    language: str = "en"  # Language code (e.g., 'en', 'es', 'fr', 'de', etc.)

@router.get("/voices")
async def get_available_voices():
    """
    Get list of available TTS voices (Sovereign Vaani Engine)
    """
    return {
        "voices": [
            {
                "name": "Vaani Teacher",
                "id": "vaani_teacher",
                "languages": ["en", "hi", "ar", "es", "fr", "ja"],
                "gender": "Female",
                "age": "Adult"
            }
        ],
        "total": 1
    }

@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech and return audio file (Google TTS)
    """
    try:
        from app.services.tts_core_functions import text_to_speech_stream
        
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Emit Signal: TTS Request Started
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="tts_request_started",
            payload={"lang": request.language, "text_len": len(request.text)}
        )

        # Use our sovereign engine (Vaani)
        t0 = time.perf_counter()
        audio_data = await text_to_speech_stream(request.text, language=request.language, use_google_tts=False)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        record_voice_latency(elapsed_ms)
        
        # Emit Signal: TTS Success
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="tts_generation_success",
            status="success",
            payload={"lang": request.language, "engine": "vaani"}
        )

        # Emit Memory (Anonymous since no user dependency in this route)
        bucket_adapter.emit_memory(
            user_id="anonymous_tts",
            session_id="tts_session",
            action="voice_generation",
            outcome="success",
            payload={"engine": "vaani", "lang": request.language}
        )

        # Vaani engine returns WAV
        media_type = "audio/wav"
        file_ext = "wav"
        
        # Return audio file
        return Response(
            content=audio_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=vaani_speech.{file_ext}"
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[TTS] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate speech: {str(e)}"
        )

def _gtts_lang_code(lang: str) -> str:
    """Map frontend language code to gTTS lang code. gTTS uses ISO 639-1 (e.g. zh-cn, pt-br)."""
    if not lang or not lang.strip():
        return "en"
    lang = lang.strip().lower()
    # gTTS uses zh-cn / zh-tw for Chinese
    if lang in ("zh", "zh-cn", "zh_cn"):
        return "zh-cn"
    if lang == "zh-tw":
        return "zh-tw"
    # Other codes (en, hi, ja, ko, ar, fr, es, etc.) are used as-is by gTTS
    return lang if len(lang) >= 2 else "en"


@router.post("/vaani")
async def vaani_text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Vaani TTS (gTTS).
    Translates text to the target language first (like Google TTS path), then speaks
    so you get actual Hindi/Japanese/etc. speech, not English in an accent.
    """
    try:
        from app.services.tts_core_functions import text_to_speech_stream
        
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Emit Signal: Vaani TTS Started
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="vaani_tts_started",
            payload={"lang": request.language}
        )

        # Use our sovereign engine (Vaani)
        t0 = time.perf_counter()
        audio_data = await text_to_speech_stream(request.text, language=request.language, use_google_tts=False)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        record_voice_latency(elapsed_ms)
        
        # Emit Signal & Memory
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="vaani_tts_success",
            status="success"
        )
        bucket_adapter.emit_memory(
            user_id="anonymous_vaani",
            session_id="vaani_session",
            action="vaani_voice_generation",
            outcome="success"
        )

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=vaani_sovereign_speech.wav"
            }
        )
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Emit failure signal
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="vaani_tts_failed",
            status="failure",
            payload={"error": str(e)}
        )
        print(f"[Vaani TTS] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate speech with Vaani TTS: {str(e)}"
        )
