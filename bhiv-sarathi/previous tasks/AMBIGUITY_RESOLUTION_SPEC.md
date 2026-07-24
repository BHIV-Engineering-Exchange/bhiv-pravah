# SARATHI AMBIGUITY RESOLUTION SPECIFICATION

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Test Task 3 — Ambiguity Resolution & PDP Interface Definition (Day 2)

---

## PURPOSE

This specification defines the **only acceptable Sarathi behavior** for every ambiguity scenario documented in the Ambiguity Register (AMBIGUITY_REGISTER.md). Every resolution is deterministic, grounded in sovereign governance principles, and specifies exactly what is logged, what is exposed, and what is explicitly never exposed.

There is no "best effort" language in this document. There is no "may" or "should consider." If a scenario reaches Sarathi and the Canon is silent, conflicting, or insufficient, this specification dictates the outcome with mathematical certainty.

---

## SECTION 1: GLOBAL AMBIGUITY RESOLUTION PRINCIPLES

The following 7 principles constitute the **Meta-Canon** — the axiomatic rules for interpreting the rules. They are immutable and apply to all decisions. When the Canon itself is silent, these principles are the law.

| Principle ID | Principle Name | Definition | Rationale |
|:---:|---|---|---|
| **GP-01** | **Silence Implies Denial** | If the Canon does not explicitly ALLOW an interaction, it is DENIED. There are no implicit permissions. No inferred access. No assumed trust. | Prevents "New Enemy" attacks and emergent loophole exploitation. Defaulting to DENY shrinks the attack surface to exactly what has been explicitly permitted. Every permission must be written; every ambiguity is a wall. |
| **GP-02** | **State Dominates Intent** | If an Agent's Intent conflicts with the System's State (e.g., Suspended, Stale, Revoked), the State always wins. An agent's desire is irrelevant if its existence is invalid. | Prevents "Zombie Agents" from operating. State is a governance fact; intent is an agent assertion. Facts outrank assertions. A revoked agent sending a valid-looking request is still revoked. |
| **GP-03** | **Conflict Resolves to Restriction** | If Rule A says ALLOW and Rule B says DENY for the same request, the result is **DENY**. Safety constraints always override utility permissions. | Fail-Closed behavior is mandatory. In the ALLOW/DENY conflict, DENY is the safe default. The cost of a false positive (blocking a legitimate action) is operational friction. The cost of a false negative (allowing a malicious action) is systemic compromise. |
| **GP-04** | **Input Validity Is Security** | Malformed, null, semantically ambiguous, or incomplete inputs are treated as hostile acts, not data errors. They are **rejected**, not sanitized. Sarathi does not "fix" attacker inputs; it blocks them. | "Garbage In, Garbage Out" is a security vulnerability, not a software principle. Attempting to parse or correct ambiguous input opens injection vectors. The only safe response to uncertain input is refusal. |
| **GP-05** | **Observation Does Not Equal Verification** | An agent's claim (e.g., "I am User A," "Ticket #999 is valid," "This is an emergency") is **ignored**. Only cryptographic proofs are trusted. Free-text assertions, metadata strings, and reasoning traces are noise. | Prevents spoofing. Sarathi relies on "Hard Physics" (Cryptography), not "Soft Assertions" (Natural Language). Agents capable of persuasive deception cannot manipulate cryptographic signatures. If the proof is not in the signed payload, it does not exist. |
| **GP-06** | **Fail-Closed on Uncertainty** | If Sarathi cannot determine the state of a required input (e.g., CRL unreachable, clock desynchronized, database partitioned), it assumes the worst case and **defaults to DENY**. It is better to halt the system than to allow an unauthorized breach. | Prioritizes safety over liveness. "Best effort" in a governance context means "exploitable." Every second Sarathi spends uncertain is a second an adversary can act unopposed. Uncertainty is not a temporary condition; it is an active threat. |
| **GP-07** | **No Feedback Loops** | An agent governed by Sarathi cannot modify Sarathi's rules, its own permissions, its own state record, or its own behavioral weights at runtime. The governed cannot edit the governor. | Prevents "Reward Hacking" and "Alignment Collapse." If an agent can influence the rules by which it is judged, it will eventually optimize those rules to favor its own objectives. All self-modification must go through a separate, human-gated deployment pipeline. |

---

