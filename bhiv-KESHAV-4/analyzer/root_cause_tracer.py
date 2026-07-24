"""
Phase 2 — Root Cause Tracing

Rules:
- Primary: anchor to unsatisfied_dependencies — first sorted entry is the root cause candidate
- If that candidate is missing from task list entirely → it is the root cause (missing dep)
- If that candidate is itself invalid → traverse deeper via BFS to find deepest invalid node
- If a task has no unsatisfied_dependencies and is itself invalid → it is its own root cause
- Backward graph traversal is used only for validation/deepening, not as primary logic
"""

from collections import deque
from typing import Any


def trace_root_causes(
    blocked_task_ids: list[str],
    tasks: list[dict[str, Any]],
    constraint_results: list[dict[str, Any]],
) -> dict[str, str]:
    """
    For each blocked task, finds root cause anchored to unsatisfied_dependencies.

    Args:
        blocked_task_ids:   sorted list of blocked task IDs (from Phase 1)
        tasks:              list of { task_id, depends_on }
        constraint_results: list of { task_id, is_valid, unsatisfied_dependencies }

    Returns:
        dict mapping task_id → root_cause_task_id (deterministic)
    """
    validity: dict[str, bool] = {
        str(e["task_id"]): bool(e.get("is_valid", True)) for e in constraint_results
    }
    unsatisfied_map: dict[str, list[str]] = {
        str(e["task_id"]): sorted(str(d) for d in (e.get("unsatisfied_dependencies") or []))
        for e in constraint_results
    }
    depends_on: dict[str, list[str]] = {
        str(t["task_id"]): sorted(str(d) for d in (t.get("depends_on") or []))
        for t in tasks
    }
    known_tasks: set[str] = set(depends_on.keys())

    def find_root_cause(task_id: str) -> str:
        # Primary anchor: first unsatisfied dependency (sorted → deterministic)
        unsatisfied = unsatisfied_map.get(task_id, [])
        if unsatisfied:
            first_unsat = unsatisfied[0]
            # missing from task list entirely → definitive root cause
            if first_unsat not in known_tasks:
                return first_unsat
            # if the unsatisfied dep is itself invalid, traverse deeper
            if not validity.get(first_unsat, True):
                return _traverse_deeper(first_unsat, validity, unsatisfied_map, depends_on, known_tasks)
            return first_unsat

        # No unsatisfied deps and task is invalid → own root cause
        return task_id

    return {task_id: find_root_cause(task_id) for task_id in blocked_task_ids}


def _traverse_deeper(
    start: str,
    validity: dict[str, bool],
    unsatisfied_map: dict[str, list[str]],
    depends_on: dict[str, list[str]],
    known_tasks: set[str],
) -> str:
    """BFS from start to find the deepest invalid node (validation pass)."""
    visited: set[str] = set()
    last_invalid = start
    queue: deque[str] = deque()

    # seed queue: prefer unsatisfied deps, fall back to depends_on
    seed = unsatisfied_map.get(start) or depends_on.get(start, [])
    queue.extend(sorted(seed))

    while queue:
        current = queue.popleft()
        if current not in known_tasks:
            return current
        if current in visited:
            continue
        visited.add(current)
        if not validity.get(current, True):
            last_invalid = current
            nxt = unsatisfied_map.get(current) or depends_on.get(current, [])
            queue.extendleft(reversed(sorted(nxt)))

    return last_invalid
