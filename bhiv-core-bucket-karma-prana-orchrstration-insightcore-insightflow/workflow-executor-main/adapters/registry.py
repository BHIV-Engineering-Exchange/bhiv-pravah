"""
Adapter Registry — Phase E

Responsibilities:
- Maintain deterministic adapter lookup
- No dynamic imports
- No runtime mutation
- One action_type → one adapter
"""

from typing import Dict, Optional

from adapters.base import BaseAdapter

# Import adapters explicitly (NO lazy loading)
from adapters.whatsapp.adapter import WhatsAppAdapter
from adapters.email.adapter import EmailAdapter
from adapters.ai.adapter import AIAdapter
from adapters.tasks.adapter import TaskAdapter


# -------------------------------------------------------------------
# Adapter Registry (LOCKED)
# -------------------------------------------------------------------

_ADAPTERS: Dict[str, BaseAdapter] = {
    "whatsapp": WhatsAppAdapter(),
    "email": EmailAdapter(),
    "ai": AIAdapter(),
    "task": TaskAdapter(),
}


def get_adapter(action_type: str) -> Optional[BaseAdapter]:
    """
    Deterministic adapter resolver.

    Rules:
    - No guessing
    - No fallback
    - Unsupported action_type → None
    """

    return _ADAPTERS.get(action_type)
