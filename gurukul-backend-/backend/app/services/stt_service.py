"""
stt_service.py — Gurukul Multilingual Speech-to-Text Service
=============================================================

Transcribes audio files to text using a two-tier engine strategy:

  Tier 1 (Primary)  — Groq Whisper API (cloud, zero local memory)
  Tier 2 (Fallback) — faster-whisper local model (runs offline)

Supported languages:
  en (English), hi (Hindi), ar (Arabic), es (Spanish), fr (French), ja (Japanese)

Usage:
    from app.services.stt_service import STTService
    svc = STTService()
    result = await svc.transcribe(audio_bytes, filename="audio.wav", language="hi")
"""

import asyncio
import io
import logging
import os
import time
import tempfile
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("STTService")

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ar": "Arabic",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
}

# Default Whisper model size for local fallback
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")   # tiny|base|small|medium|large


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TranscriptionResult:
    text: str
    language: str
    language_name: str
    confidence: float        # 0.0 – 1.0; -1 if unavailable
    engine: str              # "groq" | "faster-whisper"
    duration_ms: float
    word_count: int

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "language": self.language,
            "language_name": self.language_name,
            "confidence": self.confidence,
            "engine": self.engine,
            "transcription_time_ms": round(self.duration_ms, 2),
            "word_count": self.word_count,
        }


# ---------------------------------------------------------------------------
# Groq Whisper API transcription
# ---------------------------------------------------------------------------

def _transcribe_via_groq(audio_bytes: bytes, filename: str, language: Optional[str]) -> dict:
    """
    Call Groq's Whisper endpoint to transcribe audio.
    Returns dict with 'text' and optionally 'detected_language'.
    """
    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("groq package not installed. Run: pip install groq")

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment — Groq STT unavailable")

    client = Groq(api_key=api_key)

    # Groq expects a file-like object
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename  # Groq needs the name for MIME detection

    kwargs = {
        "file": (filename, audio_file),
        "model": "whisper-large-v3",
        "response_format": "verbose_json",
    }
    if language and language != "auto":
        kwargs["language"] = language

    transcription = client.audio.transcriptions.create(**kwargs)

    detected_lang = getattr(transcription, "language", language or "en")
    return {
        "text": transcription.text.strip(),
        "language": detected_lang,
    }


# ---------------------------------------------------------------------------
# faster-whisper local fallback
# ---------------------------------------------------------------------------

_local_model = None
_local_model_lock = asyncio.Lock() if asyncio.get_event_loop else None


def _load_local_model():
    """Load faster-whisper model lazily (only on first use)."""
    global _local_model
    if _local_model is not None:
        return _local_model
    try:
        from faster_whisper import WhisperModel
        logger.info(f"[STT] Loading faster-whisper model: {WHISPER_MODEL_SIZE}")
        _local_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("[STT] faster-whisper model loaded successfully")
        return _local_model
    except (ImportError, Exception) as e:
        logger.warning(f"[STT] faster-whisper is not available: {e}. Falling back to Cloud STT (Groq).")
        raise RuntimeError(
            f"Local STT engine (faster-whisper) not available or failed to load: {e}"
        )


def _transcribe_via_local(audio_bytes: bytes, filename: str, language: Optional[str]) -> dict:
    """Use faster-whisper local model for transcription."""
    model = _load_local_model()

    # Write audio bytes to a temp file (faster-whisper needs a path)
    suffix = os.path.splitext(filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language=language if language != "auto" else None,
            beam_size=5,
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return {
            "text": text.strip(),
            "language": info.language,
        }
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Main STT Service
# ---------------------------------------------------------------------------

class STTService:
    """
    Multilingual Speech-to-Text service for Gurukul.

    Tries Groq Whisper API first; falls back to faster-whisper if Groq
    is unavailable or if GROQ_API_KEY is not set.
    """

    def __init__(self):
        self._stats = {
            "total_requests": 0,
            "groq_successes": 0,
            "local_successes": 0,
            "failures": 0,
        }
        logger.info("[STT] STTService initialised (primary=Groq, fallback=faster-whisper)")

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = "auto",
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data (wav/mp3/m4a/webm/ogg supported).
            filename:    Filename hint for MIME detection (e.g. 'speech.wav').
            language:    BCP-47 language code or 'auto' for auto-detection.

        Returns:
            TranscriptionResult dataclass.

        Raises:
            ValueError:  Invalid language code.
            RuntimeError: Both engines failed.
        """
        if not audio_bytes:
            raise ValueError("Audio bytes are empty")

        if language and language != "auto" and language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{language}'. "
                f"Supported: {list(SUPPORTED_LANGUAGES.keys())} or 'auto'"
            )

        self._stats["total_requests"] += 1
        t0 = time.perf_counter()

        # ── Tier 1: Groq ─────────────────────────────────────────────
        try:
            raw = await asyncio.to_thread(
                _transcribe_via_groq, audio_bytes, filename, language
            )
            engine = "groq"
            self._stats["groq_successes"] += 1
            logger.info(f"[STT] Groq transcription succeeded ({len(raw['text'])} chars)")

        except Exception as groq_err:
            logger.warning(f"[STT] Groq failed ({groq_err}), trying faster-whisper...")

            # ── Tier 2: Local faster-whisper ─────────────────────────
            try:
                raw = await asyncio.to_thread(
                    _transcribe_via_local, audio_bytes, filename, language
                )
                engine = "faster-whisper"
                self._stats["local_successes"] += 1
                logger.info(f"[STT] Local transcription succeeded ({len(raw['text'])} chars)")

            except Exception as local_err:
                self._stats["failures"] += 1
                raise RuntimeError(
                    f"Both STT engines failed.\n"
                    f"  Groq error:          {groq_err}\n"
                    f"  faster-whisper error: {local_err}"
                )

        duration_ms = (time.perf_counter() - t0) * 1000
        detected_lang = raw.get("language", language or "en")
        text = raw.get("text", "")

        return TranscriptionResult(
            text=text,
            language=detected_lang,
            language_name=SUPPORTED_LANGUAGES.get(detected_lang, detected_lang),
            confidence=0.95 if engine == "groq" else 0.80,
            engine=engine,
            duration_ms=duration_ms,
            word_count=len(text.split()) if text else 0,
        )

    def get_stats(self) -> dict:
        return {
            **self._stats,
            "models": {
                "primary": "groq/whisper-large-v3",
                "fallback": f"faster-whisper/{WHISPER_MODEL_SIZE}",
            },
            "supported_languages": SUPPORTED_LANGUAGES,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

stt_service = STTService()
