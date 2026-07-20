"""Service discovery utilities for runtime manager."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from config import ConfigManager

KNOWN_ENTRYPOINTS = [
    "main.py",
    "bhiv_bucket.py",
    "integration_bridge.py",
    "prompt-runner01/run_server.py",
    "creator-core/Core-Integrator-Sprint-1.1/main.py",
]


def load_declared_services() -> Dict:
    """Authoritative service config from services.yml."""
    return ConfigManager.get_config().get("services", {})


def find_unregistered_service_files(repo_root: Path, declared_services: Dict) -> List[str]:
    """Detect candidate service scripts not registered in services.yml."""
    discovered = []
    declared_scripts = set()
    for service in declared_services.values():
        script = service.get("runner_script")
        if script:
            declared_scripts.add(str(Path(script).as_posix()))

    for path in repo_root.rglob("*_service.py"):
        rel = path.relative_to(repo_root).as_posix()
        if rel not in declared_scripts:
            discovered.append(rel)

    for entrypoint in KNOWN_ENTRYPOINTS:
        if entrypoint in declared_scripts:
            continue
        if (repo_root / entrypoint).exists():
            discovered.append(entrypoint)

    return sorted(set(discovered))
