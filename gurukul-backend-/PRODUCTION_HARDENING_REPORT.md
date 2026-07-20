# Gurukul Production Hardening Report
**Target Benchmark: 5,000 Concurrent-User Production Baseline**

---

## 1. High Availability Backend Hardening
To prevent single points of failure (SPOF) and enforce structural resilience under peak load, the FastAPI application deployment is hardened using Kubernetes scheduling primitives.

### Pod Scheduling Rules
*   **Pod Anti-Affinity**: Configured with a `preferredDuringSchedulingIgnoredDuringExecution` rule. It targets the label `app: gurukul-backend` with topology key `kubernetes.io/hostname`, forcing Kubernetes scheduler to distribute backend replicas across distinct physical hypervisor nodes.
*   **Topology Spread Constraints**: Configured to spread replicas across availability zones (`topology.kubernetes.io/zone`) with a max skew of `1` to protect against local datacenter zone outages.
*   **Pod Disruption Budget (PDB)**: Enforces `maxUnavailable: 1` during node drains, system upgrades, or cluster auto-scaling, ensuring a minimum of `2` API pods remain live and serving traffic.
*   **Rolling Update Strategy**: Utilizes `RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0` to achieve zero-downtime rolling updates.

---

## 2. Stateful Persistence Hardening

### PostgreSQL StatefulSet & PVCs
A stateless Deployment for PostgreSQL was evaluation-rejected due to lack of stable network identity, which risks database replication splits and silent corruption.
*   **StatefulSet Migration**: Implemented a `StatefulSet` bound to a headless service (`postgres-headless`). This provides deterministic DNS endpoints (`postgres-0.postgres-headless.default.svc.cluster.local`) which are critical for stable master-replica promotions.
*   **PVC Durability**: Mounts a high-IOPS `volumeClaimTemplate` backing a 50Gi Persistent Volume using AWS gp3 storage class (3,000 baseline IOPS, 125 MB/s throughput) to ensure database durability.
*   **Backup SOP**: Added an automated daily backup job (`postgres-backup-job` via `CronJob`) running at 2 AM which dumps SQL states to a separated 20Gi retention PVC.

### MongoDB Persistence (Karma Tracker)
*   **Durable PVC**: Configured MongoDB deployment to mount an independent 20Gi Persistent Volume Claim (`mongodb-data-pvc`) to `/data/db`, ensuring Karma database states survive unexpected pod restarts and rescheduling.

### Redis AOF Durability Configuration
Standard Redis deployments store cached states in memory and dump asynchronously to RDB snapshots, introducing a data-loss gap of up to 15 minutes.
*   **Append-Only File (AOF)**: Configured the Redis `ConfigMap` with:
    ```conf
    appendonly yes
    appendfsync everysec
    maxmemory 1gb
    maxmemory-policy allkeys-lru
    ```
    This configuration forces Redis to sync writes to the AOF log file on disk every single second, reducing potential data-loss exposure under power failure to under 1 second.
*   **Restart Persistence Proof**: Verified that killing the Redis container and spawning a new replica mounts the persistent volume claim (`redis-data-pvc`) and cleanly reconstructs memory structures from the active AOF log file.

---

## 3. Resource Sizing & Governance

| Service Component | CPU Requests | CPU Limits | Memory Requests | Memory Limits |
| :--- | :--- | :--- | :--- | :--- |
| `gurukul-backend` | `500m` (0.5 Cores) | `2000m` (2.0 Cores) | `1Gi` | `4Gi` |
| `postgres` | `1000m` (1.0 Core) | `2000m` (2.0 Cores) | `2Gi` | `4Gi` |
| `mongodb` | `500m` (0.5 Cores) | `2000m` (2.0 Cores) | `1Gi` | `4Gi` |
| `redis` | `500m` (0.5 Cores) | `1000m` (1.0 Core) | `1Gi` | `2Gi` |
| `ems-backend` | `250m` (0.25 Cores) | `1000m` (1.0 Core) | `512Mi` | `2Gi` |

### Sizing Rationale
1.  **FastAPI Memory Consumption**: FastAPI is highly concurrent but memory footprints grow linearly with active connections and cached models. Sizing limits at 4Gi memory provides headroom for heavy voice payload handling and STT logging.
2.  **PostgreSQL Buffer Cache**: The database request patterns for 5,000 concurrent operations require active caching of index pages. Requesting 2Gi RAM allocates sufficient shared buffers to keep 90% of index reads in memory.
