"""Runtime startup configuration validation."""

from __future__ import annotations

from collections import Counter
from typing import Dict


class RuntimeManagerConfigError(ValueError):
    """Raised when runtime manager configuration is invalid."""


def validate_services_config(services: Dict) -> None:
    """Validate service configuration and dependency graph."""
    names = set(services.keys())
    missing_health = [
        name for name, cfg in services.items() if not cfg.get("health_check_endpoint")
    ]
    if missing_health:
        raise RuntimeManagerConfigError(
            f"Missing health_check_endpoint for: {', '.join(sorted(missing_health))}"
        )

    for name, cfg in services.items():
        for dep in cfg.get("depends_on", []):
            if dep not in names:
                raise RuntimeManagerConfigError(
                    f"Service '{name}' depends on undefined service '{dep}'"
                )

    ports = [cfg.get("port") for cfg in services.values() if cfg.get("port") is not None]
    dup_ports = [str(port) for port, count in Counter(ports).items() if count > 1]
    if dup_ports:
        raise RuntimeManagerConfigError(
            f"Port collision detected for ports: {', '.join(sorted(dup_ports))}"
        )


def validate_startup_order(orchestrator) -> None:
    """Ask existing orchestrator topological sort to raise on cycles."""
    orchestrator._calculate_startup_order()
