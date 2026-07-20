# PRANA Ingestion Gap Specification

As an Integrity Sentinel, PRANA autonomously monitors the sequence continuity and chronological sanity of all ingested events without disrupting or throttling upstreams.

## Detection Mechanism
PRANA tracks event streams intrinsically by their `source_component`. For each component, PRANA maintains a read-only projection tracking the highest `observed_sequence`.

- **Sequence Continuity Violations**: Identified deterministically when the `expected_sequence` (the anticipated next chronological event sequence from the origin) does not mathematically align with the sequence ID found in the newly arrived payload.
- **Timestamp Monotonicity Violations**: Identified when `event_n.origin_timestamp < event_{n-1}.origin_timestamp` within a continuous sequence context, indicating backward clock travel from the emitter.
- **Missing Events**: Detected implicitly when the payload sequence explicitly satisfies `observed_sequence > expected_sequence`, marking a definitive continuity gap.

## Missing Event Evaluation (Deterministic Formula)
1. Let `next_expected = state.last_observed_sequence + 1`
2. Let `current = incoming_event.sequence_id`
3. `gap_detected = (current > next_expected)`
If `gap_detected` is TRUE, the exact magnitude of missing events `current - next_expected` is logged.

## Database Schema Update & Migration Structure

All PRANA signals must be persisted reliably in a pure append-only architecture. No DELETE or UPDATE privileges will be granted to any application user.

```sql
-- Migration Structure: vX.XX__create_integrity_vitality_log.sql

CREATE TABLE integrity_vitality_log (
    vitality_id BIGSERIAL PRIMARY KEY,
    source_component VARCHAR(255) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    freshness_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    expected_sequence BIGINT NOT NULL,
    observed_sequence BIGINT NOT NULL,
    gap_detected BOOLEAN NOT NULL,
    gap_magnitude BIGINT DEFAULT 0,
    monotonicity_violation BOOLEAN NOT NULL,
    
    -- Telemetry Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ensure Strict Append-Only Guarantee
CREATE OR REPLACE FUNCTION prevent_vitality_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'PRANA Integrity Violation: Mutation prohibited on append-only table integrity_vitality_log.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER block_vitality_log_updates
BEFORE UPDATE OR DELETE ON integrity_vitality_log
FOR EACH ROW EXECUTE FUNCTION prevent_vitality_log_mutation();
```
