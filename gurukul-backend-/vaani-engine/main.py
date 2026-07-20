from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import torch
from TTS.api import TTS
import time

app = FastAPI(title="Vaani Sovereign TTS Engine")

# Configuration
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
OUTPUT_DIR = "audio_samples"
REFERENCE_DIR = "voice_samples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global model variable
tts_model = None

class SpeakRequest(BaseModel):
    text: str
    language: str = "en"
    voice_profile: str = "vaani_teacher"

@app.on_event("startup")
async def load_model():
    global tts_model
    print("Initializing Vaani Engine...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.environ["COQUI_TOS_AGREED"] = "1"
    try:
        tts_model = TTS(MODEL_NAME).to(device)
        print(f"Vaani Engine ready on {device}")
    except Exception as e:
        print(f"Failed to load model: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy" if tts_model else "initializing", "device": str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() else "cpu"}

@app.post("/vaani/speak")
async def speak(request: SpeakRequest):
    if not tts_model:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    filename = f"speak_{uuid.uuid4()}.wav"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Selection of reference voice - default to reference.wav for now
    ref_voice = os.path.join(REFERENCE_DIR, "reference.wav")
    
    if not os.path.exists(ref_voice):
        # Fallback to any file in reference dir
        refs = [f for f in os.listdir(REFERENCE_DIR) if f.endswith('.wav')]
        if refs:
            ref_voice = os.path.join(REFERENCE_DIR, refs[0])
        else:
            raise HTTPException(status_code=500, detail="No reference voice samples found")

    try:
        start_time = time.time()
        tts_model.tts_to_file(
            text=request.text,
            speaker_wav=ref_voice,
            language=request.language,
            file_path=filepath
        )
        duration = time.time() - start_time
        print(f"Generated speech in {duration:.2f}s")
        
        return FileResponse(
            path=filepath,
            media_type="audio/wav",
            filename=filename
        )
    except Exception as e:
        print(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
