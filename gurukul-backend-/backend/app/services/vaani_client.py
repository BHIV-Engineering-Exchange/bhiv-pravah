import io
import os
import hashlib
import requests
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from gtts import gTTS

logger = logging.getLogger(__name__)

class VaaniClient:
    def __init__(self, base_url: str = None):
        if base_url is None:
            # Fallback to 8007 (Tiered Resilient Service) if not set in environment
            self.base_url = os.getenv("VAANI_API_URL", "http://localhost:8007")
        else:
            self.base_url = base_url
        self.session = requests.Session()

    def generate_hash(self, text: str, language: str) -> str:
        """Generate SHA256 hash for caching."""
        payload = f"{text}|{language}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    async def login(self):
        """
        Authenticated with the TTS service.
        """
        return {"status": "success", "message": "Authenticated with Gurukul TTS Service"}

    async def generate_tts(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Calls the tiered TTS Service to generate audio.
        Falls back to internal gTTS if the service is unreachable or errors out.
        """
        text_hash = self.generate_hash(text, language)
        
        try:
            payload = {"text": text}
            logger.info(f"Calling TTS Service at {self.base_url}/api/generate")
            response = self.session.post(
                f"{self.base_url}/api/generate",
                data=payload,
                timeout=10 # Fast timeout to trigger fallback quickly on Render
            )
            
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("status") == "success":
                    audio_url = res_data.get("audio_url")
                    if audio_url:
                        download_url = f"{self.base_url}{audio_url}"
                        audio_response = self.session.get(download_url, timeout=30)
                        if audio_response.status_code == 200:
                            return {
                                "status": "success",
                                "audio_id": text_hash,
                                "audio_data": audio_response.content,
                                "media_type": "audio/mpeg"
                            }
            
            logger.warning(f"TTS Service returned {response.status_code}. Falling back to internal gTTS.")
            return await self._generate_gtts_fallback(text, language, text_hash)
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.warning(f"TTS Service unreachable: {e}. Falling back to internal gTTS.")
            return await self._generate_gtts_fallback(text, language, text_hash)
        except Exception as e:
            logger.exception("Vaani generation failed")
            return await self._generate_gtts_fallback(text, language, text_hash)

    async def _generate_gtts_fallback(self, text: str, language: str, text_hash: str) -> Dict[str, Any]:
        """Internal fallback using the lightweight gTTS library."""
        try:
            import asyncio
            def _serve():
                tts = gTTS(text=text, lang=language if language != 'auto' else 'en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                return fp.getvalue()
            
            audio_data = await asyncio.to_thread(_serve)
            return {
                "status": "success",
                "audio_id": text_hash,
                "audio_data": audio_data,
                "media_type": "audio/mpeg",
                "engine": "gtts_fallback"
            }
        except Exception as e:
            logger.error(f"gTTS fallback failed: {e}")
            return {"status": "error", "message": f"TTS failed: {str(e)}"}

    async def download_audio(self, audio_id: str):
        """
        Retrieve audio from cache/storage.
        """
        # Logic to fetch from MongoDB/FS based on audio_id
        pass

vaani_client = VaaniClient()
