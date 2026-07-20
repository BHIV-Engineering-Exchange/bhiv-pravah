from typing import Any, Dict

from creator_core_engine.models import PromptRunnerInstruction

from .base import BaseAdapter


class LegalAdapter(BaseAdapter):
    product_target = "legal"

    def transform(
        self,
        instruction: PromptRunnerInstruction,
        generic_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "user_query": instruction.prompt,
            "domain_hint": instruction.module,
        }