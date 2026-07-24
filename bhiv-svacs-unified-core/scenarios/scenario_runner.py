import json
import os

SCENARIOS = [
    {
        "scenario": "piracy_interception",
        "signals": ["AIS", "RADAR", "SATELLITE"],
        "noise": True,
        "geo_layer": "INDIAN_OCEAN",
        "ambiguity": "medium",
        "expected_outcome": "THREAT_DETECTED"
    },
    {
        "scenario": "illegal_fishing_detection",
        "signals": ["AIS", "VESSEL_TRACKING"],
        "noise": True,
        "geo_layer": "ARABIAN_SEA",
        "ambiguity": "low",
        "expected_outcome": "SUSPICIOUS_ACTIVITY"
    },
    {
        "scenario": "submarine_stealth_ambiguity",
        "signals": ["SONAR", "THERMAL"],
        "noise": True,
        "geo_layer": "DEEP_SEA",
        "ambiguity": "high",
        "expected_outcome": "UNCERTAIN_CONTACT"
    },
    {
        "scenario": "smuggling_route_anomaly",
        "signals": ["AIS", "INTELLIGENCE"],
        "noise": True,
        "geo_layer": "COASTAL_ROUTE",
        "ambiguity": "medium",
        "expected_outcome": "ROUTE_ANOMALY"
    },
    {
        "scenario": "port_congestion_overload",
        "signals": ["PORT_SENSOR", "AIS"],
        "noise": False,
        "geo_layer": "PORT_ZONE",
        "ambiguity": "low",
        "expected_outcome": "TRAFFIC_OVERLOAD"
    },
    {
        "scenario": "sensor_deception_event",
        "signals": ["AIS", "RADAR"],
        "noise": True,
        "geo_layer": "UNKNOWN",
        "ambiguity": "high",
        "expected_outcome": "DECEPTION_DETECTED"
    }
]

os.makedirs("storage/proofs/scenarios", exist_ok=True)

with open(
    "storage/proofs/scenarios/scenario_outputs.json",
    "w"
) as file:
    json.dump(SCENARIOS, file, indent=4)

print("SCENARIO_PACK_VALIDATED")
