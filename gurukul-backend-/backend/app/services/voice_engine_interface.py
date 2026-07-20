"""
voice_engine_interface.py — Abstract Interface for TTS in Gurukul

All voice generation MUST implement this interface.
This ensures structural discipline and deterministic behavior across providers.
"""

from abc import ABC, abstractmethod


class VoiceEngineInterface(ABC):
    """
    Standard interface for all text-to-speech requests in Gurukul.
    Ensures structural discipline and deterministic behavior.
    """

    @abstractmethod
    async def generate_audio(self, text: str, language: str = "en") -> bytes:
        """
        Convert text to speech data (bytes).

        Args:
            text (str): The text to synthesize.
                        - Must not be empty.
                        - Must not exceed 5000 characters.
            language (str): ISO 639-1 language code.

        Returns:
            bytes: The synthesized audio data (WAV format).

        Raises:
            ValueError:   If text is empty or exceeds 5000 characters.
            TimeoutError: If inference exceeds 20 seconds.
            RuntimeError: If voice generation fails after retries.
        """
        pass

    @abstractmethod
    def get_status(self) -> dict:
        """
        Return the operational status of the voice engine.

        Expected fields:
            - uptime_seconds (int)
            - total_requests (int)
            - failure_count (int)
            - gpu_mode (bool)
            - cache_size (int)
        """
        pass
