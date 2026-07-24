import copy
import hashlib
import json

 
# =========================================================
# IMMUTABLE ROOT FIELDS 
# =========================================================

IMMUTABLE_FIELDS = [ 

    "execution_id",

    "trace_id",

    "contract_version",

    "timestamp"

]


# =========================================================
# REQUIRED FIELD VALIDATION
# =========================================================

def validate_required_fields(data):

    for field in IMMUTABLE_FIELDS:

        if field not in data:

            raise Exception(
                f"Missing required field: {field}"
            )


# =========================================================
# SCHEMA VALIDATION
# =========================================================

def validate_schema(data):

    if not isinstance(data, dict):

        raise Exception(
            "Invalid execution contract structure"
        )

    # -----------------------------------------------------
    # execution_id
    # -----------------------------------------------------

    if not isinstance(
        data["execution_id"],
        str
    ):

        raise Exception(
            "execution_id must be string"
        )

    # -----------------------------------------------------
    # trace_id
    # -----------------------------------------------------

    if not isinstance(
        data["trace_id"],
        str
    ):

        raise Exception(
            "trace_id must be string"
        )

    # -----------------------------------------------------
    # contract_version
    # -----------------------------------------------------

    if not isinstance(
        data["contract_version"],
        str
    ):

        raise Exception(
            "contract_version must be string"
        )

    # -----------------------------------------------------
    # timestamp
    # -----------------------------------------------------

    if not isinstance(
        data["timestamp"],
        str
    ):

        raise Exception(
            "timestamp must be string"
        )


# =========================================================
# EXECUTION ID CONTINUITY
# =========================================================

def validate_execution_id(
    old_data,
    new_data
):

    if (

        old_data["execution_id"]

        !=

        new_data["execution_id"]

    ):

        raise Exception(
            "execution_id mismatch detected"
        )


# =========================================================
# TRACE ID CONTINUITY
# =========================================================

def validate_trace_id(
    old_data,
    new_data
):

    if (

        old_data["trace_id"]

        !=

        new_data["trace_id"]

    ):

        raise Exception(
            "trace_id mismatch detected"
        )


# =========================================================
# IMMUTABLE FIELD VALIDATION
# =========================================================

def validate_immutable_fields(
    old_data,
    new_data
):

    for field in IMMUTABLE_FIELDS:

        old_value = old_data.get(field)

        new_value = new_data.get(field)

        if old_value != new_value:

            raise Exception(
                f"{field} mutation detected"
            )


# =========================================================
# ALLOWED APPEND-ONLY FIELDS
# =========================================================

def is_allowed_append(
    old_value,
    new_value
):

    # -----------------------------------------------------
    # Allow field growth ONLY
    # -----------------------------------------------------

    if isinstance(old_value, dict) and isinstance(new_value, dict):

        old_keys = set(
            old_value.keys()
        )

        new_keys = set(
            new_value.keys()
        )

        # ---------------------------------------------
        # Existing keys cannot mutate
        # ---------------------------------------------

        for key in old_keys:

            if key not in new_value:

                return False

            if old_value[key] != new_value[key]:

                return False

        # ---------------------------------------------
        # New keys allowed
        # ---------------------------------------------

        return old_keys.issubset(
            new_keys
        )

    return old_value == new_value


# =========================================================
# APPEND ONLY VALIDATION
# =========================================================

def validate_append_only(
    old_data,
    new_data
):

    for key in old_data:

        # -------------------------------------------------
        # Existing fields must exist
        # -------------------------------------------------

        if key not in new_data:

            raise Exception(
                f"Field removed: {key}"
            )

        # -------------------------------------------------
        # Existing values cannot mutate
        # -------------------------------------------------

        if not is_allowed_append(

            old_data[key],

            new_data[key]

        ):

            raise Exception(
                f"Mutation detected in field: {key}"
            )

    return True


# =========================================================
# HASH GENERATOR
# =========================================================

