# PRANA Anomaly Detection Specification

PRANA anomaly detection operates purely through deterministic telemetry classification rules. **PRANA CANNOT enforce actions, alter state, or block processes in response to identified anomalies.** All findings are emitted strictly as passive signals.

## Anomaly Spike Definitions

- **Sudden Submission Burst**: The velocity of incoming events (`N` events per `T` window) from a specific `source_component` exceeds pre-calculated deterministic configuration thresholds `N_max`.
- **Repeated Verification Failure**: A target component emits `M` explicit failure events or schema-violating signals within fixed window `T`.
- **Abnormal Replay Frequency**: Detection of previously verified `event_id` or `sequence_ids` being ingested repeatedly over `R` times per `T` window, potentially indicating an upstream retry storm.

## Truth Levels (Severity Classification)

All anomalies are immediately tagged with a mandatory Truth Level indicating severity:
- **Level 0 (Verifiable & Normal)**: Routine operational anomaly (e.g., standard network jitter within bounds).
- **Level 1 (Noticeable Deviation)**: Uncharacteristic latency or minor sequence mismatch.
- **Level 2 (Warning Behavior)**: Unexpected retries or moderate submission burst requiring dashboard visibility.
- **Level 3 (Major Abnormality)**: Significant, continuous sequence gaps or severe ingestion bursts from unauthenticated vectors.
- **Level 4 (Systemic Instability)**: Massive degradation. Widespread sequence collapse or critical continuous verification unreachability.

## Persistence Layer: anomaly_event

Anomalies are stored securely alongside standard telemetry in a non-mutable table structure.

```sql
-- Migration Structure: vX.XX__create_anomaly_event_table.sql

CREATE TABLE anomaly_event (
    anomaly_id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(255),                      -- Target event or context reference
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    spike_classification VARCHAR(255) NOT NULL, -- e.g., 'SUDDEN_BURST', 'REPEATED_FAILURE', 'REPLAY_STORM'
    severity_level INT NOT NULL CHECK (severity_level BETWEEN 0 AND 4),
    related_sequence BIGINT,
    source_component VARCHAR(255) NOT NULL
);

-- Ensure Strict Append-Only Guarantee
CREATE TRIGGER block_anomaly_event_updates
BEFORE UPDATE OR DELETE ON anomaly_event
FOR EACH ROW EXECUTE FUNCTION prevent_vitality_log_mutation(); -- Function provided by PRANA_INGESTION_GAP_SPEC.md
```
