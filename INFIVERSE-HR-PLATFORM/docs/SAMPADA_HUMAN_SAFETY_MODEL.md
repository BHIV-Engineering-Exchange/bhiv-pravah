# SAMPADA Human Safety Model

**Status**: Draft
**Owner**: Rishabh Yadav (authority and sign-off required)
**Purpose**: Operationalize human-centric workforce safety principles so Sampada supports people without surveillance, coercion, opaque scoring, or hidden authority.

## 1. Executive Summary

Task19 Phase 5 turns the human-centric principles from the existing growth model into a stricter safety framework for government-scale workforce operations.

The goal is to protect dignity, explainability, bounded scoring, context awareness, assistive intelligence, and reviewability while keeping human control visible and bounded.

## 2. Required Principles

### Human Dignity

- People must not be reduced to metrics.
- Workforce systems must preserve respect, context, and role-specific nuance.
- No design element should imply that a person is valuable only when a metric is high.

### Explainability

- Any meaningful output should be explainable in plain terms.
- Users should be able to understand why a signal exists and where it came from.
- Opaque score generation is not acceptable.

### Bounded Scoring

- Scores, where used, must remain bounded, contextual, and interpretable.
- Scores must not become universal truth.
- Scores must not be used as hidden disciplinary mechanisms.

### Context Awareness

- The system must account for role, organization, time, and policy context.
- The same behavior may mean different things in different scopes.
- Context must be visible when a signal is presented.

### Assistive Intelligence

- Intelligence should help humans reason, not replace bounded decision-making.
- Advisory output must remain clearly advisory.
- Assistive output must not be silently upgraded into authority.

### Reviewability

- Human-facing decisions and significant system outputs must be reviewable.
- Users must have a path to ask why a result appeared and how it was derived.
- Review pathways must be traceable.

## 3. Mechanical Implementation Guidance

This safety model must translate principles into concrete system behavior.

### What is allowed

- Contextual, clearly labeled signals
- Explainable summaries and traces
- Opt-in or policy-bounded visibility
- Advisory recommendations with provenance
- Human review of significant outputs
- Cross-system reference links that preserve ownership

### What is prohibited

- Surveillance-style monitoring
- Opaque employee scoring
- Coercive productivity ranking
- Hidden authority systems
- Unreviewable automated judgment
- Universal human-state ownership by one system
- Aggregation that erases origin

### How safety should behave

- If a signal is derived, it must say so.
- If a score is bounded, its scope must be visible.
- If a recommendation is shown, it must not pretend to be a decision.
- If a workflow can affect a human, the review path must be visible.

## 4. Consent Boundaries

Consent is not optional decoration. It is part of the safety model.

### Consent rules

- Sensitive visibility should be opt-in where policy requires it.
- Workforce categories may require different consent boundaries.
- Consent scope must be explicit and revocable when applicable.
- Consent cannot be assumed from general participation in the system.

### Consent design intent

The system must distinguish between data needed for operation and data that is merely convenient to collect. Convenience is not a valid reason to erase consent boundaries.

## 5. Visibility Controls

### Required visibility controls

- Role-based visibility
- Org-scoped visibility
- Policy-scoped visibility
- Minimum necessary data display
- Separation of private, shared, and aggregate views

### Control rules

- Private data should not leak into aggregate views without justification.
- Aggregate views should not reveal unnecessary personal detail.
- Viewers should see only what their role and policy permit.
- Visibility boundaries should be auditable.

## 6. Appeals and Challenges

Any meaningful workforce signal that affects people should be challengeable.

### Required review path

- Show the signal or decision
- Show the source or basis
- Allow a challenge where the process supports it
- Record the challenge and its resolution

### Challenge principles

- Challenges must not be hidden.
- Overrides must be recorded.
- Review outcomes must remain visible to authorized parties.
- The person affected should not be left with a black-box result.

## 7. Safety Enforcement Patterns

The following patterns should support the safety model:

- Explicit labeling of signal type
- Display of source and derivation context
- Policy-based gating of sensitive views
- Logged overrides and reviews
- Distinct advisory and authoritative UI states
- Bounded retention and access rules

## 8. Human-Centric Risk Protections

### Risks to prevent

- Identity being reduced to score
- Dashboard alerts becoming invisible discipline
- Growth signals becoming pressure systems
- Observability becoming surveillance
- Human review being replaced by opaque automation

### Required protections

- No coercive ranking systems
- No hidden performance gamification
- No perpetual monitoring as a default
- No score without explanation and scope
- No review bypass for sensitive cases

## 9. Shared Resources and Bottlenecks

The shared resources for this phase are:

- Human-centric principle vocabulary
- Consent and visibility rules
- Challenge and appeal workflow definitions
- Explainability metadata
- Score scope and bound definitions

These should remain consistent with the command center governance model and the implementation support phase.

## 10. Dependencies

This document depends on the command center governance model because safety controls must constrain the dashboard's cognitive outputs.

Later phases depend on this model because:

- Phase 6 must keep implementation support aligned to human safety boundaries.
- The final current-state and review artifacts must reflect these protections.

## 11. Exit Criteria

This document is complete when it clearly defines:

- The required human-centric principles
- The allowed and prohibited behaviors
- The consent boundaries
- The visibility controls
- The appeals and challenge pathways
- The safety enforcement patterns
- The dependency relationship to later Task19 phases

## 12. Non-Negotiable Rules

- Do not create surveillance mechanisms.
- Do not create opaque scoring systems.
- Do not weaponize growth signals.
- Do not erase consent boundaries.
- Do not let observability become coercion.
- Do not let automated output bypass human review where review is required.

## 13. Notes for Implementation Teams

Implementation teams should treat this document as a safety boundary, not a UI preference. If a feature cannot be explained, challenged, or bounded, it should not be considered Task19-compliant.
