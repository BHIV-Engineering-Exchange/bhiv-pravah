"""
Phase 4 — Resolution Signal Generation

Rules:
- One signal per bottleneck root cause only — single deterministic output
- Signal format: UNBLOCK_DEPENDENCY:<task_id>
- expected_unblock = number of blocked tasks sharing the same root cause
- No interpretation, no soft decision types — pure intelligence layer signal
"""

from typing import Any


def generate_actions(
    root_causes: dict[str, str],
    bottleneck: dict[str, Any] | None,
    constraint_results: list[dict[str, Any]],
    known_task_ids: set[str],
) -> list[dict[str, Any]]:
    """
    Generates a single deterministic resolution signal for the bottleneck root cause.

    Args:
        root_causes:        task_id -> root_cause_task_id (from Phase 2)
        bottleneck:         { task_id, impact_score, affected_tasks } or None (from Phase 3)
        constraint_results: list of { task_id, is_valid, unsatisfied_dependencies }
        known_task_ids:     set of all task_ids present in the task list

    Returns:
        List with one entry: { signal, target, expected_unblock }
        signal format: "UNBLOCK_DEPENDENCY:<task_id>"
    """
    if not root_causes or bottleneck is None:
        return []

    # single root cause: the bottleneck task's root cause only
    bottleneck_id = bottleneck["task_id"]
    rc = root_causes.get(bottleneck_id, bottleneck_id)

    # count how many blocked tasks share this root cause
    unblock_count = sum(1 for v in root_causes.values() if v == rc)

    return [{
        "signal": f"UNBLOCK_DEPENDENCY:{rc}",
        "target": rc,
        "expected_unblock": unblock_count,
    }]
