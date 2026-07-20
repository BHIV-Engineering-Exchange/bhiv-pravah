import os
from TTS.api import TTS
import torch

def download_models():
    print("Initializing Coqui XTTS v2 model download...")
    
    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    try:
        # This will trigger the download and validation of the XTTS v2 model
        # The model is usually saved to %APPDATA%/tts (Windows) or ~/.local/share/tts (Linux)
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("Model download complete and verified.")
    except Exception as e:
        print(f"Error during model download: {e}")

if __name__ == "__main__":
    download_models()
