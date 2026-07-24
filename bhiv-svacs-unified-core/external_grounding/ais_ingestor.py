
import pandas as pd
import json
import uuid
import os

os.makedirs("runtime", exist_ok=True)

csv_path = "datasets/ais/ais_runtime_data.csv"

df = pd.read_csv(csv_path)

df = df.head(10)

runtime_records = []

for _, row in df.iterrows():

    runtime_records.append({
        "trace_id": str(uuid.uuid4()),
        "mmsi": str(row["MMSI"]),
        "lat": row["LAT"],
        "lon": row["LON"],
        "speed": row["SOG"],
        "vessel_type": row["VesselType"]
    })

with open(
    "runtime/runtime_ais_trace.json",
    "w"
) as f:
    json.dump(runtime_records, f, indent=2)

print("AIS RUNTIME GENERATED")
