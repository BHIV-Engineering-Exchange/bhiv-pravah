# SARATHI ENFORCEMENT MODEL SPECIFICATION

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel — Policy Decision Point  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Task 4 — Sarathi PDP Minimal Implementation Specification (Day 5)  
**Upstream Dependencies:**  
- `sarathi_request_schema.md` (Task 4 — Day 1)  
- `sarathi_response_schema.md` (Task 4 — Day 2)  
- `evaluation_order_spec.md` (Task 4 — Day 3)  
- `failure_mode_contract.md` (Task 4 — Day 4)  
- `SARATHI_PDP_INTERFACE.md` — Sections 6.1-6.10 "Never Assume" Rules (Task 3)  
- `GOVERNANCE_VALIDATION_REPORT.md` — Assumption A3 (Orchestrator Compliance) (Task 1)  
- `SARATHI_HIGH_DENSITY_CANON_FORMALIZATION.md` — MF-02 (Downstream Validation), 60 Rules (Task 2)  
- `AMBIGUITY_RESOLUTION_SPEC.md` — 7 Global Principles (Task 3)  
- Sarathi PDP Research Report — Capability-Based Enforcement, Confused Deputy, Logging Insufficiency

---

## PURPOSE

This document defines the **Enforcement Boundary** — the architectural mechanism by which Sarathi makes governance decisions **physically binding** rather than merely advisory.

All previous specifications (Days 1-4) define WHAT the PDP decides and HOW it decides. This specification defines WHY those decisions CANNOT be ignored. It answers the fundamental question that separates real governance from governance theater:

> **If the PDP says DENY, what physically prevents the agent from acting anyway?**

The answer is the **capability token model**: the PDP does not merely say "yes" or "no" — it issues a cryptographic key on "yes" and nothing on "no." Downstream resources require this key to execute. Without the key, the action physically cannot proceed. This converts governance from a **detective control** (logging violations after they occur) to a **preventive control** (blocking violations before they execute).

This is the resolution of **Assumption A3 (Orchestrator Compliance)** from the Governance Validation Report (Task 1): "A compromised or hallucinating LLM orchestrator might just ignore the refusal. Without cryptographic enforcement, refusal is theater. Fix: Capability tokens that are required to unlock resources."

**Constitutional Authority:**
- **GP-05 (Observation ≠ Verification):** Claims of authorization are noise; only cryptographic proofs are data.
- **Canon MF-02:** "Downstream Resource Servers MUST validate Sarathi-issued tokens. Governance logic is sound; enforcement depends on token verification."
- **Canon Section 6.9:** "Never Ignore the Signature."
- **Canon Section 6.5:** "Never Cache ALLOW Verdicts."

**Industry Grounding:**
- Norm Hardy, "The Confused Deputy" (1988) — why ambient authority enables bypass
- Tyler Close, "ACLs Don't" (2009) — formal proof that capabilities are necessary for multi-principal delegation
- Dennis & Van Horn (1966) — capability-based security foundations
- NIST SP 800-207 — Zero Trust Architecture (inline enforcement)
- RFC 9449 (DPoP) — proof-of-possession token binding
- RFC 9635 (GNAP) — key-bound tokens as default
- Google Macaroons — contextual caveats with attenuation-only delegation
- UCAN Specification — DID-based capability delegation chains
- AWS Cedar — forbid-overrides-permit with formal verification
- SPIFFE/SPIRE — workload identity with short-lived SVIDs

---

## TABLE OF CONTENTS

