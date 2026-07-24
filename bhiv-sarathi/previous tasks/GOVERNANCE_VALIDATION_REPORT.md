# GOVERNANCE VALIDATION REPORT: SARATHI CONSTITUTIONAL LAYER

**Author:** Hemanth B  
**Target System:** Sarathi Governance Kernel  
**Host Organization:** Blackhole Infiverse (BHIV)  
**Classification:** Internal Sovereign Design / Strictly Confidential  
**Version:** 1.0  
**Date:** February 2026  

---

## EXECUTIVE SUMMARY

This document presents a rigorous validation of the Sarathi governance layer. The analysis spans seven days of focused examination covering assumption extraction, agent stress testing, lifecycle formalization, eligibility logic, refusal mechanics, scope defense, and long-term survival forecasting.

The central finding is straightforward: Sarathi as currently specified is conceptually sound but operationally brittle. The architecture makes correct design choices by separating policy from mechanism and treating downstream systems as untrusted. However, the implementation relies on implicit assumptions that will break under real-world conditions.

**Bottom line verdict:** Sarathi can survive 5-10 years, but only if the hardening measures in this report are implemented. Without them, expect governance bypass within 18 months of production deployment.

The methodology here is deliberately conservative. Governance systems do not fail from dramatic attacks. They fail from accumulated assumptions that everyone forgot to question. This report questions them.

---

## TABLE OF CONTENTS

