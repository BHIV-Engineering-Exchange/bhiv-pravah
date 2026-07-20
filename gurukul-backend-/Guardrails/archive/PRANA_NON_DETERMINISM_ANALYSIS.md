# PRANA Non-Determinism Analysis

## 1. Executive Summary
The replay mismatches recorded during validation indicate profound non-determinism across the BHIV systems when disconnected from their initial live-execution context. 

## 2. Root Cause Analysis

### A. Hidden State Dependency
The systems execute based on contextual, non-event-sourced data. Gurukul logic relies on active session structures and cached configurations. When pure historical payloads are replayed, the transient cache state is missing, altering how the system responds.

### B. Time-Based Randomness
Code logic relies heavily on active-generation boundaries. For instance, generating `packet_id` with `uuid4()` and stamping statuses with `datetime.now()` means no two executions of the identical payload will ever produce identical output arrays.

### C. Untracked Configuration Inputs
The system replays historical events against the *current* software configuration. Dynamic thresholds, rule limits, or minor dependency updates occurring between the original live event and the replay silently mutate the outcome.

### D. Cross-System Coupling
PRANA ingestion triggered synchronous operations in external systems. Replays effectively bombarded the message queues, leading to asynchronous race conditions. Event order was corrupted by parallel workers, destroying the ledger sequence.
