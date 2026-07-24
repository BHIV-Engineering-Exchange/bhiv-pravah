import pandas as pd
import uuid
import json


def ingest_ais_data():

    print("STEP 1: Reading CSV...")

    df = pd.read_csv("data/ais/ais_runtime_data.csv")

    print("CSV LOADED SUCCESSFULLY")
    print(df.columns)

    runtime_events = []

    for _, row in df.head(5).iterrows():

        print("Processing Row...")

        event = {
            "trace_id": str(uuid.uuid4()),
            "mmsi": str(row["MMSI"]),
            "timestamp": str(row["BaseDateTime"]),
            "lat": float(row["LAT"]),
            "lon": float(row["LON"]),
            "speed": float(row["SOG"]),
            "vessel_type": str(row["VesselType"])
        }

        runtime_events.append(event)

    print("Creating Logs Folder Output...")

    with open("logs/ais_runtime_trace.json", "w") as f:
        json.dump(runtime_events, f, indent=2)

    print("INGESTION SUCCESS")

    return runtime_events
