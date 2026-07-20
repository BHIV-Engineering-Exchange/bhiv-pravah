# PRANA Attack Surface Map (Adversarial Expansion)

**Role:** Sovereign Red-Team Architect  
**Objective:** Formalize component vulnerabilities and STRIDE exposure.  
**Tone:** Adversarial/Analytical.

## 1. System Component Decomposition

### 1.1 Signal Tier (Browser Logic)
- **Functional Description:** DOM-level event listeners for telemetry generation.
- **Entry Points:** Browser event loop, Developer Console.
- **Data Inputs:** User keyboard/mouse interaction.
- **Trust Assumptions:** Assumes browser `Event` authenticity and execution environment integrity.
- **Exposure:** High. Full manipulation capability via unverified JS injection.

### 1.2 Aggregation Tier (Packet Builder)
- **Functional Description:** State-machine converting raw signals to focused scores.
- **Entry Points:** `setInterval(5000)`.
- **Data Inputs:** Raw signal counts + Application context (`user_id`).
- **Trust Assumptions:** Assumes `performance.now()` and Local Object state are untampered.
- **Exposure:** Total "Focus" narrative control.

### 1.3 Transmission Tier (Bucket Bridge)
- **Functional Description:** Queue management and delivery to Ingest API.
- **Entry Points:** `enqueuePacket()`, `fetch()`.
- **Data Inputs:** Telemetry packets.
- **Trust Assumptions:** Assumes local `localStorage` is isolated and TLS prevents MiTM (ignores untrusted certificates).
- **Exposure:** Information Disclosure/Interception.

### 1.4 Ingestion Tier (FastAPI Endpoint)
- **Functional Description:** Public-facing API for protocol consumption.
- **Entry Points:** `/api/v1/bucket/prana/ingest`.
- **Data Inputs:** Unauthenticated JSON blobs.
- **Trust Assumptions:** Assumes the caller is the authorized application and that timestamps are real-time.
- **Exposure:** Mass Identity Forgery / Denial of Service.

### 1.5 Storage Tier (PostgreSQL/Redis)
- **Functional Description:** The "Sovereign" Ledger of truth records.
- **Entry Points:** SQL Engine, Redis CLI, internal API calls.
- **Data Inputs:** Validated packets.
- **Trust Assumptions:** Assumes administrative credentials are never compromised and that disk storage is immutable.
- **Exposure:** Repudiation / Permanent Evidence Deletion.

### 1.6 Logic Consumer Tier (Karma Tracker)
- **Functional Description:** Post-processing engine for reward/penalty enforcement.
- **Entry Points:** `/pending` polling endpoint.
- **Data Inputs:** Batched ledger records.
- **Trust Assumptions:** Assumes the ledger is an untampered reflection of reality.
- **Exposure:** Governance manipulation via forged truth injection.

### 1.7 Replay Tier
- **Functional Description:** Infrastructure for historical signal retrieval and auditing.
- **Entry Points:** Internal ledger queries.
- **Data Inputs:** Archive storage records.
- **Exposure:** Repudiation via historical record tampering.

### 1.8 Governance Tier
- **Functional Description:** Multi-custodian logic for protocol overrides and institutional state-shifts.
- **Entry Points:** Design-mode only (Technical runtime enforcement absent).
- **Exposure:** Nominalism; policy bypass without technical friction.

---

## 2. Comprehensive STRIDE Threat Enumeration

### 2.1 Spoofing
- **Threat:** **Identity Impersonation via Ingest Path.**
- **Affected Component(s):** Ingestion Tier
- **Description:** Attacker harvests a valid user ID and POSTs fake "Deep Focus" packets directly to the API, bypassing the sensor logic entirely.
- **Capability:** Low (Basic `curl` knowledge).
- **Impact:** Critical (Governance collapse).

### 2.2 Tampering
- **Threat:** **Local Signal Injection (Console Manipulation).**
- **Affected Component(s):** Signal Tier, Aggregation Tier
- **Description:** Overwriting JS variables in the browser to force a specific cognitive state (e.g., `DEEP_FOCUS`) while the user is physically absent.
- **Capability:** Low (Browser developer tools).
- **Impact:** Medium (Metric inflation).

### 2.3 Repudiation
- **Threat:** **Selective Evidence Erasure (Internal DB Admin).**
- **Affected Component(s):** Storage Tier
- **Description:** Admin deletes packets containing "DISTRACTED" or "AWAY" states for specific high-value users.
- **Capability:** High (DB Root access).
- **Impact:** Critical (Total loss of auditability).
- **Note:** If hash-chaining is unenforced, this deletion is mathematically undetectable.

### 2.4 Information Disclosure
- **Threat:** **Telemetry Metadata Poisoning.**
- **Affected Component(s):** Signal Tier, Aggregation Tier, Storage Tier
- **Description:** Malicious library injects sensitive environment data (e.g., local file names, session tokens) into the `raw_signals` field, which is then stored in the ledger.
- **Capability:** Medium (Supply chain access).
- **Impact:** High (Exfiltration of PII via "safe" channels).

### 2.5 Denial of Service
- **Threat:** **Ingest Flood (Queue Exhaustion).**
- **Affected Component(s):** Ingestion Tier, Storage Tier
- **Description:** Attacker floods the API with millions of malformed packets, filling Redis memory or overwhelming the database write buffers.
- **Capability:** Medium (Botnet/Script).
- **Impact:** High (System blinding).

### 2.6 Elevation of Privilege
- **Threat:** **Consumer Bypass (Logical Process Hijacking).**
- **Affected Component(s):** Logic Consumer Tier
- **Description:** Forcing a packet to be marked as `processed_by_karma = True` without running reinforcement logic, effectively neutralizing the penalty system.
- **Capability:** High (Internal system access).
- **Impact:** Critical (Bypass of institutional guardrails).

---

## 3. Adversarial Note on Integrity
Absent cryptographic source authentication at the Ingestion Tier, the system provides no verifiable proof of packet origin. Furthermore, without deterministic sequential anchors at the Storage Tier, the ledger offers no evidentiary proof of historical continuity. Given the currently unauthenticated Ingestion Tier, the system's "Truth" remains computationally fungible; any adversary capable of mimicking the unified schema can inject a fabricated version of reality into the sovereign ledger.
