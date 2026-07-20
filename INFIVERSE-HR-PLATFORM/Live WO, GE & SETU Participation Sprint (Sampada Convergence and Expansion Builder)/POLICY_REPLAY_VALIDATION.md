# Policy Replay Validation (Live WO/GE/SETU Sprint · Phase 4)

**Workflow position:** Step 4 of 11  
**Prerequisites:** Step 3 scenarios (reuses policy/decision IDs)  
**Next step:** Step 5 → `SETU_PARTICIPATION_EVIDENCE.md`

---

## Execution method

1. List policy definitions — confirm 3 active, unchanged after overrides.
2. Re-evaluate each policy with compliant context (tenure 200, scope_match true, approved true).
3. Document: overrides do **not** version the policy definition; outcome is context-driven.
4. Cross-reference Phase 3 decision replay chains for reconstruction proof.
5. Flag policy-conflict resolution as not a present capability (honest — not fabricated).

---

## Capture metadata

**Date**: 2026-06-27
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime code path; not deployed
**Auth type used**: API key (platform/admin)
**Status**: `live_capture` (local in-process runtime capture)
**Raw capture**: `evidence/live_workforce_governance_setu/governance_replay/phase4_policy_state.json` (reuses Phase 3 IDs from `phase3_scenarios.json`)

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Scenario Narrative

This phase re-documents the three Phase 3 scenarios (leave / visibility / approval) from the **policy-object lifecycle** angle: definition → evaluation → result → challenge path → override path → decision path → replay reconstruction, with emphasis on what changes in the policy object's state. The key finding (captured by re-evaluating each policy with a now-compliant context) is that **overrides are recorded as separate workflow/policy objects and do not mutate or version the policy definition** — the definition object is unchanged after an override; the override and decision sit alongside it and are linked by `policy_key`, `evaluation_id`, `challenge_id`, and `correlation_id`. Evaluation outcome therefore depends purely on the supplied context against the unchanged rules, which is what the re-evaluations below demonstrate.

## Policy-state model (observed)

| Aspect | Observed behavior (runtime-proven) |
|---|---|
| Definition versioning after override | **Not versioned/superseded.** `policy_definitions` record is untouched by override/decision; `GET /v1/policies/definitions` after the scenarios returned the 3 definitions unchanged (count=3). |
| Where the override lives | Separate `workflow_overrides` object (`wovr-…`, status `proposed`→`applied`); optionally `policy_overrides` for the policy-level override route. Linked by `policy_key` + `challenge_id`. |
| Decision linkage | `decisions` object references `challenge_id`, `review_id`, and the scenario `correlation_id` via `trace_references`; supersession is modeled on the decision object, not the policy definition. |
| Replay basis | Decision replay walks the `supersedes` chain on decision objects (Phase 3 Scenario A = 2-link chain). |

## Step-by-step Evidence Table (policy-state captures)

| Step | Endpoint | Request | Response (key) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|---|
| Definitions list | `GET /v1/policies/definitions?limit=50` | — | items=3 (leave/visibility/approval, all status=active, unchanged) | 200 | 10:27:12.401851Z |
| Re-eval Leave | `POST /v1/policies/evaluate` | context={tenure_days: 200} | decision=**allow** (was deny @ tenure 10 in Phase 3); evaluation_id=peval-29375563c0f8 | 200 | 10:27:12.408435Z |
| Re-eval Visibility | `POST /v1/policies/evaluate` | context={scope_match: true} | decision=**allow** (was deny); evaluation_id=peval-5ac0a96a7c20 | 200 | 10:27:12.417540Z |
| Re-eval Approval | `POST /v1/policies/evaluate` | context={approved: true} | decision=**observe** (was deny); evaluation_id=peval-2c3ab44747f1 | 200 | 10:27:12.424837Z |

## Per-domain policy lifecycle (cross-referenced to Phase 3 by ID)

- **Leave** — definition `…5629` (rules: min_tenure_days=90, effect=observe) → eval `peval-ee3ebf1c0404` (deny) → challenge `chl-879b1988d9e2` → review `rev-3c878a7f86df` (upheld) → override `wovr-4a2dfd7af7af` (applied) → decision `dec-502dd9179340`, superseded by `dec-847bc3155d34` → replay 2-link chain. Re-eval with compliant tenure → allow.
- **Visibility** — definition `…5636` (require_scope_match=true) → eval `peval-09288dac4c15` (deny) → challenge `chl-f7814862a4a0` → review `rev-f836079fc251` → override `wovr-63624f468e2f` → decision `dec-b40efca0fdd0` → replay 1-link. Re-eval with scope_match=true → allow.
- **Approval** — definition `…5641` (require_explicit_approval=true, effect=deny_until_approved) → eval `peval-2ecdfa9ca9ff` (deny) → challenge `chl-4c8a3ddbaab8` → review `rev-d820e128b861` → override `wovr-15db316d0f4a` → decision `dec-9f508b6e94b4` → replay 1-link. Re-eval with approved=true → observe.

## Replay Confirmation

- Re-evaluations prove the policy definition's rules are stable and outcome is context-driven (deny→allow/observe purely by input change), confirming overrides do not rewrite the definition.
- Decision replay reconstruction is evidenced in Phase 3 (Scenario A 2-link supersedes chain).

## Reviewer finding #4 reconciliation (operational validation)

The real Review Feedback finding #4 ("Policy Engine Needs Operational Validation") lists: policy conflicts, policy override chains, challenge lifecycle, escalation paths, replay reconstruction across policy decisions.

| Requirement | Status in Live WO/GE/SETU Sprint evidence |
|---|---|
| Challenge lifecycle | **Proven** — Phase 3 (challenge → review → complete) across 3 domains. |
| Escalation path | **Proven** — challenge → review → override → decision chain per scenario. |
| Policy override chains | **Proven** — workflow override propose→apply per scenario + a decision supersedes chain (Leave, 2 links). |
| Replay reconstruction across policy decisions | **Proven** — decision replay (Phase 3) + consolidated correlation replay packet (Phase 3 addendum). |
| **Policy conflicts** | **Not a present runtime capability / not proven** — `_evaluate_rules` evaluates a single `policy_key` against its own rules with no multi-policy conflict-resolution mechanism. Not fabricated (two-additive-fixes-only constraint). Carried as a risk in `REVIEW_PACKET.md`. |

## Known Limitations

- **Policy conflict resolution is out of current runtime scope** (no conflict engine exists); demonstrating it would require a new feature, which §0.1 and the two-additive-fixes-only rule forbid this sprint. Honestly flagged rather than simulated.
- Local in-process runtime capture (see Phase 1 header).
- To avoid pure duplication, full request/response payloads for the challenge/review/override steps are documented once in Phase 3 and cross-referenced here by ID.

## Cross-references

- Governance workflow evidence: `GOVERNANCE_REPLAY_EVIDENCE.md`
- Raw: `evidence/live_workforce_governance_setu/governance_replay/phase4_policy_state.json`, `phase3_scenarios.json`
