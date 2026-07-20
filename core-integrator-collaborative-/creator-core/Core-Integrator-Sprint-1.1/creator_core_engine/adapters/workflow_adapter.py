from typing import Any, Dict

from creator_core_engine.models import PromptRunnerInstruction

from .base import BaseAdapter, build_title


class WorkflowAdapter(BaseAdapter):
    product_target = "workflow"

    def transform(
        self,
        instruction: PromptRunnerInstruction,
        generic_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "workflow_name": build_title(instruction.topic, instruction.prompt),
            "steps": list(instruction.tasks),
        }