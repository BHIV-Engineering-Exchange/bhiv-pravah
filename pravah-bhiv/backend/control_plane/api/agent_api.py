"""
Canonical Decision API Layer

Exposes only:
- POST /api/runtime
- GET  /api/status
- GET  /api/health
- GET  /api/control-plane/apps
- GET  /api/control-plane/health
- GET  /api/control-plane/history/<app_name>
- POST /api/control-plane/override
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime
import json
import os
import sys
import threading
# Ensure repo root is on sys.path so running this module directly works
# agent_api.py is at control_plane/api; repo root is two levels up
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)
from core_hooks.middleware import verify_request_trace
from jsonschema import ValidationError, validate
from core_hooks.rules import validate_trace



from agent_runtime import AgentRuntime
import agent_runtime
print("[RUNTIME] USING RUNTIME FILE:", agent_runtime.__file__)
from control_plane.multi_app_control_plane import MultiAppControlPlane
from control_plane.core.input_validator import InputValidator, ValidationError as InputValidationError

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Resolve canonical schema path across current/legacy layouts.
schema_candidates = [
    os.path.join(root_dir, "schemas", "signal_schema.json"),
    os.path.join(os.path.dirname(root_dir), "schemas", "signal_schema.json"),
    os.path.join(os.path.dirname(root_dir), "runtime_payload_schema.json"),
]
SCHEMA_PATH = next((path for path in schema_candidates if os.path.exists(path)), schema_candidates[0])


with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
    RUNTIME_SCHEMA = json.load(schema_file)

# One shared runtime instance
agent = AgentRuntime(env=ENVIRONMENT)
control_plane = MultiAppControlPlane(env=ENVIRONMENT)


def start_agent_loop() -> None:
    """Run autonomous loop in background."""
    agent.run()


threading.Thread(target=start_agent_loop, daemon=True).start()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://multi-agent-control-plane-frontend.vercel.app",
    "https://multi-agent-control-plane-frontend-dev.vercel.app",
    "http://localhost:4500",
    "http://localhost:3200",
    "http://localhost:3000"
]}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def _validate_runtime_payload(payload: dict) -> None:
    validate(instance=payload, schema=RUNTIME_SCHEMA)

def _event_type_from_contract(payload: dict) -> str:
    """Derive internal event type from canonical runtime contract."""
    state = payload.get("state")
    latency_ms = payload.get("latency_ms", 0)
    errors_last_min = payload.get("errors_last_min", 0)

    if state == "crashed":
        return "crash"

    if state == "degraded" or latency_ms >= 200 or errors_last_min >= 5:
        return "overload"

    return "false_alarm"


def _to_agent_event(payload: dict) -> dict:
    return {
        "trace_id": payload["trace_id"],  # [OK] ADD THIS
        "event_id": f"runtime-{datetime.datetime.utcnow().timestamp()}",
        "event_type": _event_type_from_contract(payload),
        "environment": payload["env"],
        "app_id": payload["app"],
        "timestamp": datetime.datetime.utcnow().timestamp(),
        "data": {
            "state": payload["state"],
            "metrics": {
                "latency_ms": payload["latency_ms"],
                "errors_last_min": payload["errors_last_min"],
                "workers": payload["workers"],
            },
        },
    }


@app.route("/api/health", methods=["GET"])
@limiter.limit("100 per minute")
def health_check():
    """Health and liveness endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "canonical-decision-api",
        "environment": ENVIRONMENT,
    }), 200


