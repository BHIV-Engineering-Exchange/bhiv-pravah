import requests
import json

def test_maritime_ingest():
    url = "http://localhost:3000/api/v1/bucket/artifact/write"
    
    payload = {
        "artifact_id": "AIS-TEST-001",
        "content": {
            "vessel_type": "Tanker",
            "vessel_name": "BHIV Explorer",
            "confidence_score": 0.99,
            "anomaly_flag": True,
            "coordinates": {"lat": 18.9220, "lon": 72.8347}
        },
        "metadata": {
            "trace_id": "MARITIME-HARDENING-001",
            "product": "maritime_intel",
            "parent_hash": "d72681871b90e95b3cde9a4c50e859a2ecd2a44a"
        }
    }
    
    print(f"Testing ingestion to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_maritime_ingest()
