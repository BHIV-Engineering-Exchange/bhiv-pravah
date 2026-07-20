import requests
import time
import json
import os
import sys

# LIVE FLOW TEST
try:
    print("--- LIVE FLOW: Text -> TTS ---")
    start = time.time()
    resp = requests.post(
        'http://localhost:3000/api/v1/tts/vaani', 
        json={'text':'This is a live test for the review packet to demonstrate TTS stability.', 'language': 'en'},
        timeout=30
    )
    time_taken = time.time() - start
    output_filename = "response.wav (simulated output blob)" # The backend usually returns raw audio bytes
    
    print("Input text: This is a live test for the review packet to demonstrate TTS stability.")
    print(f"Output filename: {output_filename}")
    print(f"Time taken: {time_taken:.2f} seconds")
    print(f"Response status: {resp.status_code}, Length: {len(resp.content)} bytes")
    
    # HEALTH
    health = requests.get('http://localhost:3000/system/health').json()
    print("\nHealth endpoint response JSON:")
    print(json.dumps(health, indent=2))
    
    print("\n--- FAILURE CASES ---")
    print("1: Input > 5000 chars")
    long_text = "A" * 5500
    try:
        r2 = requests.post('http://localhost:3000/api/v1/tts/vaani', json={'text': long_text, 'language': 'en'})
        print("Status code:", r2.status_code)
        print("Response:", r2.text)
    except Exception as e:
        print("Exception:", e)
        
except Exception as e:
    print("Failed script:", e)
    sys.exit(1)
