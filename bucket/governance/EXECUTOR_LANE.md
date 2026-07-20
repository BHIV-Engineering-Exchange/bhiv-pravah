# Document 08: Executor Lane (Akanksha)

**Date:** January 13, 2026  
**Purpose:** Define execution boundaries for Akanksha  
**Audience:** Akanksha (executor), Ashmit (oversight)  
**Classification:** Policy (Private - share only with Akanksha)

## Overview

This document defines the execution boundaries and authority for Akanksha as the Executor of BHIV Central Depository (Bucket v1.0.0). It clarifies what can be done independently, what requires approval, and what is forbidden.

## 1. Your Role: Executor

**Akanksha, you are the Executor of BHIV Bucket** - responsible for implementing approved decisions.

### What This Means

**You have clear authority to:**
- ✅ Implement decisions Ashmit has made
- ✅ Code, test, deploy, maintain
- ✅ Make day-to-day technical decisions

**You do NOT have authority to:**
- ❌ Change governance policies
- ❌ Approve new artifact classes
- ❌ Weaken provenance guarantees
- ❌ Skip reviews

## 2. You Can Execute (Without Asking)

These changes require no approval from Ashmit. You can do them immediately:

### ✅ Refactoring (Code Quality)
- Rename variables/functions (no logic change)
- Reorganize code structure
- Improve test coverage
- Add documentation
- Fix code style
- Remove dead code

**Boundary:** Pure refactoring. Logic must not change.

### ✅ Non-Breaking Schema Extensions
- Add new optional fields (JSON)
- Add new optional agent
- Extend logging (add new fields)
- New query indices for performance

**Boundary:** Existing data still works. No migration needed.

**Example:**
```json
// OLD
{ "execution_id": "...", "status": "..." }

// NEW (backward compatible)
{ "execution_id": "...", "status": "...", "new_field": "..." }
```

### ✅ New API Endpoints (Non-Breaking)
- New /metrics endpoint
- New /analytics endpoint
- New /health-detailed endpoint

**Boundary:** Doesn't change existing endpoints. Doesn't affect baskets/agents.

### ✅ Test Coverage Improvements
- Add unit tests
- Add integration tests
- Add performance tests
- Fix flaky tests

**Boundary:** Tests don't change code behavior, only verify it.

### ✅ Documentation
- README updates
- Code comments
- Architecture docs
- Runbooks for operations
- Integration guides

**Boundary:** Pure documentation, no code changes.

### ✅ Performance Optimization
- Optimize database queries (same results)
- Add caching (same data)
- Improve API response time
- Reduce memory usage

**Boundary:** Output must be identical. No behavior change.

### ✅ Dependency Updates
- Update libraries (patch versions: 1.2.0 → 1.2.5)
- Security patches
- Bug fixes in deps

**Boundary:** Patch and minor versions only. Test thoroughly.

### ✅ Operational Changes
- Modify log rotation config
- Adjust Redis TTLs (within policy)
- Scale database connections
- Change deployment parameters

**Boundary:** Within existing policy. If you need to change policy, escalate.

### ✅ Monitoring & Observability
- Add Prometheus metrics
- Add logging
- Add alerts
- Improve debugging

**Boundary:** Doesn't change Bucket behavior.

## 3. Requires Approval (Ask Ashmit First)

These changes need Ashmit's approval before you can merge:

### ⚠️ Schema Changes (Breaking)
**Example:** Remove a field, rename a field, change field type

**Why:** Changes existing data format. Consumers may break.

**Process:**
1. You: Propose change with migration plan
2. Ashmit: Reviews impact
3. Ashmit: Approves with versioning strategy
4. You: Implement with migration
5. You: Test migration thoroughly

### ⚠️ New Agent Addition
**Example:** Adding a 13th agent to Bucket

**Why:** Changes agent inventory, affects all consumers.

**Process:**
1. You: Implement agent code
2. Ashmit: Reviews agent spec
3. Ashmit: Approves or requests changes
4. You: Update agent_spec.json
5. You: Deploy with registration

### ⚠️ Basket Configuration Changes
**Example:** Changing order of agents in a basket, adding new basket

**Why:** Changes orchestration logic, affects consumers.

**Process:**
1. You: Propose change with rationale
2. Ashmit: Reviews impact
3. Ashmit: Approves or suggests alternatives
4. You: Implement and test
5. You: Deploy

### ⚠️ Provenance Guarantee Changes
**Example:** Reducing log retention, removing audit trail, changing TTLs

**Why:** Affects what Bucket guarantees.

**Process:**
1. You: Propose with rationale
2. Ashmit: Consults compliance/Vijay if needed
3. Ashmit: Decides (may require Phase 2 planning)
4. You: Implement if approved

### ⚠️ API Endpoint Changes (Breaking)
**Example:** Changing /run-basket request format, removing endpoint

**Why:** Breaks existing integrations.

**Process:**
1. You: Propose with migration plan
2. Ashmit: Reviews impact on integrations
3. Ashmit: Approves versioning strategy
4. You: Implement v1 AND v2 (both work for period)
5. You: Sunset v1 after migration window

### ⚠️ Major Dependency Updates
**Example:** FastAPI 0.100 → 1.0 (major version)

**Why:** May introduce breaking changes.

**Process:**
1. You: Test in staging, document breaking changes
2. Ashmit: Reviews breaking changes
3. Ashmit: Approves update
4. You: Deploy carefully with rollback plan

### ⚠️ Storage Layer Changes
**Example:** Adding MongoDB sharding, changing Redis cluster

**Why:** Affects scalability and reliability.

