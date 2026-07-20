# SAMPADA Command Center Governance Model

**Status**: Draft
**Owner**: Rishabh Yadav (authority and sign-off required)
**Purpose**: Evolve the dashboard model toward government-scale operational cognition while preventing authority drift, hidden governance, and opaque scoring.

## 1. Executive Summary

Task19 Phase 4 defines how Sampada's command center should behave when used in government-scale environments. The dashboard must support high-density operational cognition, not hidden decision authority.

The core rule is simple: the dashboard can help people see and reason, but it cannot become the source of legitimacy, authority, or execution.

## 2. Executive Use Cases

The dashboard must support distinct views for the following roles:

- Minister
- Secretary
- Department Head
- HR Operator
- Auditor

### Role intent

- Minister: top-level operational visibility, escalation patterns, and broad system health.
- Secretary: portfolio-level oversight, policy-sensitive status, and cross-department coordination signals.
- Department Head: department-specific staffing, workflow, and bottleneck signals.
- HR Operator: day-to-day workforce operations, queue management, and bounded action support.
- Auditor: evidence review, trace validation, and compliance inspection.

### Use case rules

- Each role must see only what its scope and policy allow.
- Each role view must be explainable.
- No role view may imply universal authority.
- No dashboard role should silently inherit execution rights.

## 3. Cognition Separation

The dashboard must visibly separate the following cognitive stages:

- Observation
- Assessment
- Recommendation
- Decision
- Execution

### Separation requirements

- Observation is not assessment.
- Assessment is not recommendation.
- Recommendation is not decision.
- Decision is not execution.
- Execution happens in the owning or authorized execution layer, not in the dashboard by default.

### Design intent

The dashboard may help a person progress through these stages, but each stage must remain labeled and bounded. Users should never have to guess whether they are looking at a metric, a judgment, a recommendation, or an approved action.

## 4. Explainability Surfaces

Every derived insight shown in the command center must support explainability.

### Required surfaces

- Source visibility
- Calculation explanation
- Signal provenance

### Source visibility

- The dashboard must show where the data came from.
- Source systems must remain identifiable.
- Derived summaries must not hide their origin.

### Calculation explanation

- If a KPI or insight is computed, the dashboard should explain the logic at a readable level.
- Weighted or aggregated results should show the contributing signals when appropriate.

### Signal provenance

- Every insight should carry provenance metadata.
- Users should be able to inspect the chain from raw signal to derived display.

### Design intent

A user should be able to answer: "Where did this come from? Why is it shown? What was combined to produce it?" If the dashboard cannot answer that, it is not acceptable for Task19.

## 5. Authority Drift Protection

The command center must defend against dashboard-to-legitimacy-to-authority drift.

### Drift risks to prevent

- A dashboard score being treated as an official truth without review
- An operational summary becoming a hidden approval system
- A visual ranking becoming a coercive authority signal
- A recommendation widget being mistaken for a decision engine

### Required protections

- Clear labels for all computed signals
- Distinction between advisory and authoritative outputs
- Audit logging for any action originating from a dashboard workflow
- No hidden approval paths behind summary cards or widgets
- No dashboard component may claim authority on behalf of an owning system

### Design intent

The dashboard informs people. It does not grant itself legitimacy.

## 6. Government-Grade Operational Cognition

The dashboard should support low-scroll, high-density, operational cognition in a controlled way.

### Required qualities

- Fast scanability
- Hierarchical emphasis
- Bounded drill-down
- Context-sensitive surfaces
- Trace-aware drill paths

### Operational principles

- Surface the most important signals first.
- Keep detailed evidence one level down, not buried or hidden.
- Prefer context over clutter.
- Avoid random widget accumulation.

## 7. Governance Rules for Dashboard Components

### Metric cards

- Must identify whether the metric is raw, derived, or aggregated.
- Must show the source system or contributing scope.

### Alerts and flags

- Must explain the rule or signal that raised them.
- Must avoid implying disciplinary or authoritative status without review.

### Recommendations

- Must be explicitly advisory.
- Must not masquerade as decisions.

### Drills and traces

- Must show provenance and related evidence.
- Must preserve correlation IDs or trace references where available.

## 8. Shared Resources and Bottlenecks

The shared resources for this phase are:

- Executive role definitions
- Cognitive stage labels
- Explainability metadata
- Provenance display patterns
- Dashboard-to-execution boundary rules

These should remain stable across the safety model and implementation support phases.

## 9. Dependencies

This document depends on the architecture, governance, and federated workforce models because dashboard cognition must remain aligned to organization scope, policy separation, and ownership metadata.

Later phases depend on this model because:

- Phase 5 must translate these dashboard constraints into human safety rules.
- Phase 6 must use the explainability and authority boundaries during implementation support and evidence preparation.

## 10. Exit Criteria

This document is complete when it clearly defines:

- The executive use cases
- The observation/assessment/recommendation/decision/execution separation
- The source visibility, calculation explanation, and provenance surfaces
- The authority drift protection rules
- The dependency relationship to later Task19 phases

## 11. Non-Negotiable Rules

- Do not let dashboard summaries become authority.
- Do not hide signal provenance.
- Do not blur observation with decision-making.
- Do not let recommendation widgets execute anything by default.
- Do not permit dashboard cognition to override ownership boundaries.

## 12. Notes for Implementation Teams

Implementation teams should use this document to shape every dashboard and executive surface. If a component cannot show where a signal came from and what kind of cognitive stage it represents, it should not be treated as Task19-compliant.
