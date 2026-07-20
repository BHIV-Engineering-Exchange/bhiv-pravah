# PRANA Freshness Model

**PRANA** operates strictly as an Integrity Sentinel. It possesses **no enforcement power**, **no governance logic**, and **no authority to mutate state**. Its sole purpose is deterministic monitoring and telemetry.

## Event Ingestion Lifecycle
1. **Emission**: An external system or component emits an event payload containing its origin timestamp.
2. **Intake**: PRANA ingests the payload asynchronously, assigning it an immutable `observed_timestamp` upon crossing the network boundary.
3. **Assessment**: PRANA compares the event's internal expected timestamps to the `freshness_timestamp` to verify freshness deterministically without mutating, blocking, or queuing the event flow.
4. **Telemetry Logging**: PRANA appends the freshness assessment result to the append-only `integrity_vitality_log` table.

## Freshness Timestamp Definition
The `freshness_timestamp` is defined as the exact, indisputable clock time at which an event payload crosses the PRANA telemetry ingestion boundary. It is generated securely by PRANA at the moment of intake, completely independent from any origin-claimed timestamps within the event payload itself. This ensures an undeniable reference point for all subsequent calculations.

## Freshness Evaluation Method
Freshness is evaluated continuously based on a deterministic delta between origin timestamps and the `freshness_timestamp`.
- **Delta Calculation**: `Delta = freshness_timestamp - origin_timestamp`
- **Assessment**: If `Delta > MAX_ALLOWED_LATENCY_MS`, the event is deterministically classified as `stale_arrival`. Otherwise, it is `current`.
- This evaluation is purely for monitoring; no event is ever blocked or rejected on account of staleness.

## Formal Definition: Stale Event Stream
A **stale event stream** is formally defined as a contiguous sequence of events, originating from a single component, where either:
1. The observed ingestion gap `Delta(event_n, event_{n-1})` exceeds deterministic configuration bounds over a fixed window `W`.
2. A sequential count `N` of consecutive events mathematically breach the `MAX_ALLOWED_LATENCY_MS` freshness threshold.
When a stream meets this criteria, it does not trigger automated system penalties, but emits a high-severity `anomaly_event` containing the stream classification.
