import os
import json
import sys

# Configure stdout encoding for Windows
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REGISTRY_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_VALIDATE = [
    {
        "filename": "authority_registry.json",
        "required_keys": ["institutions"],
        "min_items": 10
    },
    {
        "filename": "policy_registry.json",
        "required_keys": ["policies"],
        "min_items": 10
    },
    {
        "filename": "procurement_registry.json",
        "required_keys": ["channels"],
        "min_items": 10
    },
    {
        "filename": "constraint_and_failure_registries.json",
        "required_keys": ["constraint_classes", "failure_ontology"],
        "min_items": 10
    },
    {
        "filename": "sensitivity_and_ownership_registries.json",
        "required_keys": ["sensitivity_zones", "ownership_registry"],
        "min_items": 8
    },
    {
        "filename": "constraint_interaction_map.json",
        "required_keys": ["interactions"],
        "min_items": 8
    }
]

def validate_registries():
    print("=" * 80)
    print("🛡️ GURUKUL SOVEREIGN INTELLIGENCE REGISTRY VALIDATION SUITE")
    print("=" * 80)
    
    all_passed = True
    
    for item in FILES_TO_VALIDATE:
        filepath = os.path.join(REGISTRY_DIR, item["filename"])
        print(f"Validating file: {item['filename']} ...")
        
        # Check existence
        if not os.path.exists(filepath):
            print(f" [FAILED] File does not exist at {filepath}")
            all_passed = False
            continue
            
        # Parse JSON
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("  ➔ Parse status: SUCCESS")
        except Exception as e:
            print(f" [FAILED] JSON Syntax Error: {e}")
            all_passed = False
            continue
            
        # Check required schema keys
        keys_present = True
        for key in item["required_keys"]:
            if key not in data:
                print(f" [FAILED] Missing required schema key: '{key}'")
                keys_present = False
                all_passed = False
        
        if not keys_present:
            continue
            
        # Check min item counts
        first_key = item["required_keys"][0]
        items_count = len(data[first_key])
        if items_count < item["min_items"]:
            print(f" [FAILED] Items count {items_count} is less than required minimum {item['min_items']}")
            all_passed = False
            continue
            
        print(f"  ➔ Schema conformance: PASSED ({items_count} items validated)")
        print("-" * 60)
        
    print("=" * 80)
    if all_passed:
        print("🎉 ALL CANONICAL INSTITUTIONAL INTELLIGENCE REGISTRIES PASSED STRUCTURAL AUDIT!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ SOME REGISTRIES FAILED THE COMPLIANCE AUDIT. CHECK LOGS ABOVE.")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    validate_registries()
