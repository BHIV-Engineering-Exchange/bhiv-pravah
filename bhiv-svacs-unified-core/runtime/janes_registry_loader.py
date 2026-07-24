import json

with open("data/janes_runtime_registry.json", "r") as f:
    REGISTRY = json.load(f)


def get_vessel_metadata(mmsi):
    for vessel in REGISTRY:
        if vessel["mmsi"] == str(mmsi):
            return vessel

    return {
        "vessel_class": "UNKNOWN",
        "signature_profile": "UNKNOWN",
        "propulsion_metadata": "UNKNOWN",
        "operational_role": "UNKNOWN"
    }
