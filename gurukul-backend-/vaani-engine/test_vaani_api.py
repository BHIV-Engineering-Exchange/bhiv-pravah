import requests
import os

def test_vaani_api(text, output_filename):
    url = "http://localhost:8008/vaani/speak"
    payload = {
        "text": text,
        "language": "en",
        "voice_profile": "vaani_teacher"
    }
    
    print(f"Sending request to Vaani API: {url}")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print(f"✅ Success! Audio saved to: {os.path.abspath(output_filename)}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_text = "This is a direct test of the Vaani sovereign engine. The integration is successful and the voice is now running locally."
    test_vaani_api(test_text, "audio_samples/api_test_output.wav")
