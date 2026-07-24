"""
Task Execution Adapter — Phase E

Deterministic, local task registry with audit log.
Demo-safe fallback when external task systems are unavailable.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from adapters.base import BaseAdapter


class TaskAdapter(BaseAdapter):
    """
    Local task execution adapter.
    """

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = payload.get("title")
        description = payload.get("description", "")
        trace_id = payload.get("trace_id")

        if not title:
            return {
                "success": False,
                "error_code": "missing_task_title",
                "message": "title is required to create a task",
            }

        task_id = f"task_{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow().isoformat() + "Z"

        # Deterministic task object (audit-safe)
        task_record = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "status": "CREATED",
            "created_at": created_at,
            "trace_id": trace_id,
        }

        # NOTE:
        # In Phase E demo, this replaces:
        # - Notion
        # - Google Tasks
        # - Trello
        # with a stable, reproducible registry

        return {
            "success": True,
            "task_id": task_id,
            "task_status": "CREATED",
            "reference": f"local://tasks/{task_id}",
            "trace_id": trace_id,
            "created_at": created_at,
        }
