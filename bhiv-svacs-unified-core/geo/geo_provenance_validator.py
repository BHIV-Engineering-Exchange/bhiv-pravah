import json

with open("geo/geo_provenance_schema.json") as f:
    data = json.load(f)

required = [
    "geo_source_lineage",
    "coordinate_origin",
    "sensor_origin", 
    "spatial_uncertainty",
    "timestamp_uncertainty",
    "coordinate_confidence",
    "geo_transformation_history",
    "location_reference_version",
    "geo_validation_status"
]

valid = all(field in data for field in required)

if valid:
    print("GEO_PROVENANCE_VALID")
else:
    print("GEO_PROVENANCE_INVALID")
