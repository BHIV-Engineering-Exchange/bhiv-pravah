# Canonical Chain Identity Lock

Task: Canonical Live Trace Convergence Lock + Full TANTRA Chain Proof + Final Integration Handover

Phase: 1 - Canonical Identifier Lock

Status: LOCKED

## Purpose

This document locks one canonical TANTRA execution chain identity for CET ecosystem convergence validation.

The locked identity is the only identity set to be used for the final continuity proof across:

```text
Core -> CET -> Sarathi -> Bridge -> Runtime -> InsightFlow -> Bucket
```

No boundary may regenerate, alias, substitute, normalize, or replace these identifiers. Any mismatch is a chain discontinuity and must fail closed.

## Locked Identity

| Field | Locked value |
| --- | --- |
| `execution_id` | `exec-tantra-001` |
| `trace_id` | `trace-tantra-001` |
| `cet_hash` | `89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801` |
| `schema_version` | `1.0` |
| `contract_version` | `TANTRA-CONVERGENCE-v1` |
| `bucket_key` | `b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80` |
| `flow_hash` | `6b26710573ce186585f5f3ea7a952f8ba351ee535b22d3b193ab12b1749c5f11` |

## Source Evidence

| Evidence surface | File | Locked fields proved |
| --- | --- | --- |
| End-to-end execution proof | `end_to_end_execution_proof.json` | `execution_id`, `trace_id`, `cet_hash`, `flow_hash`, stage continuity |
| Replay stability proof | `replay_proof.json` | stable `trace_id`, stable `cet_hash`, stable `flow_hash`, 0 drift |
| Bucket truth artifact | `bucket_truth/b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80.json` | persisted SUM-SCRIPT identity and byte-identical replay source |
| Mutation rejection proof | `mutation_rejection_proof.json` | fail-closed visibility for mutated `trace_id`, `execution_id`, `cet_hash`, contract body |
| Full flow driver | `python/tantra_full_flow.py` | executable chain used to produce proof artifacts |

## Boundary Lock Matrix

| Boundary | Required identifier state | Evidence |
| --- | --- | --- |
| Core payload | `decision_id` is `exec-tantra-001`; `trace_id` is `trace-tantra-001`; schema envelope version is `1.0` | Stage `1_ksml_validation` in `end_to_end_execution_proof.json` |
| CET compile | emits same `execution_id` and `trace_id`; computes locked `cet_hash` once | Stage `2_cet_compilation` |
| SUM-SCRIPT seal | recomputes and confirms locked `cet_hash`; preserves locked `trace_id` | Stage `3_sum_script_sealing` |
| Sarathi validation | receives intact SUM-SCRIPT; preserves locked `execution_id`, `trace_id`, and `cet_hash` | Stage `4_sarathi_validation` |
| Sarathi enforcement | issues enforcement decision without changing locked identifiers | Stage `5_sarathi_enforcement` |
| Bridge validation | validates contract, enforcement token, bucket reference, and locked hash continuity | Stage `6_bridge_validation` |
| Runtime execution | consumes the locked contract and returns result with same `execution_id`, `trace_id`, and `cet_hash` | Stage `7_execution_adapter` |
| InsightFlow | records append-only descriptive lineage with same `execution_id`, `trace_id`, and `cet_hash`; no authority fields | Stage `8_insightflow_lineage` |
| Bucket write | persists immutable SUM-SCRIPT under locked `bucket_key` | Stage `9_bucket_write` |
| Bucket replay | cold-read reconstruction returns byte-identical SUM-SCRIPT with same `execution_id`, `trace_id`, and `cet_hash` | Stage `10_bucket_replay` |

## Canonical Envelope

All live handoffs for this locked chain must preserve the following envelope metadata alongside the sealed SUM-SCRIPT or boundary decision artifact:

```json
{
  "execution_id": "exec-tantra-001",
  "trace_id": "trace-tantra-001",
  "cet_hash": "89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801",
  "schema_version": "1.0",
  "contract_version": "TANTRA-CONVERGENCE-v1"
}
```

The persisted SUM-SCRIPT for this chain is stored at:

```text
bucket_truth/b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80.json
```

## Continuity Rules

1. `execution_id` must originate from Core and remain `exec-tantra-001` through Bucket replay.
2. `trace_id` must originate from Core and remain `trace-tantra-001` through every observability and truth surface.
3. `cet_hash` must originate at CET seal and remain `89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801` from Sarathi onward.
4. `schema_version` must remain `1.0` in every envelope that carries this chain identity.
5. `contract_version` must remain `TANTRA-CONVERGENCE-v1` in every envelope that carries this chain identity.
6. `bucket_key` must remain the replay truth reference for the sealed SUM-SCRIPT.
7. Any mutation, missing identifier, regenerated trace, alias trace, or hash mismatch invalidates the chain.

## Rejection Visibility Requirement

If any boundary rejects this chain, the rejection artifact must include:

| Field | Required value or rule |
| --- | --- |
| `execution_id` | original locked value, when available |
| `trace_id` | original locked value, when available |
| `cet_hash` | original locked value, when available after CET seal |
| `boundary` | rejecting boundary name |
| `validation_status` | `rejected` |
| `rejection_reason` | explicit reason |
| `fail_closed` | `true` |

The mutation proof confirms that post-seal mutation attempts against `trace_id`, `execution_id`, `cet_hash`, step content, and structure are rejected before execution.

## Phase 1 Verdict

Phase 1 is locked.

The canonical chain identity for final convergence validation is:

```text
exec-tantra-001 / trace-tantra-001 / 89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801
```

This identity must be the single correlation key set for every remaining integration artifact and handover packet in the final TANTRA convergence chain.
