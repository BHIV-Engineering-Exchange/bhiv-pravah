from flask import Flask, render_template, jsonify

import json
import os

from collections import Counter


app = Flask(__name__)


# =====================================================
# SAFE JSON LOADER
# =====================================================

def load_json_lines(file_path):

    records = []

    if not os.path.exists(file_path):
        return records

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                records.append(
                    json.loads(line)
                )

            except Exception as e:

                print(
                    f"[JSON ERROR] {e}"
                )

    return records


# =====================================================
# LOAD DASHBOARD PAYLOADS
# =====================================================

def load_dashboard_payloads():

    file_path = (
        "storage/dashboard/dashboard_payloads.json"
    )

    payloads = load_json_lines(
        file_path
    )

    normalized = []

    for item in payloads:

        status = item.get(
            "status",
            "UNKNOWN"
        )

        # =============================================
        # STATUS NORMALIZATION
        # =============================================

        if status == "BLOCKED":

            reason = item.get(
                "denial_reason",
                ""
            ).lower()

            if "token" in reason:

                status = "TOKEN_DENIED"

            elif "mutation" in reason:

                status = "MUTATION_REJECTED"

            else:

                status = "REJECTED"

        normalized.append({

            "execution_id":
            item.get(
                "execution_id",
                "UNKNOWN"
            ),

            "trace_id":
            item.get(
                "trace_id",
                "UNKNOWN"
            ),

            "pipeline_stage":
            item.get(
                "pipeline_stage",
                "CORE"
            ),

            "status":
            status,

            "token_issued":
            item.get(
                "token_issued",
                False
            ),

            "telemetry_active":
            item.get(
                "telemetry_active",
                False
            ),

            "replay_available":
            item.get(
                "replay_available",
                False
            ),

            "hash_chain_verified":
            item.get(
                "hash_chain_verified",
                False
            ),

            "timestamp":
            item.get(
                "timestamp",
                "UNKNOWN"
            )
        })

    # =============================================
    # REMOVE DUPLICATES
    # =============================================

    unique = {}

    for item in normalized:

        execution_id = item.get(
            "execution_id"
        )

        unique[
            execution_id
        ] = item

    normalized = list(
        unique.values()
    )

    # =============================================
    # LATEST FIRST
    # =============================================

    normalized = sorted(

        normalized,

        key=lambda x:
        x.get("timestamp", ""),

        reverse=True
    )

    return normalized


# =====================================================
# LOAD TELEMETRY
# =====================================================

def load_telemetry():

    telemetry_file = (
        "storage/telemetry/telemetry_logs.json"
    )

    events = load_json_lines(
        telemetry_file
    )

    unique_events = []

    seen = set()

    for event in events:

        event_id = event.get(
            "event_id"
        )

        if event_id in seen:
            continue

        seen.add(event_id)

        severity = event.get(
            "severity",
            "INFO"
        )

        if event.get("status") in [

            "TOKEN_DENIED",
            "MUTATION_REJECTED",
            "REJECTED"

        ]:

            severity = "CRITICAL"

        unique_events.append({

            "event_id":
            event.get(
                "event_id"
            ),

            "execution_id":
            event.get(
                "execution_id",
                "UNKNOWN"
            ),

            "trace_id":
            event.get(
                "trace_id",
                "UNKNOWN"
            ),

            "stage":
            event.get(
                "stage",
                "UNKNOWN"
            ),

            "parent_stage":
            event.get(
                "parent_stage"
            ),

            "service":
            event.get(
                "service",
                "UNKNOWN"
            ),

            "status":
            event.get(
                "status",
                "UNKNOWN"
            ),

            "severity":
            severity,

            "timestamp":
            event.get(
                "timestamp",
                "UNKNOWN"
            )
        })

    # =============================================
    # SORT LATEST FIRST
    # =============================================

    unique_events = sorted(

        unique_events,

        key=lambda x:
        x.get("timestamp", ""),

        reverse=True
    )

    return unique_events


# =====================================================
# LOAD REJECTIONS
# =====================================================

def load_rejections():

    file_path = (
        "storage/denials/denial_logs.json"
    )

    rejections = load_json_lines(
        file_path
    )

    cleaned = []

    for item in rejections:

        reason = item.get(
            "reason",
            "UNKNOWN"
        )

        if reason == "Validation successful":
            continue

        cleaned.append({

            "execution_id":
            item.get(
                "execution_id",
                "UNKNOWN"
            ),

            "trace_id":
            item.get(
                "trace_id",
                "UNKNOWN"
            ),

            "reason":
            reason,

            "timestamp":
            item.get(
                "timestamp",
                "UNKNOWN"
            )
        })

    cleaned = sorted(

        cleaned,

        key=lambda x:
        x.get("timestamp", ""),

        reverse=True
    )

    return cleaned


# =====================================================
# SYSTEM METRICS
# =====================================================

def load_metrics():

    payloads = load_dashboard_payloads()

    statuses = [

        item.get(
            "status",
            "UNKNOWN"
        )

        for item in payloads
    ]

    counter = Counter(
        statuses
    )

    return {

        "EXECUTED":
        counter.get(
            "EXECUTED",
            0
        ),

        "REJECTED":
        counter.get(
            "REJECTED",
            0
        ),

        "TOKEN_DENIED":
        counter.get(
            "TOKEN_DENIED",
            0
        ),

        "MUTATION_REJECTED":
        counter.get(
            "MUTATION_REJECTED",
            0
        )
    }


# =====================================================
# LOAD REPLAY
# =====================================================

def load_replay(execution_id):

    replay_dir = (
        "storage/replay"
    )

    if not os.path.exists(
        replay_dir
    ):

        return None

    replay_file = os.path.join(

        replay_dir,

        f"{execution_id}.json"
    )

    if not os.path.exists(
        replay_file
    ):

        return None

    with open(
        replay_file,
        "r",
        encoding="utf-8"
    ) as file:

        try:

            return json.load(file)

        except Exception as e:

            print(
                f"[REPLAY ERROR] {e}"
            )

            return None


# =====================================================
# HOME
# =====================================================

@app.route("/")

def home():

    return render_template(
        "dashboard.html"
    )


# =====================================================
# DASHBOARD API
# =====================================================

@app.route("/api/dashboard")

def dashboard_api():

    return jsonify(
        load_dashboard_payloads()
    )


# =====================================================
# TELEMETRY API
# =====================================================

@app.route("/api/telemetry")

def telemetry_api():

    return jsonify(
        load_telemetry()
    )


# =====================================================
# REJECTION API
# =====================================================

@app.route("/api/rejections")

def rejection_api():

    return jsonify(
        load_rejections()
    )


# =====================================================
# METRICS API
# =====================================================

@app.route("/api/metrics")

def metrics_api():

    return jsonify(
        load_metrics()
    )


# =====================================================
# REPLAY API
# =====================================================

@app.route("/api/replay/<execution_id>")

def replay_api(execution_id):

    replay_data = load_replay(
        execution_id
    )

    if replay_data is None:

        return jsonify({

            "status":
            "NOT_FOUND",

            "execution_id":
            execution_id

        }), 404

    return jsonify(
        replay_data
    )


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health")

def health():

    return jsonify({

        "status":
        "ONLINE",

        "service":
        "SVACS_DASHBOARD",

        "dashboard_active":
        True,

        "telemetry_active":
        True
    })


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000
    )
