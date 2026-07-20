# PRANA State Transition Rules

## Purpose

Deterministic FSM rules for PRANA state transitions. Signal-driven, time-bounded. No inference, prediction, or adaptation.

## States

IDLE, ACTIVE, READING, TYPING, NAVIGATING, SEARCHING, VIEWING

## Transition Rules

### Rule 1: Window-Based
- Transitions occur at 2-second window boundaries only
- State constant within window
- No intermediate changes

### Rule 2: Signal-Driven
- Transitions depend on current window signals only
- No state history influence
- No signal prediction

### Rule 3: State Priority (Ambiguity Resolution)
1. NAVIGATING (highest)
2. SEARCHING
3. TYPING
4. READING
5. VIEWING
6. ACTIVE
7. IDLE (lowest)

### Rule 4: Allowed Transitions
**All states may transition to any other state.** No restrictions.

### Rule 5: Minimum Thresholds
If thresholds not met → Emit IDLE

### Rule 6: Ambiguity Handling
Ambiguous or insufficient signals → Emit IDLE

## Determinism Guarantees

1. **Same Inputs → Same Outputs:** No randomness, adaptation, or learning
2. **No State History:** Current window signals only
3. **Fixed Rules:** Rules never change
4. **Signal-Only Dependencies:** No external factors

## Time Windows

- **Duration:** Fixed 2 seconds
- **Boundaries:** Non-overlapping, t = n × 2 seconds
- **Evaluation:** At window end
- **Collection:** Continuous, assigned by timestamp

## Failure Handling

- **Signal Collection Failure:** Emit IDLE, continue
- **State Evaluation Failure:** Emit IDLE, continue
- **Transition Logic Failure:** Emit IDLE, continue

## Contract Compliance

- Observational only
- Non-invasive
- Ephemeral
- Failure-tolerant