1. [The Enforcement Problem](#1-the-enforcement-problem)
2. [Advisory vs. Enforcement Governance](#2-advisory-vs-enforcement-governance)
3. [The Capability Token Model](#3-the-capability-token-model)
4. [Signature Verification Expectation](#4-signature-verification-expectation)
5. [Downstream Resource Validation Requirement](#5-downstream-resource-validation-requirement)
6. [Why Logging Alone Is Insufficient](#6-why-logging-alone-is-insufficient)
7. [The Three Enforcement Layers](#7-the-three-enforcement-layers)
8. [Bypass Prevention — Attack Surface Analysis](#8-bypass-prevention--attack-surface-analysis)
9. [Enforcement Invariants](#9-enforcement-invariants)
10. [The Enforcement Contract — Obligations of Each Party](#10-the-enforcement-contract--obligations-of-each-party)

---

## 1. THE ENFORCEMENT PROBLEM

### 1.1 Why Governance Decisions Need Physical Enforcement

Consider the simplest possible governance architecture:

```
AGENT → "Can I read /secrets?" → PDP → "No." → AGENT → reads /secrets anyway
```

The PDP said "no." The agent ignored it. The governance decision was correct but had zero effect. This is the **advisory governance failure mode** — the governance system detects what should happen but cannot enforce it.

This is not a theoretical problem. It is the default architecture of most AI agent systems today. Per the research report: "Audit logs are classified as detective controls — they identify violations after they occur. Preventive controls stop violations before they happen. An unauthorized agent action has already been executed by the time it appears in a log."

### 1.2 The Assumption A3 Threat

From Task 1, Governance Validation Report:

> **A3: Orchestrator Compliance** — "If Sarathi says no, the orchestrator will actually stop."
> **Assessment: UNSAFE.** A compromised or hallucinating LLM orchestrator might just ignore the refusal. Without cryptographic enforcement, refusal is theater.

The threat model includes:
- **Compromised orchestrator:** Malware, prompt injection, or supply chain attack causes the orchestrator to ignore DENY verdicts.
- **Hallucinating orchestrator:** An LLM-based orchestrator incorrectly interprets a DENY as a "soft suggestion" and proceeds.
- **Buggy orchestrator:** An implementation error in the orchestrator's PDP client causes it to treat network errors as ALLOW (fail-open).
- **Malicious agent:** An agent directly calls the downstream resource, bypassing the orchestrator and PDP entirely.

In all four scenarios, the PDP's DENY verdict is structurally irrelevant because nothing enforces it.

### 1.3 The Solution: Cryptographic Enforcement

Sarathi solves this with a **capability token model**:

```
AGENT → "Can I read /secrets?" → PDP → "No." → AGENT has no key → /secrets rejects

AGENT → "Can I read /public?"  → PDP → "Yes, here is your key [token]."
→ AGENT presents key to /public → /public verifies key → Access granted
```

The critical difference: the downstream resource (`/secrets`, `/public`) requires a cryptographic key to unlock. The PDP is the only entity that can issue this key. Without the key, the resource physically rejects the request — regardless of what the agent claims, what the orchestrator says, or what the request looks like.

This converts the PDP from an **advisor** to a **gatekeeper**. The agent cannot bypass the gatekeeper because the gatekeeper holds the only key.

---

## 2. ADVISORY VS. ENFORCEMENT GOVERNANCE

### 2.1 The Two Governance Architectures

| Property | Advisory Governance | Enforcement Governance (Sarathi) |
|---|---|---|
| **PDP Output** | ALLOW/DENY flag | Cryptographic capability token (on ALLOW) or nothing (on DENY) |
| **Enforcement Point** | The caller (orchestrator) decides whether to obey | The downstream resource requires the token to execute |
| **Bypass Mechanism** | Caller ignores the flag | No bypass — token is required by resource |
| **Trust Requirement** | Caller must be trusted to obey | Caller need NOT be trusted — resource enforces |
| **Control Type** | Detective (logs violation after the fact) | Preventive (blocks violation before execution) |
| **Failure Mode** | Rogue caller proceeds unimpeded | Rogue caller is rejected by resource |
| **Analogy** | Security guard who says "stop" | Locked door that only opens with a specific key |
| **Industry Example** | OPA returning true/false | Google Macaroons, UCAN delegation tokens, AWS SigV4 |

### 2.2 Why Advisory Governance Fails for AI Agents

AI agents introduce unique challenges that make advisory governance structurally inadequate:

1. **Speed of action:** Agents act at millisecond timescales. Between a logged violation and human intervention, thousands of unauthorized operations may complete. Per the research report: "In agentic AI, actions occur at millisecond timescales; by the time a log is analyzed, hundreds of unauthorized operations may have completed."

2. **Prompt injection:** A malicious instruction injected into an agent's context can cause it to use its ambient authority for unintended purposes. Advisory governance detects this after the fact. Enforcement governance blocks the unauthorized tool call because the injected intent doesn't carry a valid capability token.

3. **Confused deputy:** Per Hardy (1988), an agent carrying both its own authority and delegated user intent cannot distinguish between them. "Under traditional IAM, every long-running agent is a confused deputy by design" (research report). Capability tokens solve this structurally — authority is explicit, not ambient.

4. **Irreversibility:** Some agent actions (data deletion, financial transactions, confidential data exfiltration) cannot be undone. Detecting them after the fact is too late. Only preventive controls are adequate.

---

## 3. THE CAPABILITY TOKEN MODEL

### 3.1 What a Capability Token Is

A capability token is a **cryptographically signed, time-bounded, scope-restricted, single-use JWT** that combines two properties from Dennis and Van Horn's 1966 definition:

- **Designation:** It identifies a specific resource (`aud` claim).
- **Authorization:** It specifies what operations are permitted (`sarathi_claims.action`, `sarathi_claims.resource_id`, `sarathi_claims.parameters_hash`).

Possessing a valid capability token is both NECESSARY and SUFFICIENT to access the referenced resource. This is the core tenet of capability-based security: "Don't separate designation from authority."

### 3.2 Token Structure (From Day 2, Section 6.2)

```json
{
  "header": {
    "alg": "EdDSA",
    "typ": "JWT",
    "kid": "sarathi-pdp-signing-key-2026-02"
  },
  "payload": {
    "iss": "sarathi.governance.bhiv.io",
    "sub": "<agent_id>",
    "aud": "<resource_type>:<resource_id>",
    "exp": "<timestamp + MAX_TOKEN_TTL (60s)>",
    "nbf": "<timestamp>",
    "iat": "<timestamp>",
    "jti": "<unique token ID, UUIDv4>",

    "sarathi_claims": {
      "correlation_id": "<from request>",
      "audit_id": "<from response>",
      "action": "<authorized action verb>",
      "resource_type": "<authorized resource type>",
      "resource_id": "<authorized resource ID>",
      "parameters_hash": "<sha256 of action parameters>",
      "data_classification": "<PDP-verified classification>",
      "risk_assessment": "<PDP-determined risk level>",
      "session_binding": "<TLS cert hash>",
      "delegation_chain_hash": "<hash of verified chain>",
      "obligations": ["<obligation_ids>"],
      "policy_version_hash": "<policy bundle used>"
    }
  },
  "signature": "<EdDSA signature>"
}
```

### 3.3 Why This Token Model Prevents Bypass

| Attack | How Advisory Fails | How Capability Token Prevents |
|---|---|---|
| **Rogue orchestrator ignores DENY** | Orchestrator proceeds without authorization | Resource requires token; orchestrator has none; request rejected |
| **Agent calls resource directly, bypassing PDP** | Resource doesn't know PDP exists | Resource requires token; agent has none; request rejected |
| **Stolen token replayed** | N/A (no token in advisory model) | Token is bound to: (1) specific agent (`sub`), (2) specific TLS session (`session_binding`), (3) specific parameters (`parameters_hash`), (4) single use (`jti` dedup). Replay fails on binding mismatch. |
| **Token used for different action** | N/A | Token scope is locked to exact action + resource + parameters. Different action = different parameters_hash = rejection |
| **Token used after revocation** | N/A | Token TTL = 60 seconds max (MF-05). Even if revocation takes 500ms to propagate, the token expires naturally in ≤60s |
| **Forged token** | N/A | Ed25519 signature verification. Forging requires PDP's private key (stored in HSM per Canon Readiness Condition 5) |
| **Prompt injection changes agent intent** | Agent uses ambient authority for unauthorized action | Token was issued for the ORIGINAL intent. The injected intent has a different parameters_hash. Resource rejects the mismatch. |

### 3.4 The Attenuation Property

Per Tyler Close's formal proof in "ACLs Don't" (2009): capabilities can be **attenuated** (restricted) but never **amplified** (expanded). This means:

- A human user's delegation token grants scopes X, Y, Z.
- The agent's capability token can include scopes X, Y (subset) — never scopes X, Y, Z, W (superset).
- The token issued by the PDP can further restrict: only scope X for this specific resource, this specific action, this specific 60-second window.

Authority only shrinks through each layer of the system. At no point can any entity create more authority than it received. This is the fundamental invariant that makes capability-based governance sound for delegation-heavy agentic systems.

### 3.5 How This Differs from ACL-Based Approaches

| Property | ACL (Access Control List) | Capability Token (Sarathi) |
|---|---|---|
| Where authority is stored | On the resource (who can access me?) | In the token (what can I access?) |
| Authority model | Ambient — identity implies permission | Explicit — token carries permission |
| Delegation | Requires centralized ACL update | Token holder can attenuate and pass |
| Confused deputy | Structural vulnerability (Hardy 1988) | Structurally prevented (Close 2009) |
| Revocation | Update ACL everywhere | Short-lived tokens (60s) + CRL |
| Multi-principal safety | Unsafe for >2 principals (proven in Close 2009) | Safe for arbitrary delegation chains |
| Verification | Resource queries central authority | Resource verifies token locally (offline) |

The critical insight from the research: "ACL-based systems cannot make correct access decisions for interactions involving more than two principals." Since Sarathi governs multi-agent systems with delegation chains (human → orchestrator → agent → sub-agent), ACLs are structurally inadequate. Capability tokens are the only sound model.

---

## 4. SIGNATURE VERIFICATION EXPECTATION

### 4.1 What Must Be Verified

Two signatures exist in the Sarathi enforcement model:

| Signature | Who Signs | Who Verifies | What It Covers | If Verification Fails |
|---|---|---|---|---|
| **Response signature** | PDP signs with its Ed25519 private key | Orchestrator/PEP verifies with PDP's public key | The entire response envelope (verdict, rules, audit_id) | Treat response as DENY (per Canon Section 6.9) |
| **Capability token signature** | PDP signs with its Ed25519 private key | Downstream resource verifies with PDP's public key | The token payload (all claims) | Reject the request (resource-side enforcement) |

### 4.2 Response Signature Verification (Orchestrator-Side)

Per Day 2, Section 9:

```
1. Receive response from PDP
2. Extract the `signature` field
3. Remove `signature` from the response JSON
4. Canonicalize remaining JSON (deterministic key order, no whitespace, UTF-8 NFC)
5. Verify Ed25519 signature using PDP's public key
6. IF verification FAILS → treat as DENY (do not proceed)
7. IF verification SUCCEEDS → read `verdict` field and act accordingly
```

**Why this matters:** Without response verification, a man-in-the-middle (MITM) attacker could intercept a DENY response from the PDP and replace it with an ALLOW response containing a forged capability token. The orchestrator, not verifying the signature, would proceed with the forged ALLOW. Response signing makes this attack detectable.

### 4.3 Capability Token Signature Verification (Resource-Side)

Per Day 2, Section 6.4:

```
1. Receive request from agent/orchestrator with capability token
2. Extract JWT from request
3. Verify EdDSA signature using PDP's public key
4. Verify `exp` is in the future (not expired)
5. Verify `aud` matches this resource's identifier
6. Verify `sarathi_claims.action` matches the requested action
7. Verify `sarathi_claims.resource_id` matches the requested resource
8. Verify `sarathi_claims.parameters_hash` matches SHA-256 of actual parameters
9. Verify `sarathi_claims.session_binding` matches TLS client cert hash
10. Verify `jti` has not been seen before (single-use)
11. Fulfill all obligations in `sarathi_claims.obligations`
12. IF ANY check fails → REJECT (do not execute)
13. IF ALL checks pass → EXECUTE the authorized action
```

**Steps 6-8 implement TOCTOU prevention (CWE-367):** The token was issued for a specific action on a specific resource with specific parameters. If any of these change between authorization and execution, the token is invalid. This eliminates the race condition window.

**Step 9 implements channel binding (RES-09):** The token is bound to the specific TLS session. Even if the token is intercepted, it cannot be used from a different connection.

**Step 10 implements single-use enforcement:** A token that has been used once cannot be reused. This prevents replay at the resource level, complementing the PDP-level deduplication (INV-09).

### 4.4 Key Distribution Model

| Parameter | Specification | Rationale |
|---|---|---|
| Algorithm | Ed25519 (EdDSA) | Deterministic (no nonce reuse risk), fast (62,000 verify/sec), compact (64-byte signatures) |
| Key rotation | Every 90 days minimum | Limits blast radius of key compromise |
| Key distribution | PDP public key distributed to ALL orchestrators and ALL downstream resources via secure out-of-band channel (NOT via the PDP itself) | If PDP distributes its own key, a compromised PDP distributes a compromised key |
| Key storage | PDP private key in HSM (per Canon Readiness Condition 5) | Private key must never be extractable from hardware |
| Rollover | During rotation, both old and new keys are valid for a transition window (equal to MAX_TOKEN_TTL = 60s) | Tokens signed with the old key that are still within TTL must remain verifiable |
| Revocation | If PDP signing key is compromised, ALL outstanding tokens are invalid. Emergency key rotation + full re-authentication required | Key compromise is a governance-critical incident |

---

## 5. DOWNSTREAM RESOURCE VALIDATION REQUIREMENT

### 5.1 The Resource as Enforcement Point

In the Sarathi model, the **downstream resource is the final enforcement point**. The PDP makes the decision. The orchestrator forwards the token. But the resource is the entity that actually grants or denies access to the protected asset. The resource is the lock; the token is the key.

This means that **resource-side validation is non-optional**. A downstream resource that accepts requests without verifying capability tokens is a governance bypass. Per Canon MF-02: "Downstream Resource Servers MUST validate Sarathi-issued tokens. Governance logic is sound; enforcement depends on token verification."

### 5.2 The Eleven Mandatory Resource-Side Checks

These are the checks from Section 4.3, formalized as a resource-side contract. Failure of ANY check means the request is rejected — the resource does NOT call the PDP to "re-check."

| Check # | What Is Verified | What It Prevents | If Failed |
|:---:|---|---|---|
| **R-01** | Ed25519 signature on JWT is valid against PDP's public key | Forged tokens | REJECT |
| **R-02** | `exp` is in the future | Expired tokens | REJECT |
| **R-03** | `aud` matches this resource's identifier | Token targeting different resource (cross-resource replay) | REJECT |
| **R-04** | `sarathi_claims.action` matches the actual requested action | Action substitution (authorized READ, executing DELETE) | REJECT |
| **R-05** | `sarathi_claims.resource_id` matches the actual target resource | Resource substitution (authorized /public, accessing /secrets) | REJECT |
| **R-06** | `sarathi_claims.parameters_hash` matches SHA-256(actual parameters) | Parameter substitution / TOCTOU (CWE-367) | REJECT |
| **R-07** | `sarathi_claims.session_binding` matches SHA-256(TLS client cert) | Token theft (replaying from different connection) | REJECT |
| **R-08** | `jti` not seen before in dedup store | Token replay | REJECT |
| **R-09** | All obligations in `sarathi_claims.obligations` can be fulfilled | Obligation bypass (ALLOW was conditional on obligations) | REJECT (treat as DENY per XACML obligation model) |
| **R-10** | `nbf` (not before) is in the past | Premature token use | REJECT |
| **R-11** | `iss` is the expected Sarathi PDP issuer | Token from rogue/compromised PDP instance | REJECT |

### 5.3 What the Resource Must NOT Do

| Prohibited Action | Why Prohibited |
|---|---|
| Accept requests without a capability token | Governance bypass — any request without a token is unauthorized |
| Accept tokens with invalid or missing signatures | Forgery bypass — unsigned tokens are indistinguishable from attacker-generated tokens |
| Call the PDP to "re-verify" a token | The PDP is a decision authority, not a verification service. The token is self-contained proof. Re-verification creates a circular dependency and a DoS vector. |
| Cache token validity | A token that was valid 1 second ago may have been revoked. Each presentation requires full verification per Canon Section 6.5 |
| Accept tokens addressed to other resources | Cross-resource replay — a token for `/public` cannot be used on `/secrets` |
| Log the full token in plaintext | The token is a bearer credential. Logging it enables insider extraction from audit logs (per Day 2, TI-14) |
| Accept a "master token" or "admin override" | Per Canon Section 6.6: "God Mode does not exist in a sovereign system." There is no token that bypasses verification. |
| Ignore obligation fulfillment failures | Per XACML: if a PEP cannot fulfill an obligation, it MUST treat the verdict as DENY. Obligations are mandatory, not advisory. |

### 5.4 Resource Registration and Compliance

For the enforcement boundary to hold, every downstream resource must:

1. **Register with the Sarathi Resource Registry** with its `resource_type` and `resource_id`.
2. **Hold the PDP's current public key** (distributed via secure out-of-band channel).
3. **Implement the 11-check verification** (Section 5.2) as a mandatory pre-execution gate.
4. **Maintain a jti dedup store** to prevent token replay.
5. **Report verification failures** to the BHIV Bucket for audit (anomaly signal).
6. **Never provide a "bypass mode"** for testing, debugging, or emergencies. The break-glass protocol flows THROUGH Sarathi (per Canon AC-26/AC-27 and RES-05), not around it.

---

## 6. WHY LOGGING ALONE IS INSUFFICIENT

### 6.1 The Detective vs. Preventive Control Distinction

Security controls exist on a spectrum:

| Control Type | When It Acts | What It Achieves | Example |
|---|---|---|---|
| **Preventive** | Before the action | Blocks unauthorized action from executing | Locked door, capability token requirement |
| **Detective** | After the action | Identifies that an unauthorized action occurred | Security camera, audit log |
| **Corrective** | After detection | Undoes or mitigates the damage | Restoring from backup, revoking access |

Logging is a **detective control**. It records what happened. It does not prevent what happened.

### 6.2 The Governance Gap

The gap between "detecting a violation" and "preventing a violation" is where damage accumulates. For AI agents, this gap is measured in milliseconds.

```
Timeline of an Advisory Governance Failure:

t=0ms    Agent requests DELETE /critical-data
t=1ms    PDP evaluates → DENY
t=2ms    Orchestrator receives DENY but ignores it (compromised/buggy)
t=3ms    Agent sends DELETE to /critical-data
t=4ms    /critical-data executes DELETE (no token requirement)
t=5ms    Audit log records the DENY from the PDP
t=100ms  Monitoring system reads audit log
t=200ms  Alert fires: "DELETE executed despite DENY"
t=500ms  Security team investigates
t=???    Data is already gone. Irreversible.
```

With enforcement governance:

```
Timeline of Enforcement Governance:

t=0ms    Agent requests DELETE /critical-data
t=1ms    PDP evaluates → DENY (no token issued)
t=2ms    Orchestrator receives DENY (with or without compliance)
t=3ms    Agent sends DELETE to /critical-data WITHOUT a token
t=4ms    /critical-data checks for capability token → NONE → REJECT
t=5ms    Data is safe. Action never executed.
```

The difference: in enforcement governance, the damage never occurs. In advisory governance, the damage occurs and is only detected afterward.

### 6.3 Five Specific Scenarios Where Logging Fails

| Scenario | Why Logging Is Insufficient | Why Enforcement Prevents |
|---|---|---|
| **Data exfiltration** | Agent copies confidential data to an external endpoint. Log shows the copy. Data is already leaked. | Without token, the source resource rejects the READ. Data never leaves. |
| **Financial transaction** | Agent executes unauthorized trade. Log shows the trade. Money is already moved. | Without token, the trading API rejects the EXECUTE. No trade occurs. |
| **Cascading deletions** | Agent deletes audit records, then critical data. Log of the first deletion is also deleted. | Without token for DELETE on BHIV_BUCKET (which is NEVER issued per Canon AI-53), audit records are safe. |
| **Prompt injection** | Injected instruction causes agent to access restricted data. Log shows access. Data is already read. | Token was issued for original intent (different parameters_hash). Injected intent has no matching token. Resource rejects. |
| **Race condition** | Agent is revoked but executes one last action before revocation propagates. Log shows post-revocation access. | Token expires in ≤60s. If revoked mid-token, resource-side jti dedup and short TTL limit the window. |

### 6.4 The Audit Trail Is Necessary But Not Sufficient

This section does NOT argue that logging is unnecessary. The BHIV Bucket (write-only audit) is a critical component of Sarathi's governance architecture. Per Day 4 (FM-05): if audit writes fail, the verdict is DENY. Logging provides:

- **Forensic reconstruction:** After an incident, logs enable understanding what happened.
- **Compliance evidence:** EU AI Act Article 12 requires automatic event logging.
- **Anomaly detection:** Patterns in logs enable detection of sophisticated multi-step attacks.
- **Accountability:** Logs establish who authorized what, when, and why.

But logging does not PREVENT. It documents. The enforcement boundary (capability token + resource-side validation) PREVENTS. Together they provide both prevention and detection — the complete security posture.

---

## 7. THE THREE ENFORCEMENT LAYERS

Sarathi implements **defense in depth** through three enforcement layers. Each layer independently prevents a class of bypass. All three must be compromised for governance to fail.

### Layer 1: PDP Inline Enforcement

```
AGENT → [Request] → ORCHESTRATOR → [Request Envelope] → PDP
                                                          │
                                           DENY ← ────── │ ──── → ALLOW + Token
```

**What it prevents:** Unauthorized requests reaching the evaluation pipeline.
**Mechanism:** The PDP sits INLINE in the request path. Requests physically cannot proceed without passing through the PDP.
**If bypassed:** Layer 2 catches it (resource requires token).

### Layer 2: Resource-Side Token Verification

```
AGENT/ORCHESTRATOR → [Action + Token] → DOWNSTREAM RESOURCE
                                                │
                                        Token valid? ── NO → REJECT
                                                │
                                               YES → EXECUTE
```

**What it prevents:** Unauthorized requests reaching the resource even if Layer 1 is bypassed.
**Mechanism:** The downstream resource requires a valid capability token. Without it, the resource rejects the request regardless of what the caller claims.
**If bypassed:** Layer 3 catches it (audit trail detects the anomaly).

### Layer 3: Audit Trail and Post-Hoc Detection

```
PDP → [Decision Log] → BHIV BUCKET (Write-Only)
RESOURCE → [Execution Log] → BHIV BUCKET (Write-Only)
                                      │
                                MONITORING → Alert on anomalies
```

**What it prevents:** Violations from going undetected.
**Mechanism:** Every PDP decision and every resource execution is logged. Correlation IDs link them. Missing correlations (decision without execution, or execution without decision) are anomalies.
**If bypassed:** This is the last line of defense. If all three layers fail, governance has been completely compromised.

### Defense in Depth Property

| Layer | Type | What It Catches | Dependency |
|---|---|---|---|
| Layer 1 (PDP Inline) | Preventive | All unauthorized requests that pass through the orchestrator | Orchestrator correctly forwards to PDP |
| Layer 2 (Resource Token) | Preventive | Requests that bypass the orchestrator or ignore PDP denial | Resource implements token verification |
| Layer 3 (Audit Trail) | Detective | Violations that somehow bypassed both Layer 1 and Layer 2 | BHIV Bucket is write-only and available |

**The key insight:** Layer 2 does NOT depend on Layer 1 behaving correctly. Even if the orchestrator is fully compromised and never contacts the PDP, Layer 2 still blocks unauthorized access because the resource demands a token that only the PDP can issue. This is the structural guarantee that makes enforcement robust against orchestrator compromise (A3).

---

## 8. BYPASS PREVENTION — ATTACK SURFACE ANALYSIS

This section enumerates every known bypass vector and demonstrates that the enforcement model prevents each one.

### 8.1 Direct Resource Access (Bypass PDP and Orchestrator)

**Attack:** Agent discovers the downstream resource's network address and calls it directly, bypassing both the orchestrator and the PDP.

**Prevention:**
- The resource requires a capability token (Layer 2). The agent has none.
- Per NIST SP 800-207A: resources should be accessible ONLY via the enforcement proxy (service mesh sidecar pattern). Direct network access is blocked at the infrastructure level.
- Per Canon Section 6.6: no resource provides a "bypass mode."

### 8.2 Orchestrator Ignoring DENY

**Attack:** A compromised orchestrator receives a DENY verdict but proceeds to forward the agent's request to the resource.

**Prevention:**
- The orchestrator has no capability token to forward (DENY produces no token).
- The resource rejects the request (no token = no access).
- The audit trail shows: PDP logged DENY, but the resource logs an unauthenticated access attempt. This correlation anomaly triggers an alert.

### 8.3 Forged Capability Token

**Attack:** An attacker constructs a fake capability token with ALLOW claims and presents it to the resource.

**Prevention:**
- The token must carry a valid Ed25519 signature (R-01).
- The PDP's private key is in an HSM — the attacker cannot extract it.
- Ed25519 forgery requires solving the discrete logarithm problem on Curve25519 — computationally infeasible.

### 8.4 Token Replay from Different Channel

**Attack:** Attacker intercepts a valid token and presents it from a different TLS session.

**Prevention:**
- `session_binding` in the token contains the SHA-256 of the original TLS client certificate (R-07).
- The attacker's TLS session has a different certificate → hash mismatch → REJECT.
- Per RFC 9449 (DPoP): proof-of-possession binds the token to the client's cryptographic identity.

### 8.5 Token Reuse (Replay Same Channel)

**Attack:** Agent uses the same token twice to execute the action twice.

**Prevention:**
- `jti` (JWT ID) dedup store at the resource (R-08). Second presentation is rejected.
- Tokens are single-use by contract (Day 2, TI-10).

### 8.6 Parameter Substitution (TOCTOU)

**Attack:** Agent requests authorization for `READ /public`, receives a token, then uses the token to execute `DELETE /secrets`.

**Prevention:**
- Token's `sarathi_claims.action` = READ. Resource checks against actual request action (DELETE). Mismatch → REJECT (R-04).
- Token's `sarathi_claims.resource_id` = /public. Resource checks against actual target (/secrets). Mismatch → REJECT (R-05).
- Token's `sarathi_claims.parameters_hash` = SHA-256 of READ /public parameters. Resource computes SHA-256 of DELETE /secrets parameters. Hash mismatch → REJECT (R-06).
- Three independent checks prevent three different dimensions of substitution.

### 8.7 Token Scope Amplification

**Attack:** Agent receives a token scoped to READ /data/public and attempts to use it for READ /data/*.

**Prevention:**
- Token's `sarathi_claims.resource_id` is `/data/public` — not a wildcard.
- Resource verifies exact match (R-05). `/data/users` ≠ `/data/public` → REJECT.
- Per Day 1, Anti-Pattern AP-01: wildcard scopes are never issued.
- Per Close (2009): capabilities can only be attenuated, never amplified.

### 8.8 Compromised PDP Instance

**Attack:** One of several PDP instances is compromised and issues unauthorized ALLOW verdicts.

**Prevention:**
- Every response carries `pdp_instance` identifier. Anomalous ALLOWs from a specific instance are detectable via audit trail correlation.
- The compromised instance's signing key can be revoked, invalidating all tokens it issued.
- This is the most dangerous attack and requires HSM compromise. Canon Readiness Condition 5 mandates hardware-grade key protection.

### 8.9 Man-in-the-Middle Between PDP and Orchestrator

**Attack:** MITM intercepts PDP's DENY response and replaces it with a forged ALLOW.

**Prevention:**
- The orchestrator verifies the response signature using the PDP's public key (Section 4.2).
- A forged response lacks a valid signature → treated as DENY (Canon Section 6.9).

### 8.10 Bypass Summary Matrix

| Attack Vector | Layer 1 Prevents? | Layer 2 Prevents? | Layer 3 Detects? | Bypass Possible? |
|---|:---:|:---:|:---:|:---:|
| Direct resource access | NO | **YES** | YES | **NO** |
| Orchestrator ignores DENY | NO | **YES** | YES | **NO** |
| Forged token | N/A | **YES** (signature) | YES | **NO** |
| Token replay (diff channel) | N/A | **YES** (session_binding) | YES | **NO** |
| Token reuse | N/A | **YES** (jti dedup) | YES | **NO** |
| Parameter substitution | N/A | **YES** (params_hash) | YES | **NO** |
| Scope amplification | **YES** (PDP never issues wildcards) | **YES** (exact match) | YES | **NO** |
| Compromised PDP | NO | NO (tokens valid) | **YES** (anomaly) | **PARTIAL** — requires HSM compromise |
| MITM (PDP↔Orchestrator) | N/A | N/A | **YES** | **NO** (response signing) |

**Result:** No attack vector achieves full bypass. The only partial bypass (compromised PDP) requires HSM compromise — a hardware-level attack that is outside the software threat model.

---

## 9. ENFORCEMENT INVARIANTS

| ID | Invariant | Consequence of Violation |
|:---:|---|---|
| **ENF-01** | Every downstream resource MUST require a Sarathi-issued capability token for every request. No exceptions. No "trusted caller" bypass. | Governance bypass — the resource becomes an unprotected asset |
| **ENF-02** | Capability tokens are issued ONLY by the PDP. No other system entity can issue tokens. | Authority fragmentation — multiple token issuers create conflicting authority sources |
| **ENF-03** | Tokens are single-use (jti dedup). Once presented, the jti is consumed and cannot be reused. | Replay vulnerability — a captured token becomes a permanent key |
| **ENF-04** | Token TTL MUST NOT exceed 60 seconds. This is not configurable upward. | Drift window expansion — longer TTL = longer window for unauthorized access after revocation |
| **ENF-05** | Token scope MUST be exact (no wildcards). The token authorizes exactly the action, resource, and parameters that were evaluated. | Scope creep — a wildcard token is an open door |
| **ENF-06** | The PDP private key MUST reside in an HSM. It must never be extractable. | Key extraction enables unlimited token forgery |
| **ENF-07** | Resources MUST verify token signatures before execution. Unverified tokens are treated as absent (REJECT). | Forgery bypass — without verification, any JWT is accepted |
| **ENF-08** | Resources MUST fulfill all obligations in the token. Unfulfilled obligations = REJECT. | Obligation bypass — conditional ALLOW becomes unconditional |
| **ENF-09** | No entity in the system may cache ALLOW verdicts or valid tokens beyond the token's TTL. | Stale authorization — cached verdicts persist after revocation |
| **ENF-10** | The enforcement model MUST NOT have a "disable" switch, "debug mode," or "testing bypass." Break-glass flows THROUGH governance (AC-26/AC-27), not around it. | Any bypass mechanism becomes the attacker's target |

---

## 10. THE ENFORCEMENT CONTRACT — OBLIGATIONS OF EACH PARTY

### 10.1 PDP Obligations

| Obligation | Reference |
|---|---|
| Issue capability tokens ONLY on ALLOW verdicts | Day 2, TI-01 |
| Sign every response with Ed25519 | OUT-04 |
| Sign every token with Ed25519 | Day 2, TI-09 |
| Never issue tokens with TTL > 60 seconds | MF-05 |
| Never issue wildcard-scoped tokens | Day 1, AP-01 |
| Include parameters_hash in every token | Day 2, TI-07 |
| Include session_binding in every token | Day 2, TI-06 |
| Record every decision in BHIV Bucket | OUT-07 |
| Protect signing key in HSM | Canon Readiness Condition 5 |

### 10.2 Orchestrator/PEP Obligations

| Obligation | Reference |
|---|---|
| Forward EVERY agent request to the PDP before execution | Day 3, EVAL-01 (Total Ordering) |
| Verify PDP response signature before acting on verdict | Canon Section 6.9 |
| If DENY: do not proceed. Do not bypass. Do not retry with same correlation_id. | INV-05, OUT-06 |
| If ALLOW: forward capability token to downstream resource | Enforcement model |
| Never cache ALLOW verdicts | Canon Section 6.5 |
| If PDP unreachable: DENY (fail-closed). Do NOT proceed without authorization. | Day 4, FM-04 |
| Forward the agent's ACTUAL intent, unmodified | Canon Section 6.10 |

### 10.3 Downstream Resource Obligations

| Obligation | Reference |
|---|---|
| Require a Sarathi capability token for EVERY request | MF-02, ENF-01 |
| Verify all 11 checks (R-01 through R-11) before execution | Section 5.2 |
| Maintain jti dedup store for single-use enforcement | ENF-03 |
| Fulfill all obligations in the token | ENF-08 |
| Never provide a bypass mode | ENF-10, Canon Section 6.6 |
| Report verification failures to BHIV Bucket | Layer 3 audit |
| Hold PDP's current public key (received out-of-band) | Section 4.4 |

---

## 11. Relationship to Previous Tasks




| Artifact | Relationship |
|---|---|
| **Task 1 — Governance Validation** | Resolves A3 (Orchestrator Compliance — token model removes orchestrator from trust chain), A7 (Intent Honesty — parameters_hash binds intent to token), A2 (Identity Persistence — session_binding) |
| **Task 2 — Canon (60 Rules)** | Implements MF-02 (downstream validation), AC-21 (Zero Trust — no request without token), AC-22 (signature verification), AC-32 (token TTL), AI-53 (audit trail as Layer 3) |
| **Task 3 — PDP Interface** | Formalizes Section 6.1 (never ALLOW on error), 6.5 (never cache), 6.6 (no God Mode), 6.9 (never ignore signature), 6.10 (no synthetic intents). MF-02 becomes the 11-check verification. |
| **Task 3 — Ambiguity Resolutions** | RES-05 (break-glass through governance, not around it), RES-09 (channel binding prevents Ghost Session) |
| **Day 1 — Request Schema** | Token issuance uses fields from Day 1: agent_id→sub, correlation_id→correlation_id, parameters_hash→parameters_hash, session_binding→session_binding |
| **Day 2 — Response Schema** | Token structure defined in Section 6. Response signing defined in Section 9. Prohibition list (Section 8) ensures minimal information leakage. |
| **Day 3 — Evaluation Order** | The 7-stage pipeline produces the verdict that the enforcement model makes binding. Stage 7 (audit write) is Layer 3. |
| **Day 4 — Failure Modes** | All 12 failure modes produce DENY = no token issued = resource rejects. FM-05 (audit sink down) overrides even valid ALLOW to DENY. FM-12 (signing key down) prevents token issuance entirely. |

---

**END OF SARATHI ENFORCEMENT MODEL SPECIFICATION**

---

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Enforcement Layers Defined | 3 (PDP Inline, Resource Token Verification, Audit Trail) |
| Resource-Side Checks | 11 (R-01 through R-11) |
| Enforcement Invariants | 10 (ENF-01 through ENF-10) |
| Attack Vectors Analyzed | 9 (direct access, orchestrator bypass, forged token, replay, reuse, parameter substitution, scope amplification, compromised PDP, MITM) |
| Bypass Possible? | 0 out of 9 achieve full bypass. 1 partial (requires HSM compromise). |
| Party Obligations | PDP: 9, Orchestrator: 7, Resource: 7 |
| Canon Rules Implemented | AC-21, AC-22, AC-24, AC-26, AC-27, AC-32, AI-53, AI-54, AI-55, MF-02, MF-05 |
| Global Principles Invoked | GP-05, GP-06, GP-07 |
| Industry Standards Referenced | Hardy 1988, Close 2009, Dennis & Van Horn 1966, NIST SP 800-207, NIST SP 800-207A, RFC 9449, RFC 9635, Google Macaroons, UCAN, SPIFFE/SPIRE, CWE-367, EU AI Act Art. 12 |
| Task 1 Assumptions Resolved | A2, A3, A7 |

---

## 11. RUNTIME PEP SPECIFICATION (GAP 1 RESOLUTION)

*Added during Gap Resolution Phase — Provides the concrete PEP deployment architecture that makes the 3-layer enforcement model operational at runtime.*

### 11.1 PEP Deployment Topology

The three enforcement layers defined in Section 7 are operationalized through three PEP deployment patterns. Each PEP type maps to a specific enforcement layer:

| Enforcement Layer | PEP Type | Deployment | Authorization Engine | Latency SLA |
|---|---|---|---|---|
| Layer 1 (PDP Inline) | Gateway PEP | API Gateway custom authorizer | Remote PDP call (HTTP/gRPC) | < 15ms |
| Layer 1 (PDP Inline) | Sidecar PEP | OPA/Cedar sidecar per pod | Local policy evaluation (localhost) | < 1ms |
| Layer 2 (Resource Verification) | Embedded Library PEP | Cedar Rust crate / OPA WASM in-process | Direct function call (zero network) | < 100μs |
| Layer 3 (Audit Trail) | Audit PEP | Async audit writer sidecar | Fire-and-forget with circuit breaker | < 500μs (non-blocking) |

### 11.2 PEP-to-PDP Communication Protocol

```
PEP → PDP Request:
  POST /v1/evaluate
  Content-Type: application/json
  Authorization: Bearer {pep_service_token}
  X-Request-ID: {correlation_id}
  X-PEP-Type: {gateway|sidecar|embedded}
  
  Body: Sarathi Request Schema (Day 1)

PDP → PEP Response:
  200 OK / 403 Forbidden / 429 Too Many Requests / 503 Unavailable
  Content-Type: application/json
  X-Evaluation-Duration-Us: {microseconds}
  
  Body: Sarathi Response Schema (Day 2)
```

### 11.3 Circuit Breaker Integration

Each PEP maintains an independent circuit breaker for its PDP connection:

```
CIRCUIT_BREAKER_CONFIG = {
    failure_window:     10 calls (sliding),
    failure_threshold:  50%,
    open_duration:      30 seconds,
    half_open_probes:   3,
    fallback_strategy:  "DENY_ALL",    // ENF-10: No bypass mode
    staleness_limit:    60 seconds     // Max age for cached decisions
}
```

Circuit breaker state transitions are security events written to BHIV Bucket (FM-05 applies — if BHIV is also down, emergency buffer captures the transition event).

### 11.4 Agent Sandbox Enforcement (Defense-in-Depth)

Each agent runtime is confined by 6 layers, with PEP integration at the network proxy:

1. **VM** — Hardware-level isolation (KVM/Apple Virtualization Framework)
2. **Namespace** — Process + network isolation (bwrap with CLONE_NEWNET, CLONE_NEWPID)
3. **Syscall** — Allowlist enforcement (seccomp BPF, ~104 bytes per filter)
4. **Network** — All egress through Unix socket → proxy with domain allowlist
5. **Filesystem** — Read-only default; deny paths for credentials (~/.ssh, ~/.aws)
6. **PEP at Proxy** — Every outbound request authorized by embedded PEP before forwarding

### 11.5 Updated Enforcement Invariants

| ID | Invariant | Original? |
|---|---|---|
| ENF-01 through ENF-10 | (Unchanged — see Section 9) | ✅ Original |
| **ENF-11** | **PEP Required at Every Trust Boundary** — No service-to-service call proceeds without PEP evaluation. Gateway authorization does not imply internal authorization. | NEW |
| **ENF-12** | **Circuit Breaker Fail-Closed** — PDP unavailability triggers DENY for all pending requests. Cached decisions expire after 60 seconds. No stale ALLOW persists indefinitely. | NEW |
| **ENF-13** | **Sandbox Mandatory for Tool-Using Agents** — Any agent that invokes external tools MUST run within the 6-layer sandbox. No exceptions, including admin agents. | NEW |
| **ENF-14** | **Tenant-Scoped Circuit Breakers** — Circuit breakers are tenant-isolated. One tenant's traffic spike cannot trigger denial for other tenants (RES-20). | NEW |

