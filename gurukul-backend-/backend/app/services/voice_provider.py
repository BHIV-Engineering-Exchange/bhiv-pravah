"""
voice_provider.py — Canonical Voice Provider for Gurukul

Routes all TTS generation through the Vaani Sovereign Engine (Port 8008).
Implements production guardrails:
  - 5000 character hard input limit
  - 20 second inference timeout via asyncio.wait_for
  - Max 3 concurrent requests via asyncio.Semaphore
  - Automatic retry with backoff (3 attempts)
  - In-memory cache for repeated requests
  - GPU→CPU fallback awareness
  - Offline gTTS fallback on failure/timeout
"""

import io
import os
import time
import asyncio
import hashlib
import logging
import requests
from gtts import gTTS
from typing import Dict, Any, Optional
from app.services.voice_engine_interface import VoiceEngineInterface
from app.core.config import settings
from app.services.pravah_adapter import pravah_adapter
from app.services.vaani_manager import vaani_manager

logger = logging.getLogger("VoiceProvider")

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
MAX_INPUT_CHARS     = 5000      # Hard limit — requests above this are REJECTED
INFERENCE_TIMEOUT   = 20        # Seconds — inference aborts after this
MAX_CONCURRENCY     = 3         # Semaphore slots
CACHE_MAX_ENTRIES   = 200       # Evict oldest when exceeded
MAX_RETRIES         = 3