**Process:**
1. You: Propose with capacity analysis
2. Ashmit: Consults Vijay if complex
3. Ashmit: Approves plan
4. You: Execute with testing and rollback

### ⚠️ Retention Policy Changes
**Example:** Changing 1-year retention to 6 months

**Why:** Policy decision, affects compliance.

**Process:**
1. You: Propose with rationale
2. Ashmit: Reviews compliance impact
3. Ashmit: Decides (may consult legal/compliance)
4. You: Implement if approved

## 4. Forbidden (You Cannot Do This)

These are off-limits. Don't do them. Don't negotiate. Don't bypass.

### ❌ Forbidden 1: Owner Authority
**You cannot:**
- Approve/reject integrations
- Change governance documents
- Set Bucket policy
- Override Ashmit's decisions

**Why:** Ashmit owns Bucket. You don't.

### ❌ Forbidden 2: Bypass Reviews
**You cannot:**
- Merge without code review
- Deploy without testing
- Bypass approval gates
- Push directly to main

**Why:** Quality and safety depend on review.

### ❌ Forbidden 3: Unsafe Deployment
**You cannot:**
- Deploy without rollback plan
- Deploy to production untested
- Deploy during critical hours
- Deploy multiple changes together (untested)

**Why:** Bucket affects all teams. Failure impacts everyone.

### ❌ Forbidden 4: Data Deletion
**You cannot:**
- Delete logs without formal process
- Hard-delete data (only Ashmit can authorize)
- Modify past execution data
- Bypass retention policy

**Why:** Audit trail integrity requires formal process.

### ❌ Forbidden 5: Change Governance Without Process
**You cannot:**
- Update governance docs unilaterally
- Change approval criteria
- Weaken provenance guarantees
- Promise Phase 2 features as current

**Why:** Governance must be intentional, documented, consistent.

### ❌ Forbidden 6: Scope Creep
**You cannot:**
- Add features Ashmit didn't approve
- Store new artifact classes
- Change integration boundaries
- Modify approved baskets without approval

**Why:** These are policy decisions, not technical decisions.

## 5. Code Review Checkpoints

When you open a PR, these checkpoints apply:

### Checkpoint 1: Does This Change Require Approval?
- **You vs Ashmit:** Read section 2 & 3 above
- **If approval needed** → Include @ashmit in PR
- **If not needed** → Proceed with review

### Checkpoint 2: Is the Code Quality Good?
- Tests added for new code
- Documentation updated if needed
- No dead code
- No security issues
- Follows code style

### Checkpoint 3: Will This Break Anything?
- Backward compatibility checked
- API contracts honored
- Dependency versions compatible
- Database migrations tested (if needed)

### Checkpoint 4: Is the Approach Sound?
- Solution makes sense architecturally
- No over-engineering
- No under-engineering
- Maintainable long-term

### Checkpoint 5: Who Reviews?
- **Code quality:** Any team member
- **Approval decisions:** Ashmit (if needed)
- **Architecture:** Ashmit (if complex)

## 6. Default Rule: IF UNSURE, ASK

When uncertain whether something needs approval:
- Ask Ashmit before implementing
- Better to ask than to implement wrong
- Use example: "This is similar to [approved change], should I ask?"
- **Timeline:** Ashmit responds within 24 hours

## 7. Escalation Path

### If Ashmit's Decision Seems Wrong to You:
1. Ask for clarification (may be miscommunication)
2. Suggest alternative approach
3. If still disagree, escalate to Vijay
4. Respect final decision

### If Blocked on Approval:
1. Ashmit responds within 24 hours (typical)
2. If delayed, follow up
3. If critical, escalate to Vijay

## 8. Success Metrics for Executor Role

You're succeeding if:
- ✅ Code is clean and well-tested
- ✅ Deployments are smooth and safe
- ✅ Zero surprise scope changes
- ✅ Ashmit approves >90% of PRs quickly
- ✅ Bucket stays stable and performant
- ✅ Team trusts your work quality

## 9. API Endpoints

### Get Executor Role
```bash
GET /governance/executor/role
```
Returns executor role definition (Akanksha).

### Get Can Execute Changes
```bash
GET /governance/executor/can-execute
```
Returns changes that can be executed without approval.

### Get Requires Approval Changes
```bash
GET /governance/executor/requires-approval
```
Returns changes that require Ashmit's approval.

### Get Forbidden Actions
```bash
GET /governance/executor/forbidden
```
Returns forbidden actions.

### Get Code Review Checkpoints
```bash
GET /governance/executor/checkpoints
```
Returns code review checkpoints.

### Get Success Metrics
```bash
GET /governance/executor/success-metrics
```
Returns success metrics for executor role.

### Get Escalation Path
```bash
GET /governance/executor/escalation-path
```
Returns escalation path for disagreements or blocks.

### Get Default Rule
```bash
GET /governance/executor/default-rule
```
Returns default rule: IF UNSURE, ASK.

### Categorize Change
```bash
POST /governance/executor/categorize-change?change_description=Add new optional field to logs
```
Categorizes a change as can_execute, requires_approval, or forbidden.

### Validate Change Request
```bash
POST /governance/executor/validate-change
```
Validates if a change request is properly categorized.

## Summary

Document 08 establishes clear execution boundaries for Akanksha as Executor:

- **9 categories** of changes that can be executed without approval
- **8 categories** of changes that require Ashmit's approval
- **6 categories** of forbidden actions
- **5 code review checkpoints** for every PR
- **Default rule:** IF UNSURE, ASK (24-hour response time)
- **Escalation path** for disagreements or blocks
- **6 success metrics** to measure executor effectiveness
- **10 new API endpoints** for programmatic access

**Status:** ✅ Implemented and integrated with existing governance layer
