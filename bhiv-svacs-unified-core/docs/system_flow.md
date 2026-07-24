# SYSTEM FLOW

---

# SVACS UNIFIED CORE ARCHITECTURE

```text
SIGNAL 
   ↓
PERCEPTION
   ↓
INTELLIGENCE
   ↓
STATE
   ↓
RAJYA
   ↓
SARATHI
   ↓
CORE
```

---

# PIPELINE OVERVIEW

The SVACS Unified Core system processes execution flows through multiple validation and intelligence stages.

Each stage performs a dedicated responsibility while preserving:

- Trace continuity
- Append-only integrity
- Contract validation
- Replay reconstruction
- Hash verification

---

# STAGE RESPONSIBILITIES

| Stage | Responsibility |
|---|---|
| SIGNAL | Generates incoming signal event |
| PERCEPTION | Detects and interprets signal |
| INTELLIGENCE | Performs anomaly/risk analysis |
| STATE | Maintains execution state |
| RAJYA | Applies validation and governance rules |
| SARATHI | Handles token generation and authorization |
| CORE | Final execution layer |

---

# SUCCESSFUL EXECUTION FLOW

```text
SIGNAL
→ PERCEPTION
→ INTELLIGENCE
→ STATE
→ RAJYA APPROVED
→ SARATHI TOKEN_GENERATED
→ CORE EXECUTED
```

---

# HIGH RISK REJECTION FLOW

```text
SIGNAL
→ PERCEPTION
→ INTELLIGENCE
→ STATE
→ RAJYA REJECTED
```

Reason:
High risk anomaly detected

---

# INVALID TOKEN FLOW

```text
SIGNAL
→ PERCEPTION
→ INTELLIGENCE
→ STATE
→ RAJYA APPROVED
→ SARATHI TOKEN_GENERATED
→ TOKEN_DENIED
```

Reason:
Invalid token detected

---

# MUTATION DETECTION FLOW

```text
SIGNAL
→ PERCEPTION
→ INTELLIGENCE
→ STATE
→ CONTRACT VALIDATION
→ MUTATION_REJECTED
```

Reason:
execution_id mismatch detected

---

# TELEMETRY SYSTEM

The telemetry system captures:

- Execution stages
- Service transitions
- Status updates
- Severity levels
- Trace identifiers
- Parent-child stage mapping

Telemetry supports:

- Real-time monitoring
- Replay reconstruction
- Forensic auditing
- Pipeline observability

---

# FORENSIC REPLAY ENGINE

The replay engine reconstructs:

- Execution chain
- Signal history
- State transitions
- Intelligence decisions
- Validation results
- Denial reasons

Replay validation ensures:

```text
Replay reconstructed successfully
Trace continuity verified
Event chain recovered
Append-only history verified
```

---

# SECURITY FEATURES

## Contract Validation

- Detects schema mismatch
- Prevents malformed execution flow
- Ensures payload integrity

## Mutation Detection

- Detects execution tampering
- Detects execution_id mismatch
- Prevents replay corruption

## Hash Chain Verification

- Validates append-only history
- Preserves forensic integrity
- Ensures trace continuity

## Token Validation

- Detects invalid tokens
- Prevents unauthorized execution
- Blocks unsafe pipeline access

---

# DASHBOARD FEATURES

The dashboard provides:

- Live execution monitoring
- Telemetry visualization
- Rejection tracking
- Replay visibility
- System metrics
- Contract monitoring
- Hash verification status

---

# SYSTEM METRICS

```text
EXECUTED
REJECTED
TOKEN_DENIED
MUTATION_REJECTED
```

Metrics are updated dynamically from execution payloads.

---

# FINAL RESULT

```text
SVACS Unified Core successfully demonstrates:

✓ Real-time telemetry
✓ Replay reconstruction
✓ Contract enforcement
✓ Mutation detection
✓ Token validation
✓ Hash verification
✓ Append-only execution logging
✓ Dashboard monitoring
```
