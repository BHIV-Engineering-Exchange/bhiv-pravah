"""JSON + console reporting for Control Center E2E."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TestRecord:
    name: str
    passed: bool
    duration_ms: float
    status: str = "pass"  # pass | fail | skip
    detail: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class E2EReport:
    suite: str = "control_center_e2e"
    started_at: str = ""
    finished_at: str = ""
    duration_ms: float = 0.0
    gateway_url: str = ""
    tests: List[TestRecord] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    compare_result: Optional[Dict[str, Any]] = None
    pipeline: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    @property
    def passed_count(self) -> int:
        return sum(1 for t in self.tests if t.status == "pass")

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tests if t.status == "fail")

    @property
    def skipped_count(self) -> int:
        return sum(1 for t in self.tests if t.status == "skip")

    def finalize(self) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.summary = {
            "total": len(self.tests),
            "passed": self.passed_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count,
        }


class E2EReporter:
    def __init__(self, *, gateway_url: str = "") -> None:
        self._suite_start = time.perf_counter()
        self.report = E2EReport(gateway_url=gateway_url)

    def record(
        self,
        name: str,
        *,
        passed: bool,
        duration_ms: float,
        detail: str = "",
        skipped: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        status = "skip" if skipped else ("pass" if passed else "fail")
        self.report.tests.append(
            TestRecord(
                name=name,
                passed=passed if not skipped else True,
                duration_ms=round(duration_ms, 2),
                status=status,
                detail=detail,
                metadata=metadata or {},
            )
        )

    def time_block(self, name: str):
        return _TimedBlock(self, name)

    def write_json(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.report.duration_ms = round((time.perf_counter() - self._suite_start) * 1000, 2)
        self.report.finalize()
        payload = asdict(self.report)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        return path

    def print_console_summary(self) -> None:
        self.report.duration_ms = round((time.perf_counter() - self._suite_start) * 1000, 2)
        self.report.finalize()
        print("\n" + "=" * 72)
        print("CONTROL CENTER E2E — SUMMARY")
        print("=" * 72)
        print(f"Gateway: {self.report.gateway_url}")
        print(f"Duration: {self.report.duration_ms:.0f} ms")
        for rec in self.report.tests:
            icon = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[rec.status]
            print(f"  [{icon}] {rec.name} ({rec.duration_ms:.0f} ms) — {rec.detail}")
        print("-" * 72)
        print(
            f"Total: {self.report.summary['total']} | "
            f"Passed: {self.report.summary['passed']} | "
            f"Failed: {self.report.summary['failed']} | "
            f"Skipped: {self.report.summary['skipped']}"
        )
        print("=" * 72)


class _TimedBlock:
    def __init__(self, reporter: E2EReporter, name: str) -> None:
        self.reporter = reporter
        self.name = name
        self._start = 0.0
        self.passed = False
        self.skipped = False
        self.detail = ""
        self.metadata: Dict[str, Any] = {}

    def __enter__(self) -> "_TimedBlock":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        duration_ms = (time.perf_counter() - self._start) * 1000
        if exc_type is not None and not self.skipped:
            self.passed = False
            self.detail = self.detail or str(exc)
        self.reporter.record(
            self.name,
            passed=self.passed,
            duration_ms=duration_ms,
            detail=self.detail,
            skipped=self.skipped,
            metadata=self.metadata,
        )
