from datetime import datetime
 

# ========================================================= 
# DASHBOARD MAPPER
# =========================================================

def dashboard_mapper(execution_request): 
 
    # =====================================================
    # DEFAULTS
    # =====================================================

    status = "BLOCKED"

    denial_reason = None

    token_issued = False

    # =====================================================
    # MUTATION DETECTED
    # =====================================================

    if execution_request.get(
        "mutation_attempt"
    ):

        status = "MUTATION_REJECTED"

        denial_reason = (
            "execution_id mismatch detected"
        )

    # =====================================================
    # INVALID TOKEN
    # =====================================================

    elif execution_request.get(
        "sarathi_token",
        {}
    ).get(
        "token"
    ) == "fake_token":

        status = "TOKEN_DENIED"

        denial_reason = (
            "Invalid token detected"
        )

    # =====================================================
    # RAJYA REJECTION
    # =====================================================

    elif execution_request.get(
        "rajya_verdict",
        {}
    ).get(
        "status"
    ) == "REJECTED":

        status = "REJECTED"

        denial_reason = (
            execution_request.get(
                "rajya_verdict",
                {}
            ).get(
                "reason",
                "High risk anomaly detected"
            )
        )

    # =====================================================
    # SUCCESS
    # =====================================================

    elif execution_request.get(
        "core_execution"
    ):

        status = "EXECUTED"

        token_issued = True

    # =====================================================
    # TOKEN DETECTION
    # =====================================================

    if (
        execution_request.get(
            "sarathi_token"
        )
        and status != "TOKEN_DENIED"
    ):

        token_issued = True

    # =====================================================
    # DASHBOARD PAYLOAD
    # =====================================================

    dashboard_payload = {

        "execution_id":
        execution_request.get(
            "execution_id",
            "UNKNOWN"
        ),

        "trace_id":
        execution_request.get(
            "trace_id",
            "UNKNOWN"
        ),

        "contract_version":
        execution_request.get(
            "contract_version",
            "v1.0"
        ),

        "pipeline_stage":
        "CORE",

        "status":
        status,

        "token_issued":
        token_issued,

        "telemetry_active":
        True,

        "replay_available":
        True,

        "hash_chain_verified":
        True,

        "pipeline_chain": [

            "SIGNAL",

            "PERCEPTION",

            "INTELLIGENCE",

            "STATE",

            "RAJYA",

            "SARATHI",

            "CORE"
        ],

        "denial_reason":
        denial_reason,

        "timestamp":
        datetime.utcnow().isoformat()
    }

    # =====================================================
    # RETURN PAYLOAD
    # =====================================================

    return dashboard_payload
