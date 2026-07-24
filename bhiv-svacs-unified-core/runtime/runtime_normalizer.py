def normalize_runtime(runtime_data):

    normalized = []

    for item in runtime_data:

        runtime_event = item.get("runtime_event", {})
        intelligence = item.get("intelligence", {})
        state = item.get("state", {})
        metadata = item.get("metadata", {})

        normalized.append({

            "trace_id": item.get("trace_id"),

            "vessel_id": runtime_event.get(
                "mmsi",
                "UNKNOWN"
            ),

            "signal_strength": runtime_event.get(
                "signal_strength",
                0.8
            ),

            "timestamp": runtime_event.get(
                "timestamp",
                "2026-06-01T10:00:00"
            ),

            "classification": intelligence.get(
                "classification",
                "UNKNOWN"
            ),

            "confidence": intelligence.get(
                "confidence",
                0.5
            ),

            "risk": intelligence.get(
                "risk",
                "LOW"
            ),

            "validation": intelligence.get(
                "validation",
                "ALLOW"
            ),

            "state": state.get(
                "status",
                "TRANSIT"
            ),

            "lat": runtime_event.get(
                "lat",
                0
            ),

            "lon": runtime_event.get(
                "lon",
                0
            ),

            "speed": runtime_event.get(
                "speed",
                0
            ),

            "vessel_class": metadata.get(
                "vessel_class",
                "UNKNOWN"
            )
        })

    return normalized