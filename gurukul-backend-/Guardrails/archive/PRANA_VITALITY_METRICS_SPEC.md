# PRANA Vitality Metrics Specification


PRANA deterministically derives vitality metrics from ingested telemetry logs and exposes them as read-only vitality snapshots for monitoring purposes.

## Deterministic Metrics Definition

- `ledger_integrity_status`: A pure boolean derived exclusively by evaluating if `ingestion_gap_count == 0` AND no Level 3/4 `anomaly_event` records exist over the current time window.
- `last_successful_verification`: The highest `freshness_timestamp` of the most recently ingested event that was processed natively without triggering an anomaly.
- `freshness_score`: A fully deterministic evaluation. Formula: `Score = MAX(0, 100 - (Median_Latency_MS / LATENCY_DENOMINATOR_CONSTANT))`.
- `ingestion_gap_count`: Precise integer sum of all `gap_detected = true` events recorded inside `integrity_vitality_log` for the current evaluation window.
- `anomaly_spike_count`: Precise integer count of events inside `anomaly_event` over the current evaluation window.

## Boot-Time Verification Routine

At system bootstrap, PRANA executes a zero-mutation initialization routine:
1. Reconstructs current sequence states (`expected_sequence`) by reading backward from the `integrity_vitality_log` up to the last known localized checkpoint.
2. Recalculates the `freshness_score` and gap counters deterministically into in-memory observables.
3. This process ensures PRANA inherently trusts only its own verifiable disk layout, discarding any external volatile state.

## Periodic Vitality Emission

PRANA operates an isolated asynchronous loop that compiles the above deterministic telemetry metrics. The resulting vitality snapshot is persisted in the `vitality_snapshot` table for monitoring and replay purposes. This emission process remains strictly non-blocking and does not interfere with primary event ingestion.

```sql
CREATE TABLE vitality_snapshot (
    snapshot_id BIGSERIAL PRIMARY KEY,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ledger_integrity_status BOOLEAN NOT NULL,
    last_successful_verification TIMESTAMP WITH TIME ZONE,
    freshness_score DECIMAL(5, 2) NOT NULL,
    ingestion_gap_count BIGINT NOT NULL,
    anomaly_spike_count BIGINT NOT NULL
);
```
