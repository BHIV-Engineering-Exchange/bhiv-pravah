#!/usr/bin/env python3
"""
Run Control Center E2E suite with JSON report output.

Usage (from backend/):
  python tests/e2e/control_center/run_control_center_e2e.py

Or via pytest:
  python -m pytest tests/e2e/control_center/test_control_center_e2e.py -v -m e2e
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    backend_root = Path(__file__).resolve().parents[3]
    os.chdir(backend_root)
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(backend_root))
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/e2e/control_center/test_control_center_e2e.py",
        "-v",
        "-m",
        "e2e",
        "--tb=short",
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, env=env)
    report = Path(backend_root) / "tests/e2e/control_center/results/control_center_e2e_report.json"
    if report.exists():
        print(f"\nReport written: {report}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
