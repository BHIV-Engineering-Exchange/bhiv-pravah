from typing import Any, Dict

from creator_core_engine.models import PromptRunnerInstruction

from .base import BaseAdapter

FORBIDDEN_FINANCE_KEYWORDS = {"trade", "trading", "buy", "sell", "execute_trade"}


class FinanceAdapter(BaseAdapter):
    product_target = "finance"

    def transform(
        self,
        instruction: PromptRunnerInstruction,
        generic_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        material = " ".join([instruction.prompt, instruction.intent, instruction.topic, *instruction.tasks]).lower()
        if any(keyword in material for keyword in FORBIDDEN_FINANCE_KEYWORDS):
            raise ValueError("Creator Core does not generate trading execution instructions.")

        return {
            "analysis_type": instruction.intent,
            "target": instruction.topic,
            "steps": list(instruction.tasks),
        }