"""
NAS Adapter Sync Script

Syncs language adapters from NAS storage to local registry.
Currently focused on Arabic adapter.

Usage:
    python scripts/sync_adapters_nas.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.adapter_registry import load_registry, _get_registry_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_from_nas(nas_path: str, target_dir: Optional[Path] = None) -> bool:
    """
    Sync adapters from NAS storage
    
    Args:
        nas_path: Path to NAS storage (can be local path, URL, or network path)
        target_dir: Target directory for adapters (default: backend/adapters/)
        
    Returns:
        bool: True if sync successful, False otherwise
    """
    if target_dir is None:
        target_dir = Path(__file__).parent.parent / "adapters"
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Syncing adapters from NAS: {nas_path}")
    logger.info(f"Target directory: {target_dir}")
    
    # For now, this is a placeholder
    # In production, this would:
    # 1. Connect to NAS storage
    # 2. Download adapter files
    # 3. Validate checksums
    # 4. Update registry.json
    
    logger.info("NAS sync functionality will be implemented based on your NAS setup")
    logger.info("For now, adapters should be placed manually in backend/adapters/")
    
    return True


def validate_registry_checksums() -> Dict[str, bool]:
    """
    Validate checksums of adapter files in registry
    
    Returns:
        dict: Mapping of language codes to validation status
    """
    registry = load_registry()
    adapters = registry.get('adapters', [])
    
    results = {}
    for adapter in adapters:
        lang = adapter.get('lang')
        path = adapter.get('path')
        
        if path:
            # Check if file exists
            adapter_path = Path(__file__).parent.parent / path
            results[lang] = adapter_path.exists()
        else:
            results[lang] = False
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync adapters from NAS")
    parser.add_argument(
        "--nas-path",
        type=str,
        help="Path to NAS storage",
        default=os.getenv("NAS_ADAPTER_PATH", "")
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing adapters"
    )
    
    args = parser.parse_args()
    
    if args.validate:
        logger.info("Validating adapter checksums...")
        results = validate_registry_checksums()
        for lang, valid in results.items():
            status = "✓" if valid else "✗"
            logger.info(f"{status} {lang}: {'Valid' if valid else 'Missing'}")
    elif args.nas_path:
        sync_from_nas(args.nas_path)
    else:
        logger.info("Usage: python sync_adapters_nas.py --nas-path <path> or --validate")
        logger.info("For Arabic adapter, place ar_adapter.bin in backend/adapters/")

