import requests
import concurrent.futures
import time
import os

API_URL = "http://127.0.0.1:8008/voice/speak"
OUTPUT_DIR = "audio_samples/stress_test"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def send_request(i):
    text = f"Stress test request number {i}. This is a stability check for the Vaani engine."
    start = time.time()
    try:
        response = requests.post(API_URL, json={"text": text, "language": "en"}, timeout=60)
        duration = time.time() - start
        if response.status_code == 200:
            return i, True, duration
        else:
            return i, False, duration
    except Exception as e:
        return i, False, str(e)

if __name__ == "__main__":
    CONCURRENT_REQUESTS = 5
    print(f"Starting Stress Test: {CONCURRENT_REQUESTS} concurrent requests...")
    
    start_all = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(send_request, i) for i in range(CONCURRENT_REQUESTS)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    total_duration = time.time() - start_all
    
    print("\n" + "="*30)
    print("STRESS TEST RESULTS")
    print("="*30)
    success_count = sum(1 for r in results if r[1])
    for i, success, duration in sorted(results):
        status = "✅" if success else "❌"
        print(f"Request {i}: {status} ({duration if isinstance(duration, float) else 'ERR'}s)")
    
    print(f"\nTotal Success: {success_count}/{CONCURRENT_REQUESTS}")
    print(f"Total Time: {total_duration:.2f}s")
    print(f"System Throughput: {CONCURRENT_REQUESTS/total_duration:.2f} req/s")
