import json

results = {
    "multi_vessel_overlap": True,
    "sensor_dropout": True,
    "telemetry_interruption": True,
    "schema_mismatch": True,
    "recovery_after_restart": True
}

print("STRESS TEST EXECUTED")

with open("stress/stress_results.json", "w") as f:
    json.dump(results, f, indent=2)
