# PRANA Cross-System Replay Results

## 1. Execution Summary
We successfully replayed identical event histories across the PRANA Ledger, Gurukul Task Engine, and the Workflow Tracking System to measure output equivalence, truth classification consistency, and ordering.

## 2. Verification Analysis

### A. Output Equivalence
**Failed.** 
While the semantic meaning of the outputs was similar, exact structural outputs diverged due to temporal mutations. Systems appended fresh execution timestamps rather than preserving historical ones, resulting in varying hashes. 

### B. Truth Classification Consistency
**Passed (Partially).**
Karma correctly identified the logic states with the same classifications, confirming that the business rules remained stable. 

### C. Ledger State Alignment
**Failed.**
Because payload IDs (`packet_id`) were generated dynamically on ingestion (via `uuid4`) instead of being deterministic derivatives of the payload, the ledger generated completely new cryptographic chain hashes. Replays essentially forged new divergent timelines rather than validating old ones.

### D. Event Ordering Preservation
**Failed.**
Asynchronous workers in Gurukul picked up the mass-replayed events and processed them out of order due to differing availability, causing state transitions to flip improperly (e.g., submitting before starting) when executed concurrently.

## 3. Recorded Mismatches
- **Output Drift**: Present across all systems due to timestamp and dynamic ID generation.
- **Timing Divergence**: Asynchronous queues corrupted logical execution order.
- **Hidden State Mutation**: Local caches retained old historical states, polluting the replay run logic dynamically.
