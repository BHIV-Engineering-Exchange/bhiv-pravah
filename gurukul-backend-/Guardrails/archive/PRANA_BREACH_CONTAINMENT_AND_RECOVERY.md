# PRANA Breach Containment and Recovery

**Status:** Resilience Specification  
**Version:** 1.0.0  
**Objective:** Deterministic recovery and non-propagation of compromise.

## 1. Compartmentalized Trust Zones
To ensure a breach in one layer doesn't propagate, the system is segmented into distinct trust zones with strict egress/ingress policies.

| Zone                | Component        | Fault Tolerance       | Breach Impact                            |
| :------------------ | :--------------- | :-------------------- | :--------------------------------------- |
| **Zone 0 (Sensor)** | PRANA Extension  | Hardware isolation.   | Local signal loss; no data corruption.   |
| **Zone 1 (Ingest)** | Bucket API       | Rate-limited VPC.     | Denial of Service; no history tampering. |
| **Zone 2 (Store)**  | DB / Merkle Tree | WORM Storage.         | History exposure; no modification.       |
| **Zone 3 (Logic)**  | Core / Policy    | Isolated Computation. | Incorrect flagging; no signal tampering. |

## 2. Fail-Safe Policy Logic
The system distinguishes between operational failure and security failure.

### 2.1 Fail-Open vs Fail-Closed
- **Sensor Failure (Zone 0):** **Fail-Open.** Stop emitting telemetry. Application continues without observability.
- **Integrity Validation Failure (Zone 2):** **Fail-Closed.** If hash chaining validation fails, the Bucket halts ingestion and flag generation. It is better to have NO data than UNTRUSTED data.
- **Enforcement Failure (Zone 3):** **Fail-Closed.** No enforcement actions are taken if the policy layer cannot be verified.

## 3. Immutable Snapshot Checkpoints
Recovery is not "auto-magic"; it is deterministic based on verified checkpoints.

- **Genesis Snapshot:** A cryptographically signed state of the system at the start of a period.
- **Periodic Checkpoints:** Hourly snapshots of the Merkle Root stored in a separate, high-durability cold-storage vault.
- **Recovery:** In the event of a DB breach, the system restores from the last verified checkpoint and re-processes the signed immutable log.

## 4. Ledger Reconciliation Protocol
If a discrepancy is detected between the Bucket and the Policy Audit Log:

1. **Isolation:** Halt automated karma updates.
2. **Analysis:** Compare the hash chain of the Bucket against the signed Merkle Roots in the external vault.
3. **Reconciliation:** Identify the first point of divergence.
4. **Restoration:** Replay packets from the last valid point to reconstruct the state.

## 5. Recovery Validation Process
A system is not "recovered" until its integrity is re-proven.

- **Step 1: Structural Integrity Check.** Re-verify the hash chain of all packets.
- **Step 2: Logic Integrity Check.** Re-verify the checksums of all Policy and Enforcement deployment artifacts.
- **Step 3: Governance Review.** Multi-Sig sign-off by 3 Custodians to resume operational status.

## 6. Self-Healing Characteristics
- **Non-Propagation:** A compromised Enforcement account cannot modify the historical PRANA signals (due to Zone 2 isolation).
- **Deterministic Restore:** Because signals are append-only and signed, the system state can be perfectly reconstructed if the code/logic is restored to its verified version.

## 7. Justification
Trust requires verification. By ensuring that any compromise is contained to its zone and that recovery is a deterministic process of state reconstruction, we preserve the "Sovereign" nature of PRANA even under successful infrastructure attack.