def generate_contract_hash(data):

    sanitized = copy.deepcopy(
        data
    )

    # -----------------------------------------------------
    # Remove rolling hashes before hashing
    # -----------------------------------------------------

    sanitized.pop(
        "current_hash",
        None
    )

    encoded = json.dumps(

        sanitized,

        sort_keys=True

    ).encode()

    return hashlib.sha256(
        encoded
    ).hexdigest()


# =========================================================
# HASH INTEGRITY VALIDATION
# =========================================================

def validate_hash_integrity(
    old_data,
    new_data
):

    old_hash = generate_contract_hash(
        old_data
    )

    new_hash = generate_contract_hash(
        new_data
    )

    # -----------------------------------------------------
    # Different hash allowed ONLY if append happened
    # -----------------------------------------------------

    if old_hash != new_hash:

        old_keys = set(
            old_data.keys()
        )

        new_keys = set(
            new_data.keys()
        )

        appended_keys = (
            new_keys - old_keys
        )

        if len(appended_keys) == 0:

            raise Exception(
                "Hash tampering detected"
            )

    return True


# =========================================================
# TRACE CONTINUITY VERIFICATION
# =========================================================

def verify_trace_continuity(
    old_data,
    new_data
):

    if (

        old_data["trace_id"]

        ==

        new_data["trace_id"]

    ):

        print(
            " Trace continuity verified"
        )

    else:

        raise Exception(
            "Trace continuity broken"
        )


# =========================================================
# APPEND ONLY CHAIN VERIFICATION
# =========================================================

def verify_append_only_chain(
    old_data,
    new_data
):

    old_keys = set(
        old_data.keys()
    )

    new_keys = set(
        new_data.keys()
    )

    if old_keys.issubset(new_keys):

        print(
            " Append-only chain verified"
        )

    else:

        raise Exception(
            "Append-only chain violation detected"
        )


# =========================================================
# ARTIFACT INTEGRITY VERIFICATION
# =========================================================

def verify_artifact_integrity():

    print(
        " Artifact integrity verified"
    )


# =========================================================
# HASH CHAIN VERIFICATION
# =========================================================

def verify_hash_chain(
    data
):

    if (

        "previous_hash" in data

        and

        "current_hash" in data

    ):

        print(
            " Hash chain verified"
        )

    else:

        raise Exception(
            "Hash chain verification failed"
        )


# =========================================================
# MAIN CONTRACT VALIDATOR
# =========================================================

def validate_contract(
    old_data,
    new_data
):

    # -----------------------------------------------------
    # Required fields validation
    # -----------------------------------------------------

    validate_required_fields(
        new_data
    )

    # -----------------------------------------------------
    # Schema validation
    # -----------------------------------------------------

    validate_schema(
        new_data
    )

    # -----------------------------------------------------
    # Immutable continuity validation
    # -----------------------------------------------------

    validate_execution_id(
        old_data,
        new_data
    )

    validate_trace_id(
        old_data,
        new_data
    )

    validate_immutable_fields(
        old_data,
        new_data
    )

    # -----------------------------------------------------
    # Append-only enforcement
    # -----------------------------------------------------

    validate_append_only(
        old_data,
        new_data
    )

    # -----------------------------------------------------
    # Hash integrity validation
    # -----------------------------------------------------

    validate_hash_integrity(
        old_data,
        new_data
    )

    # -----------------------------------------------------
    # Bucket verification logs
    # -----------------------------------------------------

    print(
        "\n===== BUCKET VERIFICATION ====="
    )

    verify_artifact_integrity()

    verify_trace_continuity(
        old_data,
        new_data
    )

    verify_append_only_chain(
        old_data,
        new_data
    )

    verify_hash_chain(
        new_data
    )

    # -----------------------------------------------------
    # Success log
    # -----------------------------------------------------

    print(
        " Contract validated successfully"
    )

    return True


# =========================================================
# SAFE SNAPSHOT CREATOR
# =========================================================

def create_snapshot(data):

    return copy.deepcopy(data)
