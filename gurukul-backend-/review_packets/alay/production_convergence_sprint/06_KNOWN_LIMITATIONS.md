# Known Limitations & Exclusions

This document registers the limitations and environmental conditions observed during this sprint.

## 1. Supabase Infrastructure Suspensions
* **Issue:** External API requests to Supabase (e.g., in `test_end_to_end_flow`) return `503 Service Suspended`.
* **Cause:** The shared test project under `fndlupkdnwvkhddirgpg.supabase.co` is currently paused or expired on the hosting provider.
* **Scope Exclusion:** End-to-end user login checks utilizing remote Supabase authentication are bypassed in current local test verification cycles. Local developer testing relies on mock sessions or direct database overrides.

## 2. In-Memory Database Tests
* **Issue:** The unit test suite (`test_convergence_convergence.py`) requires a SQL database to verify logic but should not write persistent records during test runs.
* **Solution:** Tests instantiate a temporary, in-memory SQLite database (`sqlite:///:memory:`) using standard SQLAlchemy setup.
* **Harden Safe-Path:** The import of `Base` from `app.core.database` requires `DATABASE_URL` to be present in the environment (enforcing the PostgreSQL scheme check). To bypass this, we provide a dummy `postgresql://` string in the terminal's environment variables. This prevents runtime initialization errors during tests without connecting to an actual remote host.

## 3. Network Failure Retries
* **Behavior:** The retry loop is verified synchronously during simulated outages. Under extremely high request concurrency, synchronous backoffs (1.0s, 2.0s, 3.0s) can block event loops. Future releases should switch the Pravah Adapter to asynchronous background queues for telemetry reporting.
