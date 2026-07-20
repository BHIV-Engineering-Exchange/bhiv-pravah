import json
import hashlib
import os
from cluster_engine import deterministic_cluster

def get_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()

def run_replay_test(input_file):
    print(f"Running Replay Test for: {input_file}")
    
    with open(input_file, "r") as f:
        input_data = json.load(f)
        signals = input_data.get("signals", [])
        
    # Run 1
    output1 = deterministic_cluster(signals)
    hash1 = get_hash(output1)
    
    # Run 2
    output2 = deterministic_cluster(signals)
    hash2 = get_hash(output2)
    
    print(f"Run 1 Hash: {hash1}")
    print(f"Run 2 Hash: {hash2}")
    
    if hash1 == hash2:
        print("✅ SUCCESS: Outputs are identical.")
        return True, hash1
    else:
        print("❌ FAILURE: Deterministic breakdown detected.")
        return False, None

if __name__ == "__main__":
    success, stable_hash = run_replay_test("example_input.json")
    if success:
        # Save sample output for verification
        os.makedirs("replay_test_suite", exist_ok=True)
        with open("replay_test_suite/sample_output.json", "w") as f:
            signals_input = json.load(open("example_input.json")).get("signals", [])
            json.dump(deterministic_cluster(signals_input), f, indent=2, sort_keys=True)
        print(f"Sample output saved to replay_test_suite/sample_output.json")
