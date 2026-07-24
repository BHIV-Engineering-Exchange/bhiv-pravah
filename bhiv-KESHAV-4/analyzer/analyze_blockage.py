"""
KESHAV — Dependency Intelligence Entry Point

Pipeline:
  Phase 1 → detect blocked tasks
  Phase 2 → trace root causes (anchored to unsatisfied_dependencies)
  Phase 3 → detect bottleneck
  Phase 4 → generate resolution signal
  Phase 5 → structure TANTRA output

Contract:
- trace_id accepted from input only — never generated; fail-closed if missing
- Output is TANTRA / RAJYA-compatible; consumed directly without transformation
- Fully deterministic; no mutation of input; no global state
"""

import logging
from typing import Any

from .action_generator import generate_actions
from .blocked_task_detector import detect_blocked_tasks
from .bottleneck_detector import detect_bottleneck
from .output_structurer import structure_output
from .root_cause_tracer import trace_root_causes

logger = logging.getLogger(__name__)

_FAIL_CLOSED: dict[str, str] = {
    "status": "FAIL",
    "reason": "INVALID_INPUT_CONTRACT",
    "trace_id": "",
}


def _validate(input_data: dict[str, Any]) -> None:
    """Raises ValueError with a clear message on any contract violation."""
    if not isinstance(input_data, dict):
        raise ValueError(f"input_data must be a dict, got {type(input_data).__name__}")
    if "execution_id" not in input_data:
        raise ValueError("Missing required field: 'execution_id'")
    if not isinstance(input_data["execution_id"], str):
        raise ValueError(
            f"Field 'execution_id' must be str, got {type(input_data['execution_id']).__name__}"
        )
    if "trace_id" not in input_data:
        raise ValueError("Missing required field: 'trace_id'")
    if not isinstance(input_data["trace_id"], str):
        raise ValueError(
            f"Field 'trace_id' must be str, got {type(input_data['trace_id']).__name__}"
        )
    for list_field in ("tasks", "constraint_results", "propagation_results"):
        value = input_data.get(list_field)
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(
                    f"Field '{list_field}' must be a list, got {type(value).__name__}"
                )
            for item in value:
                if not isinstance(item, dict):
                    raise ValueError(f"Item in '{list_field}' must be a dict, got {type(item).__name__}")
                if "task_id" not in item:
                    raise ValueError(f"Missing 'task_id' in item of '{list_field}'")
                if not isinstance(item["task_id"], str):
                    raise ValueError(f"'task_id' must be a string in '{list_field}'")


def analyze_and_recommend(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point. Accepts input contract, returns TANTRA output contract.

    Args:
        input_data: {
            trace_id,            (REQUIRED — passed through unchanged)
            execution_id,
            tasks:               [{ task_id, depends_on }],
            constraint_results:  [{ task_id, is_valid, unsatisfied_dependencies }],
            propagation_results: [{ task_id, affected_tasks, impact_score }]
        }

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

    On invalid input returns:
        { "status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": "" }
    """
    try:
        _validate(input_data)
    except ValueError:
        return dict(_FAIL_CLOSED)

    trace_id            = input_data["trace_id"]
    execution_id        = input_data["execution_id"]
    tasks               = input_data.get("tasks", [])
    constraint_results  = input_data.get("constraint_results", [])
    propagation_results = input_data.get("propagation_results", [])

    logger.info("analyze_and_recommend started | execution_id=%s trace_id=%s", execution_id, trace_id)

    blocked_task_ids = detect_blocked_tasks(constraint_results)
    root_causes = trace_root_causes(blocked_task_ids, tasks, constraint_results)
    bottleneck = detect_bottleneck(blocked_task_ids, propagation_results)
    known_task_ids = {t["task_id"] for t in tasks}
    actions = generate_actions(root_causes, bottleneck, constraint_results, known_task_ids)
    result = structure_output(trace_id, execution_id, root_causes, bottleneck, actions)

    logger.info("analyze_and_recommend complete | execution_id=%s", execution_id)
    return result
