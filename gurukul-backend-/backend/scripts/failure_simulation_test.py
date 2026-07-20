"""
failure_simulation_test.py — Gurukul Orchestration Layer Validation
====================================================================

Simulates service failures and validates that the RuntimeMonitor correctly
detects them and that the ServiceWatchdog recovers automatically.

Mocking strategy: stub pydantic_settings + the config module to avoid
pydantic v1/v2 import conflicts, while keeping the real `app` package.

Run:
    cd Gurukul/backend
    python scripts/failure_simulation_test.py
"""

import sys
import os
import time
import unittest
from unittest.mock import MagicMock, patch

# ------ Ensure backend package on path ------------------------------------
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ------ Stub pydantic_settings before any app import ----------------------
fake_settings = MagicMock()
fake_settings.VAANI_API_URL = "http://localhost:8008"
fake_settings.DATABASE_URL  = None
fake_settings.REDIS_URL     = "redis://localhost:6379/0"

# Patch pydantic_settings itself so BaseSettings can be 'imported'
_fake_pydantic_settings_mod = MagicMock()
_fake_pydantic_settings_mod.BaseSettings = MagicMock
sys.modules.setdefault("pydantic_settings", _fake_pydantic_settings_mod)

# Patch the config module to return our fake settings
_fake_config_mod = MagicMock()
_fake_config_mod.settings = fake_settings
sys.modules["app.core.config"] = _fake_config_mod

# Patch other heavy dependencies that might fail in the test env
sys.modules.setdefault("app.services.voice_provider", MagicMock())
sys.modules.setdefault("app.core.database",            MagicMock())
sys.modules.setdefault("app.core.karma_database",      MagicMock())

# ------ Now safe to import our new services --------------------------------
from app.services.runtime_monitor import (          # noqa: E402
    _check_vaani, _check_prana, _check_database, _check_redis,
    RuntimeMonitor, ServiceSignal,
)
from app.services.service_watchdog import ServiceWatchdog   # noqa: E402
import app.services.system_metrics as sm                    # noqa: E402


# ===========================================================================
# Test classes
# ===========================================================================

class TestRuntimeMonitor(unittest.TestCase):
    """Unit tests for individual health-check functions."""

    def test_vaani_unreachable_returns_down(self):
        import requests
        with patch("requests.get",
                   side_effect=requests.exceptions.ConnectionError("refused")):
            sig = _check_vaani()
        self.assertEqual(sig.status, "down",
                         f"Expected 'down', got '{sig.status}'")
        self.assertGreaterEqual(sig.latency_ms, 0)

    def test_prana_no_sentinel_down_or_degraded(self):
        with patch("os.path.exists", return_value=False), \
             patch("subprocess.run",
                   return_value=MagicMock(returncode=1, stdout="")):
            sig = _check_prana()
        self.assertIn(sig.status, ("down", "degraded"))

    def test_database_no_url_degraded(self):
        fake_settings.DATABASE_URL = None
        sig = _check_database()
        self.assertIn(sig.status, ("degraded", "down"))

    def test_redis_import_error_degraded(self):
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "redis":
                raise ImportError("No module named 'redis'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            sig = _check_redis()
        self.assertEqual(sig.status, "degraded")

    def test_check_all_returns_five_signals(self):
        monitor = RuntimeMonitor()
        import requests
        with patch("requests.get",
                   side_effect=requests.exceptions.ConnectionError("refused")):
            signals = monitor.check_all()
        self.assertEqual(len(signals), 5)
        for s in signals:
            self.assertIn(s.status, ("healthy", "degraded", "down"))

    def test_overall_status_all_healthy(self):
        monitor = RuntimeMonitor()
        fake = [
            ServiceSignal("A", "healthy", 10.0, "ok"),
            ServiceSignal("B", "healthy",  5.0, "ok"),
        ]
        self.assertEqual(monitor.overall_status(fake), "healthy")

    def test_overall_status_with_down_is_degraded(self):
        monitor = RuntimeMonitor()
        fake = [
            ServiceSignal("A", "healthy", 10.0, "ok"),
            ServiceSignal("B", "down",    -1.0, "refused"),
        ]
        self.assertEqual(monitor.overall_status(fake), "degraded")


class TestServiceWatchdog(unittest.TestCase):
    """Thread lifecycle and status structure tests."""

    def test_starts_and_stops_thread(self):
        import requests
        # Prevent any real HTTP/recovery calls from blocking the thread during stop()
        with patch("requests.get",
                   side_effect=requests.exceptions.ConnectionError("mocked")):
            wd = ServiceWatchdog(poll_interval=999)
            wd.start()
            time.sleep(0.3)
            self.assertTrue(wd._thread.is_alive(), "Thread should be alive after start()")
            wd.stop()
        # Give the thread up to 12 s to finish any in-flight recovery
        wd._thread.join(timeout=12)
        self.assertFalse(wd._thread.is_alive(), "Thread should be dead after stop()")

    def test_not_running_before_start(self):
        wd = ServiceWatchdog(poll_interval=999)
        self.assertFalse(wd.get_status()["watchdog_running"])

    def test_get_status_required_keys(self):
        wd = ServiceWatchdog(poll_interval=999)
        status = wd.get_status()
        for key in ("watchdog_running", "poll_interval_s",
                    "cycle_count", "uptime_s", "services"):
            self.assertIn(key, status)

    def test_reset_counters_clears_state(self):
        wd = ServiceWatchdog(poll_interval=999)
        wd._recovery_attempts["VaaniTTS"] = 5
        wd.reset_recovery_counters()
        self.assertEqual(wd._recovery_attempts, {})


class TestSystemMetrics(unittest.TestCase):
    """Metrics recording and helper function tests."""

    def setUp(self):
        sm._voice_latencies.clear()
        sm._ai_latencies.clear()
        sm._total_requests = 0
        sm._error_count    = 0
        sm._status_counts.clear()
        sm._route_counts.clear()

    def test_record_voice_latency(self):
        sm.record_voice_latency(150.0)
        self.assertEqual(len(sm._voice_latencies), 1)

    def test_record_ai_latency_multiple(self):
        sm.record_ai_latency(300.0)
        sm.record_ai_latency(200.0)
        self.assertEqual(len(sm._ai_latencies), 2)

    def test_avg_empty_returns_zero(self):
        from collections import deque
        self.assertEqual(sm._avg(deque()), 0.0)

    def test_avg_three_values(self):
        from collections import deque
        self.assertAlmostEqual(sm._avg(deque([100.0, 200.0, 300.0])), 200.0)

    def test_p95_returns_high_percentile(self):
        from collections import deque
        vals = deque(range(1, 101))   # 1 .. 100
        self.assertGreaterEqual(sm._p95(vals), 95)

    def test_format_uptime_full(self):
        result = sm._format_uptime(3661)  # 1h 1m 1s
        self.assertIn("1h", result)
        self.assertIn("1m", result)
        self.assertIn("1s", result)

    def test_format_uptime_seconds_only(self):
        result = sm._format_uptime(45)
        self.assertIn("45s", result)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Gurukul Orchestration Layer - Failure Simulation Tests")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRuntimeMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceWatchdog))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemMetrics))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{result.testsRun} passed")
    if result.failures or result.errors:
        print("  FAILURES PRESENT - see above for details")
    else:
        print("  ALL PASSED")
    print("=" * 60)
    print()

    sys.exit(0 if result.wasSuccessful() else 1)
