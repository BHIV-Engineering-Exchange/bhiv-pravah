import json

with open("runtime/runtime_ais_trace.json") as f:
    ais = json.load(f)

with open(
    "maritime_knowledge/maritime_knowledge_registry.json"
) as f:
    registry = json.load(f)

joined = []

for a in ais:

    for r in registry:

        if str(a["mmsi"])[-2:] == str(r["vessel_id"])[-2:]:

            joined.append({
                "trace_id": a["trace_id"],
                "mmsi": a["mmsi"],
                "vessel_name": r["vessel_name"],
                "vessel_class": r["vessel_class"],
                "nation": r["nation"],
                "propulsion": r["propulsion"],
                "speed": a["speed"]
            })

with open(
    "runtime/runtime_vessel_metadata_flow.json",
    "w"
) as f:
    json.dump(joined, f, indent=2)

print("RUNTIME ENRICHMENT COMPLETE")
