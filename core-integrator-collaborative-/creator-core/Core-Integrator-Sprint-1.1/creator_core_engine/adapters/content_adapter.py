from typing import Any, Dict

from creator_core_engine.models import PromptRunnerInstruction

from .base import BaseAdapter, build_title


class ContentAdapter(BaseAdapter):
    product_target = "content"

    def transform(
        self,
        instruction: PromptRunnerInstruction,
        generic_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "content_type": instruction.output_format,
            "title": build_title(instruction.topic, instruction.prompt),
            "outline": list(instruction.tasks),
        }