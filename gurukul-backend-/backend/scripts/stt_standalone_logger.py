"""
stt_standalone_logger.py — Gurukul Standalone Test Log Generator
================================================================

Generates actual multilingual test logs by calling STTService directly.
Uses a stubbed config to avoid pydantic-settings environment issues.

Run:
    cd Gurukul/backend
    python scripts/stt_standalone_logger.py
"""

import sys
import os
import time
import json
import asyncio
from unittest.mock import MagicMock

# ------ Ensure backend package path ---------------------------------------
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ------ Stub pydantic-dependent config -----------------------------------
# Manual .env loading to avoid pydantic issues
def load_env_key(key_name):
    env_path = os.path.join(BACKEND_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith(f"{key_name}="):
                    return line.split("=")[1].strip()
    return os.environ.get(key_name)

os.environ["GROQ_API_KEY"] = load_env_key("GROQ_API_KEY") or ""

_fake_settings = MagicMock()
_fake_settings.VAANI_API_URL = "http://localhost:8008"
_fake_settings.DATABASE_URL  = None
_fake_settings.REDIS_URL     = "redis://localhost:6379/0"

# Patch dependencies
_fake_pydantic_settings_mod = MagicMock()
_fake_pydantic_settings_mod.BaseSettings = MagicMock
sys.modules.setdefault("pydantic_settings", _fake_pydantic_settings_mod)
sys.modules["app.core.config"] = MagicMock(settings=_fake_settings)
sys.modules.setdefault("app.services.voice_provider", MagicMock())
sys.modules.setdefault("app.core.database",       MagicMock())
sys.modules.setdefault("app.core.karma_database",  MagicMock())

# ------ Import STT Service -----------------------------------------------
from app.services.stt_service import STTService

SAMPLES_DIR = "scripts/samples"
LANGUAGES = ["en", "hi", "ar"]  # We have samples for these three

async def generate_logs():
    print("\n" + "="*50)
    print(" Gurukul STT - Standalone Multilingual Log Generator")
    print("="*50 + "\n")

    svc = STTService()
    logs = []

    for lang in LANGUAGES:
        audio_path = os.path.join(SAMPLES_DIR, f"sample_{lang}.wav")
        
        if not os.path.exists(audio_path):
            print(f"[-] [SKIP] File missing for {lang}: {audio_path}")
            continue

        print(f"[*] [TEST] Transcribing {lang} via Groq API...")
        
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                
                result = await svc.transcribe(
                    audio_bytes=audio_bytes,
                    filename=os.path.basename(audio_path),
                    language=lang
                )
                
                log_entry = {
                    "language_code": lang,
                    "status": "SUCCESS",
                    "response": result.to_dict(),
                    "timestamp": time.strftime("%H:%M:%S")
                }
                print(f" [+] [OK]  Transcript: {result.text[:50]}...")
                logs.append(log_entry)
        except Exception as e:
            print(f" [!] [ERR] {lang} failed: {e}")

    # Save to file
    output_path = "multilingual_test_logs.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": "Gurukul Sovereign Runtime (Standalone Mode)",
            "test_results": logs
        }, f, indent=2, ensure_ascii=False)

    print(f"\n" + "="*50)
    print(f" COMPLETE: Captured {len(logs)} logs.")
    print(f" Results saved to: {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(generate_logs())
