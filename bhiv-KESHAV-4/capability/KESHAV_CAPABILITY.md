# KESHAV Capability Specification

## Metadata
* **Capability ID**: `bhiv-keshav-dependency-intelligence`
* **Capability Name**: KESHAV (Dependency Intelligence)
* **Owner**: BHIV Operational Chariot
* **Version**: 1.0.0
* **Lifecycle Status**: Published

## Purpose
KESHAV acts as the canonical deterministic dependency intelligence layer for the BHIV Operational Chariot. It provides algorithmic diagnosis, graph traversal, and root-cause determination for failure traces, strictly conforming to the TANTRA ecosystem contracts. It operates as a pure intelligence capability without side effects.

## Interface Specifications
* **Inputs**: TANTRA standard Input Contract (Trace metadata, task definitions, constraint failure details, propagation graphs).
* **Outputs**: TANTRA standard Output Contract (Root cause diagnosis, resolution signals, calculated impact scores, severity levels, deterministic timestamping).

## Authority Boundary Declaration
* **Authority Owned**: 
  - Absolute authority over algorithmic diagnosis, dependency graph traversal, and root-cause determination (Intelligence domain).
* **Authority NOT Owned**: 
  - Zero authority over policy decision (RAJYA domain).
  - Zero authority over enforcement (Sarathi domain).
  - Zero authority over physical execution actions (Core domain).
  - Zero authority over persistence and state semantics (Bucket domain).
* **Execution Rights**: 
  - Strict read-and-compute execution rights over the provided `input_data`. 
  - KESHAV possesses NO physical execution rights or external manipulation capabilities outside its own isolated compute sandbox.
* **Authority Ceiling**: 
  - KESHAV's authority ceiling is strictly capped at generating the `keshav_output` payload. It cannot bypass RAJYA, mutate upstream trace identity (`trace_id`), or force downstream enforcement by Sarathi.

## Ecosystem Placement
### Consumers
* **Current Runtime Consumer**:
  - Sarathi (via RAJYA integration)
* **Future Consumers**:
  - SETU
  - Creator Core
  - Project Management (SETU PMC)
  - Samachar
  - Marine Intelligence
  - AIAIC
  - Future TANTRA capabilities

### Dependencies
* **Upstream**: None (pure read-only compute capability).
* **Governance**: 
  - TMS defines placement.
  - GC validates authority.
  - MDU validates schemas and provenance.

### Integration Details
* **Attachment Modes**: 
  - Asynchronous / Synchronous Network API (`/analyze`)
  - Standalone compute container execution
* **Compatibility Rules**:
  - All input and output must rigidly conform to the TANTRA input/output schemas without mutation.
  - Must not mutate inputs during processing.
