import sys
import os
import logging

# Setup path for VaaniTTS_Standalone
sys.path.append(os.path.join(os.getcwd(), 'VaaniTTS_Standalone'))

from tts_service import text_to_speech_stream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vanni_test")

def test_tts_chain():
    test_text = "This is a test of the new TTS fallback system."
    
    print("\n--- Starting TTS Fallback Chain Test ---")
    
    try:
        print("\n1. Testing Full Chain (Priority: XTTS)...")
        # This will attempt XTTS first. It may fail if dependencies/models are missing,
        # which is expected in a new environment until first-run download completes.
        audio_data = text_to_speech_stream(test_text, language='en')
        print(f"Success! Generated {len(audio_data)} bytes of audio.")
        
        # Save output for manual verification
        with open("tts_verification_output.wav", "wb") as f:
            f.write(audio_data)
        print("Audio saved to 'tts_verification_output.wav'")
        
    except Exception as e:
        print(f"CRITICAL ERROR: All TTS engines failed: {e}")

if __name__ == "__main__":
    test_tts_chain()
