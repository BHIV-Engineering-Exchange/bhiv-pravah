# Frequently Asked Questions

## 1. What is Prompt Runner?
Prompt Runner is the component that converts a user prompt into a structured instruction payload. In this repository, it is implemented as a stub server in `prompt-runner01/run_server.py`.

## 2. Why does Creator Core exist?
Creator Core transforms prompt instructions into blueprint envelopes. It bridges prompt semantics and executable plan structure, preparing data for BHIV Core execution.

## 3. Why do we need CET?
CET (Constitutional Execution Translator) is the architectural stage that converts blueprints into deterministic, replay-safe execution contracts. It ensures the execution plan can be audited and re-run consistently.

## 4. What does Sarathi validate?
Sarathi is the authority validation layer. It checks whether a contract is valid, authorized, and safe to execute. In this repo, it is represented in the test harness in `full_tantra_flow_test.py`.

## 5. What is a replay?
A replay is the process of reconstructing a previously executed pipeline from stored artifacts. It is used to verify determinism and traceability.

## 6. What is a deterministic replay?
Deterministic replay means the same input and artifact chain produces the same output and hash. The system computes a deterministic hash over instruction, blueprint, and execution payloads.

## 7. What happens if Bucket is unavailable?
If Bucket is unavailable, artifact storage fails and the Integration Bridge logs warnings. The pipeline may continue in memory, but trace persistence and replay capabilities will be lost.

## 8. How does trace continuity work?
Trace continuity works by assigning a single `trace_id` at pipeline start and including it in every artifact. The Bucket stores a trace file linking all artifacts in order.

## 9. How does distributed replay work?
Distributed replay is architected as a proof and audit concept in `audit_packets/replay_logs`, but not fully implemented as a live distributed runtime in this repository.

## 10. How is TTG integrated?
TTG integration is represented as product target metadata in Creator Core. The current code does not include a production TTG runtime connector.

## 11. How is Gurukul integrated?
Gurukul is currently an architectural target label in Creator Core blueprint payloads, not a implemented runtime integration.

## 12. How are contracts validated?
Contracts are validated in the test harness by structural checks and hash consistency. A production contract validator service is not yet deployed.

## 13. What is the Integration Bridge?
The Integration Bridge orchestrates the end-to-end pipeline: Prompt Runner → Creator Core → BHIV Core → Bucket. It is implemented in `integration_bridge.py`.

## 14. What does BHIV Core do?
BHIV Core is the execution engine. It receives blueprint payloads, performs module routing, executes logic, and exposes replay endpoints.

## 15. What is BHIV Bucket?
BHIV Bucket is an append-only artifact storage system. It stores instructions, blueprints, executions, results, and trace indexes.

## 16. What artifacts are stored?
Artifacts include `instruction`, `blueprint`, `execution`, and `result`. Each artifact is stored as JSON and linked by `trace_id`.

## 17. Where are trace logs stored?
Trace index files are stored under `bhiv_bucket/traces/`. They contain artifact IDs and type mappings.

## 18. What is `trace_id`?
`trace_id` is the unique identifier assigned to one pipeline execution. It ties all related artifacts together.

## 19. What is `artifact_id`?
`artifact_id` uniquely identifies a stored artifact within the bucket, such as `instruction_...` or `blueprint_...`.

## 20. What does `full_tantra_flow_test.py` validate?
It validates the full architectural flow, including Prompt Runner, Creator Core, CET, Sarathi, Gate, Execution, Bucket, InsightFlow, and Replay.

## 21. What is InsightFlow?
InsightFlow is the telemetry layer used by Creator Core to emit event data. It writes telemetry records to `db/creator_core_telemetry/insightflow_events.jsonl`.

## 22. How do I start all services?
Use `python start_all.py`, which launches services in dependency order using `core/service_orchestrator.py`.

## 23. How do I test service health?
Run `python test_services.py` to verify each service health endpoint.

## 24. Which ports are used?
Default ports are: Creator Core `8000`, BHIV Core `8001`, Prompt Runner `8003`, Integration Bridge `8004`, and Bucket `8005`.

