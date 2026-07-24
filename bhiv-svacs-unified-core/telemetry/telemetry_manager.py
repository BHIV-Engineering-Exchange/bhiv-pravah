import json
import os
import uuid

from datetime import datetime 


# =========================================================
# TELEMETRY STORAGE
# ========================================================= 

TELEMETRY_DIR = "storage/telemetry"

TELEMETRY_FILE = (
    f"{TELEMETRY_DIR}/telemetry_logs.json"
) 


# =========================================================
# ENSURE STORAGE EXISTS
# =========================================================

os.makedirs(
    TELEMETRY_DIR,
    exist_ok=True
)


# =========================================================
# PARENT STAGE MAPPING
# =========================================================

PARENT_STAGE_MAP = {

    "SIGNAL": None,

    "PERCEPTION": "SIGNAL",

    "INTELLIGENCE": "PERCEPTION",

    "STATE": "INTELLIGENCE",

    "RAJYA": "STATE",

    "SARATHI": "RAJYA",

    "CORE": "SARATHI",

    "CONTRACT": "STATE"
}


# =========================================================
# SEVERITY MAPPING
# =========================================================

SEVERITY_MAP = {

    "COMPLETED": "INFO",

    "APPROVED": "INFO",

    "EXECUTED": "INFO",

    "TOKEN_GENERATED": "INFO",

    "TOKEN_VALIDATED": "INFO",

    "REJECTED": "CRITICAL",

    "TOKEN_DENIED": "CRITICAL",

    "INVALID_TOKEN": "CRITICAL",

    "MUTATION_REJECTED": "CRITICAL",

    "SCHEMA_FAILURE": "CRITICAL",

    "DENIED": "CRITICAL"
}


# =========================================================
# TELEMETRY EMITTER
# =========================================================

def emit_telemetry(

    execution_id,
    trace_id,
    stage,
    status,
    parent_stage=None,
    service=None,
    severity=None

):

    # =====================================================
    # AUTO PARENT STAGE
    # =====================================================

    if parent_stage is None:

        parent_stage = PARENT_STAGE_MAP.get(stage)

    # =====================================================
    # AUTO SERVICE NAME
    # =====================================================

    if service is None:

        service = stage

    # =====================================================
    # AUTO SEVERITY
    # =====================================================

    if severity is None:

        severity = SEVERITY_MAP.get(
            status,
            "INFO"
        )

    # =====================================================
    # STRUCTURED TELEMETRY EVENT
    # =====================================================

    telemetry = {

        "event_id":
        str(uuid.uuid4()),

        "execution_id":
        execution_id,

        "trace_id":
        trace_id,

        "stage":
        stage,

        "parent_stage":
        parent_stage,

        "service":
        service,

        "status":
        status,

        "severity":
        severity,

        "timestamp":
        datetime.utcnow().isoformat()
    }

    # =====================================================
    # CONSOLE OUTPUT
    # =====================================================

    print(
        f" Telemetry Emitted: {telemetry}"
    )

    # =====================================================
    # GLOBAL TELEMETRY LOG
    # =====================================================

    with open(
        TELEMETRY_FILE,
        "a"
    ) as file:

        file.write(
            json.dumps(telemetry) + "\n"
        )

    # =====================================================
    # TRACE SPECIFIC LOG
    # =====================================================

    trace_file = (
        f"{TELEMETRY_DIR}/{trace_id}.json"
    )

    with open(
        trace_file,
        "a"
    ) as file:

        file.write(
            json.dumps(telemetry) + "\n"
        )

    # =====================================================
    # RETURN EVENT
    # =====================================================

    return telemetry
