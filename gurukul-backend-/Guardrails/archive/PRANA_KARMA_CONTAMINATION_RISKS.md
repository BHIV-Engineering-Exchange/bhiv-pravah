# PRANA & Karma Contamination & Risk Analysis

## 1. Identified Risks

### 1.1 Misuse of Observational States
- **State-to-Judgment Mapping**: PRANA’s `DISTRACTED` or `OFF_TASK` states are currently mapped to the `cheat` action in the `BucketConsumer`.
  - **Risk**: High. This misinterprets observational telemetry (distraction) as a moral/policy violation (cheating).
  - **Status**: **Current Reality** (exists in `bucket_consumer.py`).
  - **Guardrail**: Document and flag the coupling between observational states and moralized action labels, as this creates a risk of misclassification.

### 1.2 User Exposure & Behavioral Nudges
- **Karmic Toasts**: The student UI provides real-time notifications about karma increases/penalties.
  - **Risk**: Medium. This introduces a feedback loop that PRANA and Karma are explicitly designed to avoid. It influences user behavior through nudges.
  - **Status**: **Current Reality** (exists in `KarmaContext.jsx`).
  - **Guardrail**: The presence of user-facing notifications constitutes a behavioral nudge and feedback loop, which should be explicitly documented as a governance risk. This exposure should be documented as a deviation from Karma’s intended role as a background record system.

### 1.3 Accidental Coupling
- **Timer Penalties**: `App.jsx` contains logic to penalize users for stopping a study timer prematurely.
  - **Risk**: Medium. The UI logic is directly writing to the Karma system based on interaction patterns. This couples the frontend UX state machine with the governance record system.
  - **Status**: **Current Reality** (exists in `App.jsx`).
  - **Guardrail**: This represents a coupling between UI lifecycle and governance records, which should be recorded as a system boundary violation.

---

## 2. Future Risk Vectors

### 2.1 Hidden Influence via STP/InsightFlow Bridges
- **Outbound Feedback Signals**: `KarmicFeedbackEngine` is designed to compute "dynamic influence" and "behavioral bias" for transmission to external bridges.
  - **Risk**: If external systems (STP Bridge) use these signals to optimize curriculum, change difficulty, or alter visibility, PRANA will have unintentionally influenced system outcomes.
  - **Status**: **Theoretical/Inactive** (STP Bridge appears to be a stub or separate module).
  - **Guardrail**: Verify whether constraint_only_mode is defined and documented, and whether downstream systems are contractually restricted from real-time adaptation.

### 2.2 Re-Interpretation of "Paap" and "Dharma"
- **Moralizing Schema**: The use of terminology like "Paap" (sin) and "Dharma" (duty) in the database schema (`PaapTokens`, `DharmaPoints`) invites judgmental interpretation by anyone auditing the data (Teachers, Admins, or future developers).
  - **Risk**: High. Neutral records can be misinterpreted as definitive character assessments.
  - **Status**: **Current Reality** (Database schema labels).
  - **Guardrail**: The use of moral-laden schema labels should be flagged as an interpretive risk for governance review.

---

## 3. Governance Safeguards (Conceptual)

1. **Isolation of Telemetry**: Ensure PRANA packets flow into a "Black Box" bucket that is NOT readable by any system with UI-write access.
2. **Action Label Neutrality**: Auditing all mappings in standardizing consumers to ensure they reflect *what happened* (e.g., `tab_switch_detected`) rather than *a judgment of what it means* (e.g., `policy_violation`).
3. **Zero-UI Exposure Policy**: Audit all Frontend contexts to ensure no references to Karma balances or levels exist in components rendered for the user.
4. **Determinism Verification**: Periodic audits to ensure that the transition from Signal → State → Karma Record remains 1:1 and does not involve probabilistic "scoring" engines.
