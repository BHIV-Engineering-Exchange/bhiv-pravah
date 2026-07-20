#!/usr/bin/env python3
"""Run SHAKTI sprint automated validation suite and write evidence artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPRINT_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = SPRINT_DIR / "evidence" / "validation_runs"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

SPRINT_TEST_FILES = [
    "tests/test_runtime_manager_sprint.py",
    "tests/test_spine_sprint.py",
    "tests/test_control_plane_sprint.py",
    "tests/test_telemetry_service_sprint.py",
    "tests/test_sprint_integration.py",
]

REQUIRED_EVIDENCE_DIRS = [
    "execution_logs",
    "replay_logs",
    "runtime_metrics",
    "trace_samples",
    "api_evidence",
    "recovery_evidence",
]


def _run(cmd: list[str], cwd: Path) -> dict:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
        "passed": proc.returncode == 0,
    }


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite": "SHAKTI sprint validation",
        "steps": [],
        "summary": {"passed": 0, "failed": 0, "partial": 0},
    }

    # 1) py_compile on sprint modules
    compile_targets = [
        "telemetry_service.py",
        "control_plane_service.py",
        "start_all.py",
        "run_recovery_verification.py",
    ]
    for pkg in ("runtime_manager", "spine"):
        compile_targets.extend(str(p) for p in sorted((REPO_ROOT / pkg).rglob("*.py")))
    compile_cmd = [sys.executable, "-m", "py_compile", *compile_targets]
    compile_result = _run(compile_cmd, REPO_ROOT)
    compile_result["name"] = "py_compile"
    report["steps"].append(compile_result)

    # 2) pytest sprint test suite
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        *SPRINT_TEST_FILES,
        "-v",
        "--tb=short",
    ]
    pytest_result = _run(pytest_cmd, REPO_ROOT)
    pytest_result["name"] = "pytest_sprint_suite"
    report["steps"].append(pytest_result)

    # 3) evidence folder presence check
    missing = []
    for sub in REQUIRED_EVIDENCE_DIRS:
        path = SPRINT_DIR / "evidence" / sub
        if not path.exists():
            missing.append(sub)
    evidence_check = {
        "name": "evidence_tree_check",
        "passed": len(missing) == 0,
        "exit_code": 0 if not missing else 1,
        "missing_dirs": missing,
        "command": "filesystem check",
    }
    report["steps"].append(evidence_check)

    # 4) Definition-of-done evidence file spot checks
    spot_checks = [
        SPRINT_DIR / "evidence/replay_logs/telemetry_hash_match_20260708T100842Z.json",
        SPRINT_DIR / "evidence/recovery_evidence/recovery_verification.json",
        SPRINT_DIR / "evidence/api_evidence/production_demo_transcript.json",
        REPO_ROOT / "REVIEW_PACKET.md",
    ]
    missing_files = [str(p.relative_to(REPO_ROOT)) for p in spot_checks if not p.exists()]
    dod_check = {
        "name": "definition_of_done_evidence_spot_check",
        "passed": len(missing_files) == 0,
        "exit_code": 0 if not missing_files else 1,
        "missing_files": missing_files,
        "command": "filesystem check",
    }
    report["steps"].append(dod_check)

    for step in report["steps"]:
        if step["passed"]:
            report["summary"]["passed"] += 1
        else:
            report["summary"]["failed"] += 1

    report["overall_passed"] = report["summary"]["failed"] == 0
    out_file = EVIDENCE_DIR / f"sprint_validation_{ts}.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    index_file = EVIDENCE_DIR / "INDEX.json"
    index = []
    if index_file.exists():
        index = json.loads(index_file.read_text(encoding="utf-8"))
    index.append({"file": out_file.name, "generated_at": report["generated_at"], "passed": report["overall_passed"]})
    index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote: {out_file}")
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
