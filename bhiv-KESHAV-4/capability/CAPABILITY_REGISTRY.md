# KESHAV Capability Registry

## Capability Metadata
* **Capability ID**: `bhiv-keshav-dependency-intelligence`
* **Capability Name**: KESHAV
* **Capability Class**: Pure Intelligence Layer (Read-Only Compute)
* **Domain**: Dependency Management & Incident Resolution
* **Owner**: BHIV Operational Chariot
* **Current Version**: 1.0.0

## Consumer Matrix
| Consumer | Integration Phase | Status | Access Rights |
|----------|-------------------|--------|---------------|
| Sarathi (via RAJYA) | Phase 1 (Runtime) | Active | Read-Only |
| SETU | Phase 2 | Planned | Read-Only |
| Creator Core | Phase 2 | Planned | Read-Only |
| SETU PMC | Phase 3 | Planned | Read-Only |
| Samachar | Phase 3 | Planned | Read-Only |
| Marine Intelligence | Future | Pending | Read-Only |
| AIAIC | Future | Pending | Read-Only |

## Provider Matrix
| Provider Layer | Purpose | Status |
|----------------|---------|--------|
| TANTRA Pipeline | Trace and execution data provision | Active |

## Attachment Rules
* Capabilities must attach to KESHAV exclusively via the `POST /analyze` API or by directly invoking the `analyzer.keshav` python module within the canonical runtime.
* Consumers are forbidden from attempting to inject state, mutate the KESHAV runtime, or bypass TANTRA schema constraints.

## Upgrade Rules
* Upgrade compatibility is strictly governed by Semantic Versioning (SemVer).
* Downstream consumers (like Sarathi) are guaranteed backward compatibility for all `MINOR` and `PATCH` upgrades.
* `MAJOR` version upgrades require a formalized migration phase coordinated by the Governance Committee (GC).

## Version History
* **v1.0.0** (Current): Initial publication of KESHAV as a canonical ecosystem capability. TANTRA compliance achieved.

## Deprecation Policy
* A minimum of 90 days deprecation notice must be provided for any `MAJOR` version bump.
* Deprecated versions will remain actively supported (bug fixes only) until all known consumers have successfully migrated.

## Discovery Metadata
* **Tags**: `intelligence`, `dependency-graph`, `root-cause-analysis`, `tantra`, `bhiv`
* **Discovery URI**: `chariot://capabilities/bhiv-keshav-dependency-intelligence/v1`
