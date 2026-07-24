# SCHEMA GOVERNANCE
## Phase 4 — Schema Governance Closure

**Service:** KESHAV-4 Propagation Engine
**Canonical Owner:** Rajaryan
**Date:** 2026-05-26

---

## Schema Ownership

| Schema | Owner | Location | Authority |
|---|---|---|---|
| `PropagationInput` | **KESHAV-4 (Rajaryan)** | `KESHAV-4/shared_schemas/schemas.py` | Full. No external party may modify. |
| `PropagationOutput` | **KESHAV-4 (Rajaryan)** | `KESHAV-4/shared_schemas/schemas.py` | Full. No external party may modify. |
| `PropagationContractViolation` | **KESHAV-4 (Rajaryan)** | `KESHAV-4/shared_schemas/schemas.py` | Full. Error code vocabulary is KESHAV-owned. |
| `KSMLInput` | **text-risk-scoring-service** | `text-risk-scoring-service/app/enforcement_schemas.py` | NOT owned by KESHAV. Consumed read-only. |
| `ContextSignal` | **text-risk-scoring-service** | `text-risk-scoring-service/app/enforcement_schemas.py` | NOT owned by KESHAV. Consumed read-only. |
| `SourceSystem` | **text-risk-scoring-service** | `text-risk-scoring-service/app/enforcement_schemas.py` | NOT owned by KESHAV. Consumed read-only. |
| `ExecuteActionResponse` | **text-risk-scoring-service** | `text-risk-scoring-service/app/enforcement_schemas.py` | NOT owned by KESHAV. Consumed read-only. |

---

## Source-of-Truth Schema Location

| Schema Domain | Source of Truth | Path |
|---|---|---|
| **KESHAV propagation schemas** | `shared_schemas/schemas.py` in `C:\blackhole\KESHAV-4` | Single file, 29 lines. Contains `PropagationInput`, `PropagationOutput`, `PropagationContractViolation`. |
| **TANTRA enforcement schemas** | `app/enforcement_schemas.py` in `C:\blackhole\text-risk-scoring-service` | Single file, 309 lines. Contains `KSMLInput`, `ContextSignal`, `SourceSystem`, `EvaluateActionRequest`, `SarathiEvaluateResponse`, `ExecuteActionResponse`. |

**There is NO third location.** No duplicate schema files exist. No local forks. No cached copies.

**Prior duplicate locations (all DEPRECATED and removed from active use):**
- `KESHAV-3/app/schemas.py` — contained `PropagationOutput` only. DEPRECATED.
- `KESHAV-1/engine.py` — no schemas (raw dicts). DEPRECATED.
- `KESHAV-2/engine.py` — no schemas (raw dicts with manual `ValueError`). DEPRECATED.

---

## Compatibility Policy

### Intra-KESHAV Compatibility

| Rule | Enforcement |
|---|---|
| `PropagationInput` and `PropagationOutput` must remain structurally synchronized | Both models use `extra="forbid"`. Any field addition/removal causes immediate Pydantic `ValidationError`, surfaced as `PropagationContractViolation("SCHEMA_MISMATCH", ...)`. |
| All string fields require `min_length=1` | Empty strings are rejected at the Pydantic boundary. No silent empty-string propagation. |
| `severity` is constrained to `Literal["LOW", "MEDIUM", "HIGH"]` | Any other value is rejected by Pydantic. No heuristic severity levels. |
| `dependency_graph` is typed as `Dict[str, List[str]]` | Non-dict or non-list values are rejected. No loose typing. |

### Cross-Service Compatibility (KESHAV → TANTRA)

| Rule | Enforcement |
|---|---|
| KESHAV output maps into `KSMLInput` via the integration layer | The mapping is performed in `shared_tests/test_live_integration.py` and `shared_tests/test_end_to_end_proof.py`. It is NOT automatic — it requires explicit construction of `KSMLInput` by the caller. |
| KESHAV does NOT directly import or depend on `KSMLInput` at runtime | The engine module (`app/engine.py`) imports only from `shared_schemas.schemas`. Cross-service imports happen only in tests. |
| `ContextSignal.value` must be in `[0.0, 1.0]` | KESHAV maps severity to signal value via `0.9 if severity == "HIGH" else 0.5`. This mapping is in the integration test, not in the engine. |

---

## Version Strategy

