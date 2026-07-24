import json

with open("shared/provenance_registry.json", "r") as f:
    data = json.load(f)

for item in data:

    required = [
        "schema_version",
        "dataset_version",
        "source_lineage",
        "dataset_origin",
        "replay_reference"
    ]

    valid = all(field in item for field in required)

    if valid:
        print("PROVENANCE_VALID")

    else:
        print("PROVENANCE_INVALID")
