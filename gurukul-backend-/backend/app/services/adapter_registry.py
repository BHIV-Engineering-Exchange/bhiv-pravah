"""
Adapter Registry Service

Manages language adapters for the Sovereign Fusion Layer.
Currently focused on Arabic language support.

Adapters are used to fine-tune the base model for specific languages,
improving translation quality and cultural context understanding.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global registry cache
_registry_cache: Optional[Dict[str, Any]] = None


def _get_registry_path() -> Path:
    """Get path to adapter registry JSON file"""
    return Path(__file__).parent.parent.parent / "adapters" / "registry.json"


def load_registry() -> Dict[str, Any]:
    """
    Load adapter registry from JSON file
    
    Returns:
        dict: Registry data with adapters and metadata
        
    Raises:
        FileNotFoundError: If registry file doesn't exist
        json.JSONDecodeError: If registry file is invalid
    """
    global _registry_cache
    
    if _registry_cache is not None:
        return _registry_cache
    
    registry_path = _get_registry_path()
    
    if not registry_path.exists():
        logger.warning(f"Registry file not found at {registry_path}, creating default...")
        _create_default_registry(registry_path)
    
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            _registry_cache = json.load(f)
        logger.info(f"Adapter registry loaded: {len(_registry_cache.get('adapters', []))} adapters")
        return _registry_cache
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in registry file: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load registry: {e}")
        raise


def _create_default_registry(registry_path: Path):
    """Create default registry file if it doesn't exist"""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_registry = {
        "version": "1.0.0",
        "last_updated": "2025-01-20",
        "adapters": [
            {
                "lang": "ar",
                "language_name": "Arabic",
                "language_name_native": "العربية",
                "tokens": 50000,
                "vram_mb": 2048,
                "version": "1.0.0",
                "path": "adapters/ar_adapter.bin",
                "status": "active",
                "description": "Arabic language adapter",
                "supported_scripts": ["arabic"],
                "rtl": True
            }
        ],
        "default_language": "ar"
    }
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(default_registry, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created default registry at {registry_path}")


def get_adapter_for_language(lang: str) -> Optional[Dict[str, Any]]:
    """
    Get adapter configuration for a specific language
    
    Args:
        lang: Language code (e.g., 'ar' for Arabic)
        
    Returns:
        dict: Adapter configuration or None if not found
    """
    registry = load_registry()
    adapters = registry.get('adapters', [])
    
    # Find adapter for language
    for adapter in adapters:
        if adapter.get('lang') == lang.lower() and adapter.get('status') == 'active':
            return adapter
    
    logger.warning(f"No active adapter found for language: {lang}")
    return None


def validate_adapter(adapter_path: str) -> bool:
    """
    Validate that adapter file exists and is accessible
    
    Args:
        adapter_path: Path to adapter file (relative or absolute)
        
    Returns:
        bool: True if adapter is valid, False otherwise
    """
    if not adapter_path:
        return False
    
    # Convert relative path to absolute
    if not Path(adapter_path).is_absolute():
        adapter_path = Path(__file__).parent.parent.parent / adapter_path
    
    adapter_file = Path(adapter_path)
    
    if not adapter_file.exists():
        logger.warning(f"Adapter file not found: {adapter_path}")
        return False
    
    # Check if file is readable
    if not adapter_file.is_file():
        logger.warning(f"Adapter path is not a file: {adapter_path}")
        return False
    
    logger.debug(f"Adapter validated: {adapter_path}")
    return True


def get_available_languages() -> list:
    """
    Get list of all available languages with adapters
    
    Returns:
        list: List of language codes with active adapters
    """
    registry = load_registry()
    adapters = registry.get('adapters', [])
    
    return [
        adapter.get('lang')
        for adapter in adapters
        if adapter.get('status') == 'active'
    ]


def get_adapter_metadata(lang: str) -> Optional[Dict[str, Any]]:
    """
    Get full metadata for an adapter
    
    Args:
        lang: Language code
        
    Returns:
        dict: Full adapter metadata including all fields
    """
    adapter = get_adapter_for_language(lang)
    if adapter:
        return {
            **adapter,
            "validated": validate_adapter(adapter.get('path', ''))
        }
    return None


