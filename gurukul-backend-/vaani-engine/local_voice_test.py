import os
import torch
from TTS.api import TTS

def test_inference(reference_path, output_path):
    print("Initializing XTTS v2 model...")
    # This will download the model weights (approx 2GB) on the first run
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    try:
        # Agree to the Coqui model license for automatic download
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=torch.cuda.is_available())
        # The license acceptance often needs to be passed during download or initialization
        # depending on the version. Let's try downloading explicitly if needed.
        # Alternatively, newer versions of the TTS API use a different bypass.
        os.environ["COQUI_TOS_AGREED"] = "1"
        tts.to(device)
        
        text = "Welcome to Gurukul. I am Vaani, your sovereign AI guide. Our journey into knowledge begins now."
        
        print(f"Generating speech for: '{text}'")
        tts.tts_to_file(
            text=text,
            speaker_wav=reference_path,
            language="en",
            file_path=output_path
        )
        print(f"Speech generated and saved to: {output_path}")
    except Exception as e:
        print(f"Inference failed: {e}")

if __name__ == "__main__":
    ref = "voice_samples/reference.wav"
    out = "audio_samples/local_test.wav"
    if os.path.exists(ref):
        test_inference(ref, out)
    else:
        print(f"Reference file not found: {ref}")
