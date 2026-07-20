# PRANA Threat Model Canon

**Status:** Canonical Security Reference  
**Version:** 1.0.0  
**Methodology:** STRIDE + MITRE ATT&CK Mapping

## 1. STRIDE Threat Analysis

### 1.1 Spoofing (S)
- **T1: External Spoofing of PRANA Emission**
    - **Vector:** Unauthorized entity POSTing to `/api/v1/telemetry/prana`.
    - **Asset:** Bucket Integrity.
    - **Impact:** High (False signals leading to incorrect karma updates).
    - **Detectability:** Medium (Requires anomalous credential usage monitoring).
    - **Containment:** Fail-closed on authentication failure; strict IP/VPC filtering.

- **T2: Internal User/System Masquerading**
    - **Vector:** Compromised service account or rogue dev impersonating a valid `system_id`.
    - **Asset:** Data Provenance.
    - **Impact:** Medium.
    - **Detectability:** Low (If credentials are valid).

### 1.2 Tampering (T)
- **T3: Bucket Data Modification**
    - **Vector:** Direct DB access by rogue admin to alter `prana_packets`.
    - **Asset:** Immutable Audit Trail.
    - **Impact:** Critical (Destroys tamper-evident guarantees).
    - **Detectability:** High (If hash chaining is implemented).
    - **Containment:** Database-level append-only constraints; cryptographic integrity checks.

- **T4: Supply Chain Logic Injection**
    - **Vector:** Malicious dependency update in `bucket_consumer` or `main.py`.
    - **Asset:** Execution Logic.
    - **Impact:** Critical (Bypasses all boundaries).
    - **Detectability:** Low (Subtile logic changes).
    - **Containment:** Dependency pinning; hash-verified builds; SBOM audits.

### 1.3 Repudiation (R)
- **T5: Signal Deletion as Denial**
    - **Vector:** Rogue dev deleting telemetry to hide evidence of misuse.
    - **Asset:** Accountability.
    - **Impact:** High.
    - **Detectability:** Medium (Requires log-level activity monitoring).
    - **Containment:** Write-once storage; external high-durability audit sinks.

### 1.4 Information Disclosure (I)
- **T6: Telemetry Exfiltration**
    - **Vector:** Interception of packets between PRANA and Bucket (TLS termination issues).
    - **Asset:** User Cognitive Privacy (Aggregated).
    - **Impact:** Low (States are non-identifying by design).
    - **Detectability:** Medium.
    - **Containment:** Mutual TLS (mTLS); ephemeral window isolation.

### 1.5 Denial of Service (D)
- **T7: Bucket Ingestion Exhaustion**
    - **Vector:** Flooding the bucket with valid/invalid packets.
    - **Asset:** System Availability.
    - **Impact:** Medium (PRANA fails-open, no application impact).
    - **Detectability:** High.
    - **Containment:** Rate limiting per `system_id`; circuit breakers.

### 1.6 Elevation of Privilege (E)
- **T8: Insider Policy Override**
    - **Vector:** Admin modifying Enforcement Layer thresholds to exempt specific users.
    - **Asset:** Governance Integrity.
    - **Impact:** Critical.
    - **Detectability:** High (If multi-sig/governance flow is enforced).
    - **Containment:** Separation of duties; multi-custodian approval for logic changes.

---

## 2. MITRE ATT&CK Mapping

| ID            | Name                              | Threat Mapping        | Containment Strategy            |
| :------------ | :-------------------------------- | :-------------------- | :------------------------------ |
| **T1565.001** | Data Manipulation: Stored Data    | Bucket Tampering (T3) | Cryptographic Hash Chaining     |
| **T1195.002** | Supply Chain: Compromised Library | Supply Chain (T4)     | Verified Builds & SBOM          |
| **T1078.001** | Valid Accounts: Default Accounts  | Rogue Insider (T8)    | MFA & Just-In-Time (JIT) Access |
| **T1561.002** | Data Destruction: Server Data     | Signal Deletion (T5)  | Append-Only Snapshots           |
| **T1098.004** | Account Manipulation: Cloud Accounts | Cloud Provider Compromise | Cross-Cloud Secret Management |

---

## 3. Specific Scenario Analysis

### 3.1 External Network Attacker
- **Entry Vector:** Publicly exposed API endpoints.
- **Asset at Risk:** System resources; signal validity.
- **Impact Severity:** High.
- **Detectability:** High (Traffic anomalies).
- **Containment Feasibility:** High (WAF, Rate Limiting).

### 3.2 Internal Rogue Developer
- **Entry Vector:** Direct code push or DB access.
- **Asset at Risk:** Structural boundaries; logic deterministic integrity.
- **Impact Severity:** Critical.
- **Detectability:** Low (Hardest to detect without multi-sig code review).
- **Containment Feasibility:** Medium (Requires strict governance).

### 3.3 Replay Manipulation
- **Entry Vector:** Capturing valid packets and re-sending them to skew focus scores.
- **Asset at Risk:** Fairness of karma updates.
- **Impact Severity:** Medium.
- **Detectability:** High (Timestamp/ID collisions).
- **Containment Feasibility:** High (Nonces and strictly increasing timestamps).

### 3.4 Post-Quantum Signature Break
- **Entry Vector:** Future quantum computer breaking RSA/ECDSA used for packet signing.
- **Asset at Risk:** Authentic telemetry origin.
- **Impact Severity:** Critical (Long-term).
- **Detectability:** Zero (Until the breach is discovered).
- **Containment Feasibility:** Low (Requires preemptive PQC migration).

---

## 4. Asset Risk Registry

| Asset                  | Primary Threat   | Detection             | Recovery              |
| :--------------------- | :--------------- | :-------------------- | :-------------------- |
| **PRANA Packet Store** | Tampering        | Merkle Root Check     | Periodic Snapshots    |
| **Governance Logic**   | Insider Override | Multi-Custodian Log   | Deterministic Restore |
| **Telemetry Keys**     | Exfiltration     | Hardware Security HSM | Global Key Rotation   |

---

## 5. Security Verdict (Prana Day 1)
PRANA's primary vulnerability is not its observability—which is ephemeral and non-sensitive—but the **integrity of the Bucket storage** and the **resistance of the Enforcement logic** to insider manipulation. Structural fortification must focus on making these layers tamper-evident and logically isolated.
