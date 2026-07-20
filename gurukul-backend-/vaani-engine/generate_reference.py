import pyttsx3
import os

def generate_reference(output_path):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    # Try to find a female/clear voice if possible
    for voice in voices:
        if "zira" in voice.name.lower() or "female" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    
    engine.setProperty('rate', 150)
    text = "Namaste. This is a reference voice sample for the Vaani sovereign engine. Today we will learn about ancient wisdom and modern technology."
    
    print(f"Generating reference audio at: {output_path}")
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    print("Reference audio generated.")

if __name__ == "__main__":
    os.makedirs("voice_samples", exist_ok=True)
    generate_reference("voice_samples/reference.wav")
