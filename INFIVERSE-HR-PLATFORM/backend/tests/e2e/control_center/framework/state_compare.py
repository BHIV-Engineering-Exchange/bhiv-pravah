"""Compare baseline vs final Control Center snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .state_capture import SystemState

STAT_KEYS = (
    "total_candidates",
    "active_jobs",
    "recent_matches",
    "pending_interviews",
    "new_candidates_this_week",
    "total_feedback_submissions",
)


@dataclass
class CompareFinding:
    name: str
    passed: bool
    detail: str
    severity: str = "error"  # error | warning | info


@dataclass
class CompareResult:
    passed: bool
    findings: List[CompareFinding] = field(default_factory=list)
    deltas: Dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, passed: bool, detail: str, *, severity: str = "error") -> None:
        self.findings.append(CompareFinding(name=name, passed=passed, detail=detail, severity=severity))
        if not passed and severity == "error":
            self.passed = False


def _num(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def compare_states(
    baseline: SystemState,
    final: SystemState,
    *,
    pipeline_correlation_id: Optional[str] = None,
    require_audit_increase: bool = True,
) -> CompareResult:
    result = CompareResult(passed=True, deltas={})

    base_audit = baseline.audit_event_count
    final_audit = final.audit_event_count
    result.deltas["audit_event_count"] = {
        "baseline": base_audit,
        "final": final_audit,
        "delta": final_audit - base_audit,
    }

    if require_audit_increase:
        result.add(
            "audit_events_increased",
            final_audit >= base_audit,
            f"audit events baseline={base_audit} final={final_audit}",
        )
        if pipeline_correlation_id:
            replay_events = (final.audit_replay or {}).get("events") or []
            found = any(
                str(e.get("correlation_id", "")) == pipeline_correlation_id
                for e in replay_events
                if isinstance(e, dict)
            )
            result.add(
                "pipeline_correlation_in_replay",
                found or final_audit > base_audit,
                f"correlation_id={pipeline_correlation_id} present_in_replay={found}",
                severity="warning" if not found else "error",
            )

    if baseline.mongo_audit_count is not None and final.mongo_audit_count is not None:
        mongo_delta = final.mongo_audit_count - baseline.mongo_audit_count
        result.deltas["mongo_control_center_audit"] = {
            "baseline": baseline.mongo_audit_count,
            "final": final.mongo_audit_count,
            "delta": mongo_delta,
        }
        result.add(
            "mongo_audit_non_decreasing",
            mongo_delta >= 0,
            f"mongo audit_logs control_center count delta={mongo_delta}",
        )

    for key in STAT_KEYS:
        b = _num((baseline.candidate_stats or {}).get(key))
        f = _num((final.candidate_stats or {}).get(key))
        result.deltas.setdefault("candidate_stats", {})[key] = {"baseline": b, "final": f, "delta": f - b}
        if f < b:
            result.add(
                f"stats_{key}_no_drop",
                False,
                f"{key} dropped from {b} to {f}",
            )
        else:
            result.add(
                f"stats_{key}_no_drop",
                True,
                f"{key} baseline={b} final={f}",
                severity="info",
            )

    base_scope = (baseline.candidate_stats or {}).get("policy_scope") or {}
    final_scope = (final.candidate_stats or {}).get("policy_scope") or {}
    if base_scope and final_scope:
        result.add(
            "policy_scope_stable",
            base_scope.get("scope_label") == final_scope.get("scope_label"),
            f"scope_label {base_scope.get('scope_label')} -> {final_scope.get('scope_label')}",
            severity="warning",
        )

    if final.metrics_dashboard:
        metrics_keys = ("performance_summary", "business_metrics", "system_metrics", "policy_scope")
        for key in metrics_keys:
            if key not in final.metrics_dashboard:
                result.add(
                    f"metrics_dashboard_has_{key}",
                    False,
                    f"missing key {key} in /metrics/dashboard",
                )

    return result
