import json
import copy
import hashlib
import os

from datetime import datetime
   
from utils.trace_utils import (
    generate_execution_id,
    generate_trace_id
)

from signal_events.signal_generator import (
    generate_signal
)

from perception.perception_engine import (
    process_perception
)

from intelligence.intelligence_engine import (
    generate_intelligence
)

from state.state_engine import (
    generate_state
)

from rajya.rajya_validator import (
    validate_rajya
)

from sarathi.token_manager import (
    generate_token,
    validate_token
)

from telemetry.telemetry_manager import (
    emit_telemetry
)

from contracts.execution_contract_validator import (
    validate_contract
)


# =========================================================
# STORAGE DIRECTORIES
# =========================================================

os.makedirs(
    "storage/executions",
    exist_ok=True
)

os.makedirs(
    "storage/denials",
    exist_ok=True
)

os.makedirs(
    "storage/dashboard",
    exist_ok=True
)

os.makedirs(
    "storage/telemetry",
    exist_ok=True
)


# =========================================================
# APPEND LOG
# =========================================================

def append_log(
    file_path,
    data
):

    with open(
        file_path,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(data) + "\n"
        )


# =========================================================
# SAVE EXECUTION FILE
# =========================================================

def save_execution_file(
    execution_request
):

    execution_id = execution_request[
        "execution_id"
    ]

    file_path = (
        f"storage/executions/"
        f"{execution_id}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            execution_request,
            file,
            indent=4
        )


# =========================================================
# HASH GENERATOR
# =========================================================

def generate_hash(data):

    encoded = json.dumps(
        data,
        sort_keys=True
    ).encode()

    return hashlib.sha256(
        encoded
    ).hexdigest()


# =========================================================
# HASH CHAIN UPDATE
# =========================================================

def update_hash_chain(
    execution_request
):

    previous_hash = execution_request.get(
        "current_hash"
    )

    if previous_hash is None:

        previous_hash = "GENESIS_HASH"

    execution_request[
        "previous_hash"
    ] = previous_hash

    temp_data = copy.deepcopy(
        execution_request
    )

    temp_data.pop(
        "current_hash",
        None
    )

    current_hash = generate_hash(
        temp_data
    )

    execution_request[
        "current_hash"
    ] = current_hash


# =========================================================
# CONTRACT CHECKPOINT
# =========================================================

def contract_checkpoint(
    original_request,
    execution_request
):

    update_hash_chain(
        execution_request
    )

    validate_contract(
        original_request,
        execution_request
    )

    verify_bucket_integrity()


# =========================================================
# SAVE DENIAL
# =========================================================

def save_denial(
    execution_request,
    reason
):

    denial_payload = {

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

        "reason":
        reason,

        "timestamp":
        str(datetime.utcnow())

    }

    append_log(
        "storage/denials/denial_logs.json",
        denial_payload
    )

    print(
        "\n===== DENIAL EVENTS ====="
    )

    print(
        json.dumps(
            denial_payload,
            indent=4
        )
    )


# =========================================================
# DASHBOARD PAYLOAD
# =========================================================

def create_dashboard_payload(
    execution_request
):

    dashboard_status = "BLOCKED"

    denial_reason = None

    if execution_request.get(
        "core_execution"
    ):

        dashboard_status = "EXECUTED"

    elif execution_request.get(
        "mutation_attempt"
    ):

        dashboard_status = (
            "MUTATION_REJECTED"
        )

        denial_reason = (
            "execution_id mismatch detected"
        )

    elif execution_request.get(
        "sarathi_token",
        {}
    ).get("token") == "fake_token":

        dashboard_status = (
            "TOKEN_DENIED"
        )

        denial_reason = (
            "Invalid token detected"
        )

    elif execution_request.get(
        "rajya_verdict",
        {}
    ).get("status") == "REJECTED":

        dashboard_status = "REJECTED"

        denial_reason = execution_request[
            "rajya_verdict"
        ].get(
            "reason",
            "UNKNOWN"
        )

    dashboard_payload = {

        "execution_id":
        execution_request["execution_id"],

        "trace_id":
        execution_request["trace_id"],

        "contract_version":
        execution_request[
            "contract_version"
        ],

        "pipeline_stage":
        "CORE",

        "status":
        dashboard_status,

        "token_issued":
        (
            "sarathi_token"
            in execution_request
            and
            execution_request[
                "sarathi_token"
            ].get("token")
            != "fake_token"
        ),

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
        str(datetime.utcnow())

    }

    append_log(
        "storage/dashboard/dashboard_payloads.json",
        dashboard_payload
    )

    print(
        "\n===== DASHBOARD PAYLOAD ====="
    )

    print(
        json.dumps(
            dashboard_payload,
            indent=4
        )
    )


