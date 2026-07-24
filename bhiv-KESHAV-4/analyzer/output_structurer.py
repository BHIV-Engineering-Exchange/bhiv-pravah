"""
Phase 5 — TANTRA Output Structuring

Output contract (TANTRA / RAJYA-compatible):
    trace_id, execution_id, root_cause, resolution_signal, impact_score, severity, timestamp

Rules:
- trace_id: accepted from input only — never generated
- Single deterministic root_cause (bottleneck's root cause only)
- resolution_signal: UNBLOCK_DEPENDENCY:<task_id>
- impact_score: bottleneck's impact_score (0 if no bottleneck)
- severity: LOW (<3), MEDIUM (3–9), HIGH (>=10) — deterministic, no interpretation
- timestamp: ISO-8601 UTC, injected at call time
- No randomness, no internal/debug fields
"""

from datetime import datetime, timezone
from typing import Any


def _severity(impact_score: int | float) -> str:
    if impact_score >= 10:
        return "HIGH"
    if impact_score >= 3:
        return "MEDIUM"
    return "LOW"


def structure_output(
    trace_id: str,
    execution_id: str,
    root_causes: dict[str, str],
    bottleneck: dict[str, Any] | None,
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Assembles deterministic TANTRA-aligned final output.

    Returns:
        {
            trace_id,
            execution_id,
            root_cause,
            resolution_signal,
            impact_score,
            severity,
            timestamp
        }
    """
    if bottleneck is not None:
        top_root_cause = root_causes.get(bottleneck["task_id"], bottleneck["task_id"])
        impact_score = bottleneck["impact_score"]
    else:
        top_root_cause = None
        impact_score = 0

    resolution_signal = actions[0]["signal"] if actions else None
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "trace_id": trace_id,
        "execution_id": execution_id,
        "root_cause": top_root_cause,
        "resolution_signal": resolution_signal,
        "impact_score": impact_score,
        "severity": _severity(impact_score),
        "timestamp": timestamp,
    }
