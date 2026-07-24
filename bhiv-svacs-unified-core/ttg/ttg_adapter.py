import json


def generate_ttg_event():

    ttg_event = {
        "ttg_event": "SUSPICIOUS_SUBMARINE",
        "zone": "Arabian Sea",
        "threat_level": "MEDIUM"
    }

    with open("ttg/ttg_runtime_bridge.json", "w") as f:
        json.dump(ttg_event, f, indent=2)

    return ttg_event
