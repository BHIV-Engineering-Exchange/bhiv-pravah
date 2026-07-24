"""
Phase 3 — Bottleneck Detection

Rules:
- Only consider blocked tasks
- Look up each blocked task's impact_score from propagation_results
- Task with the highest impact_score among blocked tasks = bottleneck
- Tie-break: lowest task_id (lexicographic) for determinism
- If no blocked tasks → return None
"""

from typing import Any


def detect_bottleneck(
    blocked_task_ids: list[str],
    propagation_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Finds the bottleneck: blocked task with highest impact_score.

    Args:
        blocked_task_ids:    sorted list of blocked task IDs (from Phase 1)
        propagation_results: list of { task_id, affected_tasks, impact_score }

    Returns:
        { task_id, impact_score, affected_tasks } or None if no blocked tasks
    """
    if not blocked_task_ids:
        return None

    blocked_set = set(blocked_task_ids)

    # build impact lookup — default 0 if task missing from propagation_results
    impact_map = {
        p["task_id"]: {
            "impact_score": p.get("impact_score", 0),
            "affected_tasks": sorted(p.get("affected_tasks", [])),
        }
        for p in propagation_results
        if p["task_id"] in blocked_set
    }

    # pick highest impact_score
    # tie-break: lowest task_id lexicographically (correct for all unicode strings)
    bottleneck_id = min(
        blocked_task_ids,
        key=lambda tid: (
            -impact_map.get(tid, {}).get("impact_score", 0),
            tid,
        ),
    )

    return {
        "task_id": bottleneck_id,
        "impact_score": impact_map.get(bottleneck_id, {}).get("impact_score", 0),
        "affected_tasks": impact_map.get(bottleneck_id, {}).get("affected_tasks", []),
    }