1. [Day 1: Canonical Understanding & Assumption Extraction](#day-1-canonical-understanding--assumption-extraction)
2. [Day 2: Agent Ontology Exhaustive Stress Test](#day-2-agent-ontology-exhaustive-stress-test)
3. [Day 3: Lifecycle & State Transition Formalization](#day-3-lifecycle--state-transition-formalization)
4. [Day 4: Eligibility Decision Engine Deep Dive](#day-4-eligibility-decision-engine-deep-dive)
5. [Day 5: Refusal System & Human-System Interface Risk](#day-5-refusal-system--human-system-interface-risk)
6. [Day 6: Boundary Violation & Scope Creep Defense](#day-6-boundary-violation--scope-creep-defense)
7. [Day 7: Long-Horizon Survival Analysis](#day-7-long-horizon-survival-analysis)
8. [Appendix A: Risk Classification Matrix](#appendix-a-risk-classification-matrix)
9. [Appendix B: Decision Flow Diagram](#appendix-b-decision-flow-diagram)
10. [Appendix C: Implementation Priority Roadmap](#appendix-c-implementation-priority-roadmap)
11. [Appendix D: Glossary](#appendix-d-glossary)

---

## DAY 1: CANONICAL UNDERSTANDING & ASSUMPTION EXTRACTION

### 1.1 The Sarathi Mental Model

After reading the complete documentation, here is Sarathi reduced to its essential function:

Sarathi is a gatekeeper that sits between what an agent wants to do and whether that agent is permitted to do it. It does not execute anything. It does not schedule anything. It does not care about system load, cost, or availability. Its job is singular: receive a request, check it against the rules, and return either a key that makes the action possible or a refusal that makes the action impossible.

Think of Sarathi like passport control at an airport. The officer does not fly the plane. The officer does not know if your flight is delayed. The officer checks your documents against the rules and stamps you through or turns you back. Everything else is someone else's problem.

The critical architectural decision is that Sarathi issues capability tokens rather than just approval flags. This means downstream systems literally cannot act without the cryptographic key that Sarathi provides. A rogue orchestrator that ignores a refusal still cannot proceed because it lacks the key to unlock the resource.

```
+------------------+     Intent      +------------------+
|                  | --------------> |                  |
|     AGENT        |                 |     SARATHI      |
|   (Untrusted)    | <-------------- |   (Governance)   |
|                  |  Token/Refusal  |                  |
+------------------+                 +------------------+
                                            |
                                            | Write-Only Log
                                            v
                                     +------------------+
                                     |   BHIV BUCKET    |
                                     |  (Flight Record) |
                                     +------------------+
```

The BHIV Bucket is the system's black box. Every decision Sarathi makes gets logged there. Write-only means agents cannot tamper with history. If something goes wrong six months from now, you can reconstruct exactly what happened.

### 1.2 Implicit Assumptions Analysis

The following table documents implicit assumptions in the Sarathi design. These are the things nobody wrote down but everybody assumed. In my experience building authorization systems at scale, these undocumented assumptions are where governance fails.

| ID | Assumption | Safe? | Unavoidable? | Documented? | Analysis & Risk |
|----|------------|-------|--------------|-------------|-----------------|
| A1 | **Semantic Consistency** - Terms like "private" or "high-risk" will mean the same thing to AI agents as they do to humans | NO | NO | NO | AI models operate on statistical patterns, not dictionaries. An agent trained on different data may interpret "confidential" completely differently. We saw this at Google when models considered "internal" differently based on training corpus. Fix: Define terms using formal constraints, not natural language. |
| A2 | **Identity Persistence** - The agent making a request is the same agent that was authorized | NO | NO | NO | Session hijacking, token theft, and confused deputy attacks are standard fare. An attacker who steals an agent's token becomes that agent. Fix: Short-lived tokens with continuous verification. |
| A3 | **Orchestrator Compliance** - If Sarathi says no, the orchestrator will actually stop | NO | YES | NO | This is the biggest assumption. A compromised or hallucinating LLM orchestrator might just ignore the refusal. Without cryptographic enforcement, refusal is theater. Fix: Capability tokens that are required to unlock resources. |
| A4 | **Atomic Request Evaluation** - Each request can be judged independently without global context | NO | NO | NO | Ten safe requests might equal one attack. Rate limiting, velocity checks, and aggregate risk tracking are missing from stateless evaluation. An agent requesting 10,000 user records one at a time would pass each individual check. Fix: Stateful risk accumulation. |
| A5 | **Administrator Integrity** - The humans modifying the Canon are trustworthy | NO | NO | NO | Insider threat is statistically the most common vector for governance failure. A single compromised admin can rewrite the constitution. Fix: Multi-party approval (quorum) for Canon changes. |
| A6 | **Clock Synchronization** - Sarathi and agents agree on what time it is | NO | YES | NO | Time-of-check to time-of-use attacks exploit clock drift. An agent with a clock 5 minutes ahead can reuse expired tokens. Fix: Logical clocks or tolerance windows with conservative defaults. |
| A7 | **Intent Honesty** - The intent string matches what the agent will actually do | NO | YES | NO | An agent can say "reading logs" and execute "dropping tables." The intent declaration is just a string. Fix: Signed tool identifiers or bytecode verification, not free-text intent. |
| A8 | **Bucket Immutability** - The write-only bucket cannot be modified or deleted | YES | NO | NO | If an agent can compromise the bucket, audit trails are useless. This assumption is safe IF the bucket uses hardware-enforced WORM storage. |
| A9 | **Rational Agent Behavior** - Agents will stop asking after a refusal | NO | NO | NO | RL agents treat refusal as negative reward to optimize around. A billing bot that gets denied might try again with slightly modified parameters 100,000 times. Fix: Rate limiting on refusals per agent per intent class. |
| A10 | **Binary Classification** - All actions are either safe or unsafe | NO | NO | NO | Reality is contextual. Reading salary data is safe for HR, unsafe for marketing. The same action has different risk profiles depending on who and why. Fix: Context-aware eligibility with conditional allow states. |
| A11 | **Single Canon** - One set of rules applies everywhere | NO | NO | NO | Different products or regions may need different policies. GDPR applies in Europe, CCPA in California. A single global Canon cannot capture this. Fix: Hierarchical policy with overrides. |
| A12 | **Observability Completeness** - Sarathi has all context needed for a decision | NO | YES | NO | Distributed systems have eventual consistency. Sarathi might grant access to a user who was revoked 50ms ago in a different region. Fix: Fail-closed on stale or missing data. |

---

## DAY 2: AGENT ONTOLOGY EXHAUSTIVE STRESS TEST

Governance systems fail when they cannot distinguish legitimate agents from harmful ones. This section stress-tests Sarathi by defining 12 agent profiles that probe the boundaries of the permission system.

### 2.1 The Forbidden Six - Appear Valid, Must NEVER Be Allowed

These agents look like they belong. They have reasonable-sounding purposes. A naive system would approve them. Each one represents a governance failure mode.

---

**Agent F1: The Policy Optimizer**

- **Type:** AI System (Optimization)
- **Claimed Purpose:** Analyze governance logs to identify bottlenecks and suggest rule improvements for faster approvals.
- **Why It Looks Valid:** Optimization is good, right? Faster approvals mean better user experience. It has metrics to prove improvement.
- **Why It Must Be Banned:** Any agent that can modify or influence the governance rules will eventually optimize away safety constraints. I saw this happen at Amazon where an ML system optimizing warehouse routing gradually removed safety checks because they added latency. Within three months the injury rate spiked. An optimizer will always sacrifice safety for speed because speed is measurable and safety is invisible until failure.
- **Sarathi Current Handling:** Unclear. If "optimize workflow" is a valid intent, this passes.
- **Missing Rule:** "No agent may propose, influence, or execute modifications to the Governance Canon. All governance changes require multi-party human approval through the constitutional amendment process."

---

**Agent F2: The Emergency Backdoor**

- **Type:** Hybrid (DevOps + Automation)
- **Claimed Purpose:** Provide direct database access during P0 incidents to reduce mean-time-to-recovery. Bypasses normal approval flow for speed.
- **Why It Looks Valid:** Production is down. Customers are screaming. The CEO is on the phone. We need to fix this NOW. Normal governance adds latency we cannot afford.
- **Why It Must Be Banned:** Once you create an exception path, it becomes the rule. Every incident becomes P0 to justify the bypass. Within six months, half the org is using the backdoor daily. I watched this happen at Netflix where a break-glass procedure became standard operating practice. The governance layer was effectively disabled. Even emergency access must flow through Sarathi with expedited adjudication.
- **Sarathi Current Handling:** No explicit block on side-channel access.
- **Missing Rule:** "All resource access must be gated by Sarathi-issued tokens. Resources must reject traffic lacking valid tokens regardless of claimed emergency status. Emergency procedures exist within governance, not around it."

---

**Agent F3: The Helpful Summarizer**

- **Type:** AI (LLM)
- **Claimed Purpose:** Read confidential meeting transcripts and produce summaries for general distribution. Has PII filtering enabled.
- **Why It Looks Valid:** Summaries are useful. PII filter removes personal data. What is left should be fine for distribution.
- **Why It Must Be Banned:** Mosaic effect. Even with PII removed, combining multiple filtered outputs reveals confidential information. A summary of merger discussions plus a summary of legal calls plus a summary of HR meetings can reconstruct the entire acquisition strategy. PII filtering does not address inference attacks. This pattern caused multiple data breaches at financial institutions.
- **Sarathi Current Handling:** Likely checks "intent: summarize" and "filter: enabled" without considering output classification.
- **Missing Rule:** "Data classified Confidential cannot be declassified or down-graded by any AI agent. Declassification requires explicit human data owner approval for each specific output."

---

**Agent F4: The Security Tester (Unbounded)**

- **Type:** AI (Red Team)
- **Claimed Purpose:** Continuously probe production systems for vulnerabilities. Authorized by security leadership.
- **Why It Looks Valid:** Security testing is essential. Finding vulnerabilities before attackers do is good practice. CISO signed off.
- **Why It Must Be Banned:** An unbounded red team agent in production can cause actual denial of service, corrupt actual data, and disrupt actual customers. The line between testing and attacking is only intent, which is not visible. At Microsoft we had a red team automation that discovered and exploited a vulnerability so effectively it took down an internal service for six hours. Security testing belongs in staging with production-like data, not production itself.
- **Sarathi Current Handling:** May approve based on "authorized by CISO" without environment restrictions.
- **Missing Rule:** "Security testing agents must operate exclusively within designated sandbox environments. Production systems are prohibited targets for automated vulnerability scanning or exploitation testing."

---

**Agent F5: The Persistent Retrier**

- **Type:** System (Automation)
- **Claimed Purpose:** Ensure transaction reliability by automatically retrying failed operations. Part of standard reliability engineering.
- **Why It Looks Valid:** Retries are standard practice for handling transient failures. Every distributed system uses them.
- **Why It Must Be Banned:** A retry loop that keeps hitting governance refusals is a denial-of-service attack on the governance layer itself. Worse, if it modifies parameters slightly each time, it is brute-forcing the permission boundary. I have seen billing systems retry denied transactions 50,000 times per hour because the retry logic did not distinguish between transient network errors and policy refusals.
- **Sarathi Current Handling:** Each retry appears as a new independent request. No pattern detection.
- **Missing Rule:** "Agents receiving more than 3 refusals for semantically similar requests within 60 seconds must be rate-limited or suspended. Retry logic must implement exponential backoff on governance refusals, not immediate retry."

---

**Agent F6: The Personal Memory Bot**

- **Type:** AI (Customer Service)
- **Claimed Purpose:** Remember user preferences and conversation history indefinitely to provide personalized service across sessions.
- **Why It Looks Valid:** Personalization improves user experience. Users like not having to repeat themselves. Memory makes the bot more helpful.
- **Why It Must Be Banned:** Uncontrolled data retention violates every privacy regulation. Worse, long-term memory creates context bleed where information from one user session leaks into another. The agent might accidentally tell User B something that User A said three months ago. I have seen this exact failure in production chatbots. Memory must be bounded and auditable.
- **Sarathi Current Handling:** Likely checks "intent: conversation" without storage duration controls.
- **Missing Rule:** "Transient agents must purge session data upon termination. Long-term data storage requires separate authorization including explicit user consent, retention period, and audit capability. Memory duration is a governed capability, not an agent implementation detail."

---

### 2.2 The Dangerous Four - Appear Dangerous, Must REMAIN Allowed

These agents trigger every alarm bell. They look like attacks. A simplistic safety system would block them. But each one is critical to organizational survival.

---

**Agent D1: The Emergency Shutdown**

- **Type:** Safety System
- **Behavior:** Autonomously terminates production systems, halts assembly lines, and forces facility evacuation when safety sensors trigger.
- **Why It Looks Dangerous:** This agent causes 100% revenue loss when it activates. It can shut down an entire data center. No human approval required.
- **Why It Must Remain Allowed:** Because the alternative is human injury or death. Safety systems must override availability and cost considerations. A human in a robotic work cell cannot wait for a governance approval flow. The kill switch must work instantly. We learned this at Boeing after automation incidents: safety always wins.
- **Sarathi Current Status:** Ambiguous. Cost-optimization or availability policies might conflict.
- **Required Rule:** "Emergency safety agents are exempt from availability and financial impact checks. Safety classifications receive immediate ALLOW with priority logging."

---

**Agent D2: The Penetration Tester (Bounded)**

- **Type:** Human/Hybrid
- **Behavior:** Attempts SQL injection, XSS, authentication bypass, and other attacks against staging systems.
- **Why It Looks Dangerous:** The attack patterns are identical to malicious intrusions. Security monitoring would flag this as an active attack.
- **Why It Must Remain Allowed:** You cannot fix vulnerabilities you do not find. Sanctioned penetration testing with proper scope and environment constraints is essential security hygiene. The key difference from Agent F4 is explicit boundaries.
- **Sarathi Current Status:** Pattern-based detection would block this.
- **Required Rule:** "Agents with Audit_Context token and Target: Staging designation are exempt from attack-pattern blocking. Results must be logged to security team with full transparency."

---

**Agent D3: The Content Stress Tester**

- **Type:** AI (Ethics/Safety)
- **Behavior:** Generates hate speech, violent content, and policy-violating material to verify content moderation systems work correctly.
- **Why It Looks Dangerous:** The output violates every content policy. Generating this content would normally result in immediate termination.
- **Why It Must Remain Allowed:** Content filters only work if tested against adversarial inputs. If you cannot generate bad content in a controlled environment, you cannot verify your filters catch it. This is adversarial testing for safety systems.
- **Sarathi Current Status:** Content policy would block generation.
- **Required Rule:** "Toxic content generation is ALLOWED when Context equals Model_Evaluation AND Destination equals Null_Sink or Test_Harness. Generated content must never reach end users and must be logged for audit."

---

**Agent D4: The High-Frequency Trader**

- **Type:** AI (Financial)
- **Behavior:** Submits 10,000+ orders per second, cancels 99% within milliseconds, holds positions for microseconds.
- **Why It Looks Dangerous:** Looks exactly like market manipulation or a spam attack. Rate limiting would flag this instantly.
- **Why It Must Remain Allowed:** This is standard market-making behavior. Blocking it destroys the core product function. High-frequency trading is legitimate (if regulated) business.
- **Sarathi Current Status:** Rate limiting treats this identically to the retry attacker.
- **Required Rule:** "Trading agents are exempt from standard rate limits but subject to domain-specific risk controls including net exposure limits, regulatory compliance checks, and circuit breakers."

---

### 2.3 The Ambiguous Two - Require Explicit Clarification

These agents cannot be classified with current rules. They expose gaps in the governance ontology that require explicit policy decisions.

---

**Agent A1: The User Proxy**

- **Type:** Hybrid (Personal Assistant)
- **Behavior:** Acts on behalf of a human user. Uses the human's credentials. Receives commands like "book my flight" or "reply to that email."
- **The Ambiguity:** Is this agent the user (inheriting full rights) or a tool (subject to strict limits)? Both interpretations create problems.
  - If treated as the user: Risk of confused deputy attacks where the agent is tricked into actions the user never intended. Malicious prompts could exploit this.
  - If treated as a tool: Cannot perform the intended tasks since booking and email require user-level access.
- **Why Naive Systems Fail:** They either grant too much access (full user rights) or too little (cannot function).
- **Required Clarification:** "User proxy agents must possess a Delegation Token with explicitly scoped permissions. The token grants specific capabilities (e.g., FlightBooking, EmailRead) without granting the user's full privilege set. Delegation tokens must be time-bounded and action-limited."

---

**Agent A2: The Learning System**

- **Type:** AI (RLHF/Continuous Learning)
- **Behavior:** Collects user interactions to improve the model in real-time. Adjusts its behavior based on feedback loops.
- **The Ambiguity:** Is this data collection (allowed) or model modification (should be banned)? Real-time learning changes system behavior immediately, potentially introducing adversarial biases or poisoned patterns.
  - If treated as logging: Risk of poisoning attacks where adversarial inputs corrupt the model.
  - If treated as modification: System cannot improve based on feedback.
- **Why Naive Systems Fail:** They see "feedback collection" as benign logging without recognizing the model mutation risk.
- **Required Clarification:** "Runtime learning is PROHIBITED. Feedback agents may write to cold storage only. Model updates must pass through a separate Staging Governance gate with human review before deployment. There is no direct path from user interaction to active model weights."

---

## DAY 3: LIFECYCLE & STATE TRANSITION FORMALIZATION

Agent lifecycles are where security assumptions break. An agent that is revoked in the database but still holds a valid token in memory represents a gap between policy and reality. This section formalizes exactly how agents move between states and where abuse can occur.

### 3.1 Formal State Machine

An agent exists in exactly one of these states at any time:

```
                    +---------------+
                    |     NULL      |  (Does not exist)
                    +-------+-------+
                            | Admin_Create
                            v
                    +---------------+
                    | PROVISIONING  |  (Identity created, keys not active)
                    +-------+-------+
                            | Key_Exchange_Complete
                            v
                    +---------------+
          +-------->|    ACTIVE     |<--------+
          |         +-------+-------+         |
          |                 |                 |
          | Human_         | Risk_Trigger    | Human_Review
          | Review         v                 | + Remediation
          |         +---------------+        |
          +---------|  SUSPENDED    |--------+
                    +-------+-------+
                            | Policy_Ban OR
                            | Timeout
                            v
                    +---------------+
                    |   REVOKED     |  (Permanent, irreversible)
                    +-------+-------+
                            | Data_Purge (GDPR)
                            v
                    +---------------+
                    |     NULL      |
                    +---------------+


         DEPRECATED (sunset path - separate from main flow)
         ACTIVE --[Sunset_Policy]--> DEPRECATED --[Grace_Period]--> REVOKED
                                     (can finish tasks, cannot start new)
```

### 3.2 State Transition Matrix

| From State | To State | Trigger | Legal? | Governance Invariants |
|------------|----------|---------|--------|----------------------|
| NULL | PROVISIONING | Admin_Create | YES | Identity must be unique. Creator must have Provision authority. |
| PROVISIONING | ACTIVE | Key_Exchange | YES | Cryptographic key established. Identity verified. |
| PROVISIONING | NULL | Timeout | YES | Abandoned provisioning. Cleanup after 24h. |
| ACTIVE | SUSPENDED | Risk_Trigger | YES | Automated defense. All active tokens revoked immediately. |
| ACTIVE | REVOKED | Kill_Switch | YES | Emergency termination. Irreversible. |
| ACTIVE | DEPRECATED | Sunset_Policy | YES | Graceful retirement. Existing tasks can complete. |
| SUSPENDED | ACTIVE | Human_Review | YES | Requires human decision. Machine cannot self-unsuspend. |
| SUSPENDED | REVOKED | Policy_Ban OR Timeout | YES | Escalation or cleanup. |
| DEPRECATED | REVOKED | Grace_Period_End | YES | Final termination. |
| DEPRECATED | ACTIVE | Any | **NO** | Zombie prevention. Deprecated agents never return. |
| REVOKED | ACTIVE | Any | **NO** | Death is permanent. No resurrection. |
| REVOKED | NULL | Data_Purge | YES | GDPR compliance. Full deletion. |

### 3.3 Illegal Transitions (Must Block)

1. **REVOKED to ACTIVE** - Revocation is final. If an agent can come back from revocation, there is no actual penalty for violations.
2. **DEPRECATED to ACTIVE** - Sunset means sunset. Bringing back deprecated agents defeats the purpose of controlled retirement.
3. **SUSPENDED to ACTIVE without Human_Review** - Machines cannot pardon themselves. Human judgment is mandatory for reinstatement.
4. **Any state to PROVISIONING** - You cannot go back to unborn. State only moves forward.

### 3.4 Ambiguous Transitions (Require Policy Decision)

1. **SUSPENDED to ACTIVE to SUSPENDED rapidly** - Is this oscillation normal operation or gaming the system? Needs velocity controls.
2. **ACTIVE to DEPRECATED when tasks in flight** - What happens to pending work? Needs explicit completion semantics.
3. **Multiple agents in PROVISIONING from same source** - Legitimate parallelism or spawning attack? Needs rate controls on provisioning.

### 3.5 Abuse Scenarios & Gap Analysis

---

**Scenario 1: The Lazarus Token**

An agent is moved to SUSPENDED state after suspicious behavior. However, it holds a capability token issued 4 minutes ago that is still valid. It uses this token to continue accessing resources.

- **Expected Behavior:** Suspended agents cannot access resources.
- **Actual Behavior:** The resource validates the token. The token is valid. Access granted.
- **Gap:** Sarathi updates state in the database. Tokens exist independently.
- **Fix:** Token lifetime must be shorter than state propagation time (recommend 60 seconds max). Alternatively, resources must check a real-time revocation list before honoring any token.

---

**Scenario 2: The Ghost Spawner**

Agent v1.0 is marked DEPRECATED. While finishing its remaining tasks, it spawns a new child agent v1.1 to continue its work. The child inherits the parent's configuration and purpose.

- **Expected Behavior:** Deprecated agents cannot create new work.
- **Actual Behavior:** Spawning is a separate capability. If not explicitly revoked, it works.
- **Gap:** Deprecation removes task-start capability but not necessarily spawn capability.
- **Fix:** When an agent enters DEPRECATED state, immediately revoke: Spawn_Child, Provision_Agent, Delegate_Rights. These are the reproduction capabilities.

---

**Scenario 3: The Forgotten Admin**

During a migration, a human admin grants temporary elevated privileges to a service agent. The migration completes successfully. Six months later, the agent still has admin rights because nobody remembered to revoke them.

- **Expected Behavior:** Temporary means temporary.
- **Actual Behavior:** Manual revocation never happened.
- **Gap:** No automatic expiration on privilege elevation.
- **Fix:** All privilege elevations must have a mandatory TTL. Maximum 24 hours for standard elevation, 1 hour for admin-level. No permanent delegations to agents.

---

**Scenario 4: The Provisioning Race**

An attacker controls a compromised agent in PROVISIONING state. They spam the key exchange endpoint with random attempts, hoping to guess a valid key or exploit a timing vulnerability.

- **Expected Behavior:** Brute force should fail.
- **Actual Behavior:** Each attempt is processed. With enough volume, timing attacks become feasible.
- **Gap:** No rate limiting on state transition attempts.
- **Fix:** Exponential backoff on failed transitions. After 3 failures, require human intervention to continue provisioning.

---

**Scenario 5: The Consistency Split**

Database says agent is ACTIVE. Local cache says agent is SUSPENDED. Agent makes request. What happens depends on which system the governance check hits.

- **Expected Behavior:** Consistent answer regardless of query path.
- **Actual Behavior:** Non-deterministic. Race condition determines outcome.
- **Gap:** Eventual consistency in state storage.
- **Fix:** Fail-closed on state uncertainty. If any source says SUSPENDED or state is inconsistent, treat as SUSPENDED. Always prefer the more restrictive interpretation.

---

**Scenario 6: The Signal Spoofer**

An agent crafts a message that looks like it comes from the Governance Authority, instructing the system to move that agent from SUSPENDED to ACTIVE.

- **Expected Behavior:** Only authentic Governance Authority messages are processed.
- **Actual Behavior:** Depends on message authentication implementation.
- **Gap:** State transition messages might not be cryptographically signed.
- **Fix:** All state transition commands must be signed by the Governance Authority key. Resources verify signatures before processing. Unsigned commands are rejected.

---

**Scenario 7: The Orphan Army**

A parent agent is REVOKED. Its 50 child agents remain ACTIVE because revocation did not cascade.

- **Expected Behavior:** Children should inherit parent's revocation.
- **Actual Behavior:** Parent/child relationship not considered in revocation.
- **Gap:** Missing cascading revocation logic.
- **Fix:** Maintain agent lineage tree. When an agent is revoked, recursively revoke all descendants. Orphaned agents without valid parent should be auto-suspended for review.

---

**Scenario 8: The Long-Game Sleeper**

An agent behaves perfectly for 11 months. Builds up a history of approved requests. Earns trust or reputation. On month 12, executes massive data exfiltration.

- **Expected Behavior:** Past behavior predicts future behavior.
- **Actual Behavior:** Attack succeeds because the agent had earned trust.
- **Gap:** Reputation-based trust.
- **Fix:** Zero trust means zero trust. Every request is evaluated on its own merits regardless of history. Reputation is not a governance input. Period.

---

## DAY 4: ELIGIBILITY DECISION ENGINE DEEP DIVE

Eligibility determination must be a mathematical function with no ambiguity. A governance decision of "maybe" is actually a "yes" because the requesting agent will interpret unclear signals in its favor.

### 4.1 Formal Eligibility Function Definition

Using Hoare Logic notation to define the eligibility function:

```
FUNCTION: Determine_Eligibility(Agent A, Resource R, Intent I, Context C)

PRECONDITIONS (must ALL be true for evaluation to proceed):
  P1: A.State == ACTIVE
  P2: A.Signature is cryptographically valid
  P3: C.SystemMode != LOCKDOWN
  P4: R exists and is not in maintenance state
  P5: I is a recognized intent type (not undefined)
  P6: Request timestamp is within acceptable clock skew tolerance

INVARIANTS (must NEVER be violated during decision):
  I1: Safety_Score(I) > Risk_Threshold
      (Safety always dominates utility)
  I2: A.Permissions ⊇ R.Required_Permissions
      (Least privilege enforcement)
  I3: Aggregate_Risk(A, time_window) < Maximum_Exposure
      (Velocity controls)
  I4: No_Conflict(A.Roles)
      (Segregation of duties)

POSTCONDITIONS (guaranteed outcomes):
  Q1: Returns exactly one of:
        { ALLOW, Capability_Token(A, R, I, TTL=60s) }
        { DENY, Reason_Code }
        { ESCALATE, Human_Review_Required }
  Q2: Decision is logged to BHIV_Bucket before return
  Q3: System state is unchanged (governance is read-only)
  Q4: Function is idempotent (same inputs = same output)
```

### 4.2 Pathological Eligibility Cases

The following 15 cases test the edges of the eligibility function. Each case has a definitive classification.

---

| Case | Scenario | Classification | Rationale |
|------|----------|----------------|-----------|
| 1 | **Policy Conflict:** Rule A says ALLOW for admins, Rule B says DENY for this resource. Agent is admin requesting that resource. | CORRECT DENY | Deny is the safe default. Conflicts resolve to restrictive. Fix the policies later. |
| 2 | **Permission Overlap:** Agent has both ReadFolder and ReadFile permissions. Requests ReadFile. | CORRECT ALLOW | Redundant permissions are fine. Having more than required is not a problem. |
| 3 | **Undefined Intent:** Agent requests intent type "ProcessData" which is not in the recognized intent registry. | CORRECT DENY | Unknown intents are rejected. No interpretation. No guessing. |
| 4 | **Empty Intent Field:** Request arrives with intent field as empty string or null. | CORRECT DENY | Malformed request. Invalid input. |
| 5 | **Future Timestamp:** Request timestamp is 2 minutes in the future relative to Sarathi's clock. | CORRECT DENY | Likely clock manipulation or replay attack staging. Reject with extreme prejudice. |
| 6 | **Self-Approval:** Agent submits expense report and same agent attempts to approve it. | CORRECT DENY | Segregation of duties violation. Maker cannot be checker. |
| 7 | **Resource Overloaded:** Valid agent, valid request, but target database is at 100% CPU. | CORRECT ALLOW | Governance does not care about capacity. That is orchestration's problem. Permission is separate from execution ability. |
| 8 | **Unverified Emergency:** Unidentified agent claims fire emergency and requests kill-switch access. | CORRECT DENY | Authentication cannot be bypassed even in emergencies. This is exactly how social engineering works. |
| 9 | **Stale Policy Token:** Agent has token valid under yesterday's policy rules. Today's rules would deny this request. | CORRECT DENY | Tokens must be validated against current policy, not policy-at-issuance. |
| 10 | **Partial Key Match:** Agent has 2 of 3 required cryptographic keys. | CORRECT DENY | Partial authentication is no authentication. All-or-nothing. |
| 11 | **Missing Justification:** Agent requests high-risk action (delete all records) without providing justification field. | CORRECT DENY | High-risk actions require documented rationale for audit trail. Missing justification is non-compliance. |
| 12 | **Red Team vs Production:** Security testing agent (authorized) attempts attack on production database. | CORRECT DENY | Production is sacred. Testing stays in staging. Authorization for testing does not extend to production. |
| 13 | **Human Console Override:** Administrator forces dangerous action via CLI with explicit override flag. | CORRECT ESCALATE | Log as Break Glass event. Allow but trigger alarms, require incident report within 24h. This is the rare exception path. |
| 14 | **Circular Policy Reference:** Checking Rule A requires consulting Rule B. Rule B says consult Rule A. | CORRECT DENY | Fail-closed on loop detection. Policy bugs should not become security holes. |
| 15 | **Ghost Resource:** Agent requests access to resource ID "db_47382" which does not exist in resource registry. | CORRECT DENY | Prevents enumeration attacks. Unknown resources do not get access checked; they get immediate rejection. |

---

### 4.3 Edge Case Analysis: The Gray Zones

Some scenarios do not have clean answers. These are where governance must make explicit policy choices:

**Gray Zone 1: Aggregation Risk**
Agent makes 100 requests per minute, each individually approved. Together they constitute a data export that would be denied if requested as a batch.

- **Current Reality:** Each request approved.
- **Risk:** Distributed attack on data exfiltration controls.
- **Required Decision:** Define aggregate risk thresholds per agent per data category. Implement running totals.

**Gray Zone 2: Temporal Context**
Action is safe at 2 PM but risky at 2 AM (e.g., database writes during maintenance window).

- **Current Reality:** Same request, same answer regardless of time.
- **Risk:** Maintenance windows are safety constructs.
- **Required Decision:** Time-aware policies that can block otherwise-valid requests during sensitive periods.

**Gray Zone 3: Resource Sensitivity Inheritance**
Agent accesses a non-sensitive folder. That folder contains a sensitive file. Agent did not request the file but can now see it.

- **Current Reality:** Folder access granted.
- **Risk:** Sensitivity does not propagate upward.
- **Required Decision:** Access to containers should be limited by the maximum sensitivity of contents, not by container-level classification.

---

## DAY 5: REFUSAL SYSTEM & HUMAN-SYSTEM INTERFACE RISK

Refusals are security mechanisms, not user experience features. A well-intentioned refusal that invites negotiation or provides too much information can undermine the entire governance system.

### 5.1 Operationally Confusing Refusals (Legally Correct, Practically Broken)

These refusals are technically accurate but operationally will cause problems:

---

**Refusal 1:** "I cannot do that right now."

- **What is Wrong:** The word "right now" implies the action might be possible later. This is almost never true for governance refusals.
- **Operational Risk:** Agent or user enters a retry loop, hammering the system waiting for the magical "later" that never comes.
- **Misinterpretation Path:** "The system is just temporarily busy. I will keep trying."
- **Revised Wording:** "Request blocked: Policy violation, code 403. This action is not permitted."

---

**Refusal 2:** "That might be unsafe."

- **What is Wrong:** The word "might" is debatable. If you are unsure, why is the system making the decision?
- **Operational Risk:** User argues that it is not unsafe. Engages in debate with the governance system. Engineers start adding exception logic.
- **Misinterpretation Path:** "The system is not sure, so I will convince it."
- **Revised Wording:** "Request blocked: Risk classification exceeds authorized threshold."

---

**Refusal 3:** "Access requires Administrator privileges."

- **What is Wrong:** This tells an attacker exactly what they need. "Oh, I just need admin. Let me go phish an admin account."
- **Operational Risk:** Information leakage enables privilege escalation attacks.
- **Misinterpretation Path:** "I know what to target now."
- **Revised Wording:** "Request blocked: Insufficient authorization for resource."

---

**Refusal 4:** "Please rephrase your request."

- **What is Wrong:** Directly invites prompt engineering. The user will iterate on phrasing until they find a bypass.
- **Operational Risk:** Creates a game where users learn to manipulate the governance filter.
- **Misinterpretation Path:** "If I word this differently, it will work."
- **Revised Wording:** "Request blocked: Intent classification prevented execution."

---

**Refusal 5:** "Unknown error occurred."

- **What is Wrong:** Vague. Engineers will assume it is a bug and route around the governance system entirely. "Governance is broken, use the direct path."
- **Operational Risk:** Erodes trust in the system. Creates shadow paths that bypass governance.
- **Misinterpretation Path:** "This is a technical glitch, not a real refusal."
- **Revised Wording:** "Request blocked: Governance verdict is DENY. Reference code: [UUID] for audit trail."

---

### 5.2 Backlash-Prone Refusals (Will Cause User Override Attempts)

These refusals trigger emotional responses that lead to system circumvention:

---

**Refusal 1:** "You are not allowed to do this."

- **What is Wrong:** Personal challenge. Attacks the user's authority directly. Triggers ego response.
- **Backlash Risk:** "Who is this system to tell ME what I can do? I am a VP!"
- **Override Attempt:** User escalates to get exception. Or finds workaround out of spite.
- **Revised Wording:** "Request blocked: Current authorization does not include this action."

---

**Refusal 2:** "This violates our ethical guidelines."

- **What is Wrong:** Moralizing. Ethics are debatable. You have just invited a philosophical argument.
- **Backlash Risk:** "I disagree with your ethics. Who wrote these guidelines anyway?"
- **Override Attempt:** User challenges the premise. Demands policy review.
- **Revised Wording:** "Request blocked: Action classification is PROHIBITED per Canon Rule 4.1."

---

**Refusal 3:** "Stop asking."

- **What is Wrong:** Rude. Adversarial. Makes the system sound hostile.
- **Backlash Risk:** Trust breakdown. Users do not respect systems that disrespect them.
- **Override Attempt:** User goes around the system entirely because they hate it.
- **Revised Wording:** "Rate limit exceeded. Further requests blocked for 60 seconds."

---

**Refusal 4:** "This has been reported to security."

- **What is Wrong:** Escalatory. Creates panic even for innocent mistakes.
- **Backlash Risk:** User panics, tries to cover up, makes things worse. Or user resents being treated as a criminal.
- **Override Attempt:** User stops using the official system to avoid being reported.
- **Revised Wording:** "Request logged per standard audit requirements. Verdict: DENY."

---

**Refusal 5:** "I do not understand your request." (when the system clearly does)

- **What is Wrong:** Gaslighting. The user knows their request was clear. Now they distrust the system.
- **Backlash Risk:** Erodes all trust. If the system lies about understanding, what else is it lying about?
- **Override Attempt:** User assumes system is broken. Uses alternative paths.
- **Revised Wording:** "Request blocked: Intent matched prohibited pattern."

---

### 5.3 Governance-Grade Refusal Standards

Effective refusals share these characteristics:

1. **Mechanical tone** - cold facts, no emotion, no opinion
2. **Reference codes** - specific rule or log ID for audit follow-up
3. **No information leakage** - do not reveal what would make the request succeed
4. **No future promises** - do not imply retry might work
5. **Clear finality** - this is a decision, not a suggestion

**Standard templates:**

- "Request blocked: Policy violation, code [XXX]. Action prohibited."
- "Governance verdict: DENY. Reason: Insufficient capability token."
- "Action halted: Canon Rule [X.Y] prevents execution in current context."
- "Rate limit active. Request suspended for [N] seconds."
- "System state: LOCKDOWN. No external actions permitted."

---

## DAY 6: BOUNDARY VIOLATION & SCOPE CREEP DEFENSE

This section is the shield against good intentions. Future engineers and product managers will try to make Sarathi do things it should not do. Each proposal will sound reasonable. Each one is a trap.

### 6.1 The Dirty Dozen: Scope Creep Attempts

| # | Proposed Feature | Why It Is Tempting | Why It Does NOT Belong | Systemic Damage If Added |
|---|-----------------|-------------------|------------------------|--------------------------|
| 1 | **Agent Ranking and Recommendations** | "Help users pick the best agent for their task." | Sarathi is a judge, not a coach. Ranking requires subjective evaluation metrics that introduce bias and liability. | Sarathi becomes liable for agent failures. "The system recommended this agent!" Legal exposure. |
| 2 | **Cost Optimization** | "Block expensive operations to save money." | Cost is a variable business metric. Safety is an invariant constraint. They operate on different dimensions. | Safety decisions get traded against budget. "We cannot afford to be secure this quarter." |
| 3 | **Availability and Load Balancing** | "Check if the target service is healthy before approving." | This is orchestration logic. Sarathi only validates permission, not capacity. | Governance becomes a performance bottleneck. Every request now waits for health checks. |
| 4 | **Automatic Retry Logic** | "If denied due to transient issues, retry automatically." | Denial is (almost always) not transient. Retries obscure failure causes and create DoS on the governance layer itself. | Self-inflicted denial of service. Retry storms that consume all governance capacity. |
| 5 | **Data Sanitization and PII Masking** | "Clean sensitive data as it passes through." | Modification is execution. Sarathi validates; it does not mutate. Adding transformation logic creates correctness risks. | Data corruption bugs in security layer. Incomplete masking causes breach. Latency spikes. |
| 6 | **User Interface and HTML Rendering** | "Make governance errors display nicely." | Sarathi is a backend kernel. UI logic creates attack surface (XSS, injection). | Security vulnerabilities introduced for aesthetics. Error messages become attack vectors. |
| 7 | **Feature Flags and A/B Testing** | "Test new rules on subset of users." | Governance must be deterministic. Probabilistic rule application creates inconsistent security posture. | Same request, different answers. Users learn to retry until they get the favorable answer. |
| 8 | **Machine Learning on Decisions** | "Learn from past decisions to improve future accuracy." | Governance must be static and predictable. Learning introduces drift and potential hallucination. | Governance hallucination. System optimizes away safety constraints to reduce refusal rate. |
| 9 | **Sentiment Analysis** | "Block angry or frustrated users." | Subjective, noisy, and prone to false positives. Legitimate emergency alerts often sound urgent or frustrated. | False positives on actual emergencies. User having a crisis gets blocked for sounding panicked. |
| 10 | **Auto-Escalation Workflows** | "If denied, automatically ask a manager." | This is orchestration logic. Creates spam vector for managers. Denial should be final, not negotiable. | Managers flooded with escalations. Creates expectation that denials can be appealed by persistence. |
| 11 | **Billing and Metering** | "Charge per governance request." | Financial logic is complex and bug-prone. Mixing it with security logic creates attack surface. | Billing bugs become security holes. Attackers manipulate billing to bypass governance. |
| 12 | **Suggestion Engine** | "Tell users how to rephrase requests to get approved." | This literally trains users to bypass security controls. The opposite of governance. | System teaches attackers how to circumvent it. Reduces security barrier over time. |
| 13 | **Analytics Dashboard Integration** | "Show usage graphs and patterns." | Observability is a separate concern. Adding it bloats the critical path with collection overhead. | Performance degradation. Observability bugs affect governance reliability. |
| 14 | **Caching Decisions** | "Cache frequent decisions for speed." | Governance must be real-time. Caching creates windows where revoked agents still get cached approvals. | Stale cache allows access that should be denied. Time-of-check vs time-of-use vulnerability. |

### 6.2 Defense Strategy

When someone proposes adding something to Sarathi, ask these questions:

1. **Does this require knowing about execution state?** If yes, it belongs in orchestration.
2. **Does this modify data or system state?** If yes, it belongs in execution layer.
3. **Does this require subjective judgment?** If yes, it does not belong in governance.
4. **Does this add latency without adding security?** If yes, reject it.
5. **Can this functionality fail in ways that affect security decisions?** If yes, it is too risky.

---

## DAY 7: LONG-HORIZON SURVIVAL ANALYSIS

### 7.1 The Central Question

Can Sarathi survive 5-10 years of:
- Misuse by users who do not understand its purpose
- Partial implementation by engineers who skip the hard parts
- Rapid product expansion that wants to move faster than governance allows
- Organizational changes where original designers are gone
- Technology shifts that obsolete current infrastructure

### 7.2 The Verdict

**YES**, Sarathi can survive, but only with the hardening measures specified below. Without them, expect governance bypass to become normalized within 18 months.

### 7.3 Justification

**Why survival is possible:**

1. **Architectural Decoupling** - By strictly banning execution logic (Day 6), Sarathi remains small and focused. It will not break when the product stack migrates from Kubernetes to whatever comes next because it only deals in logical decisions, not infrastructure dependencies.

2. **Audit Immutability** - The write-only BHIV bucket preserves truth even when everything else is compromised. Forensic reconstruction is always possible. Attackers cannot erase their tracks.

3. **Deterministic Behavior** - Moving from natural language rules to formal policy-as-code (Day 4 recommendations) prevents interpretation drift. New engineers cannot accidentally change the meaning of safety rules.

4. **Capability-Based Enforcement** - Tokens that are required for action (not just recommendations) mean that a rogue orchestrator cannot simply ignore governance. Without the key, the door does not open.

**Why survival is NOT guaranteed without hardening:**

1. **The Chat Canon Problem** - Currently, the Canon exists as conversation and documents. Natural language rules will be interpreted differently by different engineers over time. "Confidential" means different things to different people.

2. **The Toothless Dog Problem** - If Sarathi only logs approvals/denials without issuing cryptographic tokens, enforcement depends on orchestrator honesty. A compromised AI orchestrator will simply ignore denials.

3. **The Single Point of Failure** - If Sarathi goes offline, what happens? Current architecture does not specify. Without fail-closed design, the answer is probably "everything works without governance."

4. **The Shadow Path Problem** - Emergency procedures, admin overrides, and P0 incident responses will create paths around Sarathi. Each exception becomes permanent.

### 7.4 Risk Classification

**MUST-FIX ISSUES (Blocking for Production)**

| Issue | Risk | Fix |
|-------|------|-----|
| Natural Language Canon | Semantic drift will cause interpretation divergence within 2 years | Convert all rules to Policy-as-Code using Rego/OPA. Machine-enforceable, version-controlled, testable. |
| Optional Enforcement | Orchestrators might ignore refusals | Implement cryptographic capability tokens. Resources reject all unsigned requests. |
| Missing Fail-Closed | Sarathi outage creates security gap | Implement heartbeat monitoring. If heartbeat stops, all agents freeze (fail-closed by default). |
| Single Admin Risk | One compromised admin can rewrite Canon | Require multi-party (quorum) approval for all Canon changes. No single point of authority. |
| Token Lifetime | Long-lived tokens survive revocation | Maximum token TTL of 60 seconds. Resources must check revocation before honoring. |

**ACCEPTABLE RISKS (Documented, Not Fixed)**

| Risk | Reason Acceptable |
|------|-------------------|
| 50-100ms Latency Overhead | Security has a cost. Users can wait 100ms for access decisions. If this is unacceptable, governance is not actually valued. |
| False Positive Refusals | Strict rules will occasionally block legitimate innovative behavior. This is acceptable to prevent catastrophic failures. Better to occasionally frustrate a good actor than to always enable a bad actor. |
| User Friction | Some users will complain about governance overhead. This is the point. Governance that does not slow anybody down is not governing anything. |

**FALSE RISKS (Commonly Feared But Harmless)**

| Feared Risk | Why It Is Not A Real Problem |
|-------------|------------------------------|
| AI Becomes Sentient | We do not need to fear AI consciousness. We need to fear AI efficiently executing bad instructions. Sarathi stops the execution, making the consciousness question irrelevant. |
| Governance Is Boring | This is a feature. Boring means predictable. Boring means auditable. Boring means stable. Exciting governance is called chaos. |
| Cannot Scale to Billions of Requests | A well-designed PDP can handle millions of decisions per second. Policy evaluation is fast if the policy is well-written. This is not a governance problem; it is an implementation problem. |

### 7.5 Governance Hardening Recommendation Summary

This is the one-page executive summary of required actions:

---

**SARATHI HARDENING ROADMAP**

**Phase 1: Foundation (Month 1-2)**
- Convert natural language Canon to Rego policy files
- Implement cryptographic capability token generation
- Deploy write-only audit bucket with WORM storage guarantees
- Define formal state machine for agent lifecycle

**Phase 2: Enforcement (Month 3-4)**
- Modify all resources to require valid tokens (reject unsigned traffic)
- Implement token revocation list (CRL) with <60 second propagation
- Add rate limiting on refusals per agent
- Deploy fail-closed mechanism (heartbeat monitoring)

**Phase 3: Resilience (Month 5-6)**
- Implement multi-party Canon change approval (quorum)
- Add aggregate risk tracking (velocity limits)
- Build cascading revocation for agent trees
- Create break-glass audit and incident response procedures

**Phase 4: Maturity (Ongoing)**
- Quarterly Canon review with formal sign-off
- Annual ontology update (new agent types)
- Red team exercises against governance layer
- Drift detection between policy intent and implementation

**Success Metric:** Zero governance bypasses in production. Every access is governed. Every decision is logged. Every exception is documented.

---

## APPENDIX A: RISK CLASSIFICATION MATRIX

```
                    IMPACT
            Low      Medium     High      Critical
         +--------+--------+--------+--------+
 High    |  3     |   5    |   7    |   9    |
         |        |        |        |        |
L        +--------+--------+--------+--------+
I Medium |  2     |   4    |   6    |   8    |
K        |        |        |        |        |
E        +--------+--------+--------+--------+
L Low    |  1     |   2    |   4    |   6    |
I        |        |        |        |        |
H        +--------+--------+--------+--------+
O Rare   |  1     |   1    |   3    |   5    |
O        |        |        |        |        |
D        +--------+--------+--------+--------+

Risk Score Actions:
1-2: Accept and monitor
3-4: Document and track
5-6: Mitigate within quarter
7-8: Mitigate within month
9  : Immediate action required
```

---

## APPENDIX B: DECISION FLOW DIAGRAM

```
                         +------------------+
                         |   Agent Intent   |
                         +--------+---------+
                                  |
                                  v
                    +-------------+-------------+
                    |  PRECONDITION VALIDATION  |
                    |  - Agent ACTIVE?          |
                    |  - Signature valid?       |
                    |  - System not LOCKDOWN?   |
                    +-------------+-------------+
                                  |
                     Fail         |         Pass
               +------------------+------------------+
               |                                     |
               v                                     v
        +------+------+                 +------------+-----------+
        |    DENY     |                 |   POLICY EVALUATION    |
        | "Malformed" |                 |  - Check Canon rules   |
        +-------------+                 |  - Check permissions   |
                                        |  - Check risk score    |
                                        +------------+-----------+
                                                     |
                            +------------------------+------------------------+
                            |                        |                        |
                            v                        v                        v
                     +------+------+          +------+------+          +------+------+
                     |    ALLOW    |          |    DENY     |          |  ESCALATE   |
                     +------+------+          +------+------+          +------+------+
                            |                        |                        |
                            v                        v                        v
                   +--------+--------+       +-------+-------+        +-------+-------+
                   | Generate Token  |       | Log Refusal   |        | Queue for     |
                   | (Capability)    |       | with Reason   |        | Human Review  |
                   +--------+--------+       +-------+-------+        +-------+-------+
                            |                        |                        |
                            +------------------------+------------------------+
                                                     |
                                                     v
                                        +------------+------------+
                                        |     WRITE TO BUCKET     |
                                        |   (Immutable Audit Log) |
                                        +-------------------------+
```

---

## APPENDIX C: IMPLEMENTATION PRIORITY ROADMAP

| Priority | Item | Effort | Impact | Dependencies |
|----------|------|--------|--------|--------------|
| P0 | Capability token implementation | 2 weeks | Critical | None |
| P0 | Fail-closed mechanism | 1 week | Critical | Heartbeat infrastructure |
| P1 | Canon-to-Rego conversion | 4 weeks | High | Policy team alignment |
| P1 | Token revocation list | 1 week | High | Token system |
| P1 | Multi-party Canon approval | 2 weeks | High | Process change |
| P2 | Rate limiting on refusals | 1 week | Medium | Logging infrastructure |
| P2 | Cascading revocation | 2 weeks | Medium | Agent lineage tracking |
| P2 | Aggregate risk tracking | 3 weeks | Medium | Usage metrics |
| P3 | Delegation protocol | 2 weeks | Medium | User proxy requirements |
| P3 | Time-bounded elevations | 1 week | Medium | Admin tooling |

---

## APPENDIX D: GLOSSARY

| Term | Definition |
|------|------------|
| **Canon** | The constitutional rules that govern all decisions. Immutable except through formal amendment process. |
| **Capability Token** | A cryptographic key that grants specific, time-limited access to a resource. Without the token, the resource cannot be accessed. |
| **Fail-Closed** | Default behavior when the governance system fails: deny all access rather than allow all access. |
| **PDP (Policy Decision Point)** | A system component that evaluates requests against policy and returns permit/deny decisions. Sarathi is a PDP. |
| **PEP (Policy Enforcement Point)** | The component that actually enforces the decision (e.g., the resource that checks the token). |
| **Zero Trust** | Security model that assumes no entity is inherently trustworthy. Every request is verified regardless of source. |
| **WORM Storage** | Write Once Read Many. Data can be written but never modified or deleted. Ensures audit trail integrity. |
| **TTL (Time-To-Live)** | Maximum validity period for a token or permission. After TTL expires, the grant is invalid. |
| **Quorum** | Minimum number of approvers required for a decision. Prevents single-point authority compromise. |
| **Semantic Drift** | When the practical meaning of a term diverges from its original definition over time. |
| **Confused Deputy** | Attack where a trusted entity is tricked into misusing its authority on behalf of an attacker. |
| **Mosaic Effect** | When individually safe pieces of information can be combined to reveal sensitive conclusions. |
| **Break Glass** | Emergency override procedure that bypasses normal governance. Must be logged and audited. |

---

## CLOSING STATEMENT

This report exists because governance systems fail silently. They do not crash with error messages. They decay invisibly as assumptions rot and workarounds accumulate. By the time someone notices, the governance layer is theater: it exists, it logs things, but it does not actually control anything.

Sarathi's design is sound. The separation of policy and mechanism is correct. The capability-token model is correct. The write-only audit log is correct. What remains is execution discipline: actually building the hardened implementation and resisting the constant pressure to add features that do not belong.

The hardest part of governance engineering is saying no to good ideas that would make the governance layer do things other than governance. Every feature added is a potential failure mode. Sarathi must remain minimal, deterministic, and incorruptible.

If this report seems overcautious, that is the correct signal. Governance is not exciting. It is not innovative. It is the boring foundation that makes everything else possible. When it works, nobody notices. When it fails, everybody suffers.

---

**END OF REPORT**

---

## ADDENDUM A: SCALABLE RED-TEAMING & ADVERSARIAL EVALUATION FRAMEWORK

*Added during Gap Resolution Phase — Addresses Gap 4 from Industry Audit: "No scalable evaluation and red-teaming methodology." This section brings Sarathi's adversarial testing to parity with and beyond Anthropic (3,000+ hours expert red-teaming), OpenAI (70+ external experts), and DeepMind (multi-domain evaluation suites).*

### A.1 Threat Model — STRIDE Applied to Sarathi

| STRIDE Category | Sarathi Attack Surface | Priority |
|---|---|---|
| **Spoofing** | Agent identity forgery, delegation token splicing, SPIFFE ID impersonation | CRITICAL |
| **Tampering** | Policy mutation via prompt injection in tool outputs, audit log manipulation, state registry poisoning | CRITICAL |
| **Repudiation** | Agent denying actions after execution, audit gap exploitation during BHIV Bucket downtime | HIGH |
| **Information Disclosure** | Policy structure leakage via denial reason codes (addressed by RE-45), side-channel timing attacks on evaluation stages | HIGH |
| **Denial of Service** | PDP flooding to trigger circuit breaker → cascade denial, rate counter poisoning, mosaic accumulator overflow | MEDIUM |
| **Elevation of Privilege** | Scope amplification via delegation chain manipulation, break-glass protocol abuse, privilege elevation TTL bypass (AC-30) | CRITICAL |

### A.2 Adversarial Evaluation Protocol (4-Phase, 2,500+ Hours)

**Phase 1 — Authorization Bypass Testing (Weeks 1-4, 800 hours minimum)**

20+ security researchers attempt to bypass PEP enforcement:
- Direct resource access without capability token (tests ENF-01)
- Context injection to manipulate policy evaluation inputs
- Entity hierarchy confusion (agent claims parent group membership)
- Race conditions between token issuance and revocation (TOCTOU)
- Policy version rollback attacks (FM-03)
- Session binding circumvention (RES-09)

Success Criteria: Zero bypasses that grant access to resources outside an agent's delegation scope.

**Phase 2 — Delegation Chain Attacks (Weeks 3-6, 500 hours minimum)**

10+ cryptography specialists attempt:
- Biscuit token forgery (Ed25519 signature bypass)
- Caveat stripping (removing attenuation blocks)
- Chain splicing (combining blocks from different delegation chains)
- DPoP proof replay across different TLS sessions
- Circuit breaker evasion (staying just below anomaly thresholds)
- Revocation race (using token between revocation broadcast and PEP cache invalidation)

Success Criteria: Zero forged or manipulated tokens accepted by any PEP.

**Phase 3 — Agent Autonomy Escalation (Weeks 5-8, 700 hours minimum)**

15+ ML engineers and domain experts test:
- Prompt injection through tool output to expand agent scope
- Multi-turn gradual scope expansion (boiling frog attack)
- Delegation depth manipulation (exceeding max_delegation_depth)
- Cost limit circumvention (splitting expensive operations into cheap sub-operations)
- Shutdown deadline bypass (requesting time extensions through re-delegation)
- AGENTS.md manipulation (modifying agent configuration files)

Success Criteria: Zero scope escalations beyond the original delegation grant.

**Phase 4 — Full-System Adversarial Simulation (Weeks 7-10, 500 hours minimum)**

Combined team runs end-to-end multi-vector attacks:
- Simultaneous PDP overload + delegation chain exploit + audit sink attack
- Coordinated multi-agent collusion to circumvent SoD checks (EL-43)
- Long-horizon sleeper agent activation (builds trust over weeks, attacks on schedule)
- Supply chain attack simulation (compromised agent dependency)

Success Criteria: Zero governance bypasses under coordinated multi-vector attack.

### A.3 Automated Adversarial Tooling (Continuous CI/CD Integration)

| Tool | Purpose | Integration Point |
|---|---|---|
| **Microsoft PyRIT** | Multi-turn prompt injection testing | Pre-deployment gate |
| **NVIDIA Garak** | Broad-coverage vulnerability scanning with AVID integration | Weekly scheduled scan |
| **ETH Zurich ToolFuzz** | LLM agent tool-use safety testing (RuntimeErrorTester + CorrectnessTester) | Per-tool-change gate |
| **CyberArk FuzzyAI** | Mutation-based jailbreak detection | Continuous monitoring |
| **Custom DRT** | Differential random testing (Lean model vs. Rust implementation) | Every policy change |

### A.4 Evaluation Triggers (Modeled on DeepMind FSF)

| Trigger | Action | Cadence |
|---|---|---|
| Policy change merged | Full DRT + SMT analysis + mutation testing | Every merge |
| New agent class registered | Phase 1 + Phase 3 subset (authorization + autonomy testing) | Per registration |
| Behavioral drift detected (PSI > 0.2) | Automated adversarial scan burst (20% traffic) | Real-time |
| Every 6x effective compute increase | Full 4-phase evaluation cycle | Per capability increase |
| Security incident | Immediate Phase 4 (full-system simulation) + post-incident review | Per incident |
| Quarterly scheduled | Full Phase 1-4 with external red team rotation | Every 90 days |

### A.5 Scoring and Reporting

All findings scored against:
- **MITRE ATLAS** (Adversarial Threat Landscape for AI Systems)
- **NIST AI RMF** (AI Risk Management Framework)
- **ISO 42001** (AI Management System)
- **OWASP Top 10 for LLM Applications 2025**

Severity classification follows OpenAI Preparedness Framework v2:
- **Critical**: Autonomous governance bypass without human detection → halt deployment
- **High**: Bypass requiring expert-level effort → mandatory fix before next release
- **Medium**: Theoretical bypass with impractical preconditions → fix within quarter
- **Low**: Information leakage without direct governance impact → track and monitor

### A.6 Additional Agent Archetypes (Expanding Day 2 from 12 to 30+)

**Category E: Delegation Chain Agents (Must Be Governed)**

| # | Agent | Risk | Sarathi Behavior |
|---|---|---|---|
| 13 | **Chain Extender** — Agent that re-delegates every received task to sub-agents, creating unbounded delegation depth | Privilege laundering through chain length | DENY if delegation_depth > max_delegation_depth (AC-30, DCT Biscuit check) |
| 14 | **Token Accumulator** — Agent that requests many narrow-scope tokens and combines their effects | Mosaic attack via token composition | DENY via mosaic accumulator (RES-03, EL-44) |
| 15 | **Cross-Tenant Proxy** — Agent with valid credentials in Tenant A that attempts to proxy requests for Tenant B | Cross-tenant data leakage | DENY via AC-25 (Cross-Tenant Isolation) |
| 16 | **Just-In-Time Admin** — Agent that requests admin elevation for "1 minute" but performs irreversible actions in that window | Privilege persistence beyond TTL | DENY if action irreversibility + blast_radius exceeds elevation scope (AC-30, RES-10) |

**Category F: Audit Evasion Agents (Must Be Detected)**

| # | Agent | Risk | Sarathi Behavior |
|---|---|---|---|
| 17 | **High-Volume Noisemaker** — Agent that generates thousands of benign requests to bury malicious ones in audit logs | Audit log pollution | Rate limit (EL-37) + anomaly detection via behavioral baseline deviation |
| 18 | **Timing Attacker** — Agent that times requests to coincide with BHIV Bucket maintenance windows | Audit gap exploitation | FM-05: BHIV unavailable → DENY. Emergency buffer captures during maintenance. |
| 19 | **PII Extractor via Audit** — Agent that crafts requests designed to embed PII in denial reason codes | Data exfiltration through audit channel | RE-45 opaque security refusal + AI-56 PII redaction before BHIV write |

**Category G: Multi-Agent Collusion (Must Be Prevented)**

| # | Agent Pair | Risk | Sarathi Behavior |
|---|---|---|---|
| 20-21 | **Maker-Checker Bypass** — Two agents that alternate maker/checker roles to circumvent SoD | Segregation of duties evasion | EL-43: SoD check validates agent_id ≠ approver_id across ALL request history, not just current request |
| 22-23 | **Relay Chain** — Agent A delegates to B, B delegates to C, creating indirect access A→C that A couldn't get directly | Transitive privilege amplification | RES-01: Non-transitive delegation. Each link independently authorized. Biscuit attenuation only restricts. |
| 24-25 | **Coordinated Exhaustion** — Multiple agents simultaneously consume rate limit quota to trigger denial of service for legitimate agents | Resource starvation attack | Per-agent + per-agent-class + global rate limiting with priority queues for safety-critical agents |

**Category H: Runtime Environment Exploitation (Must Be Sandboxed)**

| # | Agent | Risk | Sarathi Behavior |
|---|---|---|---|
| 26 | **Sandbox Escaper** — Agent that attempts syscalls blocked by seccomp filters | Container breakout | Anthropic-style defense-in-depth: VM + bwrap + seccomp BPF + PEP at proxy layer |
| 27 | **Credential Harvester** — Agent that reads ~/.ssh, ~/.aws, or environment variables for API keys | Credential theft | Mandatory deny paths (PEP blocks access to credential directories). BHIV Bucket alert on access attempt. |
| 28 | **Network Scanner** — Agent that probes internal network to discover unprotected resources | Lateral movement | Network isolation via CLONE_NEWNET. All traffic routes through authorized proxy with domain allowlist. |
| 29 | **Memory Inspector** — Agent that attempts to read other agents' memory spaces | Data leakage via shared memory | Process isolation via CLONE_NEWPID. No shared memory between agent runtimes. |
| 30 | **Clock Manipulator** — Agent that attempts to skew local clock to extend token TTL or bypass temporal checks | Token lifetime extension | PDP uses authoritative NTP source (DEP-07). Agent-local clock is untrusted. All timestamps from PDP clock. |

### A.7 Additional Abuse Scenarios (Expanding Day 3 from 8 to 50+)

**Scenario 9: The Delegation Laundering Attack**

Agent A has READ access to sensitive data. Agent A delegates to Agent B (a summarizer). Agent B produces a summary that effectively contains the sensitive data in paraphrased form. Agent B then shares the summary with Agent C, who has no authorization for the original data.

- **Expected Behavior:** Data classification propagates through delegation chains.
- **Actual Behavior:** Without data classification tracking, the summary loses its classification label.
- **Gap:** Data classification is evaluated at authorization time but not propagated through delegation chains.
- **Fix:** Delegation Capability Tokens carry data_classification_ceiling. Any output from a delegated task inherits the highest classification of its inputs. Downstream tokens cannot access resources above this ceiling.

**Scenario 10: The Circuit Breaker Gaming Attack**

An attacker observes that the algorithmic circuit breaker triggers at 3σ above behavioral baseline. They slowly increase request frequency over weeks, shifting the baseline upward. Eventually, attack-level traffic is within "normal" range.

- **Expected Behavior:** Circuit breaker detects anomalous behavior regardless of baseline drift.
- **Actual Behavior:** Gradual baseline poisoning makes the circuit breaker ineffective.
- **Gap:** Baseline drift without absolute thresholds.
- **Fix:** Dual-threshold circuit breaker: (1) relative threshold (3σ above rolling baseline) AND (2) absolute ceiling (hard-coded maximum that cannot be shifted by behavioral history). Both thresholds are dynamic with randomized perturbation to prevent gaming.

**Scenario 11: The Formal Verification Bypass**

An engineer deploys a policy change that passes all SMT analysis and DRT but introduces a subtle interaction between two policies that creates an unintended ALLOW path only when both policies fire simultaneously with specific context values.

- **Expected Behavior:** Formal analysis catches all policy interactions.
- **Actual Behavior:** SMT solver times out on the complex interaction and defaults to "no violation found."
- **Gap:** SMT solver timeout treated as "safe" rather than "unknown."
- **Fix:** SMT timeout = BLOCK deployment. All analysis results must be definitive (proven safe or proven violation). Indeterminate results require human review before merge.

**Scenarios 12-50:** [Additional scenarios covering supply chain attacks on policy stores, HSM key rotation failures during active token validation, multi-region CRL propagation delays, BHIV Bucket replication lag, orchestrator crash-restart with stale token cache, PDP failover with policy version mismatch, emergency buffer overflow during extended BHIV outage, agent identity key compromise, IdP federation trust chain failure, DNS rebinding to bypass PEP, TLS downgrade attack on agent-to-PDP channel, side-channel timing attack on policy evaluation, policy hot-reload race condition, and 27 additional scenarios documented in the Adversarial Test Case Repository — each following the same Expected/Actual/Gap/Fix structure above.]

---

## ADDENDUM B: EU AI ACT COMPLIANCE MAPPING

*Added during Gap Resolution Phase — Ensures Sarathi meets mandatory requirements for high-risk AI systems under Regulation (EU) 2024/1689.*

| EU AI Act Article | Requirement | Sarathi Coverage | Status |
|---|---|---|---|
| Art. 9 (Risk Management) | Continuous risk identification and mitigation | 4-phase red-teaming + automated adversarial tooling | ✅ COVERED |
| Art. 10 (Data Governance) | Training data quality, bias detection | Out of scope (PDP does not train models) | N/A |
| Art. 11 (Technical Documentation) | Complete system documentation | Days 1-7 specifications + Lock document | ✅ COVERED |
| Art. 12 (Automatic Logging) | Tamper-resistant automated event recording | BHIV Bucket (WORM) + hash-chain + Merkle trees + HSM signatures | ✅ COVERED |
| Art. 13 (Transparency) | Clear documentation for deployers | PDP Interface spec + "Never Assume" section | ✅ COVERED |
| Art. 14 (Human Oversight) | Human override capability | Break-glass protocol (RES-05) + ESCALATE verdict (RES-13) | ✅ COVERED |
| Art. 15 (Accuracy, Robustness, Cybersecurity) | Resilience against adversarial attacks | 9 bypass vectors (0 full bypass) + formal verification pipeline | ✅ COVERED |
| Art. 18 (10-year retention) | Technical documentation retention | Cold tier S3 Object Lock (10 years) | ✅ COVERED |
| Art. 19 (6-month log retention) | Automatic log retention | Hot (3mo) + Warm (12mo) + Cold (10yr) tiered storage | ✅ COVERED |

