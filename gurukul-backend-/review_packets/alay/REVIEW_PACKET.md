# Observability Handover Review Packet (DevOps/Alay)

**Project**: Gurukul Observability & Sovereign Inference Validation  
**Sovereign Sprint**: Provenance Closure, Educational Replay & Yotta Pilot  
**Author**: Alay Patel (DevOps) / Engineering Assistant  
**Workspace**: `c:\Users\ASUS\OneDrive\Desktop\BHIV-Tasks\Gurukul_Observability\gurukul-backend-`  

---

## 1. Entry Point
The entry points of the UniGuru intelligence and observability system are defined as follows:
- **Web App Chat Endpoint**: Mounts at `POST /api/v1/chat` in [chat.py](../backend/app/routers/chat.py).
- **Standalone Yotta Pilot Script**: Located at [yotta_pilot.py](../backend/runtime/yotta_pilot.py).
- **Validation Scenarios Runner**: Located at [run_sovereign_validation.py](../backend/scripts/run_sovereign_validation.py).

---

## 2. Runtime Flow
The UniGuru student query lifecycle follows these steps sequentially:
1. **Intake & Metadata Check**: Resolves board, medium, and class standard from user profile attributes.
2. **Telemetry Signal request**: Emits a `chat_request` telemetry event, containing the query and user preferences, which is automatically saved to SQLite log.
3. **Curriculum Retrieval**: Passes queries to the vector store (`VectorStoreService`) to extract relevant Balbharti/NCERT curriculum context.
4. **Prompt assembly & Inference**: Grounded prompts are sent to Llama models via `sovereign_lm_core.py`.
5. **Telemetry Signal response**: Emits a `chat_response_generated` telemetry event, containing the generated response, which is also saved to SQLite log.

---

## 3. Replay Flow
Replay runs through the `PranaReplayOrchestrator` in [prana_replay_orchestrator.py](../backend/app/services/prana_replay_orchestrator.py):
1. Reads all telemetry signals from database matching the `run_id`.
2. Groups events by `submission_id` to reconstruct the student's journey.
3. Re-runs curriculum retrieval (RAG) and LLM inference generation with the original student input/preferences.
4. Performs NLP comparison on the original and replayed outputs, evaluating BLEU and ROUGE metrics to verify similarity and logs results.

---

## 4. Provenance Verification
Telemetry signals undergo strict validation in [tantra_schema_validator.py](../backend/app/services/tantra_schema_validator.py):
- **Deterministic Hashing**: Validates `integrity_hash` using `PranaDeterminismService` (excluding volatile signature headers via `EXCLUDED_EXACT_KEYS`).
- **Signature verification**: Checks the HMAC-SHA256 signature `event_signature` using `TANTRA_API_KEY` (or the debug fallback key).
- **Metadata Enforcements**: Validates `source_verification` headers and `trace_chain_validation` formats.

---

## 5. Yotta Pilot
The lightweight standalone script [yotta_pilot.py](../backend/runtime/yotta_pilot.py) runs the entire query-RAG-inference-telemetry-replay pipeline. It acts as the target candidate candidate for Yotta ShaktiStudio, ensuring the workload is modular, lightweight, and completely portable.

---

## 6. Evidence
All validation runs and test suites are fully passing. The logs are stored in [SOVEREIGN_RUNTIME_PROOF.md](../alay/SOVEREIGN_RUNTIME_PROOF.md).

### 6.1 Validation Suite Execution
![Validation Suite Execution Log](../alay/evidence/validation_suite.png)

### 6.2 Yotta Pilot Run Execution
![Yotta Pilot Execution Proof](../alay/evidence/yotta_pilot.png)

### 6.3 Database Telemetry logs Ingestion
![SQLite Database Telemetry Record](../alay/evidence/database_telemetry.png)

### 6.4 Core Unit Tests
![Unit Tests Summary](../alay/evidence/unit_tests.png)

### Verification Commands:
```bash
# Execute standalone validation scenarios
python scripts/run_sovereign_validation.py

# Execute Yotta pilot script
python runtime/yotta_pilot.py

# Run unit tests
python -m pytest tests/test_convergence_convergence.py
python -m pytest tests/test_prana_replay_orchestrator.py
python tests/test_tantra_connectors.py
```

---

## 7. Known Risks
- **External Network Outages**: Groq inference fallback relies on external endpoints. If API keys are revoked or services go down, inference falls back to mock answers.
- **SQLite DB Lock**: SQLite will lock the file during write ingestion, potentially causing locking issues if multiple parallel high-velocity request flows execute simultaneously.

---

## 8. Next Steps
1. **Scale Hardening**: Migrate SQLite to PostgreSQL for distributed environments.
2. **Key Rotation**: Set up automated key rotations for the TANTRA signature validation keys via secret vaults.
3. **Pravah Endpoint Configuration**: Map a valid telemetry collector endpoint to route metrics out of local SQLite loops.

---

## 9. Instruction for Succeeding Developers
This codebase is completely documented and verification tests are modular. To continue development:
1. Review the service architecture in `backend/app/services/`.
2. To modify schemas, edit `PRAVAH_REQUIRED_FIELDS` in `tantra_schema_validator.py`.
3. To add custom mock triggers for test flows, update `prana_replay_orchestrator.py` generation fallbacks.
4. Execute `python scripts/run_sovereign_validation.py` to ensure modifications did not introduce regression.
