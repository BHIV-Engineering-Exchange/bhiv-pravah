"""
Phase 1 — Blocked Task Detection

Rules:
- If is_valid = false in constraint_results → task is BLOCKED
- Returns sorted list of blocked task_ids (deterministic)
"""

from typing import Any


def detect_blocked_tasks(constraint_results: list[dict[str, Any]]) -> list[str]:
    """
    Scans constraint_results and returns sorted list of blocked task IDs.

    Args:
        constraint_results: list of { task_id, is_valid, unsatisfied_dependencies }

    Returns:
        Sorted list of blocked task_ids where is_valid = false
    """
    blocked = [
        entry["task_id"]
        for entry in constraint_results
        if not entry.get("is_valid", True)
    ]

    return sorted(blocked)
