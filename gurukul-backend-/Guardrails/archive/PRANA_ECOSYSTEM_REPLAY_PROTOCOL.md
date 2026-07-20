# PRANA Ecosystem Replay Protocol

## 1. Overview
This document outlines the deterministic replay validation protocol across at least three select BHIV systems, effectively testing how well PRANA can observe and validate historical inputs.

## 2. Selected Systems
1. **PRANA Ledger**: Serves as the immutable truth base for replay logs.
2. **Gurukul Backend Task Flow**: Represents the core operational workflow where task state transitions occur.
3. **Workflow / Employee Monitoring**: The dependent system relying on state transitions and timing events.

## 3. Replay Inputs
- **Historical Task Submission Events**: Re-injecting old `ON_TASK` and `SUBMITTED` events.
- **Review Outputs**: Feeding canonical grading and review decisions.
- **Next-Task Generation Events**: Emulating the spawning of subsequent logical steps.

## 4. Replay Protocol & Rules
- **Event Ordering**: Events must be sequentially dispatched exactly as timestamped in the ledger.
- **Input Reproduction**: Replay events strictly mirror original payloads, injecting a `is_replay=true` boundary flag if structurally necessary by observation modules.
- **Output Comparison**: Strict hashing comparison is enacted on final output states, omitting explicitly whitelisted volatile fields (e.g., current machine time).
- **No Authority**: PRANA must not step in to alter states or patch discrepancies; it only logs discrepancies.
