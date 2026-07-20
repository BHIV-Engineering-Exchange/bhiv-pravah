# PRANA_CROSS_PRODUCT_GOVERNANCE_PROTOCOL.md

## 1. Introduction
This Protocol defines the mandatory governance lifecycle for the PRANA telemetry layer across the BHIV ecosystem. It serves as the constitutional framework ensuring that PRANA remains a stable, non-reactive primitive as products scale.

## 2. Governance Roles

- **Custodian**: The primary guardian of PRANA invariants. Responsible for reviewing high-risk declarations and conducting annual boundary revalidations.
- **Core (Sovereign Core)**: Authority responsible for formal amendments to the System Canon.
- **Bucket/Infrastructure**: Teams maintaining the PRANA telemetry ingestion and egress pipelines.
- **Karma/Policy Layer**: Teams managing the first-level interpretation of telemetry into records.
- **Product Leads**: Responsible for filing Impact Declarations and ensuring their teams respect the "no-coupling" rule.

## 3. Mandatory Declaration Rule
No code change that interacts with PRANA (direct or indirect) may be merged into any product branch without a valid `PRANA_IMPACT_DECLARATION`. This is a hard requirement for the "Definition of Done."

## 4. Review SLAs (Advisory)
- **Category A/B**: Automatic approval.
- **Category C**: Custodian acknowledgement within 48 hours.
- **Category D**: Mandatory advisory review session scheduled within 5 business days.
*Note: Governance is advisory and intended to assist, not block, velocity.*

## 5. Escalation Path
If a conflict arises between product needs and boundary constraints:
1. **Technical Consultation**: Custodian and Product Lead seek an uncoupled alternatives.
2. **Governance Transparency**: The risk is documented in the System Integrity Dashboard.
3. **Core Review**: If the conflict impacts system-level trust, the Sovereign Core conducts a "Constitutional Audit."

## 6. Annual Boundary Revalidation
Once per calendar year, the Custodian must conduct a full revalidation of the ecosystem:
- Verify all documented dependencies still exist.
- Confirm no "Shadow Telemetry" or "Logic Creep" has occurred.
- Re-sign the **Feature Freeze Reaffirmation**.

## 7. Change Classification Matrix

| Action                        | Governance Requirement                      |
| :---------------------------- | :------------------------------------------ |
| **Logic Refactor (Internal)** | Category A Declaration.                     |
| **New Event Logging**         | Category B Declaration + Boundary Check.    |
| **Outcome Pathway Addition**  | Category C/D Declaration + Advisory Review. |
| **Primitive Mutation**        | CORE Amendment + Full Regression Audit.     |

## 8. Governance Lifecycle Model
1. **Design**: Identify telemetry needs.
2. **Declare**: Submit Impact Declaration.
3. **Verify**: Automated CI/CD boundary checks.
4. **Audit**: Periodic Custodian reviews.
5. **Reaffirm**: Annual freeze confirmation.

## 9. Freeze Reaffirmation Statement
*"We, the contributors to the BHIV ecosystem, reaffirm that PRANA is a graduated state primitive. We pledge to protect its boundaries, resist the entropy of additional intelligence, and ensure that observation never becomes control."*
