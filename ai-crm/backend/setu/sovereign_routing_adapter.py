REQUIRED_FIELDS = [
    "execution_id",
    "trace_id",
    "source_system",
    "actor",
    "intent_type",
    "target_system",
    "parameters",
    "priority",
    "timestamp",
    "schema_version",
    "tenant_id"
]

REQUIRED_GATED_FIELDS = [
    "status",
    "attestation_id",
    "policy_id",
    "policy_version",
    "checked_at"
]


def _assert_required(execution):
    missing = [field for field in REQUIRED_FIELDS if execution.get(field) is None]
    if missing:
        raise ValueError("Missing execution fields: " + ", ".join(missing))


def _default_gated_bridge_validator(execution):
    gated = (execution.get("governance") or {}).get("gated_bridge")
    if not gated:
        return {"ok": False, "reason": "gated_bridge_missing"}

    missing = [field for field in REQUIRED_GATED_FIELDS if gated.get(field) is None]
    if missing:
        return {"ok": False, "reason": "gated_bridge_incomplete", "missing_fields": missing}

    if gated.get("status") != "approved":
        return {"ok": False, "reason": "gated_bridge_not_approved", "status": gated.get("status")}

    return {"ok": True, "governance": {"gated_bridge": gated}}


def _build_sarathi_payload(execution):
    return {
        "sarathi_version": "1.0",
        "execution_id": execution.get("execution_id"),
        "trace_id": execution.get("trace_id"),
        "tenant_id": execution.get("tenant_id"),
        "intent_type": execution.get("intent_type"),
        "source_system": execution.get("source_system"),
        "target_system": execution.get("target_system"),
        "parameters": execution.get("parameters"),
        "priority": execution.get("priority"),
        "timestamp": execution.get("timestamp"),
        "schema_version": execution.get("schema_version"),
        "actor": execution.get("actor")
    }


def _build_bhiv_envelope(execution, sarathi_payload):
    return {
        "envelope_version": "1.0",
        "execution": {
            "execution_id": execution.get("execution_id"),
            "trace_id": execution.get("trace_id"),
            "tenant_id": execution.get("tenant_id"),
            "intent_type": execution.get("intent_type"),
            "source_system": execution.get("source_system"),
            "target_system": execution.get("target_system"),
            "parameters": execution.get("parameters"),
            "priority": execution.get("priority"),
            "timestamp": execution.get("timestamp"),
            "schema_version": execution.get("schema_version"),
            "actor": execution.get("actor")
        },
        "routing": sarathi_payload,
        "governance": execution.get("governance"),
        "provenance": execution.get("provenance"),
        "replay": execution.get("replay")
    }


class SovereignRoutingAdapter:
    def __init__(self, gated_bridge_validator=None):
        self.gated_bridge_validator = gated_bridge_validator or _default_gated_bridge_validator

    def to_sarathi_payload(self, execution):
        _assert_required(execution)
        return _build_sarathi_payload(execution)

    def to_bhiv_envelope(self, execution):
        _assert_required(execution)
        sarathi_payload = _build_sarathi_payload(execution)
        return _build_bhiv_envelope(execution, sarathi_payload)

    def build_routing_packet(self, execution):
        try:
            _assert_required(execution)
        except ValueError as error:
            return {
                "ok": False,
                "reason": "execution_contract_invalid",
                "details": str(error)
            }

        gated = self.gated_bridge_validator(execution)
        if not gated.get("ok"):
            return {
                "ok": False,
                "reason": gated.get("reason"),
                "details": gated.get("missing_fields") or gated.get("status")
            }

        sarathi_payload = _build_sarathi_payload(execution)
        bhiv_envelope = _build_bhiv_envelope(execution, sarathi_payload)

        return {
            "ok": True,
            "sarathi_payload": sarathi_payload,
            "bhiv_envelope": bhiv_envelope,
            "governance": gated.get("governance")
        }
