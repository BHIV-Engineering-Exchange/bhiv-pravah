# 🛡️ BHIV HR Platform - Ownership Matrix

This document defines the system ownership boundaries and responsibilities to maintain constitutional alignment and prevent scope creep.

| Area | Owner | Role | System Authority | Constitutional Boundaries |
| :--- | :--- | :--- | :--- | :--- |
| **System & Architecture** | Rishabh Yadav | Owner / Leader | State mutation, architecture directives, prioritizations, acceptance approval | Final gatekeeper of all codebase modifications and feature inclusions. |
| **Frontend UI** | Nikhil | Collaborator | Interface wiring, API mapping, dashboard data display | Consumption of API Gateway responses; zero direct orchestration. |
| **Infra & DevOps** | Vinayak / Raj | Collaborator | Port mappings, container lifecycles, orchestration environments, deployment uptime | Environment configurations; maintains platform availability. |
| **Observability & Docs** | Shashank (Sampada) | Support Builder | Trace evidence collection, workflow replay verification, developer guides | Strictly read-only on execution authority; signal/visibility layer only. |

---

## 🔒 Constitutional Boundary Affirmation
- **Read-Only Observation**: The Sampada role has visibility into system transactions, traces, and metrics.
- **No Direct Execution**: The Sampada role must not initiate state-changing commands or alter workflow processing logic.
- **Reference**: Detailed separation models are documented in [SHASHANK_REENTRY_ALIGNMENT.md](file:///c:/Users/Shani/Downloads/INFIVERSE-HR-PLATFORM-main/docs/SHASHANK_REENTRY_ALIGNMENT.md) and [SAMPADA_CURRENT_STATE.md](file:///c:/Users/Shani/Downloads/INFIVERSE-HR-PLATFORM-main/SAMPADA_CURRENT_STATE.md).
