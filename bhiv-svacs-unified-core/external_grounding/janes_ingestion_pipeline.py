import json
from datetime import datetime

vessels = [
    {
        "vessel_name": "Arleigh Burke",
        "class": "Destroyer",
        "nation": "USA",
        "source": "Jane's Fighting Ships",
        "page": 101,
        "edition": "Archive Edition"
    },
    {
        "vessel_name": "Type 23",
        "class": "Frigate",
        "nation": "UK",
        "source": "Jane's Fighting Ships",
        "page": 155,
        "edition": "Archive Edition"
    }
]

with open(
    "maritime_knowledge/janes_registry.json",
    "w"
) as f:
    json.dump(vessels, f, indent=2)

print("JANES INGESTION COMPLETE")