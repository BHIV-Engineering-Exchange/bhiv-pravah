"""CLI entrypoint for runtime manager."""

from __future__ import annotations

import logging
import sys

from .manager import RuntimeManager, RuntimeManagerConfigError


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    try:
        manager = RuntimeManager()
        manager.print_startup_plan()
        return manager.run(check_interval=5)
    except RuntimeManagerConfigError as exc:
        print(f"[CONFIG ERROR] {exc}")
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"[FATAL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
