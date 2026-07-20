# Governance Exercise & Replay Evidence (Live WO/GE/SETU Sprint · Phase 3)

**Workflow position:** Step 3 of 11  
**Prerequisites:** Steps 1–2 (workforce context exists)  
**Next step:** Step 4 → `POLICY_REPLAY_VALIDATION.md`

---

## Execution method

1. Run three independent scenarios: **Leave**, **Visibility**, **Approval**.
2. Per scenario, execute full chain:
   `Policy Created → Evaluated → Challenge → Review → Complete → Override Propose → Override Apply → Decision → Replay`.
3. Scenario A (Leave): record superseding decision → 2-link replay chain.
4. Supplemental: consolidated replay packet via `run_capture_addendum.py` (one correlation id, 5 events).
5. Confirm: `GET /v1/decisions/replay?decision_id=<id>` returns expected chain length.

---

## Capture metadata

**Date**: 2026-06-27
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime code path; not deployed
**Auth type used**: API key (platform/admin)
**Status**: `live_capture` (local in-process runtime capture)
**Raw capture**: `evidence/live_workforce_governance_setu/governance_replay/phase3_scenarios.json`

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Scenario Narrative

Three independent, complete governance scenarios were executed end-to-end through the real runtime: **Leave**, **Visibility**, and **Approval** policy domains. Each followed the required flow `Policy Created → Policy Evaluated → Challenge Raised → Review Assigned → Review Completed → Override Proposed → Override Applied → Decision Recorded → Replay Generated`. Every evaluation produced a `deny` (the condition that motivates a challenge), each review was completed `upheld`, each override was proposed then applied, and a decision was recorded and replayed. The Leave scenario additionally recorded a superseding decision to demonstrate a genuine multi-link replay chain. Each scenario ran under its own correlation id so its audit trail is independently reconstructable.

## Per-scenario IDs (real, captured)

| Field | Scenario A — Leave | Scenario B — Visibility | Scenario C — Approval |
|---|---|---|---|
| correlation_id | `c8cd9063-697e-4259-9ec7-c821e0383e83` | `bab5ee03-1e19-4e1c-b72f-8c0ae57d1d2e` | `7dda13e6-1ffa-4147-aa99-505eb00b2ee2` |
| policy_id | `6a3fa580df4f34fc035c5629` | `6a3fa580df4f34fc035c5636` | `6a3fa580df4f34fc035c5641` |
| evaluation_id | `peval-ee3ebf1c0404` | `peval-09288dac4c15` | `peval-2ecdfa9ca9ff` |
| evaluation decision | deny (tenure 10 < 90) | deny (scope_match=false) | deny (explicit approval required) |
| challenge_id | `chl-879b1988d9e2` | `chl-f7814862a4a0` | `chl-4c8a3ddbaab8` |
| review_id | `rev-3c878a7f86df` | `rev-f836079fc251` | `rev-d820e128b861` |
| review outcome | upheld | upheld | upheld |
| override_id (workflow) | `wovr-4a2dfd7af7af` | `wovr-63624f468e2f` | `wovr-15db316d0f4a` |
| override status | applied | applied | applied |
| decision_id | `dec-502dd9179340` | `dec-b40efca0fdd0` | `dec-9f508b6e94b4` |
| superseding decision | `dec-847bc3155d34` | — | — |
| replay chain length | **2** | 1 | 1 |

## Step-by-step Evidence Table — Scenario A (Leave)

| Step | Endpoint | Response (key) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|
| Policy Created | `POST /v1/policies/definitions` | policy_id=…5629, policy_key=leave_policy | 200 | 10:27:12.168549Z |
| Policy Evaluated | `POST /v1/policies/evaluate` | evaluation_id=peval-ee3ebf1c0404, decision=deny | 200 | 10:27:12.181781Z |
| Challenge Raised | `POST /v1/governance/challenges` | challenge_id=chl-879b1988d9e2, status=open | 200 | 10:27:12.191214Z |
| Review Assigned | `POST /v1/governance/reviews` | review_id=rev-3c878a7f86df, status=assigned | 200 | 10:27:12.202620Z |
| Review Completed | `POST /v1/governance/reviews/{id}/complete` | outcome=upheld, challenge→resolved | 200 | 10:27:12.213996Z |
| Override Proposed | `POST /v1/governance/overrides` | override_id=wovr-4a2dfd7af7af, status=proposed | 200 | 10:27:12.224743Z |
| Override Applied | `POST /v1/governance/overrides/{id}/apply` | status=applied | 200 | 10:27:12.234864Z |
| Decision Recorded | `POST /v1/decisions` | decision_id=dec-502dd9179340 | 200 | 10:27:12.241391Z |
| Decision Superseded | `POST /v1/decisions` (supersedes prior) | decision_id=dec-847bc3155d34 | 200 | 10:27:12.252928Z |
| Replay Generated | `GET /v1/decisions/replay?decision_id=dec-847bc3155d34` | replay_type=supersedes_chain, **chain length=2** | 200 | 10:27:12.261450Z |

## Step-by-step Evidence Table — Scenario B (Visibility)

