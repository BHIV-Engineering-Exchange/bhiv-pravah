import json
import hashlib

 
# =========================================================
# GENERATE CONTRACT HASH
# =========================================================

def generate_contract_hash(data):  

    encoded_data = json.dumps(
        data,
        sort_keys=True
    ).encode()

    return hashlib.sha256(
        encoded_data
    ).hexdigest()


# =========================================================
# VALIDATE EXECUTION CONTRACT
# =========================================================

def validate_contract(
    original_request,
    current_request
):

    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    required_fields = [
        "execution_id",
        "trace_id",
        "contract_version",
        "timestamp"
    ]

    for field in required_fields:

        if field not in current_request:

            raise Exception(
                f"{field} missing in execution contract"
            )

    # -----------------------------------------------------
    # IMMUTABLE FIELD VALIDATION
    # -----------------------------------------------------

    immutable_fields = [
        "execution_id",
        "trace_id",
        "contract_version",
        "timestamp"
    ]

    for field in immutable_fields:

        original_value = original_request.get(field)

        current_value = current_request.get(field)

        if original_value != current_value:

            raise Exception(
                f"{field} mismatch detected"
            )

    # -----------------------------------------------------
    # HASH CHAIN VALIDATION
    # -----------------------------------------------------

    previous_hash = current_request.get(
        "previous_hash"
    )

    current_hash = current_request.get(
        "current_hash"
    )

    if not previous_hash:

        raise Exception(
            "previous_hash missing"
        )

    if not current_hash:

        raise Exception(
            "current_hash missing"
        )

    if previous_hash == current_hash:

        raise Exception(
            "hash chain invalid"
        )

    # -----------------------------------------------------
    # TRACE FORMAT VALIDATION
    # -----------------------------------------------------

    if not str(
        current_request["trace_id"]
    ).startswith("trace_"):

        raise Exception(
            "invalid trace_id format"
        )

    # -----------------------------------------------------
    # EXECUTION FORMAT VALIDATION
    # -----------------------------------------------------

    if not str(
        current_request["execution_id"]
    ).startswith("exec_"):

        raise Exception(
            "invalid execution_id format"
        )

    # -----------------------------------------------------
    # CONTRACT VALIDATION SUCCESS
    # -----------------------------------------------------

    print(
        " Contract validated successfully"
    )

    return True


# =========================================================
# CORE EXECUTION ENGINE
# =========================================================

def execute_core(token_data):

    if not token_data:

        raise Exception(
            "Missing token data"
        )

    return {
        "execution_result": {
            "status": "SUCCESS",
            "message": "Core execution completed"
        }
    }
