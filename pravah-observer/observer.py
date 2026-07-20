#!/usr/bin/env python3
"""Simple log‑tail observer for ai‑crm.
   Reads /app/logs/*.log inside the container, parses new lines, and POSTs
   them to the Pravah Decision Brain endpoint.
"""
import os, time, json, hmac, hashlib, pathlib, requests

OBSERVER_URL = os.getenv(
    "PRAVAH_OBSERVER_URL", "http://host.docker.internal:8000/api/runtime"
)
HMAC_KEY = os.getenv("PRAVAH_OBSERVER_KEY", "")
LOG_DIR = os.getenv("AI_CRM_LOG_DIR", "/app/logs")

def sign_payload(payload: dict) -> str:
    if not HMAC_KEY:
        return ""
    mac = hmac.new(HMAC_KEY.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256)
    return mac.hexdigest()

def send_event(event: dict):
    headers = {"Content-Type": "application/json"}
    sig = sign_payload(event)
    if sig:
        headers["X-Pravah-Signature"] = sig
    try:
        resp = requests.post(OBSERVER_URL, json=event, headers=headers, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[observer] failed to send event: {e}")

def tail_file(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            event = {
                "app_id": "ai-crm",
                "event_type": "log_line",
                "timestamp": time.time(),
                "data": {"filename": str(path), "line": line.rstrip()},
            }
            send_event(event)

def main():
    log_dir = pathlib.Path(LOG_DIR)
    if not log_dir.is_dir():
        print(f"[observer] log directory {LOG_DIR} not found")
        return
    while True:
        for log_file in log_dir.glob("*.log"):
            tail_file(log_file)
        time.sleep(1)

if __name__ == "__main__":
    main()
