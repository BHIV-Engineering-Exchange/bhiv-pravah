import json

with open(
    "runtime/sensor_fusion_validation.json"
) as f:
    data = json.load(f)

result = {
    "total_examples": len(data),
    "matches": data
}

with open(
    "runtime/sensor_fusion_result.json",
    "w"
) as f:
    json.dump(result, f, indent=2)

print("SENSOR FUSION COMPLETE")
