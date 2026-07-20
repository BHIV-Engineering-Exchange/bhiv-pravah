# PRANA Red Team Threat Intelligence Baseline (Second Pass)

**Role:** Sovereign Red-Team Architect  
**Project:** 45-Day Hardening Program Baseline  
**Status:** COMPLETE (Final Adversarial Expansion)

## 1. Formal Severity Model Definition

To ensure objective ranking of integrity risks, we apply the following mathematical weighting:

### 1.1 The Formula
`Risk Score = (Likelihood * 0.4) + (Impact * 0.4) + (Detectability_Inversion * 0.2)`

### 1.2 Dimension Definitions
- **Likelihood (0–10):** Frequency of technical path availability (10 = trivial/always available).
- **Impact (0–10):** Breadth of governance/logic collapse (10 = total institutional loss of truth).
- **Detectability Inversion (0–10):** The difficulty of discovering the breach *after* it has occurred (10 = zero footprint/forensic erasure).

### 1.3 Weighting Justification
- **Likelihood & Impact (40% each):** PRANA's value is derived from its reach and the magnitude of its "truth." High-impact, low-likelihood threats (e.g., PQ break) must be balanced against high-likelihood, moderate-impact threats (e.g., console mocking).
- **Detectability Inversion (20%):** PRANA is an audit system. A failure that hides itself is fundamentally more dangerous than one that leaves a trail, even if the impact is lower.

---

## 2. Top 10 Most Dangerous Threats (Re-Ranked)

| Rank | Threat Name | Score | Blast Radius | Time-to-Detection | Forensic Survivability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Unverified Ingest Payload Injection** | **9.5** | System-Wide | Months (Audit Only) | **None** (Looks like valid telemetry) |
| **2** | **Administrative Ledger Purge** | **9.2** | targeted / Multi | **Infinite** | **Destroyed** (No gap detection) |
| **3** | **Time-Source NTP Poisoning** | **8.4** | System-Wide | Weeks | Evidence Fragmented (Logs exist) |
| **4** | **Snapshot Logic Rollback** | **8.0** | System-Wide | Immediate | Partial (Hypervisor logs) |
| **5** | **Signal Logic Mocking (JS-Console)** | **7.8** | Single User | Impossible | **None** (Data appears original) |
| **6** | **Consumer Domain Impersonation** | **7.5** | System-Wide | Hours | Evidence Intact (Queues empty) |
| **7** | **Supply Chain "raw_signals" Exfil** | **7.2** | Multi-user | Months | Evidence Partial (Hidden in blobs) |
| **8** | **Monitoring Heartbeat Forgery** | **6.8** | Infrastructure | Weeks | Evidence Intact (Local stats) |
| **9** | **Transport Layer Replay (Scale)** | **6.4** | Multi-user | Days | Evidence Intact (Duplicate IDs) |
| **10**| **Identity Authority Bypass** | **6.0** | System-Wide | Days | Evidence Intact (Auth logs) |

---

## 3. High-Severity Threat Expansion

### 3.1 Unverified Ingest Payload Injection (Rank 1)
- **Vector:** The `/ingest` API endpoint is exposed to the public network without session-binding or identity proof requirements.
- **Propagation:** An external actor can inject arbitrary focus scores for any `user_id` without authenticating.
- **Detection Latency:** Detection only occurs if institutional outcomes (rewards) deviate significantly from historical statistical norms.
- **Blast Radius:** Every user recorded in the Gurukul/EMS identity domain.

### 3.2 Administrative Ledger Purge (Rank 2)
- **Vector:** Direct DB access combined with the lack of technical sequence anchors.
- **Propagation:** Malicious deletion of evidence packets (`STATE='DISTRACTED'`) for specific high-privilege students.
- **Detection Latency:** Forever. Without a technical proof-of-sequence, the "absence of evidence" appears as "perfect behavior."
- **Blast Radius:** Targeted manipulation of any user's integrity record.

### 3.3 Time-Source NTP Poisoning (Rank 3)
- **Vector:** Spoofing NTP responses to the ingestion server.
- **Propagation:** Forcing the server clock to drift allows for "Window Compression"—simulating 1 hour of telemetry in 1 real-time minute.
- **Detection Latency:** High. Requires correlation with secondary, off-system time sources.
- **Blast Radius:** System-wide timing integrity.

---

## 4. Still-Unprotected Surfaces (Residual Risk)

1. **Protocol Anonymity:** The Ingest Tier cannot technically distinguish between the genuine PRANA sensor and a script/bot.
2. **Context Blindness:** The Ledger Store assumes that the `user_id` context provided by the client is the true actor.
3. **Sequence Fragility:** The "chain of truth" is logical only. If the database is modified at rest, there is no mathematical proof to detect the mutation.
4. **Governance Nominalism:** Override policies exist only in documentation; the runtime has no technical "governed execution" paths.
5. **Recovery Ambiguity:** Restoring a database snapshot erases all telemetry generated between the snapshot and the crash, with no secondary "Blind Mirror" to recover the lost interval.

## 5. Architectural Verdict: The "Trust Vacuum"
PRANA possesses an advanced structural design on paper, but its runtime currently operates in a **Trust Vacuum**. The system makes no effort to verify its inputs, its source, its sequence, or its context. Until these boundaries are technically enforced, PRANA serves as a high-fidelity record of whatever an adversary chooses to tell it.
