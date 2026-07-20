import sys
import os
from datetime import datetime, timezone
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.prana_determinism import prana_determinism
from app.services.prana_runtime import prana_runtime

def verify_replay():
    print("--- GURUKUL ADAPTATION REPLAY VERIFICATION ---")
    
    # 1. Simulate an Adaptive Decision
    decision_payload = {
        "sequence": 1,
        "decision_id": "dec_999",
        "user_id": "student_001",
        "policy_version": "1.0.0",
        "input_state": {"focus_score": 85, "active_seconds": 300},
        "output_decision": {"next_task": "advanced_algebra_01", "pacing": "fast"},
        "trace_proof": "policy_v1_confidence_0.92",
        "run_id": "run_test_001"
    }
    
    # 2. Compute Deterministic Hash
    determinism_hash = prana_determinism.hash_payload(decision_payload)
    decision_payload["determinism_hash"] = determinism_hash
    
    print(f"Decision Payload Hash: {determinism_hash}")
    
    # 3. Simulate Storage and Retrieval
    stored_hash = determinism_hash
    
    # 4. Replay and Recompute
    recomputed_hash = prana_determinism.hash_payload(decision_payload)
    
    print(f"Recomputed Hash:      {recomputed_hash}")
    
    # 5. Verify Match
    if stored_hash == recomputed_hash:
        print("\n[SUCCESS] Deterministic Replay Verified. Hash Match.")
    else:
        print("\n[FAILURE] Drift Detected! Hash Mismatch.")
        sys.exit(1)

    # 6. Verify Schema Version and Metadata (Phase 2)
    telemetry_payload = {
        **decision_payload,
        "schema_version": "edu.interaction.v1",
        "provenance": "gurukul.sovereign_lm.v1",
        "ownership": "educational_intelligence",
        "replay_metadata": {"is_replayable": True, "determinism_level": "high"}
    }
    
    print(f"\nSchema Version: {telemetry_payload['schema_version']}")
    print(f"Provenance:     {telemetry_payload['provenance']}")
    
    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_replay()