| Aspect | Policy |
|---|---|
| **Schema version identifier** | `model_config = ConfigDict(extra="forbid")` serves as implicit version enforcement. Any structural change to the schema is immediately breaking. |
| **Semantic versioning** | Not currently tracked numerically. The schema is versioned implicitly by its structural hash (any field add/remove/rename is a breaking change). |
| **Backward compatibility** | NOT guaranteed. KESHAV uses `extra="forbid"`, which means any new field is a breaking change in both directions. This is intentional — silent field evolution is more dangerous than explicit breakage. |
| **Forward compatibility** | NOT guaranteed. Same rationale as above. |

---

## Upgrade Handling

### Upgrade Procedure (KESHAV-Owned Schemas)

1. **Modify** `shared_schemas/schemas.py` with the new field/type/constraint.
2. **Run** `pytest shared_tests/ -v` to identify all breakage points.
3. **Fix** all tests that reference the changed field.
4. **Run** the full 33-test suite — all must pass.
5. **Update** `REVIEW_PACKET.md` with the new schema definition.
6. **Commit** with a descriptive message: `schema: add/remove/modify <field> in <model>`.

### Upgrade Procedure (TANTRA-Owned Schemas Consumed by KESHAV)

1. **Pull** the latest `text-risk-scoring-service` changes.
2. **Run** `pytest shared_tests/test_live_integration.py shared_tests/test_end_to_end_proof.py -v` to identify breakage.
3. **Fix** the integration mapping code in the test files.
4. **Do NOT modify** `enforcement_schemas.py` — it is not KESHAV-owned.
5. **Do NOT create** a local fork or cached copy of the TANTRA schemas.

---

## Deprecation Strategy

| Rule | Policy |
|---|---|
| **Field deprecation** | Fields are never silently removed. Removal is a breaking change enforced by `extra="forbid"`. |
| **Schema deprecation** | Deprecated schemas are moved to DEPRECATED repositories (KESHAV-1, KESHAV-2, KESHAV-3). They are never deleted but are no longer imported or tested. |
| **Schema migration** | There is no migration framework. Schema changes are atomic — old schema is replaced by new schema in a single commit. |

---

## Breakage Response Model

| Scenario | Response |
|---|---|
| **KESHAV schema change breaks KESHAV tests** | Fix tests. Schema change is intentional. Tests must conform to the new schema. |
| **KESHAV schema change breaks TANTRA integration tests** | Fix the integration mapping in `test_live_integration.py` / `test_end_to_end_proof.py`. Coordinate with TANTRA pipeline owner if the mapping semantics change. |
| **TANTRA schema change breaks KESHAV integration tests** | Fix the integration mapping in KESHAV tests. Do NOT fork or cache the TANTRA schema. |
| **Unknown field appears in input** | Rejected instantly by Pydantic `extra="forbid"`. `PropagationContractViolation("SCHEMA_MISMATCH", ...)` raised. |
| **Missing required field in input** | Rejected instantly by Pydantic. `PropagationContractViolation("SCHEMA_MISMATCH", ...)` raised. |
| **Wrong type in input** | Rejected instantly by Pydantic. `PropagationContractViolation("SCHEMA_MISMATCH", ...)` raised. |

---

## Provenance Guarantees

| Guarantee | Evidence |
|---|---|
| **Schema origin is traceable** | `PropagationInput` and `PropagationOutput` exist in exactly one file: `shared_schemas/schemas.py`. No copies, no caches, no re-exports through other modules. |
| **Schema is not generated** | Schemas are hand-written Pydantic models. No code generation, no reflection, no dynamic schema creation. |
| **Schema is not inherited** | Neither `PropagationInput` nor `PropagationOutput` inherits from any base class other than `pydantic.BaseModel`. No mixin pollution. |
| **Schema is not mutated at runtime** | Both models use `ConfigDict(extra="forbid")`. Pydantic v2 models are immutable after construction. No `__setattr__` override. |
| **Schema coupling is explicit** | KESHAV's `engine.py` imports from `shared_schemas.schemas`. Integration tests import from `text-risk-scoring-service/app/enforcement_schemas`. Both import paths are visible in source code, not hidden behind dynamic imports or plugin systems. |

---

## Anti-Silent-Authority Declaration

KESHAV-4 schemas carry **NO silent authority**:

- They do NOT make enforcement decisions.
- They do NOT trigger actions.
- They do NOT persist state.
- They do NOT communicate with external services.
- They do NOT contain business logic beyond structural validation.

The schemas are **passive structural contracts**. They validate input shape and output shape. Nothing more.
