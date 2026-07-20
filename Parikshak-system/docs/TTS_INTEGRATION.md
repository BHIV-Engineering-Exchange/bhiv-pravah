# 🔊 Vaani TTS Integration Guide

This document covers the integration of **Vaani TTS Standalone** into the Live Task Review Agent — enabling audio readback of evaluation results.

---

## Overview

Vaani TTS provides text-to-speech synthesis with:

- **gTTS** (Google TTS) — primary engine, returns MP3, supports 30+ languages
- **pyttsx3** — offline fallback, returns WAV, works without internet
- **Groq LLM** — optional translation layer (requires `GROQ_API_KEY`)
- **Prosody Mapper** — language/tone → pitch, speed, emphasis hints for RL-TTS

---

## Backend Integration

### File: `app/api/tts.py`

Exposes two FastAPI endpoints and bridges to `VaaniTTS_Standalone/tts_service.py`.

The module uses `sys.path` injection to import from `VaaniTTS_Standalone/`:

```python
import sys, os
_vaani_path = os.path.join(os.path.dirname(__file__), '..', '..', 'VaaniTTS_Standalone')
sys.path.insert(0, _vaani_path)
from tts_service import text_to_speech_stream
from prosody_mapper import generate_prosody_hint
```

### Environment Variables Used

Vaani TTS reads these directly from the environment (via your `.env` file):

| Variable | Used By | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | `tts_service.translate_text()` | Enables cross-lingual translation |
| `GROQ_API_ENDPOINT` | `tts_service.translate_text()` | Optional override for Groq endpoint |
| `GROQ_MODEL_NAME` | `tts_service.translate_text()` | Model fallback (default: `llama-3.3-70b-versatile`) |

> English TTS does **not** require any API key — gTTS is free for English.

---

## Frontend Integration

### Component: `src/components/TtsButton.js`

A self-contained button that fetches audio from the backend and plays it inline using the HTML5 Audio API.

**Usage:**

```jsx
// Speak the evaluation summary
<TtsButton text={review.evaluation_summary} lang="en" tone="neutral" />

// Speak a hint in educational tone
<TtsButton text={hint} lang="en" tone="educational" />

// Speak in Arabic with educational prosody
<TtsButton text="مرحبا بالعالم" lang="ar" tone="educational" />
```

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `text` | string | required | Text to synthesize |
| `lang` | string | `'en'` | BCP-47 language code |
| `tone` | string | `'educational'` | Prosody tone name |
| `className` | string | `''` | Extra CSS classes |

**Behaviour:**

- Click once → fetches audio URL, plays inline
- Click again → stops playback immediately
- Audio ends naturally → button resets to "Listen" state

### Service: `getTtsStream()` in `taskService.js`

```javascript
// Returns the URL string for the TTS audio
const audioUrl = taskService.getTtsStream(text, lang, tone);
```

---

## Supported Languages

| Code | Language | Translation Needed |
|------|----------|--------------------|
| `en` | English | No (direct) |
| `ar` | Arabic | Yes (via Groq) |
| `hi` | Hindi | Yes (via Groq) |
| `fr` | French | Yes (via Groq) |
| `de` | German | Yes (via Groq) |
| `es` | Spanish | Yes (via Groq) |
| `zh` | Chinese | Yes (via Groq) |
| `ja` | Japanese | Yes (via Groq) |

---

## Prosody Tones (Arabic)

Configured in `VaaniTTS_Standalone/data/prosody_mappings.json`:

| Tone | Pitch | Speed | Use Case |
|------|-------|-------|----------|
| `neutral` | 0.5 | 1.0 | General readback |
| `educational` | 0.6 | 0.9 | Hints and explanations |
| `excited` | 0.8 | 1.2 | Positive score announcements |

---

## Testing the TTS Endpoint

```bash
# Fetch and save MP3
curl "http://localhost:8000/api/v1/tts/speak?text=Score+is+72+out+of+100&lang=en" -o output.mp3

# Prosody hints
curl "http://localhost:8000/api/v1/tts/prosody?text=Hello&lang=ar&tone=educational"
```
