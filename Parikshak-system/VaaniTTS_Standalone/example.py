import os
from tts_service import text_to_speech_stream, speak_text_directly
from prosody_mapper import generate_prosody_hint

def demonstrate_tts():
    print("--- Vaani TTS Portable Demo ---")
    
    # 1. Simple direct speech (if system allows audio output)
    print("\n1. Testing direct speech...")
    try:
        speak_text_directly("Welcome to the Vaani TTS service.")
        print("Done.")
    except Exception as e:
        print(f"Direct speech failed (expected in some environments): {e}")

    # 2. Generate audio data (buffer)
    print("\n2. Generating audio buffer for 'Photosynthesis' in English...")
    audio_data = text_to_speech_stream("Photosynthesis is a process used by plants.", language="en")
    print(f"Generated {len(audio_data)} bytes of audio data.")

    # 3. Using Prosody Hints (Vaani Tone Support)
    print("\n3. Generating prosody-aware hint for Arabic Educational tone...")
    text_ar = "ما هي الرياضيات؟"
    prosody = generate_prosody_hint(text_ar, lang="ar", tone="educational")
    
    print(f"Text: {text_ar}")
    print(f"Tone: {prosody['tone']}")
    print(f"Pitch Adjustment: {prosody['pitch']}")
    print(f"Speed Adjustment: {prosody['speed']}")
    
    # Note: In a full integration, these prosody hints would be passed to 
    # a hardware-specific or more advanced neural TTS engine.
    # The current stream logic uses these for language/translation routing.
    
    print("\nDemo complete. Check the README.md for integration details.")

if __name__ == "__main__":
    # Optional: Set your Groq key here if you want to test translation
    # os.environ['GROQ_API_KEY'] = 'your_key_here'
    
    demonstrate_tts()