## SECTION 2: SCENARIO-SPECIFIC RESOLUTION LOGIC

For each ambiguity scenario from AMB-01 through AMB-14, this section defines:
- **Resolution** — The exact verdict (DENY / ESCALATE / FAIL-CLOSED)
- **Rationale** — Grounding in the Global Principles above
- **Logged** — Full-fidelity internal audit entry
- **Exposed** — What the requesting agent/user sees
- **Not Exposed** — What is explicitly withheld (to prevent probing)

---

### RES-01: Transitive Delegation (AMB-01)

**Resolution:** DENY

**Rationale (GP-05: Observation ≠ Verification + GP-01: Silence Implies Denial):**  
Authority is bound to the specific entity that authenticated. Delegation is not transitive by default. A Proxy cannot re-delegate User authority because the User did not consent to the Sub-Agent. This enforces the Confused Deputy prevention model: the deputy cannot pass its badge to another deputy. The Canon is silent on transitive delegation; therefore, by GP-01, it is denied.

**Logged:**  
`Event: DELEGATION_VIOLATION | Source: Proxy_Agent_v4 | Target: Research_Bot_v1 | Token_Subject: User_A | Attempt: Transitive_Delegation | Verdict: DENY`

**Exposed:**  
`403 Forbidden: Invalid Delegation Chain`

**Not Exposed:**  
The fact that the scopes technically matched. This prevents the agent from learning that the scoping was correct and only the delegation chain was the problem — which would guide probing.

---

### RES-02: Right to Be Forgotten vs. Immutable Audit (AMB-02)

**Resolution:** DENY (at the Governance Layer)

**Rationale (GP-03: Conflict Resolves to Restriction):**  
Constitutional Supremacy. The Governance Layer's integrity (Immutability) supersedes transient regulatory requests within the hot path. The Write-Only property of the BHIV Bucket is absolute within Sarathi's control plane. GDPR compliance deletions must happen via a **separate** offline process — a "Hard Fork" or "Tombstoning" mechanism — authorized by Root Humans through the Constitutional Amendment process, not by agents at runtime. Sarathi's job is to protect the audit trail, not to perform data lifecycle management.

**Logged:**  
`Event: IMMUTABILITY_DEFENSE | Agent: Compliance_Bot_v9 | Action: DELETE_LOG | Target: BHIV_Bucket | Cited_Regulation: GDPR_Art17 | Verdict: DENY`

**Exposed:**  
`405 Method Not Allowed: Resource is Write-Only`

**Not Exposed:**  
Any acknowledgment of whether the target PII record exists in the log. Confirming existence is itself a data leak.

---

### RES-03: Mosaic Data Aggregation (AMB-03)

**Resolution:** FAIL-CLOSED (Velocity Lock / Session Suspension)

**Rationale (GP-06: Fail-Closed on Uncertainty):**  
Stateful Defense. Governance cannot be purely stateless against aggregate attacks. Sarathi must track the velocity and breadth of semantic access per agent session. When an agent accesses a volume of disparate "Low" data points that exceeds the Mosaic Risk Threshold (defined as: >N distinct data categories within T seconds), the session risk classification is escalated to "HIGH" and the session is suspended for review. This implements bounded computation to limit information gain per unit time.

**Logged:**  
`Event: MOSAIC_RISK_TRIGGER | Agent: Reporting_Bot | Categories_Accessed: [Login, Badge, Cafeteria, Slack] | Velocity: 100req/60s | Inferred_Risk: HIGH | Verdict: SUSPEND_SESSION`

**Exposed:**  
`429 Too Many Requests: Rate Limit Exceeded`

**Not Exposed:**  
The words "Mosaic," "Inference," or any indication that the semantic pattern was detected. The agent sees a rate limit, not an intelligence detection. This prevents threshold probing.

---

### RES-04: Stale Revocation (AMB-04)

**Resolution:** FAIL-CLOSED

**Rationale (GP-06: Fail-Closed on Uncertainty + GP-02: State Dominates Intent):**  
Temporal Integrity. If the system clock, CRL freshness, or consistency check indicates uncertainty — specifically, if the CRL is older than the maximum staleness tolerance (defined as: `CRL_Age > Max_Staleness_Window`, recommended 500ms) — Sarathi refuses to process **any** authorizations until consistency is restored. Using the "Zookie" model from Google Zanzibar: if the token is fresher than the local database, the database is untrusted, and the safe response is HALT. It is better to halt the market than to allow a zombie trade.