| Step | Endpoint | Response (key) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|
| Policy Created | `POST /v1/policies/definitions` | policy_id=…5636, visibility_policy | 200 | 10:27:12.269913Z |
| Policy Evaluated | `POST /v1/policies/evaluate` | evaluation_id=peval-09288dac4c15, decision=deny | 200 | 10:27:12.275373Z |
| Challenge Raised | `POST /v1/governance/challenges` | challenge_id=chl-f7814862a4a0 | 200 | 10:27:12.285145Z |
| Review Assigned | `POST /v1/governance/reviews` | review_id=rev-f836079fc251 | 200 | 10:27:12.290998Z |
| Review Completed | `POST …/complete` | outcome=upheld | 200 | 10:27:12.299391Z |
| Override Proposed | `POST /v1/governance/overrides` | override_id=wovr-63624f468e2f | 200 | 10:27:12.306422Z |
| Override Applied | `POST …/apply` | status=applied | 200 | 10:27:12.316218Z |
| Decision Recorded | `POST /v1/decisions` | decision_id=dec-b40efca0fdd0 | 200 | 10:27:12.322214Z |
| Replay Generated | `GET /v1/decisions/replay?decision_id=dec-b40efca0fdd0` | chain length=1 | 200 | 10:27:12.328001Z |

## Step-by-step Evidence Table — Scenario C (Approval)

| Step | Endpoint | Response (key) | HTTP | Timestamp (UTC) |
|---|---|---|---|---|
| Policy Created | `POST /v1/policies/definitions` | policy_id=…5641, approval_policy | 200 | 10:27:12.335607Z |
| Policy Evaluated | `POST /v1/policies/evaluate` | evaluation_id=peval-2ecdfa9ca9ff, decision=deny | 200 | 10:27:12.340560Z |
| Challenge Raised | `POST /v1/governance/challenges` | challenge_id=chl-4c8a3ddbaab8 | 200 | 10:27:12.349229Z |
| Review Assigned | `POST /v1/governance/reviews` | review_id=rev-d820e128b861 | 200 | 10:27:12.355368Z |
| Review Completed | `POST …/complete` | outcome=upheld | 200 | 10:27:12.362028Z |
| Override Proposed | `POST /v1/governance/overrides` | override_id=wovr-15db316d0f4a | 200 | 10:27:12.369673Z |
| Override Applied | `POST …/apply` | status=applied | 200 | 10:27:12.376511Z |
| Decision Recorded | `POST /v1/decisions` | decision_id=dec-9f508b6e94b4 | 200 | 10:27:12.384461Z |
| Replay Generated | `GET /v1/decisions/replay?decision_id=dec-9f508b6e94b4` | chain length=1 | 200 | 10:27:12.391522Z |

## Replay Confirmation

- **Scenario A** decision replay (`GET /v1/decisions/replay?decision_id=dec-847bc3155d34`) returned `replay_type=supersedes_chain` with a **2-link chain** `[dec-502dd9179340 → dec-847bc3155d34]`, proving superseded-decision reconstruction from the ledger.
- **Scenarios B & C** decision replays returned single-link supersedes chains for their recorded decisions.
- The decision-record (`POST /v1/decisions`) used the runtime endpoint cleanly (it accepts `challenge_id`, `review_id`, `trace_references`, and `supersedes` directly), so that endpoint was chosen over `/v1/governance/reviews/{id}/decision` (which takes query params only).

## Consolidated replay packet (supplemental — Review Feedback finding #5)

The reviewer's finding #5 ("Decision Ledger Needs Replay Demonstration") asks for a single **replay packet** reconstructing `Decision → Challenge → Review → Override → Final State`. The three scenarios above prove each link; this supplemental capture reconstructs the whole chain from **one correlation id** (`6fc87bbd-32a7-451b-b6be-bf677fcde457`) using two real replay surfaces. Raw: `evidence/live_workforce_governance_setu/addendum/multiorg_and_replay_packet.json`.

Packet object IDs (real): evaluation `peval-5d2d1a1f709c` → challenge `chl-24304516b790` → review `rev-3294164d3184` (**outcome=upheld** = Review/Final) → override `wovr-689f1967576e` (**status=applied** = Override/Final) → decision `dec-8dc496d8ca66`.

| Replay surface | Endpoint | Reconstructed sequence | Count | HTTP | Timestamp (UTC) |
|---|---|---|---|---|---|
| Workforce trace-replay | `GET /v1/workforce/trace-replay?correlation_id=6fc87bbd…` | policy_evaluate → challenge_create → review_assign → workflow_override_record → decision_record | 5 | 200 | 10:27:47.533450Z |
| Control Center audit-replay | `GET /v1/control-center/audit-replay?correlation_id=6fc87bbd…` | decision_record → workflow_override_record → review_assign → challenge_create → policy_evaluate (grouped, newest-first) | 5 | 200 | 10:27:47.540859Z |

This is a single, correlation-linked packet that ties the Decision back through Override, Review, Challenge to the originating policy evaluation — i.e. the governance lineage reconstructs in one query, not just per-endpoint. ("Final State" = review outcome `upheld` + override `applied` + recorded decision.) Note `review_complete` and `override_apply` do not themselves write audit rows in the current runtime, so they appear as state transitions on the review/override objects rather than as separate replay events — documented honestly rather than implied.

## Policy-conflict note (Review Feedback finding #4)

Finding #4 also lists "policy conflicts." The current `policy_engine` runtime evaluates one `policy_key` at a time against its own rules (`_evaluate_rules`); it has **no multi-policy conflict-resolution mechanism**. Per the two-additive-fixes-only constraint, no such feature was invented for this sprint. Policy-conflict resolution is therefore recorded as **not a present runtime capability / not yet proven** (carried in `REVIEW_PACKET.md` Risks and `POLICY_REPLAY_VALIDATION.md`), rather than fabricated.

## Known Limitations

- Local in-process runtime capture (see Phase 1 header).

## Cross-references

- Policy-state view of these same scenarios: `POLICY_REPLAY_VALIDATION.md`
- Lineage field proof for a governance decision: `LINEAGE_PROPAGATION_EVIDENCE.md`
- Raw: `evidence/live_workforce_governance_setu/governance_replay/phase3_scenarios.json`
