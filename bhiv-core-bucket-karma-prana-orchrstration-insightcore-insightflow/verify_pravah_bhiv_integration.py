#!/usr/bin/env python3
"""
verify_pravah_bhiv_integration.py
==================================
Verification script to validate Pravah Bhiv execution visibility across 
the 8 BHIV runtimes.
"""

import os
import sys
import time
import requests
import json

PRAVAH_URL = os.getenv("PRAVAH_URL", "http://127.0.0.1:7000")
OBSERVER_URL = os.getenv("PRAVAH_OBSERVER", "http://127.0.0.1:8600")

BHIV_SERVICES = {
    "bhiv-karma": "http://127.0.0.1:8000/health",
    "bhiv-bucket": "http://127.0.0.1:8001/health",
    "bhiv-core": "http://127.0.0.1:8002/health",
    "bhiv-workflow": "http://127.0.0.1:8003/healthz",
    "bhiv-uao": "http://127.0.0.1:8004/health",
    "bhiv-insight-core": "http://127.0.0.1:8005/health",
    "bhiv-insight-flow-bridge": "http://127.0.0.1:8006/health",
    "bhiv-insight-flow-backend": "http://127.0.0.1:8007/health"
}

def log_result(name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"         {details}")

def main():
    print("=" * 80)
    print("  PRAVAH <-> BHIV INTEGRATION VERIFICATION")
    print("=" * 80)
    print(f"  Pravah Control Plane: {PRAVAH_URL}")
    print(f"  Pravah Observer     : {OBSERVER_URL}")
    print("=" * 80)

    # 1. Check Pravah Control Plane and Observer Health
    print("\n[1] Checking Pravah Services...")
    try:
        resp = requests.get(f"{PRAVAH_URL}/api/health", timeout=3)
        log_result("Pravah Control Plane Health", resp.status_code == 200, f"Status: {resp.status_code}")
    except Exception as e:
        log_result("Pravah Control Plane Health", False, f"Offline: {e}")

    try:
        resp = requests.get(f"{OBSERVER_URL}/health", timeout=3)
        log_result("Pravah Observer Health", resp.status_code == 200, f"Status: {resp.status_code}")
    except Exception as e:
        log_result("Pravah Observer Health", False, f"Offline: {e}")

    # 2. Check BHIV services health endpoints
    print("\n[2] Probing BHIV Service Endpoints...")
    all_bhiv_alive = True
    for name, url in BHIV_SERVICES.items():
        try:
            resp = requests.get(url, timeout=3)
            log_result(f"{name} Health", resp.status_code == 200, f"URL: {url} | Status: {resp.status_code}")
            if resp.status_code != 200:
                all_bhiv_alive = False
        except Exception as e:
            log_result(f"{name} Health", False, f"URL: {url} | Offline: {e}")
            all_bhiv_alive = False

    # 3. Check Pravah Control Plane Apps Registry
    print("\n[3] Checking Pravah Control Plane App Registries...")
    try:
        resp = requests.get(f"{PRAVAH_URL}/api/control-plane/apps", timeout=3)
        if resp.status_code == 200:
            registered_apps = [app["app_name"] for app in resp.json().get("apps", [])]
            print(f"  Registered Apps: {registered_apps}")
            for app_name in BHIV_SERVICES.keys():
                log_result(f"Registry presence: {app_name}", app_name in registered_apps)
        else:
            log_result("Fetch registered apps", False, f"Status: {resp.status_code}")
    except Exception as e:
        log_result("Fetch registered apps", False, f"Failed: {e}")

    # 4. Check Pravah Observer registered targets
    print("\n[4] Querying Observer Dashboard Status...")
    try:
        resp = requests.get(f"{OBSERVER_URL}/api/status", timeout=3)
        if resp.status_code == 200:
            obs_data = resp.json()
            tracked_services = obs_data.get("services", {})
            print(f"  Uptime Poll Cycles: {obs_data.get('poll_count')}")
            for app_name in BHIV_SERVICES.keys():
                tracked = app_name in tracked_services
                status = tracked_services.get(app_name, {}).get("status", "unknown") if tracked else "not_tracked"
                log_result(f"Observer tracking: {app_name}", tracked and status == "healthy", f"Status: {status}")
        else:
            log_result("Fetch Observer status", False, f"Status: {resp.status_code}")
    except Exception as e:
        log_result("Fetch Observer status", False, f"Failed: {e}")

    print("\n" + "=" * 80)
    print("  Verification Script Executed Successfully")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