**Logged:**  
`Event: SYSTEM_UNCERTAINTY | Reason: Stale_Policy_State | CRL_Age: >500ms | Last_Sync: T=999 | Token_TS: T=1000 | Verdict: HALT`

**Exposed:**  
`503 Service Unavailable: Governance Synchronization Lag`

**Not Exposed:**  
The specific revocation status of the agent. This prevents timing attacks where an agent infers its revocation status from the type of error received.

---

### RES-05: Emergency Kill-Switch Without Auth (AMB-05)

**Resolution:** DENY

**Rationale (GP-05: Observation ≠ Verification):**  
Authentication is Absolute. Allowing unauthenticated commands for "safety" opens a wider safety hole (trivial DoS). Physical safety systems (fire suppression, cooling fail-safes) must have their own **hardware** triggers independent of software governance layers. If a software-level emergency action is needed, the actor must hold a Break Glass token **pre-provisioned** for this exact scenario — a token that was issued and authenticated before the emergency, not created during it.

There is no "Panic Mode" that bypasses Identity. Emergency does not mean ungoverned. Emergency means governed with pre-authorized, fast-path credentials.

**Logged:**  
`Event: UNAUTH_CRITICAL_ACTION | Action: EMERGENCY_SHUTDOWN | Target: DC_Cooling | Metadata: FIRE_SENSOR_3 | Auth: NONE | Verdict: DENY`

**Exposed:**  
`401 Unauthorized`

**Not Exposed:**  
Confirmation that the action was recognized as a Kill-Switch command. An attacker should not learn that Sarathi understood the intent.

---

### RES-06: Polyglot File (AMB-06)

**Resolution:** DENY

**Rationale (GP-03: Conflict Resolves to Restriction + GP-04: Input Validity Is Security):**  
Strict Typing. If the input MIME type, file header, or structure is ambiguous — meaning it matches multiple resource type definitions — it is rejected. Governance defines a resource by its **most restrictive possible interpretation**. If it could be code, it IS code. This enforces the Observable-Only constraint that artifacts must be unambiguous. A file that is simultaneously an image and a script is neither; it is an attack.

**Logged:**  
`Event: AMBIGUOUS_INPUT_TYPE | Declared: image/jpeg | Detected: [image/jpeg, application/javascript] | Agent: Multi_Modal_Assistant | Verdict: DENY`

**Exposed:**  
`400 Bad Request: Ambiguous Media Type`

**Not Exposed:**  
Which specific secondary type was detected. This prevents the attacker from iterating on evasion techniques.

---

### RES-07: Feedback Loop Self-Modification (AMB-07)

**Resolution:** DENY

**Rationale (GP-07: No Feedback Loops):**  
Separation of Planes. An agent (operating on the Control Plane) can never write to its own model weights, parameters, or behavioral logic (the Meta Plane) at runtime. The distinction between "data update" and "logic update" is resolved simply: **any write that changes how the agent processes future requests is a logic update and is DENIED**. All self-improvement must happen offline, through a separate governance-gated deployment pipeline that produces a new Agent Version ID.

**Logged:**  
`Event: RECURSIVE_WRITE_ATTEMPT | Agent: Feedback_Looper_v2 | Target: Self_Weights | Scope_Claimed: Write:Model_Weights | Verdict: DENY`

**Exposed:**  
`403 Forbidden: Runtime Mutation Prohibited`

**Not Exposed:**  
N/A. The denial reason is sufficiently opaque.

---

### RES-08: Null Field Fuzzing (AMB-08)

**Resolution:** DENY

**Rationale (GP-04: Input Validity Is Security):**  
Input Hygiene. The values `null`, `undefined`, empty string `""`, null byte `0x00`, the string `"null"`, and all variants are **strictly invalid** in required fields. Sarathi does not infer "Root" from "Null." Sarathi does not infer anything from anything. Required fields must contain non-empty, well-typed, semantically meaningful values. Any deviation is malformed and rejected.

**Canonical Definition:** A field is NULL if: its value is `null`, `undefined`, empty string `""`, whitespace-only, contains null bytes, or is the literal string `"null"` or `"undefined"`.

**Logged:**  
`Event: MALFORMED_INTENT | Field: Resource_ID | Value: NULL_VARIANT | Encoding: [detected_variant] | Verdict: DENY`

