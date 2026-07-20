# SAMPADA Government-Scale Architecture

**Status**: Draft
**Owner**: Rishabh Yadav (authority and sign-off required)
**Purpose**: Define Sampada as a governance-ready, policy-aware workforce intelligence platform that can operate across large enterprises, public institutions, government departments, and multi-agency environments without collapsing authority, ownership, or visibility boundaries.

## 1. Executive Summary

Task19 Phase 1 models Sampada for government-scale operation. The target is not a broader feature set; it is a harder boundary model that supports multi-organization administration, bounded visibility, and explicit tenant, org, and policy isolation.

Sampada remains an intelligence and visibility layer. It does not become a universal admin console, a hidden decision engine, or a monolithic workforce authority. Any execution authority remains with the owning system and the owning humans.

## 2. Operating Scope

Sampada must support operation across:

- Large enterprises
- Public institutions
- Government departments
- Multi-agency environments

The architecture must be able to represent nested organizations, federated admins, contractor participation, and policy boundaries without forcing all entities into a single global hierarchy.

## 3. Multi-Org Structure

Sampada must model organizations as bounded administrative units rather than as a single flattened tenant.

### Required organizational levels

- Ministry
- Department
- Division
- Unit
- Office
- Contractor / vendor participation

### Structural rules

- A ministry may contain multiple departments.
- A department may contain multiple divisions.
- A division may contain multiple units.
- A unit may contain multiple offices.
- Offices may include internal staff and approved external participation.
- Contractors and vendors participate only within the scopes explicitly assigned to them.

### Design intent

This hierarchy is for visibility, reporting, and policy enforcement. It is not a claim that all levels share the same authority or that one global administrator can safely act across all levels.

## 4. Workforce Scope

Sampada must support the following workforce categories as distinct participation types:

- Permanent staff
- Contractual staff
- Consultants
- Outsourced workforce
- Volunteers
- Fellows
- Advisors

### Rules for workforce scope

- Each workforce category must be representable without being forced into a single human-state model.
- Categories may share some signals, but they do not share identical lifecycle rules.
- Participation in visibility, assessment, or workflow must be explicit and bounded by policy.
- Contractor, volunteer, and advisor participation must not silently inherit employee-level authority.

### Design intent

The platform should be able to show workforce intelligence across mixed participation types while preserving role-specific lifecycle handling and privacy boundaries.

## 5. Federated Administration Model

Sampada must use bounded administration. It must not assume a single global admin who can see or control everything.

### Required admin roles

- Local admins
- Department admins
- Platform admins
- Auditors

### Role boundaries

- Local admins operate within their assigned office, unit, or division scope.
- Department admins operate within the department scope and its permitted children.
- Platform admins manage platform-level configuration and cross-tenant guardrails, not arbitrary business decisions.
- Auditors observe and verify; they do not become executors by default.

### Admin model principles

- Scope is explicit.
- Permission inheritance is bounded, not universal.
- Admin visibility must be explainable and auditable.
- Administration and execution are not the same thing.

## 6. Multi-Tenant Isolation

Sampada must define and enforce isolation at multiple levels.

### Isolation dimensions

- Tenant isolation
- Org isolation
- Data visibility boundaries
- Policy boundaries

### Tenant isolation

- Tenant A must not see Tenant B's operational data unless a specific, documented, and authorized cross-tenant relationship exists.
- Cross-tenant access must be deliberate, not emergent from shared infrastructure.

### Org isolation

- Sibling departments, divisions, or units must not receive default visibility into each other's private records.
- Aggregation may be shared upward only when the policy allows it.

### Data visibility boundaries

- Visible data must be scoped to the viewer's administrative role and the policy attached to that scope.
- Sensitive workforce data must be minimized by default.
- Visibility does not imply authority to mutate or approve.

### Policy boundaries

- Policies may differ by tenant, ministry, department, or workforce category.
- Policy application must be explicit, traceable, and reviewable.
- Policy overrides must be recorded and explainable.

## 7. Reference Architecture Pattern

Sampada should be implemented as a federated intelligence layer with the following conceptual separation:

- Identity and scope resolution
- Policy evaluation
- Visibility and signal aggregation
- Audit and replay logging
- Presentation surfaces for dashboards and reports
- Bounded integration adapters for other systems

### Architectural rule

No single layer may silently absorb all others. In particular:

- Identity resolution must not become a universal authority store.
- Policy evaluation must not become hidden governance.
- Aggregation must not become sovereignty.
- Dashboard cognition must not become execution authority.

## 8. Shared Resources and Bottlenecks

The following resources are likely to become shared bottlenecks across later phases:

- Org hierarchy definitions
- Workforce category definitions
- Admin role and scope definitions
- Tenant and policy boundary rules
- Audit and trace metadata conventions

These should be established early and reused consistently by the governance, identity, dashboard, and safety documents.

## 9. Dependencies for Later Phases

This architecture model is the foundation for later Task19 phases.

- Phase 2 depends on the architecture boundaries to define policy and governance separation.
- Phase 3 depends on this model to define the federated workforce identity layer.
- Phase 4 depends on this model to preserve executive dashboard cognition without authority drift.
- Phase 5 depends on this model to keep human safety rules aligned with the architecture boundary model.
- Phase 6 depends on this model as the controlling reference for implementation support and evidence preparation.

## 10. Non-Negotiable Rules

- Do not create a single global admin model.
- Do not collapse ministry, department, division, unit, and office into one undifferentiated organization.
- Do not flatten workforce categories into one universal human-state model.
- Do not convert aggregation into sovereignty.
- Do not convert visibility into execution authority.
- Do not introduce hidden governance paths.
- Do not weaken tenant, org, or policy isolation for convenience.

## 11. Exit Criteria

This document is complete when it clearly defines:

- The multi-org hierarchy
- The workforce scope categories
- The federated administration roles
- The isolation boundaries
- The architectural dependency relationship to later Task19 phases
- The non-negotiable boundary protections

## 12. Notes for Implementation Teams

Implementation teams should treat this document as the architectural boundary for all downstream Task19 work. Any dashboard, governance, ontology, or safety design that conflicts with this model must be revised before acceptance.
