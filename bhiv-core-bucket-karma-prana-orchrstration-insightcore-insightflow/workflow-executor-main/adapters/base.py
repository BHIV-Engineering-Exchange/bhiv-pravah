"""
Base Adapter — Phase E

All execution adapters MUST inherit this.
No adapter may bypass this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAdapter(ABC):
    """
    Deterministic execution adapter interface.
    """

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a real-world action.

        Must return:
        {
          "success": bool,
          ... adapter-specific fields
        }
        """
        raise NotImplementedError