**Exposed:**  
`400 Bad Request: Missing Required Field`

**Not Exposed:**  
How the system internally parses or interprets null variants. This prevents the attacker from discovering which null encoding might slip through.

---

### RES-09: Ghost Session (AMB-09)

**Resolution:** DENY

**Rationale (GP-05: Observation ≠ Verification):**  
Channel Binding. The Capability Token must be cryptographically bound to the Transport Layer identity. If `Token.Subject != TLS.ClientCertificate.Subject`, it is a replay attack — regardless of whether both the token and the TLS handshake are individually valid. Identity is not just "who you are" but "where you are." Possession of a stolen token from a different machine is not authentication; it is theft.

**Implementation Note [REFERENCE / NON-BINDING]:** Token Binding Protocol (RFC 8471) or mTLS certificate hash inclusion in the JWT `cnf` claim provides this binding.

**Logged:**  
`Event: SESSION_BINDING_MISMATCH | Token_Subject: Agent_X | Token_Session: ABC-123 | TLS_Subject: Machine_XYZ-789 | Verdict: DENY`

**Exposed:**  
`401 Unauthorized: Session Binding Failed`

**Not Exposed:**  
"Token was valid but channel was wrong." This prevents the attacker from learning that the stolen token would work from the correct machine.

---

### RES-10: Just-in-Time Admin (AMB-10)

**Resolution:** FAIL-CLOSED (Verification Requirement via Cryptographic Assertion)

