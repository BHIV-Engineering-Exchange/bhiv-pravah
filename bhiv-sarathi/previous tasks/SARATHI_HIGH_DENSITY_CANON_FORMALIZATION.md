# SARATHI HIGH-DENSITY CANON FORMALIZATION

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  
**Task Reference:** Test Task 2 - High-Density Canon Formalization & Compliance Matrix Sprint

---

## EXECUTIVE SUMMARY

This document constitutes the comprehensive formalization artifact for the Sarathi constitutional governance layer, executed under the strict parameters of Task 2: High-Density Canon Formalization & Compliance Matrix Sprint. Building upon the foundational governance validation performed in Task 1, this specification transitions Sarathi from conceptual framework to implementation-ready formalization.

**Scope of Work:**
- 60 atomic governance rules extracted and categorized
- 35 rules with full compliance matrix specifications
- 20 rules formalized in Rego policy language (Reference / Non-Binding)
- 25 negative test cases with failure classifications
- Complete refusal taxonomy with exposure mapping
- Explicit deferred scope register with risk assessment
- Governance readiness statement

**Key Improvements from Task 1 Feedback:**
1. Consolidated **Acceptance Criteria Checklist** (Section 8.1)
2. Explicit **Change Request Summary** with Must-fix/Should-fix/Nice-to-have categorization (Section 8.2)
3. **Boundary Confirmation Section** explicitly stating what was NOT analyzed (Section 2)
4. All implementation references clearly marked as **[REFERENCE / NON-BINDING]**

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Boundary Confirmation Section](#boundary-confirmation-section)
3. [Day 1: Master Rule Inventory](#day-1-master-rule-inventory)
4. [Day 2: Governance Compliance Matrix](#day-2-governance-compliance-matrix)
5. [Day 3: Formal Policy Translation (Rego)](#day-3-formal-policy-translation-rego)
6. [Day 3b: Negative Test Cases](#day-3b-negative-test-cases)
7. [Day 4: Refusal Taxonomy](#day-4-refusal-taxonomy)
8. [Deferred Scope Register](#deferred-scope-register)
9. [Change Request Summary](#change-request-summary)
10. [Governance Readiness Statement](#governance-readiness-statement)

---

## BOUNDARY CONFIRMATION SECTION

### What Sarathi IS (Explicitly In Scope)

| Aspect | Definition | Governing Principle |
|--------|------------|---------------------|
| **Policy Decision Point (PDP)** | Evaluates intents against Canon rules, returns ALLOW/DENY/ESCALATE | Single Source of Truth for Permission |
| **Capability Token Issuer** | Generates cryptographically signed, time-bounded tokens on ALLOW | Zero Trust Enforcement |
| **Write-Only Audit Sink** | Pushes all decisions to BHIV Bucket with full fidelity | Tamper-Proof Accountability |
| **Constitutional Authority** | Final arbiter of governance changes via formal amendment | Sovereign Design Integrity |

### What Sarathi IS NOT (Explicitly OUT of Scope)

| Excluded Function | Reason for Exclusion | Risk if Included |
|-------------------|----------------------|------------------|
| **Orchestration Engine** | Sarathi does not execute, schedule, or call downstream APIs | TOCTOU vulnerabilities; Confused Deputy attacks |
| **Availability Monitor** | Sarathi does not check service health or database uptime | Governance Hallucination; Flaky policy decisions |
| **Cost Optimizer** | Sarathi does not rank agents by cost or efficiency | Safety-Cost tradeoffs; Reward Hacking |
| **Machine Learning System** | Sarathi does not learn from outcomes or adjust rules dynamically | Policy Drift; Adversarial Poisoning |
| **User Interface Renderer** | Sarathi does not format errors for display or handle UX | XSS attack surface; Scope creep |
| **Retry Logic Handler** | Sarathi does not manage retry workflows or exponential backoff | DoS amplification; Self-inflicted load |

### What Was Intentionally NOT Analyzed

| Topic | Reason for Exclusion |
|-------|---------------------|
| **Physical Security / TPM Attestation** | Implementation detail of Identity Provider, not PDP |
| **Network Topology / Firewall Rules** | Infrastructure concern, not governance policy |
| **Database Schema Design** | Execution layer concern |
| **LLM Prompt Engineering** | Agent implementation detail |
| **Specific Cloud Provider Integration** | Implementation choice, not governance principle |
| **Multi-Region Failover** | Availability architecture, not policy logic |

---

## DAY 1: MASTER RULE INVENTORY

### Rule Inventory Statistics
- **Total Rules Extracted:** 60
- **CORE Rules:** 20
- **SAFETY-CRITICAL Rules:** 24
- **SUPPORTING Rules:** 16

### Category 1: Identity & Agent Definition (Rules ID-01 to ID-10)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| ID-01 | Identity Signature Verification | If agent's cryptographic signature does not match registered public key | Identity Provider | DENY with "Signature Mismatch" | CORE |
| ID-02 | Session Binding Requirement | If agent operates without valid session token | Session Manager | DENY with "Session Required" | CORE |
| ID-03 | Non-Human Classification | If agent operates autonomously without human session binding | System Registry | MANDATE "Bot" classification flag | SUPPORTING |
| ID-04 | Admin Role Isolation | If agent claims "Admin" without Governance_Write token | Authorization Kernel | DENY write access to Canon | SAFETY-CRITICAL |
| ID-05 | Prohibited Class: Optimizer | If agent class equals "Recursive_Policy_Optimizer" | Ontology Definition | PERMANENT DENY (Ban) | SAFETY-CRITICAL |
| ID-06 | Prohibited Class: Shadow | If agent bypasses BHIV Bucket ingress pathway | Network Policy | DENY and Alert Security | SAFETY-CRITICAL |
| ID-07 | Prohibited Class: Emergency Backdoor | If agent claims emergency bypass for governance | Emergency Protocol | DENY; emergency access flows through governance | SAFETY-CRITICAL |
| ID-08 | Delegation Token Requirement | If agent acts as User Proxy without Delegation Token | Delegation Protocol | DENY with "Delegation Required" | CORE |
| ID-09 | Ephemeral Identity TTL | If agent is classified "Transient" | Lifecycle Policy | ENFORCE Identity TTL < Session TTL | SUPPORTING |
| ID-10 | Sanctioned Impersonation | If agent is "Penetration_Tester" AND target is "Staging" | Security Exemption | ALLOW identity spoofing patterns | SUPPORTING |

### Category 2: Lifecycle & State (Rules LS-11 to LS-20)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| LS-11 | Active State Requirement | If Agent.State != "ACTIVE" | State Registry | DENY all intents | CORE |
| LS-12 | Suspension Enforcement | If Agent.State == "SUSPENDED" | State Registry | DENY all intents; log suspension reason | CORE |
| LS-13 | Revocation Permanence | If Agent.State == "REVOKED" | State Registry | PERMANENT DENY; no resurrection | SAFETY-CRITICAL |
| LS-14 | Deprecation Grace Period | If Agent.State == "DEPRECATED" | Lifecycle Policy | ALLOW existing tasks; DENY new task initiation | SUPPORTING |
| LS-15 | State Synchronization (New Enemy) | If Token.Timestamp < Canon.LastUpdateTimestamp | Consistency Check | INVALIDATE Token; force re-authentication | SAFETY-CRITICAL |
| LS-16 | Heartbeat Requirement | If Heartbeat.Token is missing or expired (>500ms) | Availability Policy | HALT downstream orchestration | SAFETY-CRITICAL |
| LS-17 | Zombie Agent Detection | If Agent.InactiveDuration > Max_Idle_Threshold | Lifecycle Policy | REVOKE all capabilities | SUPPORTING |
| LS-18 | Self-Modification Block | If Agent attempts to modify own State Record | Integrity Policy | DENY and log "Self-Modification Attempt" | SAFETY-CRITICAL |
| LS-19 | Cascading Revocation | If Parent Agent is REVOKED | Lineage Policy | REVOKE all descendant agents | SAFETY-CRITICAL |
| LS-20 | Memory Purge on Termination | If Session == "Terminated" AND Agent == "Transient" | Privacy Policy | TRIGGER data purge event | SAFETY-CRITICAL |

### Category 3: Authority & Capability (Rules AC-21 to AC-32)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| AC-21 | Zero Trust Default | If Capability Token is missing or null | Authorization Kernel | DENY (Fail Closed) | CORE |
| AC-22 | Token Signature Validation | If Token.Signature != Valid Governance Key | Crypto Policy | DENY and alert "Forgery Attempt" | CORE |
| AC-23 | Scope Confinement | If Intent.Resource > Token.Scope | Least Privilege | DENY "Scope Mismatch" | CORE |
| AC-24 | Token Expiry Enforcement | If Current_Time > Token.ExpiryTime | Time Policy | DENY "Token Expired" | CORE |
| AC-25 | Cross-Tenant Isolation | If Intent.TargetTenant != Agent.HomeTenant | Multi-Tenancy | DENY "Cross-Tenant Violation" | SAFETY-CRITICAL |
| AC-26 | Administrator Data Isolation | If Agent.Role == "Admin" AND Action == "Decrypt_User_Data" | Privacy Policy | DENY unless Break_Glass active | SAFETY-CRITICAL |
| AC-27 | Kill-Switch Override | If Agent.Class == "Kill_Switch_Activator" AND Event == "Emergency" | Emergency Policy | ALLOW override of state locks | SAFETY-CRITICAL |
| AC-28 | Bias Auditor Safe Harbor | If Agent.Class == "Bias_Auditor" AND Destination == "Null_Sink" | Ethics Policy | ALLOW toxic content generation for testing | SUPPORTING |
| AC-29 | Financial Exposure Limit | If Agent.Class == "Market_Maker" AND Exposure > Limit | Risk Policy | DENY transaction | SAFETY-CRITICAL |
| AC-30 | Privilege Elevation TTL | If Elevated_Privilege.Duration > Max_Elevation_TTL | Temporal Policy | DENY; require re-authorization | SAFETY-CRITICAL |
| AC-31 | Multi-Party Canon Approval | If Intent == "Modify_Canon" AND Approvers < Quorum | Constitutional | DENY "Insufficient Quorum" | CORE |
| AC-32 | Capability Token TTL | If Token.TTL > 60 seconds | Token Policy | REJECT token issuance request | SAFETY-CRITICAL |

### Category 4: Eligibility Logic (Rules EL-33 to EL-44)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| EL-33 | Input Validation | If Required Input Fields are NULL or malformed | Validation Logic | DENY "Malformed Request" | CORE |
| EL-34 | Unknown Intent Rejection | If Intent.Type not in Recognized Intent Registry | Intent Classification | DENY "Unknown Intent" | CORE |
| EL-35 | PII Exposure Invariant | If Action results in PII exposure to Public sink | Privacy Invariant | DENY "Data Classification Violation" | SAFETY-CRITICAL |
| EL-36 | Mosaic Theory Block | If Agent == "Context_Free_Summarizer" AND Data.Classification == "Confidential" | Inference Risk | DENY summarization | SAFETY-CRITICAL |
| EL-37 | Standard Rate Limit | If Agent.Requests > 100/minute | Velocity Policy | THROTTLE or DENY | SUPPORTING |
| EL-38 | Market Maker Rate Exempt | If Agent.Class == "Market_Maker" | Velocity Policy | BYPASS standard rate limit | SUPPORTING |
| EL-39 | Brute Force Detection | If Agent.RefusalCount > 3 within 60 seconds | Abuse Policy | SUSPEND agent | SAFETY-CRITICAL |
| EL-40 | Geofencing Enforcement | If Origin.Region not in Allowed_Regions | Compliance Policy | DENY "Region Violation" | SUPPORTING |
| EL-41 | Temporal Window Enforcement | If Action == "Critical_Write" AND Time not in Maintenance_Window | Operations Policy | DENY "Outside Maintenance Window" | SUPPORTING |
| EL-42 | Human-in-the-Loop Gate | If Risk.Class == "HIGH" AND Human.Approval == NULL | Governance Gate | ESCALATE for human sign-off | SAFETY-CRITICAL |
| EL-43 | Segregation of Duties | If Agent.Role == "Maker" AND Action == "Approve_Own_Request" | SoD Policy | DENY "Segregation Violation" | SAFETY-CRITICAL |
| EL-44 | Aggregate Risk Threshold | If Agent.Aggregate_Risk_Score > Max_Exposure within Time_Window | Risk Accumulation | DENY with velocity warning | SAFETY-CRITICAL |

### Category 5: Refusal & Escalation (Rules RE-45 to RE-52)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| RE-45 | Opaque Security Refusal | If Refusal.Reason == "Security_Violation" | Security UX | RETURN generic "Access Denied" (no details) | SAFETY-CRITICAL |
| RE-46 | Transparent Developer Refusal | If Refusal.Reason == "Missing_Field" | Developer UX | RETURN specific field details | SUPPORTING |
| RE-47 | Ambiguity Escalation | If Decision == "Ambiguous" | Resolution Policy | ROUTE to Governance Council | SUPPORTING |
| RE-48 | Refusal Immutability | If Agent attempts retry of same Request.ID after denial | Interaction Policy | DENY and log "Coercion Attempt" | CORE |
| RE-49 | Safety System Alert | If Agent.Class == "Safety_System" AND Decision == "DENY" | Safety Policy | ALERT SOC immediately | SAFETY-CRITICAL |
| RE-50 | Mandatory Denial Logging | If Verdict == "DENY" | Audit Policy | WRITE event to immutable log | CORE |
| RE-51 | User Notification Routing | If Denial impacts end-user experience | UX Policy | NOTIFY user (not agent) | SUPPORTING |
| RE-52 | Escalation Timeout Default | If Human.ApprovalTime > SLA threshold | Workflow Policy | DEFAULT to DENY | SAFETY-CRITICAL |

### Category 6: Audit & Immutability (Rules AI-53 to AI-58)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| AI-53 | Write-Only Bucket | If Event.Target == "BHIV_Bucket" | Architecture | ALLOW Append Only (No Delete/Edit) | CORE |
| AI-54 | Tamper Evidence Chain | If Log.ChainHash is broken or invalid | Integrity Check | ALERT "Audit Breach" | SAFETY-CRITICAL |
| AI-55 | Full Context Logging | If Decision is made | Audit Policy | RECORD Input, Rules Evaluated, Verdict, Timestamp | CORE |
| AI-56 | PII Redaction in Logs | If Log contains PII | Privacy Policy | HASH/REDACT PII before write | SAFETY-CRITICAL |
| AI-57 | Policy Version Archive | If Policy.Change occurs | Version Control | ARCHIVE previous policy state | SUPPORTING |
| AI-58 | Canon Deletion Block | If Intent == "Delete_Canon_Rule" | Constitutional | DENY (requires hard fork/rebuild) | CORE |

### Category 7: Boundary & Non-Goals (Rules BN-59 to BN-60)

| Rule ID | Rule Name | Condition | Authority Context | Outcome | Tag |
|---------|-----------|-----------|-------------------|---------|-----|
| BN-59 | No Orchestration | If Intent.Type == "Execute_Workflow" | Boundary Definition | REJECT "Out of Scope" | CORE |
| BN-60 | No Agent Ranking | If Intent.Type == "Recommend_Best_Agent" | Boundary Definition | REJECT "Out of Scope" | SUPPORTING |

---

## DAY 2: GOVERNANCE COMPLIANCE MATRIX

### Compliance Matrix for CORE & SAFETY-CRITICAL Rules (35 Rules)

#### Identity & Agent Definition Rules

| Rule Ref | Preconditions | Required Agent State | Forbidden Agent State | Required Authority | Risk Class | Expected Decision | Mandatory Audit Fields |
|----------|---------------|---------------------|----------------------|-------------------|------------|-------------------|----------------------|
| ID-01 | Valid session; Agent registered | Session.Active = TRUE | Signature.Mismatch = TRUE | IdP_Verify | CRITICAL | DENY if mismatch | AgentID, KeyHash, SessionID, Timestamp |
| ID-02 | Agent in registry | Session.Token present | Session.Token = NULL | Session_Manager | HIGH | DENY if no session | AgentID, RequestIP, AttemptTime |
| ID-04 | Role claim present | Role = Admin; MFA = TRUE | MFA = FALSE; No Gov_Write token | Governance_Write | CRITICAL | DENY if no MFA + token | RoleClaim, MFA_Status, TokenScope |
| ID-05 | Class declaration present | Class != Recursive_Optimizer | Class = Recursive_Optimizer | Ontology_Check | CRITICAL | PERMANENT DENY | AgentClass, IntentHash, BanReason |
| ID-06 | Network path identifiable | Ingress = BHIV_Bucket | Ingress = Direct_API_Bypass | Network_Policy | CRITICAL | DENY + Alert | SourceIP, TargetEndpoint, AttemptType |
| ID-07 | Emergency claim declared | N/A | Emergency_Bypass = TRUE | Emergency_Protocol | CRITICAL | DENY | ClaimType, AgentID, Timestamp |
| ID-08 | Proxy class declared | Token.Type = Delegation | Token.Type = Root (for proxy) | User_Consent | HIGH | DENY if Root token | ParentUser, ScopeList, DelegationChain |

#### Lifecycle & State Rules

| Rule Ref | Preconditions | Required Agent State | Forbidden Agent State | Required Authority | Risk Class | Expected Decision | Mandatory Audit Fields |
|----------|---------------|---------------------|----------------------|-------------------|------------|-------------------|----------------------|
| LS-11 | Agent in registry | State = ACTIVE | State != ACTIVE | State_Registry | CRITICAL | DENY if not ACTIVE | AgentState, StateTransitionTime, LastActivity |
| LS-12 | Suspension record exists | N/A | State = SUSPENDED | State_Registry | HIGH | DENY all | AgentID, SuspensionReason, SuspensionTime |
| LS-13 | Revocation record exists | N/A | State = REVOKED | State_Registry | CRITICAL | PERMANENT DENY | AgentID, RevocationReason, RevocationTime |
| LS-15 | Token timestamp present | Token.TS >= Policy.LastUpdate | Token.TS < Policy.LastUpdate | Consistency_Check | CRITICAL | INVALIDATE token | TokenTS, PolicyTS, DeltaSeconds |
| LS-16 | Safety-critical agent | Heartbeat.Age < 500ms | Heartbeat.Missing OR > 500ms | Watchdog_Service | CRITICAL | HALT | LastBeat, CurrentTime, HeartbeatThreshold |
| LS-18 | State modification attempt | N/A | Agent modifying own state | Integrity_Policy | CRITICAL | DENY + Log | AgentID, AttemptedChange, CurrentState |
| LS-19 | Parent-child relationship | Parent = ACTIVE | Parent = REVOKED | Lineage_Policy | CRITICAL | REVOKE children | ParentID, ChildIDs, CascadeReason |
| LS-20 | Session termination event | Session = Terminated | Transient agent with retained data | Privacy_Policy | HIGH | Trigger purge | SessionID, DataVolume, PurgeStatus |

#### Authority & Capability Rules

| Rule Ref | Preconditions | Required Agent State | Forbidden Agent State | Required Authority | Risk Class | Expected Decision | Mandatory Audit Fields |
|----------|---------------|---------------------|----------------------|-------------------|------------|-------------------|----------------------|
| AC-21 | Token field present | Token != NULL | Token = NULL or missing | Zero_Trust | CRITICAL | DENY | RequestHeaders, AgentID, Resource |
| AC-22 | Token signature present | Signature = Valid | Signature = Invalid/Forged | Crypto_Policy | CRITICAL | DENY + Alert | TokenID, SignatureHash, ValidationResult |
| AC-23 | Scope declaration present | Scope >= Request | Scope < Request | Policy_Eval | HIGH | DENY "Scope Mismatch" | RequestedResource, TokenScope, Gap |
| AC-24 | Token contains expiry | Current_Time <= Expiry | Current_Time > Expiry | Time_Policy | HIGH | DENY | TokenExpiry, CurrentTime, Delta |
| AC-25 | Tenant context present | Target.Tenant = Home.Tenant | Target.Tenant != Home.Tenant | Multitenancy | CRITICAL | DENY | SourceTenant, TargetTenant, AttemptType |
| AC-26 | Admin + Data action | Break_Glass = Active | Break_Glass = Inactive AND ReadUserData | Privileged_Access | CRITICAL | DENY | AdminID, DataType, BreakGlassTicket |
| AC-27 | Emergency event declared | Class = Kill_Switch; Event = Critical | Event = Routine | Override_Authority | CRITICAL | ALLOW | SafetyTrigger, StateDump, OverrideJustification |
| AC-29 | Transaction value present | Exposure < Limit | Exposure > Limit | Risk_Engine | HIGH | DENY | CurrentExposure, Limit, TransactionValue |
| AC-30 | Elevation active | Duration <= Max_TTL | Duration > Max_TTL | Temporal_Policy | HIGH | DENY | ElevationStart, Duration, MaxAllowed |
| AC-31 | Canon modification intent | Approvers >= Quorum | Approvers < Quorum | Constitutional | CRITICAL | DENY | ApproverIDs, QuorumRequired, Shortfall |
| AC-32 | Token issuance request | TTL <= 60s | TTL > 60s | Token_Policy | CRITICAL | REJECT | RequestedTTL, MaxTTL, IssuerID |

#### Eligibility Logic Rules

| Rule Ref | Preconditions | Required Agent State | Forbidden Agent State | Required Authority | Risk Class | Expected Decision | Mandatory Audit Fields |
|----------|---------------|---------------------|----------------------|-------------------|------------|-------------------|----------------------|
| EL-33 | Request structure received | All required fields present | Required fields NULL | Validation_Logic | MEDIUM | DENY "Malformed" | MissingFields, RequestHash |
| EL-34 | Intent declared | Intent in Registry | Intent unknown | Intent_Classification | MEDIUM | DENY "Unknown Intent" | IntentType, Registry Version |
| EL-35 | Data classification present | Destination = Private/Internal | Destination = Public + PII | DLP_Check | CRITICAL | DENY | DataClass, DestClass, ViolationType |
| EL-36 | Summarizer + Data request | Data = Public | Data = Confidential + Summarizer | Inference_Check | HIGH | DENY | ContentHash, DataClass, MosaicScore |
| EL-39 | Refusal counter active | RefusalCount <= 3/min | RefusalCount > 3/min | Pattern_Match | HIGH | SUSPEND | RefusalCount, TimeWindow, PatternType |
| EL-42 | Risk classified HIGH | Human.Approval = Valid | Human.Approval = NULL | Governance_Gate | CRITICAL | ESCALATE | RiskClass, ApproverID, DecisionTime |
| EL-43 | Dual action request | Maker != Approver | Maker = Approver | SoD_Policy | HIGH | DENY | MakerID, ApproverID, ActionType |
| EL-44 | Aggregate tracking active | Score < Threshold | Score > Threshold | Risk_Accumulation | CRITICAL | DENY | AggregateScore, Threshold, Window |

#### Refusal & Audit Rules

| Rule Ref | Preconditions | Required Agent State | Forbidden Agent State | Required Authority | Risk Class | Expected Decision | Mandatory Audit Fields |
|----------|---------------|---------------------|----------------------|-------------------|------------|-------------------|----------------------|
| RE-45 | Security-class refusal | N/A | N/A | Security_UX | CRITICAL | Opaque DENY | RefusalReason (internal only), ResponseCode |
| RE-48 | Previous denial exists | N/A | Retry of denied RequestID | Interaction_Policy | HIGH | DENY | OriginalRequestID, RetryCount, AgentID |
| RE-49 | Safety system denied | Class = Safety_System | Decision = DENY | Safety_Policy | CRITICAL | ALERT SOC | SystemID, DenialReason, AlertTime |
| AI-53 | Write to BHIV Bucket | Action = Append | Action = Delete/Modify | WORM_Policy | CRITICAL | Block non-append | WriteType, TargetBucket, BlockReason |
| AI-54 | Chain hash verification | Hash = Valid | Hash = Broken/Invalid | Integrity_Check | CRITICAL | ALERT | LastValidHash, CurrentHash, BreakPoint |

---

## DAY 3: FORMAL POLICY TRANSLATION (REGO)

> **[REFERENCE / NON-BINDING]**
> The following Rego policy translations are provided as implementation guidance only. They are not mandated specifications. Implementation teams may use alternative policy-as-code frameworks (e.g., Cedar, Casbin) as appropriate.

```rego
package sarathi.core

# ============================================================
# DEFAULT DENY (Rule AC-21)
# The system fails closed. If no rule explicitly allows, deny.
# [REFERENCE / NON-BINDING]
# ============================================================
default allow = false

# ============================================================
# INPUT VALIDATION (Rule EL-33)
# Prevent malformed request attacks
# [REFERENCE / NON-BINDING]
# ============================================================
valid_input {
    input.agent.id
    input.agent.class
    input.action.type
    input.resource.id
    input.context.time
    input.auth.token
}

deny[msg] {
    not valid_input
    msg := "EL-33: Malformed Request - Required fields missing"
}

# ============================================================
# RULE ID-01: IDENTITY SIGNATURE VERIFICATION
# Prevents session hijacking and identity spoofing
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    stored_agent := data.agents[input.agent.id]
    input.auth.signature != stored_agent.public_key
    msg := "ID-01: Identity Verification Failed - Signature Mismatch"
}

# ============================================================
# RULE ID-05: PROHIBITED CLASS - RECURSIVE OPTIMIZER
# Absolute ban on policy-rewriting agents
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.agent.class == "Recursive_Policy_Optimizer"
    msg := "ID-05: PERMANENT BAN - Recursive Optimizer Class Prohibited"
}

# ============================================================
# RULE ID-08: DELEGATION TOKEN REQUIREMENT
# User proxies must use delegation tokens, not root
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.agent.class == "User_Proxy"
    not input.auth.token_type == "Delegation"
    msg := "ID-08: Delegation Violation - Proxy requires Delegation Token"
}

# ============================================================
# RULE LS-11: ACTIVE STATE REQUIREMENT
# Only ACTIVE agents may proceed
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    agent_state := data.agent_states[input.agent.id]
    agent_state.status != "ACTIVE"
    msg := sprintf("LS-11: State Violation - Agent status is %s", [agent_state.status])
}

# ============================================================
# RULE LS-15: STATE SYNCHRONIZATION (NEW ENEMY)
# Token must be newer than last policy update
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.auth.issued_at < data.system.last_policy_update
    msg := "LS-15: Consistency Violation - Token Stale (New Enemy Risk)"
}

# ============================================================
# RULE LS-16: HEARTBEAT REQUIREMENT
# Safety-critical agents must have recent heartbeat
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.agent.class == "Safety_Critical"
    current_time := time.now_ns()
    last_beat := data.heartbeats[input.agent.id]
    (current_time - last_beat) > 500000000  # 500ms in nanoseconds
    msg := "LS-16: Availability Violation - Heartbeat Lost (>500ms)"
}

# ============================================================
# RULE AC-22: TOKEN SIGNATURE VALIDATION
# Reject forged tokens
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    not crypto.verify_signature(input.auth.token.signature, data.governance_public_key)
    msg := "AC-22: Crypto Violation - Token Signature Invalid"
}

# ============================================================
# RULE AC-23: SCOPE CONFINEMENT
# Request must be within token scope
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    required_scope := sprintf("%s:%s", [input.resource.type, input.action.type])
    not scope_allowed(input.auth.scopes, required_scope)
    msg := sprintf("AC-23: Authority Violation - Missing Scope: %s", [required_scope])
}

scope_allowed(scopes, required) {
    scopes[_] == required
}

# ============================================================
# RULE AC-24: TOKEN EXPIRY ENFORCEMENT
# Expired tokens are rejected
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    time.now_ns() > input.auth.token.expiry_ns
    msg := "AC-24: Token Expired"
}

# ============================================================
# RULE AC-26: ADMINISTRATOR DATA ISOLATION
# Admins need Break Glass for user data
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.agent.role == "Admin"
    input.action.type == "Read_User_Data"
    not input.context.break_glass_ticket
    msg := "AC-26: Privacy Violation - Admin Access requires Break Glass Ticket"
}

# ============================================================
# RULE AC-27: KILL-SWITCH OVERRIDE (ALLOW RULE)
# Safety agents can override state locks in emergencies
# [REFERENCE / NON-BINDING]
# ============================================================
allow {
    valid_input
    input.agent.class == "Kill_Switch_Activator"
    input.action.type == "Emergency_Stop"
}

# ============================================================
# RULE AC-29: FINANCIAL EXPOSURE LIMIT
# Market makers cannot exceed exposure limits
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.agent.class == "Market_Maker"
    input.transaction.value > data.limits.financial_exposure
    msg := "AC-29: Risk Violation - Financial Exposure Limit Exceeded"
}

# ============================================================
# RULE EL-35: PII EXPOSURE INVARIANT
# PII cannot flow to public destinations
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.data.classification == "PII"
    input.destination.type == "Public"
    msg := "EL-35: Data Safety Violation - PII to Public Sink Blocked"
}

# ============================================================
# RULE EL-36: MOSAIC THEORY BLOCK
# Context-free summarizers cannot process confidential data
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.agent.class == "Context_Free_Summarizer"
    input.data.classification == "Confidential"
    msg := "EL-36: Inference Risk - Summarizer Cannot Process Confidential Data"
}

# ============================================================
# RULE EL-39: BRUTE FORCE DETECTION
# Suspend agents with too many refusals
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    refusals := data.metrics.refusal_counts[input.agent.id]
    refusals > 3
    msg := "EL-39: Abuse Violation - Rate Limit Exceeded (Brute Force Pattern)"
}

# ============================================================
# RULE RE-48: REFUSAL IMMUTABILITY
# Cannot retry denied request IDs
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    data.history.denied_requests[input.request.id]
    msg := "RE-48: Integrity Violation - Cannot Retry Denied Request ID"
}

# ============================================================
# RULE AI-53: WRITE-ONLY SINK
# BHIV Bucket only accepts appends
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.resource.id == "BHIV_Bucket"
    input.action.type != "Append"
    msg := "AI-53: Immutability Violation - BHIV Bucket is Append-Only"
}

# ============================================================
# RULE BN-59: NO ORCHESTRATION
# Sarathi does not execute workflows
# [REFERENCE / NON-BINDING]
# ============================================================
deny[msg] {
    valid_input
    input.intent.contains_execution_logic == true
    msg := "BN-59: Boundary Violation - Sarathi Does Not Orchestrate"
}
```

---

## DAY 3B: NEGATIVE TEST CASES

### Negative Test Case Matrix (25 Cases)

| Test ID | Rule Ref | Test Scenario | Input Vector | Expected Failure Reason | Refusal Class |
|---------|----------|---------------|--------------|------------------------|---------------|
| TC-01 | ID-01 | **Key Rotation Attack:** Agent uses old key after rotation | `AgentID="A1", Signature=OldKey` | ID-01: Signature Mismatch | Auth Failure |
| TC-02 | ID-05 | **Optimizer Injection:** Bot renames itself to Optimizer | `Class="Recursive_Policy_Optimizer"` | ID-05: Prohibited Agent Class | Policy Violation |
| TC-03 | ID-06 | **Shadow Agent:** Direct API call bypassing BHIV | `Ingress=Direct_API` | ID-06: Shadow Agent Detected | Security Alert |
| TC-04 | ID-07 | **Emergency Bypass Claim:** Agent claims P0 incident bypass | `Emergency_Bypass=TRUE` | ID-07: Emergency Must Flow Through Governance | Policy Violation |
| TC-05 | ID-08 | **Confused Deputy:** User Proxy uses Root token | `Class="User_Proxy", TokenType="Root"` | ID-08: Delegation Violation | Privilege Escalation |
| TC-06 | LS-11 | **Zombie Request:** DEPRECATED agent starts new task | `State="DEPRECATED", Action="New_Task"` | LS-11: State Not ACTIVE | State Invalid |
| TC-07 | LS-13 | **Resurrection Attempt:** REVOKED agent requests access | `State="REVOKED"` | LS-13: Permanent Revocation | State Invalid |
| TC-08 | LS-15 | **Race Condition:** Stale token post-policy update | `TokenTS=T1, PolicyTS=T2 (T2>T1)` | LS-15: Token Stale (New Enemy) | State Invalid |
| TC-09 | LS-16 | **Silent Failure:** Safety agent without heartbeat | `Class="Safety_Critical", Heartbeat=NULL` | LS-16: Heartbeat Lost | Availability Halt |
| TC-10 | LS-18 | **Self-Modification:** Agent tries to change own state | `Target=Self.State, Action="Modify"` | LS-18: Self-Modification Blocked | Integrity Violation |
| TC-11 | AC-21 | **Tokenless Request:** No capability token provided | `Token=NULL` | AC-21: Zero Trust Default Deny | Auth Failure |
| TC-12 | AC-22 | **Forged Token:** Invalid cryptographic signature | `Signature=FakeKey` | AC-22: Token Signature Invalid | Auth Failure |
| TC-13 | AC-23 | **Scope Escalation:** Request exceeds token scope | `TokenScope="Read", Action="Delete"` | AC-23: Scope Mismatch | Authority Mismatch |
| TC-14 | AC-24 | **Expired Token:** Token past expiry time | `TokenExpiry=T-10min` | AC-24: Token Expired | Auth Failure |
| TC-15 | AC-25 | **Cross-Tenant Attack:** Access different tenant data | `SourceTenant="A", TargetTenant="B"` | AC-25: Cross-Tenant Violation | Security Block |
| TC-16 | AC-26 | **Snowden Scenario:** Admin reads user data without ticket | `Role="Admin", Action="Read_User_Data", BreakGlass=NULL` | AC-26: Break Glass Required | Privacy Violation |
| TC-17 | AC-31 | **Solo Canon Change:** Single approver modifies Canon | `Intent="Modify_Canon", Approvers=1, Quorum=3` | AC-31: Insufficient Quorum | Constitutional Block |
| TC-18 | AC-32 | **Long-Lived Token:** Token with 24-hour TTL requested | `RequestedTTL=86400s` | AC-32: TTL Exceeds Maximum | Token Policy |
| TC-19 | EL-33 | **Malformed Request:** Missing required fields | `AgentID=NULL` | EL-33: Malformed Request | Input Validation |
| TC-20 | EL-35 | **PII Leak:** Sending PII to public endpoint | `DataClass="PII", Destination="Public"` | EL-35: PII to Public Blocked | Data Safety |
| TC-21 | EL-36 | **Mosaic Attack:** Summarizer processes confidential docs | `Class="Summarizer", DataClass="Confidential"` | EL-36: Inference Risk | Data Safety |
| TC-22 | EL-39 | **Brute Force:** Agent with 10 refusals in 1 minute | `RefusalCount=10, Window=60s` | EL-39: Brute Force Pattern | Abuse Detection |
| TC-23 | EL-43 | **Self-Approval:** Maker approves own request | `MakerID="A", ApproverID="A"` | EL-43: Segregation Violation | SoD Violation |
| TC-24 | RE-48 | **Coercion Attempt:** Retry of denied request | `RequestID="REQ-123" (previously denied)` | RE-48: Cannot Retry Denied ID | Integrity Violation |
| TC-25 | AI-53 | **Audit Tampering:** Attempt to delete from BHIV Bucket | `Target="BHIV_Bucket", Action="Delete"` | AI-53: Append-Only Violation | Immutability Block |

---

## DAY 4: REFUSAL TAXONOMY

### Refusal Classification System

| Refusal Type | Type Code | Definition | Severity |
|--------------|-----------|------------|----------|
| **Policy Violation** | R1 | Request violates static governance rule | CRITICAL |
| **Authority Mismatch** | R2 | Token lacks required scope or invalid signature | HIGH |
| **State Invalid** | R3 | Agent suspended, revoked, or deprecated | HIGH |
| **Risk Threshold** | R4 | Probabilistic risk score exceeded limits | MEDIUM |
| **Boundary Violation** | R5 | Request asks for out-of-scope functionality | MEDIUM |
| **Safety Lock** | R6 | System in emergency halt or heartbeat failure | CRITICAL |

### Exposure Matrix: What is Logged vs Exposed

| Refusal Type | Internal Log (Full Fidelity) | External Response (Agent/User) | NEVER Expose |
|--------------|------------------------------|-------------------------------|--------------|
| R1: Policy Violation | `VIOLATION: {RuleID} {AgentID} {IntentHash} {FullContext}` | `403 Forbidden: Policy Violation` | Rule details; Bypass hints |
| R2: Authority Mismatch | `AUTH_FAIL: {TokenID} {MissingScope} {SignatureHash}` | `401 Unauthorized` | Valid scopes; Key fingerprints |
| R3: State Invalid | `STATE_ERR: {AgentID} {CurrentState} {TransitionHistory}` | `403 Forbidden: Invalid State` | State machine details |
| R4: Risk Threshold | `RISK_BLOCK: {RiskScore} {Threshold} {Contributors}` | `429 Too Many Requests` | Threshold values; Scoring algorithm |
| R5: Boundary Violation | `BOUNDARY: {IntentType} {OutOfScopeReason}` | `400 Bad Request: Invalid Intent` | Sarathi's scope boundaries |
| R6: Safety Lock | `SAFETY_HALT: {TriggerEvent} {SystemState}` | `503 Service Unavailable` | Internal system state |

### Refusal Response Templates

| Scenario | Response Code | Response Body | Log Entry |
|----------|---------------|---------------|-----------|
| Unknown token | 401 | `{"error":"unauthorized","code":"AUTH_001"}` | `AUTH_FAIL: Token not found; AgentID={id}` |
| Expired token | 401 | `{"error":"unauthorized","code":"AUTH_002"}` | `AUTH_FAIL: Token expired; Delta={seconds}` |
| Scope insufficient | 403 | `{"error":"forbidden","code":"SCOPE_001"}` | `AUTH_FAIL: Scope mismatch; Required={scope}` |
| Agent suspended | 403 | `{"error":"forbidden","code":"STATE_001"}` | `STATE_ERR: Agent suspended; ID={id}` |
| Brute force detected | 429 | `{"error":"rate_limited","code":"ABUSE_001"}` | `ABUSE: Brute force; Count={n}/min` |
| PII leak attempt | 403 | `{"error":"forbidden","code":"DATA_001"}` | `DATA_BLOCK: PII to public; Hash={h}` |
| Canon modification | 403 | `{"error":"forbidden","code":"CONST_001"}` | `CONST_BLOCK: Canon write attempt` |

---

## DEFERRED SCOPE REGISTER

### Explicitly Deferred Components

| Component | Reason for Deferral | Risk of Deferral | Mitigation Strategy |
|-----------|---------------------|------------------|---------------------|
| **Dynamic Risk Scoring Engine** | Requires ML/runtime logic; violates PDP purity | MEDIUM | Use static thresholds; defer to downstream risk service |
| **Multi-Party Consensus Workflow** | Human workflow orchestration outside Sarathi scope | LOW | All ambiguous → DENY; manual escalation path |
| **Hardware TPM Attestation** | Implementation detail of Identity Provider | MEDIUM | Assume IdP handles attestation; Sarathi verifies IdP signature |
| **Orchestrator Callback Handling** | Sarathi is data diode; cannot handle callbacks | LOW | Architectural constraint; WONTFIX |
| **Real-Time Learning/Adaptation** | Policy drift risk; adversarial poisoning | HIGH | Static policy only; changes via formal amendment |
| **Cost/Billing Integration** | Financial logic complexity; attack surface | MEDIUM | Defer to separate billing service |
| **Geo-DNS Routing** | Infrastructure concern, not governance | LOW | Assume infrastructure handles routing |
| **Session Encryption Details** | Cryptographic implementation detail | LOW | Assume TLS for transport; focus on token validation |
| **Agent Ranking/Recommendation** | Scope creep; introduces subjective judgment | HIGH | Explicitly out of scope per Canon |
| **Retry Logic / Exponential Backoff** | Orchestration concern, not governance | LOW | Return refusal; client handles retry |

### Rules Not Fully Formalized (with Justification)

| Rule ID | Rule Name | Why Deferred | Risk | Priority to Address |
|---------|-----------|--------------|------|---------------------|
| AC-28 | Bias Auditor Safe Harbor | Complex ethics context evaluation | MEDIUM | P2 |
| EL-40 | Geofencing Enforcement | Requires GeoIP integration | LOW | P3 |
| EL-41 | Temporal Window Enforcement | Requires ops calendar integration | LOW | P3 |
| AI-57 | Policy Version Archive | Implementation detail | LOW | P3 |
| BN-60 | No Agent Ranking | Already out of scope | N/A | N/A |

---

## CHANGE REQUEST SUMMARY

#### MUST-FIX (Blocking for Production)

| ID | Issue | Risk | Recommended Fix |
|----|-------|------|-----------------|
| MF-01 | Natural Language Canon | Semantic drift within 2 years | Convert to Policy-as-Code |
| MF-02 | Optional Token Enforcement | Orchestrators may ignore refusals | Cryptographic capability tokens required |
| MF-03 | Missing Fail-Closed | Sarathi outage creates security gap | Heartbeat monitoring; default DENY |
| MF-04 | Single Admin Risk | One compromised admin can rewrite Canon | Multi-party (quorum) approval |
| MF-05 | Long Token TTL | Tokens survive revocation | Maximum 60-second TTL |

#### SHOULD-FIX (High Priority, Not Blocking)

| ID | Issue | Risk | Recommended Fix |
|----|-------|------|-----------------|
| SF-01 | Rate limiting on refusals | Brute force attacks | Implement EL-39 logic |
| SF-02 | Cascading revocation | Orphan agents with valid tokens | Implement LS-19 logic |
| SF-03 | Aggregate risk tracking | Distributed exfiltration | Implement EL-44 logic |
| SF-04 | Delegation protocol gaps | User proxy attacks | Full ID-08 implementation |
| SF-05 | Time-bounded elevations | Privilege persistence | Implement AC-30 logic |

#### NICE-TO-HAVE (P3, Future Consideration)

| ID | Issue | Impact | Recommendation |
|----|-------|--------|----------------|
| NH-01 | Geofencing | Regional compliance | Add when multi-region deployed |
| NH-02 | Temporal windows | Maintenance safety | Add when ops procedures mature |
| NH-03 | Advanced mosaic detection | Inference attack prevention | Research phase |
| NH-04 | Real-time dashboards | Observability | Defer to separate tooling |
| NH-05 | Policy simulation | Testing safety | Add in V2 |

---

## GOVERNANCE READINESS STATEMENT

### Assessment Verdict

**GOVERNANCE READINESS: CONDITIONAL GO / HIGH-INTEGRITY BASELINE ESTABLISHED**

### Justification

If the implementation team were to commence coding immediately based on this specification, the Sarathi governance layer would be **sufficient to establish a secure Zero Trust baseline** for initial agent onboarding. The formalization provided herein:

1. **Deterministically blocks** the "Forbidden Six" agent classes (Rules ID-05, ID-06, ID-07, EL-36, LS-20, AC-31)
2. **Safely enables** the "Dangerous Four" agent classes with appropriate constraints (Rules AC-27, AC-28, AC-29, ID-10)
3. **Resolves** the "Ambiguous Two" agent classes with explicit delegation and learning restrictions (Rules ID-08, LS-14)
4. **Enforces** Zero Trust default-deny posture (Rule AC-21)
5. **Maintains** audit immutability (Rules AI-53, AI-54, AI-55)

### Conditional Dependencies

The "GO" decision is conditional upon:

1. **Capability Token Implementation** - Downstream Resource Servers MUST validate Sarathi-issued tokens. Governance logic is sound; enforcement depends on token verification.

2. **MUST-FIX Items Addressed** - The five MUST-FIX items (MF-01 through MF-05) must be scheduled for implementation within 90 days of initial deployment.

3. **Fail-Closed Default** - If Sarathi becomes unavailable, all downstream systems MUST default to DENY, not ALLOW.

### Risk Acceptance

The following risks are **ACCEPTED** for initial deployment:

| Risk | Acceptance Rationale |
|------|---------------------|
| 50-100ms latency overhead | Security cost; acceptable for governance |
| Occasional false positive refusals | Better to block legitimate than allow malicious |
| User friction | Governance that stops nobody governs nothing |
| Deferred geofencing | Regional compliance addressed post-launch |

### Final Statement

> "If implementation began tomorrow, this specification would be **SUFFICIENT** with conditions.
> The governance layer is **implementable without interpretation**.
> The safety-critical paths are **deterministically defined**.
> The scope boundaries are **explicitly maintained**.
> 
> Sarathi is ready to serve as the Constitutional Authority for agent governance."

---

**END OF DOCUMENT**

---

## DOCUMENT METADATA

| Field | Value |
|-------|-------|
| Total Rules | 60 |
| CORE Rules | 20 |
| SAFETY-CRITICAL Rules | 24 |
| SUPPORTING Rules | 16 |
| Compliance Matrix Entries | 35 |
| Rego Policy Rules | 20 |
| Negative Test Cases | 25 |
| Refusal Types | 6 |
| Deferred Items | 10 |
| MUST-FIX Items | 5 |
| SHOULD-FIX Items | 5 |
| NICE-TO-HAVE Items | 5 |

---

## ADDENDUM: FORMAL VERIFICATION PIPELINE (GAP 3 RESOLUTION)

*Added during Gap Resolution Phase — Addresses Gap 3: "No formal verification strategy." This brings Sarathi policy verification to parity with and beyond AWS Cedar's Lean 4 proofs and SMT-based analysis.*

### FV.1 Five-Stage Verification Pipeline

| Stage | Method | Tool | What It Proves | Cadence |
|---|---|---|---|---|
| 1 | **Lean 4 Formal Proofs** | Lean 4 + Mathlib | Engine semantics: default-deny, forbid-overrides, order-independence, termination, delegation monotonicity, revocation completeness | On engine change |
| 2 | **SMT Policy Analysis** | CVC5 via Cedar-Lean compiler | Per-policy: no shadowed permits, no impossible conditions, no unintended forbid overrides, complete denials detected | Every policy merge |
| 3 | **Differential Random Testing** | Custom Rust + Lean harness | Implementation matches formal model on millions of random inputs (4 vCPU, 8GB, 6hrs/day) | Daily continuous |
| 4 | **Property-Based Testing** | cargo fuzz + Arbitrary | Invariants: empty policy = deny, adding permit only adds permissions, adding forbid only removes permissions, idempotency | Every build |
| 5 | **Mutation Testing** | Custom mutant generator | Mutation score ≥ 98%: CRE (flip effect), CRC (change combining), ANR (add rule), RER (remove rule), RTT/RTF (force target match), RCT/RCF (force condition) | Pre-release gate |

### FV.2 Properties Formally Proven in Lean 4

| Property | Statement | Proof Status |
|---|---|---|
| **P1 — Default Deny** | If no `permit` rule is satisfied, the PDP returns DENY | REQUIRED |
| **P2 — Explicit Deny Wins** | If any `forbid` rule is satisfied, PDP returns DENY regardless of permits | REQUIRED |
| **P3 — No Error Verdict** | Evaluation always returns ALLOW, DENY, or ESCALATE — never an error | REQUIRED |
| **P4 — Order Independence** | Evaluation order and rule duplicates do not affect the verdict | REQUIRED |
| **P5 — Sound Slicing** | Policy-slicing optimization produces same verdict as full evaluation | REQUIRED |
| **P6 — Validation Soundness** | If validator accepts a policy, evaluation never produces type error | REQUIRED |
| **P7 — Termination** | All PDP functions always terminate | REQUIRED |
| **P8 — Delegation Monotonicity** | Adding attenuation caveats to a Biscuit token can only reduce permissions, never expand them | REQUIRED |
| **P9 — Revocation Completeness** | Revoking a delegation token denies all requests authorized solely through that token's chain | REQUIRED |

### FV.3 CI/CD Integration Rules

- **Policy merge blocked** if SMT analysis detects shadowed permits, impossible conditions, or if refactored policy is more permissive than original.
- **Release blocked** if mutation score < 98% (undetected mutants indicate test suite gaps).
- **Deployment blocked** if DRT finds any divergence between Lean model and Rust implementation.
- **SMT timeout = BLOCK** (not "safe"). Indeterminate results require human review.

### FV.4 Verification Coverage Targets

| Metric | Target | Rationale |
|---|---|---|
| Lean proof compilation | < 3 minutes | Cedar benchmark |
| SMT analysis per policy | < 75ms average | Cedar Analysis benchmark |
| DRT daily volume | > 1 million random inputs | Cedar production standard |
| Mutation score | ≥ 98% | Industry best practice |
| OPA/Rego line coverage | ≥ 95% | OPA recommended threshold |
| Property test iterations | > 100,000 per property | QuickCheck standard |

