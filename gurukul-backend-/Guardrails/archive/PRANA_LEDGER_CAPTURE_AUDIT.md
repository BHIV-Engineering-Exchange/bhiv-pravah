# PRANA Ledger Capture Audit

**Database Technology**: PostgreSQL (SQL)  
**Schema Implementation**: `EMS System/app/models.py`  
**Capture Endpoint**: `/bucket/prana/ingest`

## Ledger Schema Analysis
The system captures packets into the `prana_packets` table with the following structure:

| Field Name        | Type        | Constraint | Purpose                              |
|-------------------|-------------|------------|--------------------------------------|
| `packet_id`       | String(64)  | Unique, Not Null | Unique trace ID for the window |
| `employee_id`     | String(255) | Not Null | Unified user identifier                |
| `state`           | String(32)  | Not Null | Observed cognitive state               |
| `integrity_score` | Float       | Not Null | Focus metric (0.0 - 1.0)               |
| `active_seconds`  | Float       | Not Null | Active time in window                  |
| `idle_seconds`    | Float       | Not Null | Idle time in window                    |
| `away_seconds`    | Float       | Not Null | Away time in window                    |
| `raw_signals`     | JSON        | Not Null | Immutable bridge of truth signals      |
| `client_timestamp`| DateTime    | Not Null | Emission time                          |
| `received_at`     | DateTime    | Default: NOW | Ingestion time                     |

## Integrity Verification

### Append-Only Behavior
- **Confirmed**: `bucket.py` only contains `db.add(record)` and `db.commit()`. No update or delete operations exist in the PRANA ingestion path.
- **Divergence**: The system uses PostgreSQL instead of the "Canon" MongoDB suggestion, providing stronger ACID guarantees for the ledger.

### Data Types & Consistency
- **Time Accounting**: Validated at ingestion. Sum of `active + idle + away` must equal 5.0 (±0.1 tolerance).
- **Ordering**: Captured by both `client_timestamp` and `received_at`.
- **Duplication**: `packet_id` uniqueness ensures no storage-level duplication, though the bridge can resend if acknowledgement fails (at-least-once).

## Unexpected Observations
- **employee_id**: The system maps `user_id` to `employee_id` for backward compatibility, even for Gurukul students.
- **Focus vs Integrity**: The 0-100 `focus_score` from the frontend is converted to a 0-1.0 `integrity_score` during ingestion.