## 25. How do I configure service URLs?
Service URLs are set via environment variables and validated in `creator-core/Core-Integrator-Sprint-1.1/config/service_urls.py` and `config/services.yml`.

## 26. What is the difference between local and remote deployment?
Local deployment runs all services on localhost. Remote deployment runs services on separate hosts, requiring correct URL configuration and network access.

## 27. What should I do if the prompt runner fails?
Check `prompt-runner01/run_server.py`, ensure the service is running, and verify `/health` returns 200.

## 28. What if Creator Core returns an invalid response?
Creator Core validates instruction schemas and returns HTTP 500 if the response shape is invalid. Check `creator_core_engine/service.py` logs.

## 29. What if BHIV Core rejects a request?
BHIV Core performs security validation and gateway response sanitization. Validate your request `user_id` and request structure.

## 30. How do I inspect bucket contents?
Browse the `bhiv_bucket/` directory and use `GET /bucket/artifact/{artifact_id}` or `GET /bucket/trace/{trace_id}`.

## 31. Can artifacts be modified after storage?
No. The Bucket is append-only and must not modify existing stored artifacts.

## 32. What is deterministic hash?
A deterministic hash is a checksum computed from instruction, blueprint, and execution payloads to prove replay consistency.

## 33. Where is hash computed?
It is computed in `integration_bridge.py` inside `_compute_hash()`.

## 34. What are replay endpoints in BHIV Core?
BHIV Core exposes `/replay/{instruction_id}`, `/replay/validate/{instruction_id}`, and `/replay/statistics`.

## 35. What if `trace_id` is missing?
If a trace ID is missing, the pipeline cannot reconstruct the artifact chain. Ensure it is created early in Integration Bridge.

## 36. What is `full_handover_packet_v1.md`?
It is the final review packet summarizing the handover and acceptance status.

## 37. What configuration files matter most?
`config/services.yml`, `.env.integration_bridge`, `creator-core/Core-Integrator-Sprint-1.1/.env.example`, and `config/config.py`.

## 38. Where are service dependencies defined?
Service dependencies are defined in `config/services.yml` and used by `core/service_orchestrator.py`.

## 39. What is `core/service_mesh.py`?
It provides health and connection helpers for the orchestrator and service management.

## 40. What is `deploy_and_test.py`?
A helper script that verifies service readiness, starts services, and checks runtime conditions.

## 41. What if the bucket trace file is inconsistent?
Check `bhiv_bucket/traces/{trace_id}.json` and stored artifact IDs. The trace index must match artifact files.

## 42. Are TTG/TTV/Gurukul implemented?
Not fully. They are present as product target labels and architectural intentions, but not as live runtime connectors.

## 43. How is the `artifact_chain` represented?
In Integration Bridge output, `artifact_chain` maps artifact labels to stored artifact IDs.

## 44. What is the `pipeline_result`?
`pipeline_result` is the assembled final result returned by Integration Bridge after execution.

## 45. Does the system support video services?
BHIV Core has video service configuration, but it is optional and not core to the handover pipeline.

## 46. What is `NOOPUR`?
A toggleable remote integration option in BHIV Core. It is disabled by default unless `INTEGRATOR_USE_NOOPUR=true`.

## 47. How do I update the prompt runner URL?
Set the `PROMPT_RUNNER_URL` environment variable in `.env.integration_bridge` or `.env` as appropriate.

## 48. Where are audit artifacts stored?
Audit artifacts are stored under `audit_packets/`, including architecture, replay logs, and governance documentation.

## 49. What should I do if I need to continue development?
Start by reading the `README.md`, `SYSTEM_ARCHITECTURE_GUIDE.md`, and `REPOSITORY_MAP.md`. Then use `start_all.py` and `test_services.py` to validate runtime behavior.

## 50. How do I confirm acceptance?
The final review packet `review_packets/full_handover_packet_v1.md` contains acceptance statements from Siddhesh and Karan.
