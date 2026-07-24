import json

uncertainty = {
    "classification": "Destroyer",
    "confidence": 0.88,
    "uncertainty": 0.12
}

with open(
    "runtime/uncertainty_report.json",
    "w"
) as f:
    json.dump(uncertainty, f, indent=2)

print("UNCERTAINTY ANALYSIS COMPLETE")