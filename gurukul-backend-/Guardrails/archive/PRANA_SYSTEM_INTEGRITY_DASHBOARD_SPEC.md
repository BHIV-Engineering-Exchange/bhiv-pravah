# PRANA_SYSTEM_INTEGRITY_DASHBOARD_SPEC.md

## 1. Dashboard Purpose
The PRANA System Integrity Dashboard is a conceptual, documentation-driven monitoring surface. It exists solely to provide a high-level view of the state and governance health of the PRANA ecosystem across all BHIV products. It is **NOT** a user-tracking tool or a performance analytics engine.

## 2. Mandatory Metrics & Indicators

| Indicator              | Type      | Definition                                                          |
| :--------------------- | :-------- | :------------------------------------------------------------------ |
| **PRANA Version**      | Static    | Current canonical version (e.g., VERIFIED-LOCK-1).                  |
| **Freeze Status**      | Boolean   | Confirmation that the Feature Freeze is in effect (100%).           |
| **Boundary Integrity** | Status    | Result of the latest automated scan for boundary violations.        |
| **Dependency Map**     | Inventory | List of all products and modules with an active Impact Declaration. |
| **Last Audit Date**    | Timestamp | Date of the most recent Governance Audit.                           |
| **Breach Count**       | Integer   | Number of documented boundary or sovereignty violations.            |

### 2.1 Forbidden Data
The following data points are strictly prohibited from this specification and any resulting implementation:
- **User Personas/Names**: No PII or user-level identifiers.
- **Activity Scores**: No "Focus Scores," "Productivity Ranks," or "Judgment Metrics."
- **Behavioral Heatmaps**: No visual representation of aggregate user interactions.
- **Engagement Analytics**: No "feature usage" or "retention" metrics.

## 3. Data Sources
This dashboard aggregates data from **non-production, secondary sources**:
- **Governance Logs**: Standardized audit records.
- **Impact Declarations**: Metadata from merged Pull Requests.
- **Checksum Proofs**: Verification hashes of the frozen PRANA core.
- **CI/CD Scans**: Results from automated boundary checks during build.

## 4. Integrity Check Process
- **Per-Release**: Every production release must include a "Boundary Integrity Assertion" in the release notes.
- **Daily Heartbeat**: A conceptual check ensuring the PRANA bucket consumer is active and adhering to the egress filter rules.

## 5. Escalation Protocol (Advisory)
If the dashboard indicates a "Boundary Integrity: FAILED" status:
1. **Internal Alert**: Notify the Custodian and the relevant Product Lead.
2. **Impact Assessment**: Conduct a mandatory Governance Review of the offending module.
3. **Advisory Labeling**: Mark the specific linkage as "NON-COMPLIANT" in the dashboard.
4. **Remediation Plan**: Draft a boundary restoration plan; no enforcement action is taken on live traffic.

## 6. System Health Indicators
- **Green**: 100% Invariant Compliance, 0 Open Breaches.
- **Yellow**: 100% Invariant Compliance, Category D Dependency Detected (Audited).
- **Red**: Boundary Violation Detected or Unauthorized Coupling Found.
