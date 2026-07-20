# PRANA Internal Resilience Model

**Status:** Governance Specification  
**Version:** 1.0.0  
**Objective:** Internal abuse resistance and institutional safety.

## 1. No Central Super-Admin Design
PRANA rejects the primitive of a "Global Admin" with override authority. Administrative power is fragmented into specific, verifiable roles.

### 1.1 Role-Based Privilege Isolation

| Role | Authority | Constraints |
| :--- | :--- | :--- |
| **Telemetry Custodian** | Manages PRANA sensor keys. | Cannot access raw database or modify logic. |
| **Ledger Auditor** | Grants read access to audit logs. | Read-only; cannot modify or delete signals. |
| **Governance Architect** | Proposes changes to Policy Layer. | Proposals require Multi-Sig approval. |
| **Enforcement Guardian** | Authorizes specific enforcement actions. | Requires valid Advisory Flags + Multi-Sig. |

### 1.2 Separation of Duties (SoD)
The system enforces a "Two-Person Rule" for all structural changes:
- **Change Initiation:** Architect proposes a logic update.
- **Change Verification:** Guardian validates against Threat Model.
- **Change Execution:** System automatically deploys ONLY if strictly matching the verified proposal.

## 2. Multi-Signature Governance for Structural Changes
Structural changes (schema updates, threshold modification, key rotation) require digital signatures from a majority of Custodians.

- **Mechanism:** M-of-N multi-signature (e.g., 3-of-5).
- **Auditability:** Every multi-sig event is recorded in the Append-Only Log.
- **Resistance:** Prevents "Admin Override Abuse" and "Silent Schema Mutation" by a single rogue actor.

## 3. Zero-Trust Internal Access Model
"Verify Everything, Trust Nothing."

### 3.1 Identity-Centric Access
- No IP-based trust.
- Every internal service request must carry a verifiable identity token (SPIFFE-compatible).
- Access to the Bucket Ingestion API is limited to authenticated PRANA sensors via mutual TLS (mTLS).

### 3.2 Secret Key Isolation
- PRANA signing keys must live in HSMs (Hardware Security Modules) or isolated TPMs (Trusted Platform Modules).
- **Key Exfiltration Resistance:** Keys are non-exportable; only the "Sign" operation is exposed.

## 4. Immutable Write Guarantees
To prevent T3 (Bucket Tampering) and T8 (Insider Override):
- **Write-Once Logic:** Once a policy threshold is set for a season, it cannot be modified without a full governance cycle.
- **Database Hardening:** PostgreSQL `ROW LEVEL SECURITY` (RLS) and custom triggers to prevent `UPDATE` or `DELETE` on the `prana_packets` table.

## 5. Defense Scenarios

| Threat                         | Model Defense              | Mechanism                                            |
| :----------------------------- | :------------------------- | :--------------------------------------------------- |
| **Silent Schema Mutation**     | Immutable Write Guarantees | DB-level rejection of schema changes during runtime. |
| **Admin Override Abuse**       | Multi-Signature Governance | 3-Custodian approval required for override.          |
| **Logging Backdoor Insertion** | Separation of Duties       | Code audit signature required for deployment.        |
| **Secret Key Exfiltration**    | HSM Isolation              | Keys cannot be read by system admins.                |

## 6. Zero-Trust Verification Flow
1. **Request:** Actor requests access to Signal Audit.
2. **Identification:** System verifies Actor's hardware-bound identity.
3. **Authorization:** System checks Role Matrix + JIT (Just-In-Time) window.
4. **Fulfillment:** Read-only access granted; audit record created.

## 7. Justification
This complexity is required to remove the "Internal Rogue" as a single point of failure. By fragmenting authority, we ensure that PRANA’s structural boundaries are self-defending.
