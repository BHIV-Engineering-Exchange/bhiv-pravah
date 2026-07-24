import sys
import os

# =========================================================
# ROOT PROJECT PATH
# =========================================================

sys.path.append(
    os.path.abspath( 
        os.path.join(
            os.path.dirname(__file__),
            '..'
        )
    )
)

# =========================================================
# IMPORTS
# =========================================================

from orchestration.live_pipeline import run_pipeline
from replay.execution_replay import replay_execution


# =========================================================
# APPROVED FLOW
# =========================================================

print("\n===== APPROVED FLOW =====\n")

approved_result = run_pipeline(
    risk_level="LOW"
)

replay_execution(
    approved_result["execution_id"]
)


# =========================================================
# REJECT FLOW
# =========================================================

print("\n===== REJECT FLOW =====\n")

reject_result = run_pipeline(
    risk_level="HIGH"
)

replay_execution(
    reject_result["execution_id"]
)


# =========================================================
# INVALID TOKEN FLOW
# =========================================================

print("\n===== INVALID TOKEN FLOW =====\n")

invalid_token_result = run_pipeline(
    risk_level="LOW",
    invalid_token=True
)

replay_execution(
    invalid_token_result["execution_id"]
)


# =========================================================
# MUTATION REJECTION FLOW
# =========================================================

print("\n===== MUTATION REJECTION FLOW =====\n")

mutation_result = run_pipeline(
    risk_level="LOW",
    mutation_test=True
)

replay_execution(
    mutation_result["execution_id"]
)


# =========================================================
# SCHEMA FAILURE FLOW
# =========================================================

print("\n===== SCHEMA FAILURE FLOW =====\n")

run_pipeline(
    schema_failure_test=True
)
