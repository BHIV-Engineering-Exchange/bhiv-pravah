import pandas as pd
import json
from pathlib import Path

# =========================
# PATHS
# =========================

csv_path = "datasets/janes/SVACS_Maritime_Knowledge_Pack .csv"

output_dir = Path("maritime_knowledge")
output_dir.mkdir(parents=True, exist_ok=True)

# =========================
# LOAD CSV
# =========================

df = pd.read_csv(csv_path)

# =========================
# CONVERT TO JSON
# =========================

records = df.to_dict(orient="records")

# =========================
# SAVE REGISTRY
# =========================

with open(
    "maritime_knowledge/maritime_knowledge_registry.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(records, f, indent=4)

# =========================
# SOURCE MANIFEST
# =========================

source_manifest = {
    "source_name": "Jane's Fighting Ships",
    "source_file": csv_path,
    "record_count": len(records),
    "version": "v1",
    "status": "INGESTED"
}

with open(
    "maritime_knowledge/janes_source_manifest.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(source_manifest, f, indent=4)

# =========================
# PROVENANCE MANIFEST
# =========================

provenance_manifest = {
    "pipeline": [
        "Guptchar Ingestion",
        "Samachar Processing",
        "Maritime Knowledge Store"
    ],
    "lineage_status": "ACTIVE",
    "replay_safe": True
}

with open(
    "maritime_knowledge/janes_provenance_manifest.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(provenance_manifest, f, indent=4)

print("Jane's ingestion completed successfully.")