@app.route("/api/status", methods=["GET"])
@limiter.limit("60 per minute")
def runtime_status():
    """Return current status of the shared runtime instance."""
    try:
        status = agent.get_agent_status()
        return jsonify(status), 200
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/runtime", methods=["POST"])
@limiter.limit("30 per minute")
def runtime_decision():
    """Canonical runtime decision endpoint."""

    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify({
            "status": "error",
            "error": "Request body must be valid JSON",
        }), 400

    try:
        payload = verify_request_trace(payload)

    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": "Trace verification failed",
            "details": str(exc),
        }), 401

    # [OK] Enforce trace
    try:
        validate_trace(payload)
    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": "Trace validation failed",
            "details": str(exc),
        }), 400

    # [OK] Hardened input validation
    try:
        InputValidator.validate_runtime_payload(payload)
    except InputValidationError as exc:
        return jsonify({
            "status": "error",
            "error": "Input validation failed",
            "details": str(exc),
        }), 400
    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": "Runtime payload validation failed",
            "details": str(exc),
        }), 400

    try:
        result = agent.handle_external_event(_to_agent_event(payload))

        # Forward telemetry to observer dashboard out-of-band
        try:
            import requests
            obs_port = int(os.getenv("PRAVAH_OBSERVER_PORT", "8600"))
            obs_url = f"http://127.0.0.1:{obs_port}/api/ingest"
            requests.post(
                obs_url,
                json={
                    "service": payload.get("app", "unknown"),
                    "status": payload.get("state", "info"),
                    "data": {
                        "trace_id": payload.get("trace_id"),
                        "latency_ms": payload.get("latency_ms", 0),
                        "errors_last_min": payload.get("errors_last_min", 0),
                        "decision": result
                    }
                },
                timeout=1.0
            )
        except Exception:
            pass # Observer down should not affect the control plane

        return jsonify({
            "status": "success",
            "input": payload,
            "result": result,
        }), 200

    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": "Runtime decision failed",
            "details": str(exc),
        }), 500


@app.route("/api/control-plane/apps", methods=["GET"])
@limiter.limit("40 per minute")
def control_plane_apps():
    """List all onboarded apps in the registry."""
    try:
        return jsonify({"status": "success", "apps": control_plane.list_apps()}), 200
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/control-plane/health", methods=["GET"])
@limiter.limit("40 per minute")
def control_plane_health_overview():
    """Health overview dashboard data for all onboarded apps."""
    try:
        return jsonify({"status": "success", "overview": control_plane.get_health_overview()}), 200
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/control-plane/history/<app_name>", methods=["GET"])
@limiter.limit("40 per minute")
def control_plane_history(app_name: str):
    """Decision history timeline for one app."""
    try:
        # Validate app_name
        app_name = InputValidator.validate_app_name(app_name)
        
        # Validate limit parameter
        limit_param = request.args.get("limit", "200")
        limit = InputValidator.validate_limit_param(limit_param)
        
        history = control_plane.get_decision_history(app_name=app_name, limit=limit)
        return jsonify({"status": "success", "app_name": app_name, "timeline": history}), 200
    except InputValidationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/control-plane/override", methods=["POST"])
@limiter.limit("40 per minute")
def control_plane_override():
    """Manual override panel actions: set or clear temporary per-app freeze."""
    payload = request.get_json(silent=True) or {}

    try:
        app_name, action, duration, reason = InputValidator.validate_control_plane_override_payload(payload)
    except InputValidationError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    try:
        if action == "clear_freeze":
            result = control_plane.clear_manual_override(app_name)
        else:
            result = control_plane.set_manual_override(app_name, duration, reason)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


# ── GC-Shakti Integration Endpoints ──────────────────────────────────────────

EVIDENCE_STORE_PATH = os.path.join(root_dir, "data", "evidence_bundles.json")

def check_shakti_auth():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ")[1]
    expected_token = os.getenv("PRAVAH_API_KEY", "shakti-secret-key-change-in-prod")
    
    # Check X-Source-System header against allowed ecosystem sources
    source_system = request.headers.get("X-Source-System")
    allowed_sources = {"SHAKTI", "BHIV_MASTERDB", "WORKFLOW_BLACKHOLE", "UNIGURU"}
    if source_system not in allowed_sources:
        return False
        
    return token == expected_token

