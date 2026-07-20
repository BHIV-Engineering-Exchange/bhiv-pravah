### 📹 Staging Verification Screen Recordings (Google Drive)

Below are the direct Google Drive links to the screen recordings capturing the EKS staging verification sequences for all core scenarios:

| Failure Scenario | Target Behavior Demonstrated | Google Drive Screen Recording Link |
| :--- | :--- | :--- |
| **Scenario 1: Database Failure Lifecycle** | DB scaled to 0 -> Metric drops to 0.0 -> Watchdog logs recovery start -> DB scaled to 1 -> Metric resolves to 1.0. | [Database Failure Recording](https://drive.google.com/file/d/1jI4YJ-UO4-Er2UqnxfsiiWi5EoszAfoo/view?usp=sharing) |
| **Scenario 2: Redis Cache Degradation** | Redis scaled to 0 -> Metric drops to 0.0 -> Redis scaled to 1 -> Metric resolves back to 1.0. | [Redis Outage Recording](https://drive.google.com/file/d/1PBczM4EXGVg6g_P0umtMPPIBSSOGIqcG/view?usp=sharing) |
| **Scenario 3: High Latency Operations** | Port-forward active -> Run `test_stability_2.py` -> Verify voice latency spikes reflected in `/metrics` and average averages ~1.38s. | [Latency Stress Recording](https://drive.google.com/file/d/112MWaeYkaFrDOaCyGDoQpac4FDHLbWJJ/view?usp=sharing) |
| **Scenario 4: Watchdog Retry & Escalation** | Postgres offline >120s -> Stream watchdog logs for 3 retry attempts -> Witness critical lockout escalation. | [Watchdog Escalation Recording](https://drive.google.com/file/d/1Mf9okfUom6E3CJnrmPnH-jKvvdvm5EQ-/view?usp=sharing) |
| **Scenario 5: Database Outage Dashboard Alerts** | Demonstrates the EKS PostgreSQL database outage, metrics propagation, active Prometheus alerts, and Grafana connection health status dials turning red. | [Database Dashboard Recording](https://drive.google.com/file/d/13i2y4m2bAaAvXQywMpL41RAdI7ZMv3oi/view?usp=sharing) |
| **Scenario 6: Latency Stress Dashboard Telemetry** | Shows the live stability stress test execution, average/p95 voice latency metric spikes, and the time-series charts updating dynamically inside Grafana and Prometheus. | [Latency Dashboard Recording](https://drive.google.com/file/d/1D6AtQ1Wwwx4FSghF5YPqubMme_rJOFCL/view?usp=sharing) |
