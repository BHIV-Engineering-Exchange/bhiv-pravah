# Safety Rules - Deterministic Adaptive System

## A. Core Safety Principles

### Single-State Rule
Only one adaptive state can be active at any time. This eliminates all state collision possibilities identified in Day 1 analysis.

### Lock Precedence
States are processed in strict chronological order. New requests are blocked if any state is currently active.

### Cooldown Rationale  
Each state type has mandatory cooldown periods to prevent rapid state thrashing:
- Avatar interactions: 300-500ms
- Navigation: 200ms  
- Notifications: 1000ms
- Timers: 100ms
- Loading states: 500ms

### Determinism Guarantees
The system behaves predictably under all conditions:
- 100 rapid signals → exactly 1 state executes
- System crashes → hard reset to neutral state
- Unknown states → safely ignored
- Cleanup failures → automatic recovery

## B. State Transition Rules

### Allowed Transitions
- Neutral → Any State
- Any State → Neutral (via cleanup)
- State A → State B (forced cleanup of A first)

### Blocked Transitions
- State → Same State (re-entry prevention)
- State A → State B (while A is active)
- Any State → New State (during cooldown period)

### Re-entry Behavior
All re-entry attempts are silently blocked. No error messages, no alternative behaviors.

### Cooldown Enforcement
States cannot re-activate until their cooldown period expires, regardless of signal frequency.

## C. Signal Flood Handling

### Absorption Strategy
The system uses a "drop everything" approach:
- First signal: Process normally
- Subsequent signals: Increment drop counter, return false
- No queuing, no batching, no delayed processing

### Why Chaos Cannot Occur
1. **Central Lock**: Only one state mutex exists
2. **Immediate Blocking**: Conflicting signals return false immediately  
3. **Cooldown Walls**: Even after state exit, cooldown prevents immediate re-entry
4. **Forced Cleanup**: Every state transition includes complete cleanup
5. **Hard Reset Fallback**: Any failure triggers system recovery

## D. Cleanup Guarantees

### What Is Always Cleaned
- All registered timers and timeouts
- All event listeners and handlers
- All observers (Intersection, Mutation, Resize)
- All CSS classes and inline styles
- All intervals and recurring timers

### When Cleanup Occurs
- State exit (normal path)
- State replacement (forced path)
- System error (hard reset path)
- Component unmount (automatic path)

### Fallback Behavior
If any cleanup step fails:
1. System performs hard reset
2. All registered items are forcefully cleared
3. State registry is emptied
4. System returns to neutral state
5. Drop counter resets

## E. Safety Validation

### Exit Check Confirmation
✅ Two states can NEVER overlap - central mutex enforces exclusivity
✅ Cooldowns are enforced - time-based blocking prevents rapid cycling  
✅ Cleanup is guaranteed - registry ensures complete resource release
✅ Re-entry is blocked - same-state requests return false immediately
✅ No new behavior introduced - only existing states governed
✅ Existing UI flows preserved - same interfaces, deterministic execution

### Failure Protection
- Unknown states are ignored (silence > reaction)
- Cleanup failures trigger hard reset (determinism > partial recovery)
- Signal floods are absorbed (ignore > queue)
- Timing ambiguities default to NO-OP (caution > assumption)

### Performance Characteristics
- Zero overhead when no conflicts occur
- O(1) blocking for conflicting signals
- Automatic resource cleanup prevents memory leaks
- Deterministic timing eliminates race conditions