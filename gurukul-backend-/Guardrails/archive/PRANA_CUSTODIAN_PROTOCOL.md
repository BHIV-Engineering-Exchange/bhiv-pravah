# PRANA_CUSTODIAN_PROTOCOL.md

## A. Custodian Responsibilities
The Custodian is the primary guardian of the system invariants. In every interaction with the codebase:
1. **Check Invariants**: Ensure the 1:1 mapping of signal to state remains unchanged.
2. **Check Boundary Integrity**: Verify that no semantic data (text, coordinates) is being ingested.
3. **Confirm Non-Intelligence Posture**: Ensure no predictive or interpretive logic has crept into the system.
4. **Confirm No Data Aggregation**: Verify that PRANA remains ephemeral and windowed.

## B. Contamination Detection
Detecting "Logic Creep" and "Inference":
- **Implicit Logic**: If code elsewhere in the system asks "Is the user bored?", and it uses PRANA signals to answer, the boundary is contaminated.
- **Dependency Introduction**: If a product module (e.g., `learning.py`) imports a PRANA utility, it must be for observational logging only, never for control flow.
- **Behavioral Inference**: Any code that attempts to deduce *intent* from PRANA states is a violation.

## C. Escalation Protocol
If a violation is detected:
1. **Freeze Integration**: Stop all data flow between PRANA and the contaminating module.
2. **Document Breach**: Create a record in the Governance Log detailing the specific line of code and the invariant violated.
3. **Audit Invariant**: Re-verify all core PRANA primitives for side effects.
4. **Governance Review**: Conduct a formal review to restore the boundary.

## D. Mandatory Embedded Testing (MANDATORY)
Every future task in the BHIV workspace must include a **PRANA Boundary Check**. This is a non-negotiable step in the "Definition of Done" for any PRANA-interacting code:
- `ASSERT(PRANA_INPUT == RAW_SIGNALS_ONLY)`
- `ASSERT(PRANA_OUTPUT == CANONICAL_STATES_ONLY)`
- `ASSERT(SYSTEM_OUTCOME != DEPENDENT_ON_PRANA)`
- `ASSERT(USER_NOTIFIED == FALSE)`
