import os
import sys
import subprocess
import logging
import httpx
import threading
from app.core.config import settings

logger = logging.getLogger("VaaniManager")

class VaaniManager:
    """
    Manages the background provisioning and readiness state of the Vaani/XTTS engine.
    Ensures that multi-GB downloads don't block the main application and provides
    fast feedback to the VoiceProvider for tiered fallbacks.
    """
    _instance = None
    _lock = threading.Lock()
    _downloading = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VaaniManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.vaani_url = settings.VAANI_API_URL
        self.download_script = os.path.join(
            os.path.dirname(__file__), "..", "..", "scripts", "download_xtts.py"
        )

    async def is_ready(self) -> bool:
        """
        Check if the Vaani engine is up and its model is loaded.
        Returns False instantly if the engine is unreachable or still initializing.
        """
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(f"{self.vaani_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("model_loaded", False)
                return False
        except Exception:
            # Engine not running or unreachable
            return False

    def trigger_download(self):
        """
        Triggers the download_xtts.py script.
        This should be called within a FastAPI BackgroundTask.
        """
        if self._downloading:
            logger.info("Download already in progress. Skipping duplicate trigger.")
            return

        with self._lock:
            if self._downloading:
                return
            self._downloading = True

        try:
            logger.info(f"Starting background XTTS download via {self.download_script}...")
            
            # Run the download script as a subprocess
            # We use sys.executable to ensure we use the same environment
            result = subprocess.run(
                [sys.executable, self.download_script],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("XTTS download completed successfully.")
            logger.debug(f"Download output: {result.stdout}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"XTTS download failed with exit code {e.returncode}: {e.stderr}")
        except Exception as e:
            logger.error(f"Error while triggering XTTS download: {e}")
        finally:
            with self._lock:
                self._downloading = False

# Singleton instance
vaani_manager = VaaniManager()
