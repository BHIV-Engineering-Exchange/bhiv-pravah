"""
TTG/TTV Adapter Package
======================
TANTRA-compliant adapters for Text-to-Game and Text-to-Video integration.

Components:
- Input Normalizers: Convert TTG/TTV inputs to unified prompts
- Output Adapters: Transform Core outputs to product-specific formats
- TANTRA Bridge: Enforce pipeline flow and system boundaries
"""

from .ttg_input_normalizer import TTGInputNormalizer
from .ttv_input_normalizer import TTVInputNormalizer
from .ttg_output_adapter import TTGOutputAdapter
from .ttv_output_adapter import TTVOutputAdapter
from .tantra_bridge import TANTRAIntegrationBridge

__all__ = [
    "TTGInputNormalizer",
    "TTVInputNormalizer",
    "TTGOutputAdapter",
    "TTVOutputAdapter",
    "TANTRAIntegrationBridge"
]
