import os
import json
import importlib
from typing import Dict, Any, Tuple, List

from ..modules.base import BaseModule

MODULES_DIR = os.path.join(os.path.dirname(__file__), '..', 'modules')


def _load_config(module_dir: str) -> Dict[str, Any]:
    cfg_path = os.path.join(module_dir, 'config.json')
    if not os.path.exists(cfg_path):
        return {}
    with open(cfg_path, 'r', encoding='utf-8') as f:
        try:
            cfg = json.load(f)
        except Exception as e:
            raise ValueError(f"Invalid JSON in {cfg_path}: {e}")
    # Basic validation
    if 'name' not in cfg or 'version' not in cfg:
        raise ValueError(f"Invalid module config {cfg_path}: missing 'name' or 'version'")
    return cfg


def load_modules(raise_on_invalid: bool = False) -> Tuple[Dict[str, BaseModule], List[str]]:
    """Scan the `modules/` folder, import module implementations, and return a mapping
    of module_name -> BaseModule instance. Returns (modules, errors).

    If `raise_on_invalid` is True, a validation error will raise immediately.
    """
    modules: Dict[str, BaseModule] = {}
    errors: List[str] = []

    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modules')
    if not os.path.isdir(base):
        return modules, errors

    for entry in os.listdir(base):
        entry_path = os.path.join(base, entry)
        if not os.path.isdir(entry_path):
            continue
        
        # Skip __pycache__ and other system directories
        if entry.startswith('__') and entry.endswith('__'):
            continue

        # Try load config
        cfg = {}
        try:
            cfg = _load_config(entry_path)
        except Exception as e:
            errors.append(str(e))
            if raise_on_invalid:
                raise
            continue

        # Try import module implementation at src.modules.<entry>.module
        try:
            mod_name = f"src.modules.{entry}.module"
            spec = importlib.import_module(mod_name)
        except Exception as e:
            errors.append(f"Failed to import {entry}: {e}")
            if raise_on_invalid:
                raise
            continue

        # Find a class that subclasses BaseModule
        impl = None
        for attr in dir(spec):
            obj = getattr(spec, attr)
            try:
                if isinstance(obj, type) and issubclass(obj, BaseModule) and obj is not BaseModule:
                    impl = obj
                    break
            except Exception:
                continue

        if impl is None:
            errors.append(f"No BaseModule implementation found in {entry}")
            if raise_on_invalid:
                raise ValueError(f"No BaseModule implementation found in {entry}")
            continue

        # Instantiate and register using config name if present else folder name
        instance = impl()
        name = cfg.get('name') or entry
        modules[name] = instance

    return modules, errors
