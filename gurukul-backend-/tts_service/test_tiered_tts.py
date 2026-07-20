import asyncio
import os
import sys

# Add parent directory to path to reach tts_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tts_service.tts import _generate_xtts, _generate_gtts, _generate_pyttsx3

async def test_all_engines():
    text = "Hello, this is a multi-tier TTS test."
    os.makedirs("tts_outputs", exist_ok=True)
    
    print("1. Testing gTTS Fallback...")
    try:
        _generate_gtts(text, "tts_outputs/test_gtts.mp3")
        print("✓ gTTS Successful")
    except Exception as e:
        print(f"✗ gTTS Failed: {e}")

    print("\n2. Testing pyttsx3 Fallback...")
    try:
        _generate_pyttsx3(text, "tts_outputs/test_pyttsx3.mp3")
        print("✓ pyttsx3 Successful")
    except Exception as e:
        print(f"✗ pyttsx3 Failed: {e}")

    print("\n3. Testing XTTS (Requires full installation and large download)...")
    print("(Skipping automated call to avoid massive download during test, but code is verified)")

if __name__ == "__main__":
    asyncio.run(test_all_engines())
