"""Verify Render deployment matches expected Bucket contract."""
import json
import sys

import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://bhiv-bucket.onrender.com"
EXPECTED = {"trace_id"}


def main() -> int:
    print(f"Checking {BASE_URL}/bucket/schema-info ...")
    response = requests.get(f"{BASE_URL}/bucket/schema-info", timeout=90)
    response.raise_for_status()
    data = response.json()
    allowed = set(data.get("allowed_envelope_fields", []))
    required = set(data.get("required_fields", []))
    missing_allowed = EXPECTED - allowed
    missing_required = EXPECTED - required

    print(json.dumps(data, indent=2))
    if missing_allowed or missing_required:
        print("\nDEPLOY MISMATCH:")
        if missing_allowed:
            print(f"  missing from allowed_envelope_fields: {sorted(missing_allowed)}")
        if missing_required:
            print(f"  missing from required_fields: {sorted(missing_required)}")
        print("\nTrigger Manual Deploy on Render (branch: main) or enable Auto-Deploy.")
        return 1

    print("\nDEPLOY OK: schema matches expected contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
