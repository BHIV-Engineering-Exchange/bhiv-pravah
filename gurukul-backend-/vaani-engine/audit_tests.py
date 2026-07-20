import requests
import os
import time

API_URL = "http://127.0.0.1:8008/voice/speak"

def run_test(name, text, lang="en"):
    print(f"\n[TEST] {name} | Lang: {lang}")
    start = time.time()
    try:
        response = requests.post(API_URL, json={
            "text": text,
            "language": lang
        }, timeout=120)
        
        duration = time.time() - start
        if response.status_code == 200:
            print(f"✅ Pass! ({duration:.2f}s)")
            return True, duration
        else:
            print(f"❌ Fail! Status: {response.status_code} | Error: {response.text}")
            return False, duration
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, 0

if __name__ == "__main__":
    tests = [
        ("Short English", "Knowledge is power.", "en"),
        ("Hindi Support", "नमस्ते, ब्लैकहोल इन्फिवर्स में आपका स्वागत है।", "hi"),
        ("Arabic Support", "مرحبا بكم في كوروكل. نحن نتعلم التقنيات الحديثة.", "ar"),
        ("Long Text", "The ancient Vedic wisdom emphasizes the unity of the self with the ultimate reality. This philosophy has inspired millions for millennia. In modern times, technology acts as a bridge to bring this knowledge back to the global community in an accessible way. We are building the future by looking at the past.", "en"),
        ("Special Characters", "What happens with $#@! & symbols or numbers like 1234567890?", "en"),
        ("Empty String", "", "en"),
    ]
    
    results = []
    for name, text, lang in tests:
        success, duration = run_test(name, text, lang)
        results.append((name, success, duration))
    
    print("\n" + "="*30)
    print("AUDIT SUMMARY")
    print("="*30)
    for name, success, duration in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {duration:.2f}s")
