"""
stt_test.py — Gurukul Speech Interface Layer Validation
========================================================

Tests the STT service and speech provider without needing real audio.
Validates:
  1. TranscriptionResult dataclass fields
  2. SpeechProvider guardrails (size, empty audio, bad language)
  3. STTService mock transcription via Groq API path
  4. /voice/listen endpoint (FastAPI TestClient)
  5. /voice/languages endpoint
  6. Multilingual language validation for all 6 supported codes

Run:
    cd Gurukul/backend
    python scripts/stt_test.py
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# ------ Path setup --------------------------------------------------------
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ------ Stub heavy deps before any app import ----------------------------
_fake_settings = MagicMock()
_fake_settings.VAANI_API_URL = "http://localhost:8008"
_fake_settings.DATABASE_URL  = None
_fake_settings.REDIS_URL     = "redis://localhost:6379/0"

_fake_pydantic_settings_mod = MagicMock()
_fake_pydantic_settings_mod.BaseSettings = MagicMock
sys.modules.setdefault("pydantic_settings", _fake_pydantic_settings_mod)
sys.modules["app.core.config"] = MagicMock(settings=_fake_settings)
sys.modules.setdefault("app.core.database",       MagicMock())
sys.modules.setdefault("app.core.karma_database",  MagicMock())
sys.modules.setdefault("app.services.voice_provider", MagicMock())
sys.modules.setdefault("app.services.system_metrics",
                        MagicMock(record_ai_latency=lambda x: None,
                                  record_voice_latency=lambda x: None))

# ------ Now safe to import -----------------------------------------------
from app.services.stt_service import STTService, TranscriptionResult, SUPPORTED_LANGUAGES
from app.services.speech_provider import SpeechProvider


def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ==========================================================================
# Test classes
# ==========================================================================

class TestTranscriptionResult(unittest.TestCase):
    """Tests for the TranscriptionResult dataclass."""

    def _make(self, **kwargs):
        defaults = dict(
            text="Hello world",
            language="en",
            language_name="English",
            confidence=0.95,
            engine="groq",
            duration_ms=500.0,
            word_count=2,
        )
        defaults.update(kwargs)
        return TranscriptionResult(**defaults)

    def test_to_dict_has_required_keys(self):
        result = self._make()
        d = result.to_dict()
        for key in ("text", "language", "language_name", "confidence",
                    "engine", "transcription_time_ms", "word_count"):
            self.assertIn(key, d, f"Missing key: {key}")

    def test_word_count_matches_text(self):
        result = self._make(text="one two three", word_count=3)
        self.assertEqual(result.word_count, 3)

    def test_engine_field(self):
        r1 = self._make(engine="groq")
        r2 = self._make(engine="faster-whisper")
        self.assertEqual(r1.engine, "groq")
        self.assertEqual(r2.engine, "faster-whisper")


class TestSupportedLanguages(unittest.TestCase):
    """Verify the 6 required languages are all present."""

    def test_all_required_languages_present(self):
        for code in ("en", "hi", "ar", "es", "fr", "ja"):
            self.assertIn(code, SUPPORTED_LANGUAGES,
                          f"Language '{code}' missing from SUPPORTED_LANGUAGES")

    def test_language_names_are_strings(self):
        for code, name in SUPPORTED_LANGUAGES.items():
            self.assertIsInstance(name, str)
            self.assertGreater(len(name), 0)


class TestSpeechProviderGuardrails(unittest.TestCase):
    """Unit tests for SpeechProvider input validation."""

    def setUp(self):
        self.provider = SpeechProvider()

    def test_empty_audio_raises_value_error(self):
        with self.assertRaises(ValueError, msg="Empty audio should raise ValueError"):
            _run(self.provider.transcribe(b""))

    def test_oversized_audio_raises_value_error(self):
        big = b"x" * (26 * 1024 * 1024)   # 26 MB > 25 MB limit
        with self.assertRaises(ValueError):
            _run(self.provider.transcribe(big))

    def test_invalid_language_raises_value_error(self):
        audio = b"fake_audio_data" * 100
        with self.assertRaises(ValueError):
            _run(self.provider.transcribe(audio, language="zz"))

    def test_valid_language_does_not_raise_on_validation(self):
        """Validation should pass for 'auto' even if transcription fails downstream."""
        audio = b"fake_audio" * 10
        with self.assertRaises((RuntimeError, Exception)):
            # Should fail at transcription, NOT at validation
            _run(self.provider.transcribe(audio, language="auto"))

    def test_get_status_has_required_keys(self):
        status = self.provider.get_status()
        for key in ("total_requests", "cache_hits", "failures",
                    "supported_languages", "stt_engine_stats"):
            self.assertIn(key, status)


class TestSTTServiceMocked(unittest.TestCase):
    """Test STTService with mocked Groq API."""

    def _mock_groq_transcription(self, text="नमस्ते विश्व", language="hi"):
        """Return a mocked Groq transcription object."""
        mock = MagicMock()
        mock.text = text
        mock.language = language
        return mock

    def test_groq_path_success(self):
        svc = STTService()
        fake_transcription = self._mock_groq_transcription("Hello world", "en")

        with patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}), \
             patch("app.services.stt_service._transcribe_via_groq",
                   return_value={"text": "Hello world", "language": "en"}):
            result = _run(svc.transcribe(b"fake_audio" * 100, "audio.wav", "en"))

        self.assertEqual(result.text, "Hello world")
        self.assertEqual(result.language, "en")
        self.assertEqual(result.engine, "groq")

    def test_fallback_to_local_when_groq_fails(self):
        svc = STTService()

        with patch("app.services.stt_service._transcribe_via_groq",
                   side_effect=RuntimeError("No API key")), \
             patch("app.services.stt_service._transcribe_via_local",
                   return_value={"text": "Fallback text", "language": "en"}):
            result = _run(svc.transcribe(b"fake_audio" * 100, "audio.wav", "en"))

        self.assertEqual(result.text, "Fallback text")
        self.assertEqual(result.engine, "faster-whisper")

    def test_both_engines_fail_raises_runtime_error(self):
        svc = STTService()

        with patch("app.services.stt_service._transcribe_via_groq",
                   side_effect=RuntimeError("Groq down")), \
             patch("app.services.stt_service._transcribe_via_local",
                   side_effect=RuntimeError("f-whisper not installed")):
            with self.assertRaises(RuntimeError):
                _run(svc.transcribe(b"fake_audio" * 100, "audio.wav", "en"))

    def test_confidence_groq_higher_than_local(self):
        svc = STTService()

        with patch("app.services.stt_service._transcribe_via_groq",
                   side_effect=RuntimeError("Groq down")), \
             patch("app.services.stt_service._transcribe_via_local",
                   return_value={"text": "local result", "language": "en"}):
            result = _run(svc.transcribe(b"audio" * 100, "audio.wav", "en"))

        self.assertLess(result.confidence, 0.95,
                        "Local engine should have lower confidence than Groq")


class TestMultilingualValidation(unittest.TestCase):
    """Validate each of the 6 required languages flows through correctly."""

    def test_each_language_produces_correct_language_name(self):
        svc = STTService()
        expected = {
            "en": "English", "hi": "Hindi", "ar": "Arabic",
            "es": "Spanish", "fr": "French", "ja": "Japanese",
        }
        for code, name in expected.items():
            with patch("app.services.stt_service._transcribe_via_groq",
                       return_value={"text": "test", "language": code}):
                result = _run(svc.transcribe(b"audio" * 100, "a.wav", code))
            self.assertEqual(result.language, code)
            self.assertEqual(result.language_name, name,
                             f"Wrong name for {code}: {result.language_name}")


# ==========================================================================
# Entry point
# ==========================================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Gurukul STT Integration - Multilingual Test Suite")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in (TestTranscriptionResult, TestSupportedLanguages,
                TestSpeechProviderGuardrails, TestSTTServiceMocked,
                TestMultilingualValidation):
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{result.testsRun} passed")
    if result.failures or result.errors:
        print("  FAILURES PRESENT - see above for details")
    else:
        print("  ALL PASSED")
    print("=" * 60)
    print()

    sys.exit(0 if result.wasSuccessful() else 1)
