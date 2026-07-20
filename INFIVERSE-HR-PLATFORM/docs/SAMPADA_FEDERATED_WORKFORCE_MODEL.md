# SAMPADA Federated Workforce Model

**Status**: Draft
**Owner**: Rishabh Yadav (authority and sign-off required)
**Purpose**: Define an implementation-ready federated workforce ontology and identity model aligned to the TMS / MDU direction while preserving domain ownership boundaries and anti-centralization guardrails.

## 1. Executive Summary

Task19 Phase 3 defines the minimum shared workforce reference that Sampada can use without becoming the canonical owner of all human-state data.

The model is intentionally federated:

- Sampada owns growth, lifecycle, and workforce intelligence.
- Niyantran owns execution telemetry.
- Artha owns payroll truth.
- Other systems participate only within their bounded scopes.

This phase does not create a universal human ledger. It creates a shared reading layer with traceable sources, lineage, and ownership metadata.

## 2. Canonical Workforce Reference

Sampada may maintain a minimal shared identity layer for cross-system reference, but that layer must stay small and bounded.

### Required characteristics

- Minimal shared identity only
- Stable cross-system references
- Explicit source declarations
- Clear ownership metadata
- Traceable correlation identifiers

### Required fields for the shared identity layer

- Workforce reference ID
- Local system ID
- Source system
- Tenant or org scope
- Role or participation type
- Correlation ID history
- Ownership metadata
- Data freshness or last updated marker

### Boundaries

- This layer is a reference layer, not the full truth of a person.
- No one system should be forced to own every attribute.
- Derived signals must remain marked as derived.

## 3. Domain Ownership

### Sampada

Sampada owns:

- Growth signals
- Lifecycle signals
- Workforce intelligence
- Observability for workforce activity
- Challengeable interpretations and dashboard cognition

### Niyantran

Niyantran owns:

- Execution telemetry
- Tasking and execution evidence
- Downstream operational signals

### Artha

Artha owns:

- Payroll truth
- Payroll calculations
- Financial state related to compensation

### Others

Other systems may contribute bounded participation only when explicitly defined:

- Logistics
- CRM
- Departmental systems
- External partners

### Ownership rule

No domain may silently take ownership of another domain's truth. Sampada may correlate signals from other systems, but it does not absorb their sovereignty.

## 4. Signal Interoperability

The federated workforce model must support interoperable signals across systems without flattening their ownership boundaries.

### Required interoperability features

- Cross-system references
- Trace lineage
- Correlation IDs
- Source declarations
- Ownership metadata

### Cross-system references

- A record may point to a source system record without replacing it.
- The reference must preserve the source system as the authoritative origin.

### Trace lineage

- Any derived signal must be able to show where it came from.
- Lineage must include source systems, transformation steps, and timestamped correlation.

### Correlation IDs

- Correlation IDs must connect events across Sampada, Niyantran, Artha, and other participating systems.
- Correlation IDs are mandatory for replay and audit use cases.

### Source declarations

- Every signal should identify whether it is source data, derived data, or an aggregate.
- Derived status must be visible to users and reviewers.

### Ownership metadata

- Every participating signal must identify the owning domain.
- Ownership metadata must be preserved across API boundaries and dashboards.

## 5. Anti-Centralization Guardrails

### Non-negotiable restrictions

- Prevent a universal human-state model.
- Prevent one system from claiming all workforce truth.
- Prevent derived intelligence from becoming canonical fact by default.
- Prevent silent promotion of advisory output into authoritative state.

### Required protections

- Derived intelligence must remain challengeable interpretation.
- Source systems must remain visible.
- Ownership transfer must be explicit.
- Aggregation must not erase origin.

### Design intent

Sampada may help humans understand the workforce. It must not silently become the place where all workforce truth is stored, approved, and frozen.

## 6. Identity and Reference Boundaries

### Identity boundaries

- Local identity and source identity may differ.
- Workforce reference identity is allowed to bridge systems, but it must not replace the authoritative domain record.

### Participation boundaries

- A person may participate in multiple systems with different roles.
- Participation does not imply identical visibility everywhere.

### Derivation boundaries

- Scores, insights, and summaries are interpretations.
- Interpretations must not be presented as unchallengeable truth.

## 7. Shared Resources and Bottlenecks

The shared resources that will likely bottleneck later phases are:

- Workforce reference ID conventions
- Ownership metadata format
- Correlation ID propagation rules
- Source declaration rules
- Lineage and derivation vocabulary

These should be kept stable across the dashboard, safety, and implementation support phases.

## 8. Dependencies

This document depends on the Phase 1 architecture model and Phase 2 governance model because identity and signal boundaries must fit the org and policy scope.

Later phases depend on this model because:

- Phase 4 must surface derived intelligence with provenance and ownership context.
- Phase 5 must constrain safety rules to human-centric, challengeable interpretation.
- Phase 6 must use the ownership metadata and trace lineage rules during implementation hardening and evidence preparation.

## 9. Exit Criteria

This document is complete when it clearly defines:

- The minimal shared identity layer
- The domain ownership split across Sampada, Niyantran, Artha, and others
- The interoperability requirements for cross-system signals
- The anti-centralization guardrails
- The derived-intelligence-versus-canonical-truth rule
- The dependency relationship to later Task19 phases

## 10. Non-Negotiable Rules

- Do not create a universal human-state model.
- Do not centralize all workforce truth in Sampada.
- Do not erase source ownership through aggregation.
- Do not promote derived intelligence to canonical truth.
- Do not allow a reference layer to become a hidden authority layer.

## 11. Notes for Implementation Teams

Implementation teams should treat this document as the boundary for any cross-system workforce identity work. If a signal, schema, or dashboard cannot show source, ownership, and derivation clearly, it is not compliant with Task19 Phase 3.