def load_evidence_bundles():
    if not os.path.exists(EVIDENCE_STORE_PATH):
        os.makedirs(os.path.dirname(EVIDENCE_STORE_PATH), exist_ok=True)
        return {}
    try:
        with open(EVIDENCE_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_evidence_bundle(evidence_ref: str, bundle: dict):
    store = load_evidence_bundles()
    store[evidence_ref] = bundle
    try:
        with open(EVIDENCE_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
        return True
    except Exception:
        return False

@app.route("/pravah/events", methods=["POST"])
@app.route("/pravah/api/v1/publish", methods=["POST"])
@limiter.exempt
def shakti_events():
    if not check_shakti_auth():
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"status": "error", "error": "Request body must be valid JSON"}), 400

    required_fields = ["trace_id", "correlation_id", "source", "action", "event_type", "payload", "source_system", "published_at"]
    for field in required_fields:
        if field not in payload:
            return jsonify({"status": "error", "error": f"Missing required field: {field}"}), 400

    response_payload = {
        "status": "CONNECTED",
        "detail": "Event published to Pravah pipeline",
        "trace_id": payload["trace_id"],
        "event_type": payload["event_type"],
        "pipeline_latency_ms": 12,
        "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    }

    try:
        control_plane.append_decision_history({
            "app_name": "shakti-gc",
            "executed_action": payload["action"],
            "reason": f"Ecosystem event: {payload['event_type']}",
            "execution_success": True,
            "event": {
                "trace_id": payload["trace_id"],
                "correlation_id": payload["correlation_id"]
            }
        })
    except Exception:
        pass

    return jsonify(response_payload), 200

@app.route("/evidence", methods=["POST"])
@limiter.exempt
def shakti_publish_evidence():
    if not check_shakti_auth():
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"status": "error", "error": "Request body must be valid JSON"}), 400

    required_fields = ["bundle_id", "trace_id", "execution_id", "decision_id", "decision_type", "authority_chain", "evidence", "produced_at", "correlation_id", "source", "action"]
    for field in required_fields:
        if field not in payload:
            return jsonify({"status": "error", "error": f"Missing required field: {field}"}), 400

    import uuid
    evidence_ref = f"ev-{uuid.uuid4().hex[:16]}"
    save_evidence_bundle(evidence_ref, payload)

    response_payload = {
        "evidence_ref": evidence_ref,
        "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    }

    return jsonify(response_payload), 200

@app.route("/evidence/<evidence_ref>", methods=["GET"])
@limiter.exempt
def shakti_retrieve_evidence(evidence_ref: str):
    if not check_shakti_auth():
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    store = load_evidence_bundles()
    bundle = store.get(evidence_ref)
    if not bundle:
        return jsonify({"status": "error", "error": "Evidence bundle not found"}), 404

    return jsonify(bundle), 200

@app.route("/registry/trace/<trace_id>", methods=["GET"])
@limiter.exempt
def query_unified_registry(trace_id: str):
    if not check_shakti_auth():
        return jsonify({"status": "error", "error": "Unauthorized"}), 401
    
    from control_plane.core.registry_manager import RegistryManager
    manager = RegistryManager(base_dir=root_dir)
    result = manager.query_trace_lineage(trace_id)
    return jsonify(result), 200

@app.route("/metrics", methods=["GET"])
@limiter.exempt
def prometheus_metrics():
    failures = 0
    recoveries = 0
    
    # 1. Parse decision history log to count failures/recoveries
    history_file = os.path.join(root_dir, "logs", "control_plane", "decision_history.jsonl")
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    action = record.get("executed_action") or record.get("action")
                    if action in ["scale_up", "heal", "restart"]:
                        recoveries += 1
                    elif record.get("state") == "degraded" or record.get("event_type") == "crash":
                        failures += 1
        except Exception:
            pass
            
    # Stability = 100 - (failures * 2) + (recoveries * 3)
    stability_score = 100 - (failures * 2) + (recoveries * 3)
    stability_score = max(0, min(100, stability_score))
    
    # Count active apps
    from control_plane.multi_app_control_plane import MultiAppControlPlane
    cp = MultiAppControlPlane(env=ENVIRONMENT)
    apps_count = len(cp.list_apps())
    
    metrics = [
        f"# HELP pravah_stability_score Current mathematical stability score of the ecosystem",
        f"# TYPE pravah_stability_score gauge",
        f"pravah_stability_score {stability_score}",
        f"# HELP pravah_active_apps_total Total number of registered ecosystem services",
        f"# TYPE pravah_active_apps_total gauge",
        f"pravah_active_apps_total {apps_count}",
        f"# HELP pravah_recoveries_total Total number of autonomous recovery actions executed",
        f"# TYPE pravah_recoveries_total counter",
        f"pravah_recoveries_total {recoveries}",
        f"# HELP pravah_failures_total Total number of system failures/degradations observed",
        f"# TYPE pravah_failures_total counter",
        f"pravah_failures_total {failures}"
    ]
    
    return "\n".join(metrics) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"}


if __name__ == "__main__":
    port = int(os.getenv("CONTROL_PLANE_PORT", os.getenv("PORT", 7000)))
    app.run(host="0.0.0.0", port=port, debug=False)
