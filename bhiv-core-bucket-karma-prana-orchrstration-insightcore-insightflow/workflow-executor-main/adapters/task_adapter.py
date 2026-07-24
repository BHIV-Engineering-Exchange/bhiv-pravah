from typing import Dict, Any
from adapters.base import ExecutionAdapter


class TaskAdapter(ExecutionAdapter):
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = payload.get("title")

        if not title:
            return {
                "success": False,
                "error_code": "missing_task_title",
                "message": "title is required to create a task"
            }

        # Real system hook placeholder
        # Example: call task-service / DB insert

        return {
            "success": True,
            "task_id": "task_live_001",
            "title": title
        }
