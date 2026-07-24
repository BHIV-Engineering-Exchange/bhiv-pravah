import json

with open("governance/dataset_governance_registry.json") as f:
    data = json.load(f)

required_fields = [
    "dataset_owner",
    "dataset_trust_score",
    "dataset_origin",
    "approval_state",
    "validation_status",
    "dataset_expiry_policy",
    "federated_registry_reference",
    "dataset_change_log",
    "source_confidence", 
    "schema_authority_reference"
]

valid = True

for dataset in data:
    for field in required_fields:
        if field not in dataset:
            valid = False

if valid:
    print("DATASET_GOVERNANCE_VALID")
else:
    print("DATASET_GOVERNANCE_INVALID")
