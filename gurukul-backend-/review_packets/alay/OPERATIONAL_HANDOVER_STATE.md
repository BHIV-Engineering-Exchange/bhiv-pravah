# Deliverable 5: Operational Handover State
**Gurukul DevOps & Infrastructure Handover Registry — Observability Hardening Sign-Off**

---

> [!IMPORTANT]  
> This operational handover state registry details the exact hardening accomplishments, known architectural gaps, cluster risks, and remaining engineering requirements for staging-to-production deployment approval.

---

## 🟢 1. Current Hardening Status

The core runtime observability and autonomous recovery layers have been configured, deployed, and validated under staging test scenarios in the `gurukul-staging` namespace.

### A. Telemetry Metrics Integration
*   **Redis Telemetry Hardened**: Decoupled metrics and watchdog from the redundant `REDIS_URL` environment variables. Refactored the telemetry gateway (`prometheus_exporter.py`), runtime monitor (`runtime_monitor.py`), and watchdog daemon (`service_watchdog.py`) to connect using `REDIS_HOST` and `REDIS_PORT` directly. This unifies connection parameters across all backend codebases.
*   **Heartbeat Visibility**: Implemented the missing `is_alive(self)` method in the `ServiceWatchdog` thread manager, allowing the `/metrics` endpoint to monitor thread vitality dynamically under `gurukul_watchdog_active`.
*   **Voice Generation SLA Telemetry**: Integrated the missing `record_voice_latency` callback inside the voice router (`tts.py`). Voice latency average (`gurukul_voice_latency_seconds_avg`) and p95 outliers (`gurukul_voice_latency_seconds_p95`) are now fully calculated and reported under concurrent load.

### B. Startup & Router Stability
*   **FastAPI Import Safety**: Resolved a silent router import failure in `main.py` by introducing missing FastAPI dependencies (`APIRouter`, `HTTPException`, `Response`) inside `tts.py`. The Sovereign voice endpoints bind cleanly to port `3000` on service startup.
*   **TANTRA Contract Compliance**: Injected required metadata schema properties (`schema_version`, `provenance`, `ownership`, and `replay_metadata`) inside the `bucket_adapter.py` event core payload, eliminating TANTRA contract schema violations during concurrent bursts.

### C. Watchdog Auto-Recovery
*   **Cooldown and Retry Boundaries**: The watchdog safely sweeps and triggers recovery actions for PostgreSQL, Redis, Vaani, and PRANA streams, enforcing a max 3 restart attempts ceiling and 120s cooldowns to prevent infinite restart loops.

---

## 🟡 2. Known Operational Gaps

While the staging environment is fully functional, the following differences exist between our staging setup and full production environments:

*   **Round-Robin Telemetry Scrape (EKS Multi-Replica Multi-Scrape)**: Because the `gurukul-backend` deployment scales to 3 replicas in staging, hitting the shared service endpoint (e.g. `http://gurukul-backend.gurukul-staging.svc:80/metrics`) round-robins metrics requests. Standard Prometheus setups scrape each pod IP individually using endpoint discovery, but manual curl queries targeting the service port-forward will retrieve fluctuating round-robin values. Direct port-forwarding to specific pod names (e.g. `pod/gurukul-backend-xxxx`) is required for single-pod validation logs.
*   **In-Memory Event Queue Buffer Limit**: `BucketAdapter` caches failed memory events in a thread-safe, in-memory queue (`_queue`) with a max size of 100 events. If the remote `BUCKET_URL` endpoint experiences an outage exceeding 50 minutes under sustained load, the buffer will overflow and drop oldest events to prevent memory bloat.
*   **Single-Threaded Watchdog Dispatcher**: The watchdog processes service recoveries sequentially. If a recovery script blocks (e.g. a database query timeout), subsequent checks for other services are delayed.

---

## 🔴 3. Known Operational Risks

*   **Auto-Recovery Lockout (SRE Fatigue Risk)**: Once a service (like PostgreSQL) exceeds 3 recovery attempts, the watchdog escalates and locks out further auto-recovers. The service remains offline until an operator manually deletes the pod or resets the watchdog counter. If Slack/PagerDuty notification loops fail, outages will persist without auto-recovery.
*   **GPU CPU-Fallback SLA Degradation**: On clusters without GPU provisioning, the XTTS voice model falls back gracefully to CPU mode. While functional, CPU generation times increase from ~150ms to ~1.38s. This latency increase triggers warning thresholds in Prometheus and increases thread blockages under concurrent user traffic.
*   **MongoDB Concurrency Lock Collisions**: Q-learning state writes use optimistic locking. Under high concurrent student workloads, state collisions will trigger transaction aborts and retry cycles, driving up latency times.

---

## 🔵 4. Remaining Work & Next Steps

*   **Block B Convergence Alignment**: Draft the Pravah Convergence Discussion with **Shivam Pal** to reconcile duplicated metrics between the Pravah stream and the Prometheus exporter, and outline a unified metrics collection topology.
*   **Alertmanager Notification Verification**: Configure the target PagerDuty service keys and Slack webhook endpoints inside [`k8s/monitoring/alertmanager.yaml`](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Gurukul_Observability/gurukul-backend-/k8s/monitoring/alertmanager.yaml) to complete real-world alert notification checks.
*   **HPA Autoscaler Stress Testing**: Trigger autoscaler scaling checks using the EKS backend HPA settings (`backend_hpa.yml`) to verify backend pod scaling when CPU limits exceed 80%.
*   **Persistent Event Backlog Storage**: Assess the feasibility of migrating the in-memory `BucketAdapter` queue buffer to a lightweight, local SQLite database on a persistent volume to protect failed memory events from being lost if the backend pod is restarted.
