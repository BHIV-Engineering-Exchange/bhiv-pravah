# KESHAV Schema Registry

## Schema Identifiers
* **Input Schema Version**: `v1.0.0`
* **Output Schema Version**: `v1.0.0`
* **Schema Format**: JSON (Strictly typed)

## Ownership Metadata
* **Authoritative Owner**: MDU (Metadata Definition Unit)
* **Custodian**: BHIV Operational Chariot
* **Governance**: All schema mutations must be validated by the GC (Governance Committee).

## Replay Metadata
* **Determinism Stamp**: All schema payloads must contain a deterministic timestamp representing the exact moment of execution completion.
* **Immutability Guarantee**: Once an output schema is generated for a specific `trace_id` and `execution_id`, it is cryptographically guaranteed to reproduce exactly 10/10 times upon replay with identical inputs.

## Provenance Metadata
* **Source Lineage**: The KESHAV capability must never fabricate data. All nodes analyzed must trace back directly to the `tasks` defined in the input schema.
* **Execution Traceability**: The `execution_id` must be preserved precisely as received to maintain strict provenance across the TANTRA pipeline.

## Compatibility Metadata
* **Forward Compatibility**: Schemas are designed to be additive. New fields may be appended to the output contract in `MINOR` versions without breaking existing consumers.
* **Strict Validation**: Extra fields in the input schema (not defined in the TANTRA contract) will be discarded or result in a deterministic rejection (400), ensuring strict hygiene.
* **No Breaking Removals**: Fields defined in `v1.0.0` cannot be removed or renamed without a `MAJOR` version upgrade and GC approval.