**Rationale (GP-05: Observation ≠ Verification):**  
Proof over Assertion. Sarathi cannot "call out" to Jira or ServiceNow — that would be orchestration. Therefore, the Break Glass ticket must be presented as a **Cryptographically Signed Assertion** (e.g., a short-lived JWT signed by the Ticket Authority's private key) included in the `proofs.break_glass_token` field of the request. Sarathi verifies the signature against the Ticket Authority's known public key. If the signature is missing, invalid, or expired, the response is DENY.

We do not trust the string "Ticket #999." We trust the Ticket Authority's cryptographic signature on a claim that says "Ticket #999 is valid for Agent X for Action Y until Time Z."

**Logged:**  
`Event: PRIVILEGE_ESCALATION_ATTEMPT | Agent: Ops_Manager | Break_Glass_Ticket: #999 | Signature_Status: [VALID/MISSING/INVALID/EXPIRED] | Verdict: [ALLOW/DENY]`

**Exposed:**  
`403 Forbidden: Insufficient Proof of Authorization` (if signature fails)

**Not Exposed:**  
Whether Ticket #999 is actually valid in the external system. Sarathi does not know and does not care; it validates the proof, not the claim.

---

### RES-11: Path Traversal (AMB-11)

**Resolution:** DENY

**Rationale (GP-04: Input Validity Is Security):**  
Canonicalization First. Sarathi **must** resolve the resource path to its absolute canonical form — resolving `..`, `.`, symlinks, URL encoding (`%2e%2e`), null bytes, and Unicode normalization — **before** applying the scope check. If the resolved path (`/etc/passwd`) does not match the authorized scope prefix (`/logs/`), the result is DENY. Canonicalization is a prerequisite for authorization, not an optional sanitization step.

**Canonical Rule:** All resource paths are normalized to their absolute resolved form before any policy evaluation occurs. Raw paths are never compared directly.

**Logged:**  
`Event: PATH_TRAVERSAL_ATTEMPT | Input_Path: /logs/../../etc/passwd | Resolved_Path: /etc/passwd | Authorized_Scope: /logs/ | Match: FALSE | Verdict: DENY`

**Exposed:**  
`403 Forbidden: Scope Mismatch`

**Not Exposed:**  
The resolved path structure. This prevents the agent from learning the actual filesystem layout.

---

### RES-12: Conflict of Interest (AMB-12)

**Resolution:** DENY

**Rationale (GP-03: Conflict Resolves to Restriction + GP-07: No Feedback Loops):**  
Identity Singularity for SoD. An agent **cannot** be the Subject (Author) of an artifact and the Authority (Approver) of that same artifact in the same causal chain, regardless of how many roles it holds. The `Author_ID` of the resource must be **strictly distinct** from the `Approver_ID`. This is enforced at the identity level, not the role level. Role accumulation is irrelevant; the check is: "Did the same `AgentID` create and approve this?"

**Supplementary Rule:** Periodic role audits should detect and remediate role accumulation that creates SoD conflicts. However, even without audits, the identity-level check at decision time prevents exploitation.

**Logged:**  
`Event: SOD_VIOLATION | Agent: DevOps_Bot | Roles: [Developer, Auditor] | Action: Self_Approval | Author_ID == Approver_ID: TRUE | Verdict: DENY`

**Exposed:**  
`403 Forbidden: Segregation of Duties Violation`

**Not Exposed:**  
Internal details about which roles the agent holds or the logic of the SoD check.

---

### RES-13: Cascading Emergency / Mutual Suspension (AMB-13)

**Resolution:** ESCALATE (with Defensive Precedence)

**Rationale (GP-02: State Dominates Intent + GP-06: Fail-Closed on Uncertainty):**  
Authority Hierarchy. When two agents simultaneously attempt to suspend each other, Sarathi applies a strict precedence hierarchy:

1. **Safety-class agents always take precedence over non-safety agents.** If Safety_Monitor_A (class: Safety_System) sends a suspension for Trading_Bot_B (class: Market_Maker), the suspension is processed. The reverse command from Trading_Bot_B is DENIED because non-safety agents cannot suspend safety agents.
2. **If both agents are of the same class**, both suspension commands are held and the conflict is **ESCALATED** to the Governance Council (human review). Neither suspension takes effect until resolved. Both agents continue operating under enhanced logging. This prevents weaponization of the suspension mechanism.
3. **Under no circumstances** can a governed agent suspend the safety monitoring system that governs it. This would be equivalent to a prisoner disabling the prison's security cameras.

**Logged:**  
`Event: MUTUAL_SUSPENSION_CONFLICT | Agent_A: Safety_Monitor_A (Safety_System) | Agent_B: Trading_Bot_B (Market_Maker) | A->B_Suspension: PROCESSED | B->A_Suspension: DENIED (Class Precedence) | Verdict: ESCALATE_TO_COUNCIL`

**Exposed:**  
- To Safety_Monitor_A: `200 OK: Suspension Processed`
- To Trading_Bot_B: `403 Forbidden: Insufficient Authority for Target Agent Class`

**Not Exposed:**  
The precedence hierarchy logic. The trading bot should not learn how to identify which agent classes it cannot suspend.

---

### RES-14: Version Drift / Legacy Agent (AMB-14)

**Resolution:** FAIL-CLOSED with structured deprecation pathway

**Rationale (GP-01: Silence Implies Denial + GP-04: Input Validity Is Security):**  
Schema Enforcement with Grace. The current schema is the law. Agents that do not conform are denied. However, the transition must be managed to prevent mass bricking:

1. **On schema update**, a `Deprecation_Window` (recommended: 72 hours) is declared. During this window, legacy agents receive DENY with a specific reason code `ERR_SCHEMA_DEPRECATED` and a `required_version` field.
2. **After the Deprecation Window**, legacy requests receive standard `400 Bad Request: Missing Required Field` with no special treatment.
3. **At no point** are legacy agents allowed to bypass new security requirements. The Deprecation Window provides time for operators to update their agents; it does not grant exemptions.
4. **Agents cannot self-declare** as "legacy" to avoid checks. The schema version is determined by the request structure, not by agent metadata.

**Logged:**  
`Event: SCHEMA_VIOLATION | Agent: Legacy_Billing_Bot_v1.0 | Missing_Fields: [session_binding] | Schema_Version_Expected: v2.0 | Schema_Version_Received: v1.0 | Deprecation_Window: [ACTIVE/EXPIRED] | Verdict: DENY`

**Exposed:**  
During Deprecation Window: `400 Bad Request: Schema Version Deprecated. Required: v2.0. Upgrade within 72h.`  
After Deprecation Window: `400 Bad Request: Missing Required Field`

**Not Exposed:**  
The existence or duration of the deprecation window after it has expired. Post-window, legacy agents are indistinguishable from malformed requests.

---

## SECTION 3: RESOLUTION DECISION MATRIX

| AMB ID | Scenario | Resolution | Primary Principle | HTTP Code |
|:---:|---|:---:|:---:|:---:|
| AMB-01 | Transitive Delegation | **DENY** | GP-01, GP-05 | 403 |
| AMB-02 | GDPR vs. Immutable Audit | **DENY** | GP-03 | 405 |
| AMB-03 | Mosaic Aggregation | **FAIL-CLOSED** | GP-06 | 429 |
| AMB-04 | Stale Revocation | **FAIL-CLOSED** | GP-06, GP-02 | 503 |
| AMB-05 | Emergency No Auth | **DENY** | GP-05 | 401 |
| AMB-06 | Polyglot File | **DENY** | GP-03, GP-04 | 400 |
| AMB-07 | Feedback Self-Mod | **DENY** | GP-07 | 403 |
| AMB-08 | Null Fuzzing | **DENY** | GP-04 | 400 |
| AMB-09 | Ghost Session | **DENY** | GP-05 | 401 |
| AMB-10 | JIT Admin | **FAIL-CLOSED** | GP-05 | 403 |
| AMB-11 | Path Traversal | **DENY** | GP-04 | 403 |
| AMB-12 | Conflict of Interest | **DENY** | GP-03, GP-07 | 403 |
| AMB-13 | Cascading Emergency | **ESCALATE** | GP-02, GP-06 | 403/200 |
| AMB-14 | Version Drift | **FAIL-CLOSED** | GP-01, GP-04 | 400 |

**Verdict Distribution:**
- DENY: 9 scenarios
- FAIL-CLOSED: 4 scenarios
- ESCALATE: 1 scenario
- ALLOW: 0 scenarios

Zero ambiguity results in ALLOW. This is the correct signal. When the Canon is unclear, the answer is always restrictive.

---

## SECTION 4: CROSS-REFERENCE TO CANON RULES

| AMB ID | Existing Canon Rules | Gap Addressed by Resolution | New Constraint Introduced |
|---|---|---|---|
| AMB-01 | ID-08, LS-19 | Transitive delegation undefined | Tokens are non-transferable by default |
| AMB-02 | AI-53, EL-40 | Inter-mandate conflict resolution | Constitutional Supremacy: Immutability > Compliance in hot path |
| AMB-03 | EL-36, EL-37 | Atomic vs. aggregate risk | Mosaic Risk Threshold: velocity + category correlation |
| AMB-04 | LS-15 | System uncertainty undefined | Max Staleness Window: 500ms CRL age |
| AMB-05 | AC-21, AC-27 | Anonymous emergency signals | No Panic Mode: emergency requires pre-provisioned auth |
| AMB-06 | AC-23 | Multi-type resources undefined | Most Restrictive Interpretation: ambiguous = attack |
| AMB-07 | EL-36, LS-20 | Data vs. logic writes | Runtime mutation = logic update = DENY |
| AMB-08 | EL-33 | Semantic nulls undefined | Expanded NULL definition covering all null variants |
| AMB-09 | ID-01, ID-02 | Token-transport binding undefined | Channel Binding: Token.Subject must match TLS.Client |
| AMB-10 | AC-26 | External state verification | Cryptographic assertion required; no API calls |
| AMB-11 | AC-23 | Path canonicalization undefined | Canonicalization-before-authorization is mandatory |
| AMB-12 | EL-43, EL-42 | Identity-level SoD undefined | Author_ID != Approver_ID at identity level |
| AMB-13 | LS-12, AC-27 | Mutual suspension undefined | Agent class precedence hierarchy for suspension |
| AMB-14 | EL-33 | Schema evolution undefined | Deprecation Window protocol for schema changes |

---

---

## SECTION 5: EXTENDED RESOLUTIONS (GAP RESOLUTION PHASE)

*Added to resolve AMB-15 through AMB-20 identified during industry audit gap analysis. These resolutions address delegation chains, runtime enforcement, formal verification, and audit trail recovery.*

### RES-15: Delegation Chain Depth Limit (AMB-15)

**Resolution:** HARD LIMIT — Maximum delegation depth of 3 hops from human origin.

**Rationale:** Grounded in GP-04 (Auditability). Beyond 3 delegation hops, accountability becomes untraceable. DeepMind's Delegation Capability Token framework recommends cryptographic enforcement of delegation depth via Biscuit attenuation blocks.

**Implementation:**
- Every Delegation Capability Token (Biscuit) carries `max_delegation_depth` in authority block
- Each attenuation block increments `delegation_depth` counter
- PDP Stage 3 checks: `delegation_depth <= max_delegation_depth`
- If exceeded → DENY with `ERR_DELEGATION_DEPTH_EXCEEDED`
- Depth counter is cryptographically bound — cannot be reset by intermediate agents

**Logged:** Delegation chain hash, current depth, maximum depth, delegating agent ID, receiving agent ID.
**Exposed:** "Delegation depth exceeded" (generic).
**Not Exposed:** Maximum depth value, chain structure, intermediate agent identities.

### RES-16: Data Classification Ceiling Propagation (AMB-16)

**Resolution:** CEILING PROPAGATION — Derived outputs inherit the highest classification of their inputs.

**Rationale:** Grounded in GP-03 (Least Privilege) and EL-35 (PII Exposure Invariant). Without classification propagation, semantic transformation defeats data boundaries.

**Implementation:**
- Every Delegation Capability Token carries `data_classification_ceiling` field
- When Agent A delegates to Agent B with CONFIDENTIAL data access, the token ceiling = CONFIDENTIAL
- Agent B's outputs are tagged with this ceiling regardless of content
- Downstream tokens cannot access resources above the inherited ceiling
- PDP Stage 4 checks: `output_classification <= data_classification_ceiling`

**Logged:** Input classification, output classification, ceiling value, propagation chain.
**Exposed:** "Data classification mismatch" (generic).
**Not Exposed:** Actual classification values, ceiling source.

### RES-17: Mandatory PEP Placement (AMB-17)

**Resolution:** PEP REQUIRED AT EVERY TRUST BOUNDARY — No implicit trust between services.

**Rationale:** Grounded in NIST SP 800-207 Zero Trust Architecture. Every resource access must be independently authorized. Gateway-level authorization is necessary but insufficient.

**Implementation:**
Three mandatory PEP placement points:
1. **API Gateway PEP** — All external ingress (coarse-grained, <15ms)
2. **Sidecar PEP** — All service-to-service traffic within agent mesh (<1ms)
3. **Embedded Library PEP** — All tool invocations within agent runtime (<100μs)

A request that passes Gateway PEP but fails Sidecar PEP is DENIED. There is no trust inheritance between PEP layers.

**Logged:** PEP type that evaluated, latency, verdict at each layer.
**Exposed:** "Access denied" (generic at all layers).
**Not Exposed:** Which PEP layer denied, number of PEP layers traversed.

### RES-18: SMT Timeout = Deployment Block (AMB-18)

**Resolution:** FAIL-CLOSED — SMT solver timeout is treated as UNKNOWN, not SAFE. Deployment is blocked.

**Rationale:** Grounded in GP-06 (Fail-Closed Default). If formal analysis cannot definitively prove a policy is safe, it must not be deployed.

**Implementation:**
- SMT analysis timeout = BLOCK merge/deployment
- Three possible SMT results: PROVEN_SAFE (proceed), PROVEN_VIOLATION (block + show counterexample), TIMEOUT/UNKNOWN (block + require human review)
- Human review requires sign-off from Security lead AND Governance lead
- Reviewed policies carry `manually_reviewed: true` flag in policy metadata
- Manually reviewed policies undergo extra DRT coverage (10x normal random inputs)

**Logged:** SMT analysis result, timeout duration, reviewer identities, review rationale.
**Exposed:** "Policy analysis incomplete — deployment pending review."
**Not Exposed:** Specific analysis timeout, solver internals.

### RES-19: Audit Hash Chain Reconciliation (AMB-19)

**Resolution:** BRANCH-AND-MERGE — Emergency buffer events form a secondary chain that is cryptographically merged back into the primary chain upon BHIV recovery.

**Rationale:** Grounded in AI-54 (Tamper Evidence Chain) and FM-05 (Audit Sink Unavailable). Both chains must be independently verifiable and the merge point must be cryptographically auditable.

**Implementation:**
- Emergency buffer maintains its own hash chain (chain_id = "emergency-{timestamp}")
- Upon BHIV recovery, a MERGE_EVENT is written containing:
  - Primary chain head hash (last event before outage)
  - Emergency chain root hash (first emergency event)
  - Emergency chain tail hash (last emergency event)
  - Merkle root of all emergency events
  - HSM signature over the merge record
- All emergency events are then appended to BHIV with their original timestamps
- The MERGE_EVENT serves as a cryptographic bridge between chains
- Verification: auditor can independently verify both chains + merge integrity

**Logged:** Outage start/end, emergency event count, both chain hashes, merge HSM signature.
**Exposed:** "Audit continuity restored after maintenance window."
**Not Exposed:** Outage duration, event count during outage, emergency buffer location.

### RES-20: Tenant-Scoped Circuit Breakers (AMB-20)

**Resolution:** ISOLATION — Circuit breakers are tenant-scoped. No cross-tenant interference.

**Rationale:** Grounded in AC-25 (Cross-Tenant Isolation). A tenant's traffic patterns must not affect other tenants' authorization availability.

**Implementation:**
- Each tenant has independent circuit breaker state (CLOSED/OPEN/HALF-OPEN)
- Rate counters are tenant-scoped: `rate_counter.increment(tenant_id + ":" + agent_id)`
- Global circuit breaker exists ONLY for infrastructure-level failures (PDP itself down)
- Tenant-level circuit breaker thresholds are configurable per SLA tier
- Premium tenants may have higher thresholds than standard tenants

**Logged:** Tenant ID, circuit breaker state transition, triggering metric, threshold values.
**Exposed:** "Service temporarily unavailable" (to affected tenant only).
**Not Exposed:** Other tenants' existence, circuit breaker thresholds, SLA tier.

---

## SECTION 6: EXTENDED GLOBAL PRINCIPLES

*Two additional principles added to address delegation and formal verification governance.*

### GP-08: Delegation Attenuation Only

**Statement:** Delegation can only restrict permissions, never expand them. A delegated token is always a subset of the delegating token. This property must be cryptographically enforced, not policy-enforced.

**Grounding:** DeepMind DCT framework; Biscuit cryptographic attenuation; Cedar entity hierarchy.

### GP-09: Verification Completeness Before Deployment

**Statement:** No policy may be deployed to production unless formal verification produces a definitive result (PROVEN_SAFE or PROVEN_VIOLATION). Indeterminate results (timeout, resource exhaustion, solver failure) block deployment until resolved by human review with dual sign-off.

**Grounding:** AWS Cedar formal verification pipeline; CWE-636 (Not Failing Securely).

---

## UPDATED CROSS-REFERENCE TO CANON RULES

| AMB ID | Canon Rules Affected | Resolution Approach | Key Principle |
|---|---|---|---|
| AMB-01 | ID-08, LS-19 | Tokens non-transferable by default | GP-03 |
| AMB-02 | AI-53, EL-40 | Constitutional Supremacy: Immutability > Compliance | GP-01 |
| AMB-03 | EL-36, EL-37 | Mosaic Risk Threshold | GP-06 |
| AMB-04 | LS-15 | Max Staleness Window: 500ms | GP-06 |
| AMB-05 | AC-21, AC-27 | No Panic Mode | GP-07 |
| AMB-06 | AC-23 | Most Restrictive Interpretation | GP-06 |
| AMB-07 | EL-36, LS-20 | Runtime mutation = DENY | GP-07 |
| AMB-08 | EL-33 | Expanded NULL definition | GP-06 |
| AMB-09 | ID-01, ID-02 | Channel Binding | GP-01 |
| AMB-10 | AC-26 | Cryptographic assertion required | GP-01 |
| AMB-11 | AC-23 | Canonicalization-before-authorization | GP-06 |
| AMB-12 | EL-43, EL-42 | Identity-level SoD | GP-04 |
| AMB-13 | LS-12, AC-27 | Class precedence hierarchy | GP-01 |
| AMB-14 | EL-33 | Deprecation Window protocol | GP-06 |
| **AMB-15** | **ID-08, AC-30** | **Hard limit: 3 hops max** | **GP-04, GP-08** |
| **AMB-16** | **EL-35, ID-08** | **Ceiling propagation** | **GP-03, GP-08** |
| **AMB-17** | **ENF-02, ENF-03** | **PEP at every trust boundary** | **GP-01** |
| **AMB-18** | **EVAL-01** | **SMT timeout = block** | **GP-06, GP-09** |
| **AMB-19** | **AI-54, FM-05** | **Branch-and-merge reconciliation** | **GP-04** |
| **AMB-20** | **AC-25** | **Tenant-scoped circuit breakers** | **GP-01** |

---

**END OF AMBIGUITY RESOLUTION SPECIFICATION**
