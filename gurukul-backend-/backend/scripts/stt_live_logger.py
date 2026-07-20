"""
stt_live_logger.py — Gurukul Multilingual Test Log Generator
=============================================================

This script performs real-world tests for all 6 supported languages.
It captures the actual JSON response from the /voice/listen endpoint
and saves it to a 'multilingual_test_logs.json' file.

Prerequisite:
  1. Backend must be running (uvicorn app.main:app --port 3000)
  2. GROQ_API_KEY must be set in .env
  3. You must have sample audio files for each language in a 'data/samples/' folder.

Run:
    python scripts/stt_live_logger.py
"""

import os
import requests
import json
import time

API_URL = "http://localhost:3000/api/v1/voice/listen"
LANGUAGES = ["en", "hi", "ar", "es", "fr", "ja"]
SAMPLES_DIR = "scripts/samples"  # Put your test .wav files here

def generate_logs():
    print("\n" + "="*50)
    print(" Gurukul STT - Multilingual Log Generator")
    print("="*50 + "\n")

    logs = []

    for lang in LANGUAGES:
        audio_path = os.path.join(SAMPLES_DIR, f"sample_{lang}.wav")
        
        if not os.path.exists(audio_path):
            print(f"[-] [SKIP] No audio file found for {lang}: {audio_path}")
            continue

        print(f"[*] [TEST] Transcribing {lang} ({audio_path})...")
        
        try:
            with open(audio_path, "rb") as f:
                files = {"audio": (os.path.basename(audio_path), f, "audio/wav")}
                data = {"language": lang}
                
                t0 = time.perf_counter()
                resp = requests.post(API_URL, files=files, data=data)
                duration = (time.perf_counter() - t0) * 1000

                if resp.status_code == 200:
                    result = resp.json()
                    log_entry = {
                        "language_code": lang,
                        "status": "SUCCESS",
                        "response": result,
                        "actual_latency_ms": round(duration, 2)
                    }
                    print(f" [+] [OK]  Transcript: {result['transcript'][:50]}...")
                    logs.append(log_entry)
                else:
                    print(f" [!] [FAIL] Status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f" [!] [ERR] {e}")

    # Save to file
    output_path = "multilingual_test_logs.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": "Gurukul Sovereign Runtime",
            "test_results": logs
        }, f, indent=2, ensure_ascii=False)

    print(f"\n" + "="*50)
    print(f" COMPLETE: Captured {len(logs)} logs.")
    print(f" Results saved to: {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Create samples dir if missing
    if not os.path.exists(SAMPLES_DIR):
        os.makedirs(SAMPLES_DIR)
        print(f"[*] Created {SAMPLES_DIR}. Please place sample_.wav files there.")
    else:
        generate_logs()
