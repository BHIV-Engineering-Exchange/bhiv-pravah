import os
import torch
import uuid
from TTS.api import TTS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VaaniInterface")

class VaaniEngine:
    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        os.environ["COQUI_TOS_AGREED"] = "1"
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading Vaani model: {self.model_name} on {self.device}...")
            self.model = TTS(self.model_name).to(self.device)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Vaani model initialization failed: {e}")

    def generate_voice(self, text, language="en", voice_profile="vaani_teacher", reference_dir="voice_samples", output_dir="audio_samples"):
        """
        Standardized interface for voice generation.
        """
        # 1. Input Validation & Stabilization
        if not text or not text.strip():
            logger.warning("Empty text received. Returning early to prevent crash.")
            return None, "Empty text provided"

        # Ensure directories exist
        os.makedirs(output_dir, exist_ok=True)

        # 2. Reference Voice Selection
        # Default to reference.wav, fallback to first wav in reference_dir
        ref_path = os.path.join(reference_dir, "reference.wav")
        if not os.path.exists(ref_path):
            refs = [f for f in os.listdir(reference_dir) if f.endswith('.wav')]
            if not refs:
                return None, "No reference voice samples found"
            ref_path = os.path.join(reference_dir, refs[0])

        # 3. Output Path Generation
        filename = f"voice_{uuid.uuid4()}.wav"
        output_path = os.path.join(output_dir, filename)

        # 4. Inference Execution
        try:
            logger.info(f"Generating voice for text length: {len(text)} | Lang: {language}")
            self.model.tts_to_file(
                text=text,
                speaker_wav=ref_path,
                language=language.lower(),
                file_path=output_path
            )
            return output_path, None
        except Exception as e:
            logger.error(f"Inference crash: {e}")
            return None, str(e)

# Singleton instance for the service
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = VaaniEngine()
    return _engine

def generate_voice(text, language="en", voice_profile="vaani_teacher"):
    """
    Standalone function interface as required by the spec.
    """
    engine = get_engine()
    return engine.generate_voice(text, language, voice_profile)
