# PRANA_GOVERNANCE_AUDIT_MODEL.md

## 1. Governance Philosophy
The PRANA Governance Audit Model is procedural and advisory. It is designed to provide guidance and ensure adherence to system invariants without acting as a blocking authority for product development, provided declarations are transparently filed.

## 2. Contamination Detection Checklist

Before approval, auditors must verify:
## 2. Formal Audit Standards

### 2.1 Invariant: No Inference (Signal Semantics)
**Risk Explanation**: Introducing interpretive logic turning raw telemetry into intent-based conclusions (e.g., "User is bored") compromises the deterministic nature of PRANA.
- **Boundary Violation**: Violates the "Non-Reactive" and "Non-Judgmental" invariants by adding a probabilistic layer over deterministic signal mapping.
- **Verification Method**: Static analysis of downstream consumers for non-canonical labels (sentiment, cognitive load keywords).
- **Required Evidence**: Code mapping logic from `bucket_consumer` to product-level state.
- **Pass Criteria**: 1:1 mapping of PRANA primitives to neutral activity records.
- **Fail Criteria**: Presence of heuristic weighting or emotive/intent descriptors (e.g., `user_intent_focus`, `engagement_quality`).
- **Common Violation Patterns**: Using a threshold of "Low Scroll + High IDLE" to label a user as "Unproductive".
- **False-Positives**: Technical logging for performance (e.g., "Latency: High") is permitted; it is not user inference.
- **Severity**: **High**
- **Review Escalation**: Custodian + Sovereign Core.

### 2.2 Invariant: No Individual Ranking (Record Semantics)
**Risk Explanation**: Socializing or comparing telemetry data between individuals creates behavioral pressure and gamifies privacy-sensitive signals.
- **Boundary Violation**: Violates the "Civilizational Charter" against using telemetry for competitive or evaluative social contexts.
- **Verification Method**: UI inspect for leadership boards or backend query patterns involving `GROUP BY` on user IDs for ranking purposes.
- **Required Evidence**: Dashboard mockups and SQL/NoSQL query definitions.
- **Pass Criteria**: Retrieval of PRANA data only for single-user context or fully anonymous population aggregates (N > 50).
- **Fail Criteria**: Display of "Top 10 Focused Students" or "User Rank" based on Focus telemetry.
- **Common Violation Patterns**: Calculating "Percentile Focus" compared to other users.
- **False-Positives**: Calculating personal improvements (User T1 vs User T2) is permitted if the data remains trapped in the user's local context.
- **Severity**: **Critical**
- **Review Escalation**: Custodian + Sovereign Core + Ethics Lead.

### 2.3 Invariant: No Direct UX Triggers (Product Flow)
**Risk Explanation**: Allowing PRANA packets to trigger UI changes turns an observability system into an enforcement or "nagging" system.
- **Boundary Violation**: Introduces a real-time feedback loop where the system reacts *to* the user, creating a psychological nudge.
- **Verification Method**: Search for `PranaContext` or `useKarma` subscriptions inside `useEffect` or state-dispatching functions in the frontend.
- **Required Evidence**: Frontend component tree and state management flow diagrams.
- **Pass Criteria**: PRANA data is used only for display or background logging; UI navigation is independent of telemetry.
- **Fail Criteria**: Auto-refresh, modal popups, or button-disabling logic triggered by PRANA state changes.
- **Common Violation Patterns**: Displaying a "Are you still there?" popup because PRANA emitted `IDLE`.
- **False-Positives**: Performance-based UI changes (e.g., reducing framerate when the tab is `NAV_BACKGROUND`) are permitted system-level optimizations.
- **Severity**: **Medium**
- **Review Escalation**: Product Lead + Custodian.

### 2.4 Invariant: No Semantic Leak (Sovereignty)
**Risk Explanation**: Capture of semantic content (what is being read/typed) violates the primary privacy boundary of the platform.
- **Boundary Violation**: Breaches the "Non-Invasive" guarantee; transforms telemetry into surveillance.
- **Verification Method**: Audit of `extra_data` or `metadata` JSON blobs for string values or identifiable references.
- **Required Evidence**: Schema definitions for the PRANA ingestion bucket.
- **Pass Criteria**: Payload contains strictly boolean, integer counts, or standardized enum values.
- **Fail Criteria**: JSON fields containing natural language, URLs with PII parameters, or CSS selectors identifying specific content.
- **Common Violation Patterns**: Appending the `page_title` or `input_field_value` to a PRANA packet for "context".
- **False-Positives**: Logging the generic `route_id` (e.g., `/dashboard`) is permitted for orientation.
- **Severity**: **Critical**
- **Review Escalation**: Custodian + DPO (Data Protection Officer).

### 2.5 Invariant: Fail-Open Integrity (Orchestration)
**Risk Explanation**: Making a product feature dependent on PRANA availability forces users to accept telemetry as a "tax" for usage.
- **Boundary Violation**: Violates the "Failure-Tolerant" guarantee; prevents the user from "opting-out" through system failure.
- **Verification Method**: Stress test by blocking the PRANA API endpoint and observing application behavior.
- **Required Evidence**: Unit tests demonstrating functionality with `PranaService` initialized to `null`.
- **Pass Criteria**: Core features (learning, chat, subjects) work perfectly when the PRANA stream is disconnected.
- **Fail Criteria**: Error boundaries triggered by PRANA timeouts or "Locked" features requiring a "Focus Check".
- **Common Violation Patterns**: A "Retry" button that blocks the UI until the PRANA socket connects.
- **False-Positives**: A small "Telemetry Disconnected" indicator in the admin debug console is permitted.
- **Severity**: **High**
- **Review Escalation**: Infrastructure Lead + Custodian.

## 3. Audit Checkpoints

### 3.1 Feature Proposals
Prior to technical design, the product lead must identify if PRANA is a intended data source. Early advisory consultation with the Custodian is recommended to avoid "Control-by-Design" flaws.

### 3.2 PR Reviews
Automated grep-scans should flag any new imports of `app.utils.karma` or `contexts/PranaContext`. Flagged PRs require a category declaration as per the `PRANA_IMPACT_DECLARATION_STANDARD`.

### 3.3 Outcome Logic Changes
Any change to the "Influence Vector" (how Karma or Telemetry affects user status) requires a mandatory re-audit of the PRANA-to-Outcome mapping.

### 3.4 Silent Drift Indicators
Indicators that governance is drifting:
- Increase in "Category C" declarations without corresponding Custodian reviews.
- Product teams bypassing the declaration via "internal" utility wrappers.
- Development of "shadow telemetry" that mimics PRANA but bypasses invariants.

## 4. Governance Review Flow

1. **Proposal**: Product team drafts feature spec.
2. **Declaration**: Impact declaration is appended to the spec.
3. **Custodian Review**: (Conditional) The Custodian reviews Category C/D declarations for boundary integrity.
4. **Approval / Revision**: Custodian provides "Non-Blocking Advisory Approval" or requests specific "Invariance Fixes."

## 5. Documentation Retention
All Governance Reviews and declarations must be logged in a **Governance ADR (Architecture Decision Record)** format. These logs must be retained for the life of the product to provide a clear audit trail for future system custodians.

## 6. Non-Enforcement Policy
The Custodian advises on boundary safety. If a product team chooses to proceed against an advisory rejection, the "High-Risk Coupling" must be explicitly flagged in the `PRANA_SYSTEM_INTEGRITY_DASHBOARD`. The Custodian does not "block" merges but "marks" them for downstream risk assessment.
