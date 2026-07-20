from abc import ABC, abstractmethod
from typing import Any, Dict

from creator_core_engine.models import PromptRunnerInstruction


class BaseAdapter(ABC):
    product_target: str

    @abstractmethod
    def transform(
        self,
        instruction: PromptRunnerInstruction,
        generic_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert generic payloads into product-specific blueprint payloads."""


def build_title(topic: str, prompt: str) -> str:
    if topic:
        return topic.replace("_", " ").strip().title()
    return prompt.strip().rstrip(".")[:80]