# Vaani TTS Portable Service

A standalone, portable text-to-speech service with prosody and tone support, extracted from the Gurukul project.

## Features
- **High-Quality Speech**: Uses Google TTS (gTTS) for natural-sounding audio.
- **Offline Fallback**: Automatically falls back to system voices (`pyttsx3`) if offline.
- **Prosody Mapping**: Support for different tones (educational, excited, formal, etc.) through the Vaani prosody mapper.
- **Multilingual**: Built-in support for multiple languages including Arabic, English, Hindi, and more.
- **Translation**: Integrated translation fallback via Groq API.

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration (Optional)

For translation support, set the following environment variables:
- `GROQ_API_KEY`: Your Groq API key.
- `GROQ_MODEL_NAME`: (Optional) Default model to use.

## Usage

See `example.py` for a detailed demonstration of how to integrate and use the service.

```python
from tts_service import text_to_speech_stream
from prosody_mapper import generate_prosody_hint

# Generate a prosody-aware audio stream
audio_data = text_to_speech_stream("Hello world", language="en")
```

## Folder Structure
- `tts_service.py`: Core logic for audio generation and translation.
- `prosody_mapper.py`: Service for mapping tones to speech patterns.
- `data/prosody_mappings.json`: Data configuration for languages/tones.
- `example.py`: Getting started script.
