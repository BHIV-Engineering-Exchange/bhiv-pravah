# Open Work Register

## Completed work

- Core pipeline orchestration implemented in `integration_bridge.py`
- Artifact storage system implemented in `bhiv_bucket.py`
- Creator Core blueprint generation implemented in `creator-core/Core-Integrator-Sprint-1.1/creator_core_engine/`
- Service orchestration implemented in `start_all.py` and `core/service_orchestrator.py`
- Health check and deployment validation implemented in `test_services.py` and `deploy_and_test.py`
- Full TANTRA flow simulation implemented in `full_tantra_flow_test.py`
- Audit and architecture documentation available under `audit_packets/`

## Partially completed work

- Prompt Runner exists as a stub but not a full production prompt transformer
- CET, Sarathi, and Gate are present as validation harness stages but not deployable services
- Replay system has bucket trace retrieval and core replay endpoints, but distributed replay is not fully implemented
- Remote deployment guidance exists, but end-to-end remote validation is incomplete
- TTG/TTV/Gurukul product labels exist in metadata, but runtime connectors are not built

## Future work

1. Replace Prompt Runner stub with a real prompt processing service.
2. Promote CET, Sarathi, and Gate from simulation to deployable microservices.
3. Build full distributed replay infrastructure and validation nodes.
4. Add explicit schema definitions for instruction, blueprint, execution, and result artifacts.
5. Harden service-to-service security and request validation.
6. Implement true TTG/TTV/Gurukul integration surfaces.
7. Add a centralized observability dashboard for service health and artifact traceability.
8. Create a production-ready deployment pipeline for remote hosting.

## Blocked work

- Real Prompt Runner implementation: blocked by missing prompt processing codebase
- CET/Sarathi/Gate production deployment: blocked by lack of service definitions and runtime contracts
- Distributed replay: blocked by missing distributed validation engine and logging standards
- Remote deployment completion: blocked by incomplete remote service integration and environment validation

## Technical debt

- Mixed config management across `config/services.yml`, `.env`, and service-local config
- Prompt Runner stub is not production-ready
- In-memory fallback replay in Integration Bridge is not durable
- Audit and replay logs are not normalized to a formal proof format
- Lack of schema versioning for artifact payloads beyond ad hoc values

## Constitutional concerns

- No full enforcement layer for CET/Sarathi/Gate outside the test harness
- Deterministic replay claims are not fully backed by distributed proof
- Artifact immutability relies on developer discipline rather than a hardened contract store
- Service-to-service authorization is not fully defined in the current architecture

## Integration concerns

- Integration Bridge must trust the prompt runner and creator core response shapes
- Bucket availability is a single point of failure for artifact persistence
- BHIV Core replay depends on internal memory and gateway state
- TTG/TTV/Gurukul labels are not yet supported by external runtime adapters

## Priority order

1. Prompt Runner production implementation
2. CET/Sarathi/Gate deployable runtime
3. Distributed replay infrastructure
4. Remote deployment validation
5. Schema and contract hardening

## Owners

- `integration_bridge.py` and full pipeline: Owner TBD (should be Siddhesh/Karan)
- Creator Core: Owner TBD (should be Siddhesh/Karan)
- BHIV Core runtime: Owner TBD (should be Siddhesh/Karan)
- Bucket artifact storage: Owner TBD (should be Siddhesh/Karan)
- Audit and replay proofing: Owner TBD (should be Siddhesh/Karan)

## Dependencies

- `creator-core/Core-Integrator-Sprint-1.1/main.py` depends on local Creator Core configuration
- `integration_bridge.py` depends on Prompt Runner, Creator Core, BHIV Core, and Bucket
- BHIV Core depends on `config/config.py` and optional Noopur/Video integration
- Replay depends on bucket trace persistence and artifact chain completeness

## Notes

This register is the single source of open system work. It should be updated whenever a new item is started, blocked, or completed.
