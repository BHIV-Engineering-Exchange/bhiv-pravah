#!/usr/bin/env python3
"""
KESHAV Production Validation Script

Checks:
  1. All tests pass (123 tests)
  2. Code coverage >= 90%
  3. Linting passes
  4. Type checking passes
  5. Required production files exist
  6. API smoke test (in-process, no subprocess, no ports)

Usage:
    python validate_production.py
"""

import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: str) -> tuple[bool, str]:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    return r.returncode == 0, r.stdout + r.stderr


def _ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}")


def check_tests() -> bool:
    print("\n[1] Tests")
    ok, out = _run("python -m pytest tests/ -q --tb=short")
    if ok and "passed" in out:
        for line in out.splitlines():
            if "passed" in line:
                _ok(line.strip())
                return True
    _fail("test suite failed")
    print(out[-2000:])
    return False


def check_coverage() -> bool:
    print("\n[2] Coverage")
    ok, out = _run(
        "python -m pytest --cov=analyzer --cov=tantra "
        "--cov-report=term-missing --cov-fail-under=90 -q"
    )
    if ok:
        for line in out.splitlines():
            if "TOTAL" in line:
                _ok(line.strip())
                return True
    _fail("coverage below 90%")
    return False


def check_lint() -> bool:
    print("\n[3] Lint")
    ok, out = _run("ruff check analyzer tantra tests api.py metrics.py")
    if ok:
        _ok("ruff: no violations")
        return True
    _fail("ruff violations found")
    print(out)
    return False


def check_typecheck() -> bool:
    print("\n[4] Type check")
    ok, out = _run("mypy analyzer")
    if ok:
        _ok("mypy: no issues")
        return True
    _fail("mypy issues found")
    print(out)
    return False


def check_files() -> bool:
    print("\n[5] Required files")
    required = [
        "api.py", "metrics.py", "conftest.py", "pyproject.toml", "Makefile",
        "Dockerfile", "docker-compose.yml", "k8s-deployment.yaml", "keshav.service",
        ".dockerignore", ".env.example",
        "prometheus-alerts.yaml", "grafana-dashboard.json",
        "sample_input.json",
        "README.md", "DEPLOYMENT.md", "RUNBOOK.md",
        "analyzer/analyze_blockage.py",
        "tantra/pipeline.py",
    ]
    all_ok = True
    for f in required:
        if Path(f).exists():
            _ok(f)
        else:
            _fail(f"{f} -- MISSING")
            all_ok = False
    return all_ok


def check_api() -> bool:
    """In-process API test using Flask test client. No subprocess, no ports, no hanging."""
    print("\n[6] API smoke test")

    # clear any cached modules so metrics state is fresh
    for mod in list(sys.modules):
        if mod in ("api", "metrics"):
            del sys.modules[mod]

    import api as _api
    from fastapi.testclient import TestClient
    client = TestClient(_api.app)
    all_ok = True

    # health
    r = client.get("/health")
    if r.status_code == 200 and r.json().get("status") == "OK":
        _ok("GET /health -> 200 OK")
    else:
        _fail(f"GET /health -> {r.status_code} {r.content}")
        all_ok = False

    # valid analyze
    payload = json.loads(Path("sample_input.json").read_text())
    r = client.post("/analyze", json=payload)
    data = r.json()
    if r.status_code == 200 and "root_cause" in data and "severity" in data:
        _ok(f"POST /analyze -> 200, root_cause={data['root_cause']}, severity={data['severity']}")
    else:
        _fail(f"POST /analyze -> {r.status_code} {data}")
        all_ok = False

    # malformed input -> 400
    r = client.post("/analyze", json={"execution_id": "x"})
    if r.status_code == 400:
        _ok("POST /analyze (bad input) -> 400 fail-closed")
    else:
        _fail(f"POST /analyze (bad input) -> unexpected {r.status_code}")
        all_ok = False

    return all_ok


def main() -> int:
    print("=" * 50)
    print("KESHAV -- Production Validation")
    print("=" * 50)

    results = {
        "Tests":     check_tests(),
        "Coverage":  check_coverage(),
        "Lint":      check_lint(),
        "Typecheck": check_typecheck(),
        "Files":     check_files(),
        "API":       check_api(),
    }

    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    all_ok = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_ok = False

    print()
    if all_ok:
        print("KESHAV IS PRODUCTION READY")
        return 0
    print("KESHAV IS NOT PRODUCTION READY -- fix failures above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
