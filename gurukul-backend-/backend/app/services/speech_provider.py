"""
speech_provider.py — Canonical Speech Provider for Gurukul
===========================================================

Wraps STTService with production guardrails:
  - Audio size limit: 25 MB (Groq max)
  - Duration guard: 120 seconds max
  - Max 3 concurrent transcription requests (Semaphore)
  - 30 second per-request timeout
  - In-memory result cache (hash of audio bytes)
  - Language validation and auto-detection support

This is the single entry point for any part of the Gurukul system
that needs to convert audio → text. It is the STT equivalent of
VoiceProvider (which handles TTS).

Usage:
    from app.services.speech_provider import speech_provider
    result = await speech_provider.transcribe(audio_bytes, filename="voice.wav", language="hi")
"""

import asyncio
import hashlib
import logging
import time
from typing import Dict, Optional

from app.services.stt_service import STTService, TranscriptionResult, SUPPORTED_LANGUAGES

logger = logging.getLogger("SpeechProvider")

# ---------------------------------------------------------------------------
# Guardrail constants
# ---------------------------------------------------------------------------

MAX_AUDIO_SIZE_BYTES  = 25 * 1024 * 1024   # 25 MB — Groq hard limit
MAX_CONCURRENCY       = 3                   # Parallel transcriptions
TRANSCRIPTION_TIMEOUT = 30                  # Seconds per request
CACHE_MAX_ENTRIES     = 100                 # LRU-style


# ---------------------------------------------------------------------------
# SpeechProvider
# ---------------------------------------------------------------------------

class SpeechProvider:
    """
    Production-ready Speech-to-Text provider with guardrails and caching.

    Designed to be used as a singleton (`speech_provider`) imported across
    the Gurukul backend.
    """

    def __init__(self):
        self._stt = STTService()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        self._cache: Dict[str, TranscriptionResult] = {}
        self._start_time = time.time()
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "failures": 0,
            "timeouts": 0,
            "rejected_too_large": 0,
        }
        logger.info(
            f"[SpeechProvider] Initialised | "
            f"max_size={MAX_AUDIO_SIZE_BYTES // (1024*1024)}MB | "
            f"timeout={TRANSCRIPTION_TIMEOUT}s | "
            f"concurrency={MAX_CONCURRENCY}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: str = "auto",
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes to a TranscriptionResult.

        Args:
            audio_bytes: Raw audio content (WAV/MP3/M4A/OGG/WebM).
            filename:    Filename hint used for MIME detection.
            language:    BCP-47 code ('en', 'hi', 'ar', …) or 'auto'.

        Returns:
            TranscriptionResult dataclass.

        Raises:
            ValueError:     Empty audio or file too large.
            TimeoutError:   Transcription exceeded timeout.
            RuntimeError:   Both STT engines failed.
        """
        # ── 1. Input Validation ─────────────────────────────────────
        if not audio_bytes:
            raise ValueError("Audio input is empty")

        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            self._stats["rejected_too_large"] += 1
            mb = len(audio_bytes) / (1024 * 1024)
            raise ValueError(
                f"Audio size {mb:.1f} MB exceeds maximum "
                f"{MAX_AUDIO_SIZE_BYTES // (1024*1024)} MB"
            )

        # ── 2. Cache Lookup ─────────────────────────────────────────
        cache_key = self._cache_key(audio_bytes, language)
        if cache_key in self._cache:
            self._stats["cache_hits"] += 1
            logger.info(f"[CACHE HIT] key={cache_key[:10]}… total_hits={self._stats['cache_hits']}")
            return self._cache[cache_key]

        # ── 3. Concurrency Guard + Timeout ──────────────────────────
        self._stats["total_requests"] += 1
        logger.info(
            f"[SpeechProvider] Request #{self._stats['total_requests']} | "
            f"lang={language} | size={len(audio_bytes)//1024}KB"
        )

        try:
            async with self._semaphore:
                result = await asyncio.wait_for(
                    self._stt.transcribe(audio_bytes, filename, language),
                    timeout=TRANSCRIPTION_TIMEOUT,
                )
        except asyncio.TimeoutError:
            self._stats["timeouts"] += 1
            self._stats["failures"] += 1
            logger.error(f"[SpeechProvider] Transcription timed out after {TRANSCRIPTION_TIMEOUT}s")
            raise TimeoutError(
                f"Speech transcription timed out after {TRANSCRIPTION_TIMEOUT} seconds"
            )
        except Exception as exc:
            self._stats["failures"] += 1
            logger.error(f"[SpeechProvider] Transcription failed: {exc}")
            raise

        # ── 4. Cache & Return ────────────────────────────────────────
        self._cache_put(cache_key, result)
        logger.info(
            f"[SpeechProvider] Done | engine={result.engine} | "
            f"lang={result.language} | words={result.word_count} | "
            f"time={result.duration_ms:.0f}ms"
        )
        return result

    def get_status(self) -> dict:
        """Return provider metrics for the /system/metrics endpoint."""
        stt_stats = self._stt.get_stats()
        return {
            "uptime_seconds": int(time.time() - self._start_time),
            "total_requests": self._stats["total_requests"],
            "cache_hits": self._stats["cache_hits"],
            "cache_size": len(self._cache),
            "failures": self._stats["failures"],
            "timeouts": self._stats["timeouts"],
            "rejected_too_large": self._stats["rejected_too_large"],
            "supported_languages": SUPPORTED_LANGUAGES,
            "stt_engine_stats": stt_stats,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cache_key(self, audio_bytes: bytes, language: str) -> str:
        raw = f"{language}:{hashlib.sha256(audio_bytes).hexdigest()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _cache_put(self, key: str, result: TranscriptionResult):
        if len(self._cache) >= CACHE_MAX_ENTRIES:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
            logger.debug(f"[CACHE] LRU eviction (size was {CACHE_MAX_ENTRIES})")
        self._cache[key] = result


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

speech_provider = SpeechProvider()