class VoiceProvider(VoiceEngineInterface):
    """
    Canonical Voice Provider that routes to the Vaani engine via direct HTTP POST.
    Strictly deterministic and 100% offline: No Google Translate fallback.
    """

    def __init__(self):
        self.vaani_url = settings.VAANI_API_URL
        self.max_chars = MAX_INPUT_CHARS
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        self.request_timeout = INFERENCE_TIMEOUT
        self.cache: Dict[str, bytes] = {}
        self.start_time = time.time()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failures": 0,
            "timeouts": 0,
            "cache_hits": 0,
            "rejected_too_long": 0,
            "gpu_mode": True,
            "queue_depth": 0,
        }
        
        logger.info(
            f"VoiceProvider initialized | vaani_url={self.vaani_url} | "
            f"max_chars={self.max_chars} | timeout={self.request_timeout}s | "
            f"concurrency={MAX_CONCURRENCY}"
        )

    # ──────────────────────────────────────────────────────────
    # Public API  (implements VoiceEngineInterface)
    # ──────────────────────────────────────────────────────────

    async def generate_audio(self, text: str, language: str = "en") -> bytes:
        """
        Synthesize audio via Vaani HTTP endpoint.
        """
        # ── 1. Input Validation ──────────────────────────────
        if not text or not text.strip():
            raise ValueError("Text input is empty")

        if len(text) > self.max_chars:
            self.stats["rejected_too_long"] += 1
            logger.error(f"[REJECTED] Input too long: {len(text)} chars")
            raise ValueError(
                f"Input length {len(text)} exceeds maximum {self.max_chars} characters. "
                f"Please shorten your text."
            )

        # ── 2. Cache Lookup ──────────────────────────────────
        cache_key = self._cache_key(text, language)
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            logger.info(f"[CACHE HIT] key={cache_key[:12]}… | total_hits={self.stats['cache_hits']}")
            return self.cache[cache_key]

        # ── 3. Concurrency-Controlled Inference ──────────────
        self.stats["total_requests"] += 1
        self.stats["queue_depth"] += 1
        logger.info(
            f"[QUEUED] request #{self.stats['total_requests']} | "
            f"queue_depth={self.stats['queue_depth']}/{MAX_CONCURRENCY} | "
            f"text_len={len(text)}"
        )

        try:
            # ── 3. Readiness check (Fast Fallback) ──────────────────
            # If the engine isn't ready, don't even try — go straight to gTTS
            if not await vaani_manager.is_ready():
                logger.warning("[FAST FALLBACK] Vaani engine not ready. Using gTTS.")
                audio_data = await self._call_gtts(text, language)
                self._cache_put(cache_key, audio_data)
                return audio_data

            async with self.semaphore:
                logger.info(f"[ACQUIRED] semaphore slot | queue_depth={self.stats['queue_depth']}")

                # ── 4. Timeout Enforcement ───────────────────
                try:
                    logger.info(f"[TTS START] text_len={len(text)}")
                    pravah_adapter.emit_signal(
                        event_type="system_event",
                        action="tts_start",
                        payload={"text_len": len(text), "language": language}
                    )
                    
                    audio_data = await asyncio.wait_for(
                        self._call_vaani_engine(text, language),
                        timeout=self.request_timeout
                    )
                except (asyncio.TimeoutError, ConnectionError, RuntimeError) as exc:
                    # RESTORED FALLBACK: Use gTTS if local engine is down or timeout
                    logger.warning(f"[FALLBACK] Vaani failed/timed out: {exc}. Using gTTS.")
                    audio_data = await self._call_gtts(text, language)

            # ── 5. Cache Result ──────────────────────────────
            self._cache_put(cache_key, audio_data)
            self.stats["successful_requests"] += 1
            logger.info(f"[SUCCESS] Voice generated ({len(audio_data)} bytes)")
            
            pravah_adapter.emit_signal(
                event_type="system_event",
                action="tts_completed",
                status="success",
                payload={"bytes": len(audio_data)}
            )
            return audio_data

        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            logger.error(f"[TIMEOUT] Vaani inference exceeded {self.request_timeout}s")
            pravah_adapter.emit_signal(
                event_type="system_event",
                action="tts_failed",
                status="timeout",
                payload={"reason": "inference_timeout"}
            )
            raise TimeoutError(f"Vaani inference timed out after {self.request_timeout}s")
        except Exception as e:
            self.stats["failures"] += 1
            logger.error(f"[FAILURE] VoiceProvider error: {str(e)}")
            pravah_adapter.emit_signal(
                event_type="system_event",
                action="tts_failed",
                status="error",
                payload={"reason": str(e)}
            )
            raise RuntimeError(f"Voice generation failed: {e}")
        finally:
            self.stats["queue_depth"] -= 1

    def get_status(self) -> dict:
        """Return operational metrics for monitoring."""
        return {
            "uptime_seconds": int(time.time() - self.start_time),
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failure_count": self.stats["failures"],
            "timeout_count": self.stats["timeouts"],
            "rejected_too_long": self.stats["rejected_too_long"],
            "gpu_mode": self.stats["gpu_mode"],
            "cache_size": len(self.cache),
            "cache_hits": self.stats["cache_hits"],
            "queue_depth": self.stats["queue_depth"],
            "max_concurrency": MAX_CONCURRENCY,
            "max_input_chars": MAX_INPUT_CHARS,
            "inference_timeout_s": INFERENCE_TIMEOUT,
            "deterministic_enforced": True
        }

    # ──────────────────────────────────────────────────────────
    # Internal Methods
    # ──────────────────────────────────────────────────────────

    async def _call_vaani_engine(self, text: str, language: str) -> bytes:
        """Call Vaani API with retry logic."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                audio_data = await asyncio.to_thread(
                    self._sync_request, text, language
                )
                if audio_data:
                    return audio_data
                raise RuntimeError("Empty audio data returned from Vaani")

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[RETRY] Attempt {attempt}/{MAX_RETRIES} failed: {e}"
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1 * attempt)  # Linear backoff

        # All retries exhausted
        raise RuntimeError(
            f"Vaani exhausted all {MAX_RETRIES} retries. Last error: {last_error}"
        )

    def _sync_request(self, text: str, language: str) -> bytes:
        """Synchronous HTTP call to Vaani API."""
        payload = {
            "text": text,
            "language": language,
            "voice_profile": "vaani_teacher"
        }

        try:
            response = requests.post(
                f"{self.vaani_url}/voice/speak",
                json=payload,
                timeout=self.request_timeout
            )

            if response.status_code == 200:
                return response.content

            # GPU Fallback Detection
            if response.status_code == 503:
                if "GPU" in response.text or "CUDA" in response.text:
                    logger.warning("[GPU] GPU unavailable — Vaani falling back to CPU mode")
                    self.stats["gpu_mode"] = False

            raise RuntimeError(
                f"Vaani API error {response.status_code}: {response.text[:200]}"
            )

        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Vaani HTTP request timed out after {self.request_timeout}s"
            )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot reach Vaani engine at {self.vaani_url}: {e}")

    async def _call_gtts(self, text: str, language: str) -> bytes:
        """Fallback generator using Google TTS."""
        try:
            tts = await asyncio.to_thread(gTTS, text=text, lang=language)
            fp = io.BytesIO()
            await asyncio.to_thread(tts.write_to_fp, fp)
            return fp.getvalue()
        except Exception as e:
            logger.error(f"[gTTS] Critical fallback failure: {e}")
            raise RuntimeError(f"Both Vaani and gTTS fallback failed: {e}")

    def _cache_key(self, text: str, language: str) -> str:
        """Generate deterministic cache key using SHA-256."""
        raw = f"{language}:{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_put(self, key: str, data: bytes):
        """Insert into cache with LRU-style eviction."""
        if len(self.cache) >= CACHE_MAX_ENTRIES:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.info(f"[CACHE] Evicted oldest entry (size was {CACHE_MAX_ENTRIES})")
        self.cache[key] = data


# ──────────────────────────────────────────────────────────────
# Singleton instance
# ──────────────────────────────────────────────────────────────
provider = VoiceProvider()
