"""Start local Sampada gateway with backend/.env loaded (no secret output)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ENV_PATH = REPO / "backend" / ".env"
GATEWAY_DIR = REPO / "backend" / "services" / "gateway"
PYTHON = REPO / "backend" / "venv" / "Scripts" / "python.exe"


def load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value and not value.startswith("<"):
            os.environ[key] = value


def main() -> int:
    if not PYTHON.exists():
        print("BLOCKER: backend venv missing — run setup_venv.bat first")
        return 1
    load_env(ENV_PATH)
    cmd = [
        str(PYTHON),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    return subprocess.call(cmd, cwd=str(GATEWAY_DIR), env=os.environ.copy())


if __name__ == "__main__":
    raise SystemExit(main())
