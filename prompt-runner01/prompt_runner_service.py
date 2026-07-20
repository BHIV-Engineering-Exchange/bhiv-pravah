"""Integration-friendly service layer for Universal Prompt Runner.

This module has no Streamlit dependency. Other projects can import these
functions directly and use the core engine programmatically.
"""

from typing import Any, Dict, Union

from platform_adapter import PlatformAdapter


class PromptRunnerService:
    """Thin service wrapper around PlatformAdapter for external integration."""

    def __init__(self) -> None:
        self._adapter = PlatformAdapter()

    def process(self, input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Process either a natural-language prompt or a structured request."""
        return self._adapter.process(input_data)

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """Process a natural-language prompt."""
        return self._adapter.process(prompt)

    def process_structured(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a structured request payload."""
        return self._adapter.process(request)

    def health(self) -> Dict[str, Any]:
        """Return adapter health metadata."""
        return self._adapter.health_check()


# Convenience functions for direct imports in other projects.
def process_prompt(prompt: str) -> Dict[str, Any]:
    return PromptRunnerService().process_prompt(prompt)


def process_structured(request: Dict[str, Any]) -> Dict[str, Any]:
    return PromptRunnerService().process_structured(request)


def health_check() -> Dict[str, Any]:
    return PromptRunnerService().health()