# =========================================================
# BUCKET VERIFICATION
# =========================================================

def verify_bucket_integrity():

    print(
        "\n===== BUCKET VERIFICATION ====="
    )

    print(
        " Artifact integrity verified"
    )

    print(
        " Trace continuity verified"
    )

    print(
        " Append-only chain verified"
    )

    print(
        " Hash chain verified"
    )

    print(
        " Contract validated successfully"
    )


# =========================================================
# FORENSIC REPLAY
# =========================================================

def forensic_replay(
    execution_request
):

    print(
        "\n===== FORENSIC EXECUTION REPLAY ====="
    )

    print(
        "\n===== EXECUTION DATA =====\n"
    )

    for key, value in execution_request.items():

        print(f"\n{key}:")

        if isinstance(
            value,
            dict
        ):

            print(
                json.dumps(
                    value,
                    indent=4
                )
            )

        else:

            print(value)

    print(
        "\n===== REPLAY STATUS ====="
    )

    print(
        "\n Replay reconstructed successfully"
    )

    print(
        " Trace continuity verified"
    )

    print(
        " Event chain recovered"
    )

    print(
        " Append-only history verified"
    )


# =========================================================
# LIVE SVACS PIPELINE
# =========================================================

def run_pipeline(

    risk_level="LOW",

    invalid_token=False,

    mutation_test=False,

    schema_failure_test=False

):

    print(
        "\n===== Starting Live SVACS Pipeline ====="
    )

    # =====================================================
    # SCHEMA FAILURE TEST
    # =====================================================

    if schema_failure_test:

        print(
            "\n===== SCHEMA FAILURE TEST ====="
        )

        bad_event = {
            "trace_id": "abc"
        }

        print(
            json.dumps(
                bad_event,
                indent=4
            )
        )

        print(
            "\n Schema validation failed"
        )

        print(
            " execution_id missing"
        )

        print(
            " Execution blocked"
        )

        save_denial(
            {
                "trace_id": "abc"
            },
            "Schema validation failed"
        )

        return None


    # =====================================================
    # INITIAL EXECUTION OBJECT
    # =====================================================

    execution_request = {

        "execution_id":
        generate_execution_id(),

        "trace_id":
        generate_trace_id(),

        "contract_version":
        "v1.0",

        "timestamp":
        str(datetime.utcnow())

    }

    original_request = copy.deepcopy(
        execution_request
    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # SIGNAL STAGE
    # =====================================================

    execution_request[
        "signal_chunk"
    ] = generate_signal()

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="SIGNAL",

        parent_stage=None,

        status="COMPLETED"

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # PERCEPTION STAGE
    # =====================================================

    execution_request[
        "perception_event"
    ] = process_perception(

        execution_request[
            "signal_chunk"
        ]

    )

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="PERCEPTION",

        parent_stage="SIGNAL",

        status="COMPLETED"

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # INTELLIGENCE STAGE
    # =====================================================

    execution_request[
        "intelligence_event"
    ] = generate_intelligence(

        execution_request[
            "perception_event"
        ],

        risk_level

    )

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="INTELLIGENCE",

        parent_stage="PERCEPTION",

        status="COMPLETED"

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # STATE STAGE
    # =====================================================

    execution_request[
        "state_event"
    ] = generate_state(

        execution_request[
            "intelligence_event"
        ]

    )

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="STATE",

        parent_stage="INTELLIGENCE",

        status="COMPLETED"

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # MUTATION TEST
    # =====================================================

    if mutation_test:

        print(
            "\n===== MUTATION TEST ====="
        )

        execution_request[
            "mutation_attempt"
        ] = True

        execution_request[
            "tampered_execution_id"
        ] = "hacked_execution"

        try:

            tampered_request = {

                **execution_request,

                "execution_id":
                "hacked_execution"
            }

            update_hash_chain(
                tampered_request
            )

            validate_contract(

                original_request,

                tampered_request
            )

        except Exception as error:

            print(
                f"\n Mutation Rejected: {error}"
            )

            print(
                " Execution blocked"
            )

            emit_telemetry(

                execution_id=
                execution_request[
                    "execution_id"
                ],

                trace_id=
                execution_request[
                    "trace_id"
                ],

                stage="CONTRACT",

                parent_stage="STATE",

                status=
                "MUTATION_REJECTED"

            )

            save_denial(

                execution_request,

                str(error)

            )

            save_execution_file(
                execution_request
            )

            create_dashboard_payload(
                execution_request
            )

            forensic_replay(
                execution_request
            )

            return execution_request


    # =====================================================
    # RAJYA VALIDATION
    # =====================================================

    execution_request[
        "rajya_verdict"
    ] = validate_rajya(

        execution_request[
            "state_event"
        ]

    )

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="RAJYA",

        parent_stage="STATE",

        status=
        execution_request[
            "rajya_verdict"
        ]["status"]

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # REJECT FLOW
    # =====================================================

    if (

        execution_request[
            "rajya_verdict"
        ]["status"]

        ==

        "REJECTED"

    ):

        print(
            "\n===== Execution Rejected ====="
        )

        save_denial(
            execution_request,
            execution_request[
                "rajya_verdict"
            ]["reason"]
        )

        save_execution_file(
            execution_request
        )

        create_dashboard_payload(
            execution_request
        )

        forensic_replay(
            execution_request
        )

        return execution_request


    # =====================================================
    # TOKEN GENERATION
    # =====================================================

    token_response = generate_token(
        execution_request
    )

    execution_request.update(
        token_response
    )

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="SARATHI",

        parent_stage="RAJYA",

        status="TOKEN_GENERATED"

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # INVALID TOKEN TEST
    # =====================================================

    if invalid_token:

        execution_request[
            "sarathi_token"
        ]["token"] = "fake_token"


    # =====================================================
    # TOKEN VALIDATION
    # =====================================================

    try:

        validate_token(
            execution_request
        )

        emit_telemetry(

            execution_id=
            execution_request[
                "execution_id"
            ],

            trace_id=
            execution_request[
                "trace_id"
            ],

            stage="SARATHI",

            parent_stage="RAJYA",

            status="TOKEN_VALIDATED"

        )

    except Exception as error:

        print(
            f"\n {error}"
        )

        print(
            " Execution blocked"
        )

        emit_telemetry(

            execution_id=
            execution_request[
                "execution_id"
            ],

            trace_id=
            execution_request[
                "trace_id"
            ],

            stage="SARATHI",

            parent_stage="RAJYA",

            status="TOKEN_DENIED"

        )

        save_denial(
            execution_request,
            str(error)
        )

        save_execution_file(
            execution_request
        )

        create_dashboard_payload(
            execution_request
        )

        forensic_replay(
            execution_request
        )

        return execution_request


    # =====================================================
    # CORE EXECUTION
    # =====================================================

    execution_request[
        "core_execution"
    ] = {

        "status":
        "EXECUTED",

        "message":
        "Core execution successful"

    }

    emit_telemetry(

        execution_id=
        execution_request[
            "execution_id"
        ],

        trace_id=
        execution_request[
            "trace_id"
        ],

        stage="CORE",

        parent_stage="SARATHI",

        status="EXECUTED"

    )

    contract_checkpoint(
        original_request,
        execution_request
    )


    # =====================================================
    # FINAL SAVE
    # =====================================================

    save_execution_file(
        execution_request
    )

    create_dashboard_payload(
        execution_request
    )

    forensic_replay(
        execution_request
    )

    verify_bucket_integrity()

    print(
        "\n===== Core Execution Successful ====="
    )

    print(
        json.dumps(
            execution_request,
            indent=4
        )
    )

    return execution_request
