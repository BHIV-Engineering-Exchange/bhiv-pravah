from typing import Any, Dict

from creator_core_engine.models import PromptRunnerInstruction

from .base import BaseAdapter


class AssistantAdapter(BaseAdapter):
    product_target = "assistant"

    def transform(
        self,
        instruction: PromptRunnerInstruction,
        generic_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "goal": instruction.topic,
            "plan_steps": list(instruction.tasks),
        }